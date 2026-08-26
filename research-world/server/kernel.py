from __future__ import annotations

import json
import math
import secrets
from dataclasses import dataclass, field
from inspect import isawaitable
from pathlib import Path

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

from .admission import (
    AdmissionPolicy,
    AdmissionVerdict,
    PendingAdmissionPolicy,
    validate_claims,
    validate_project_claim_ids,
)
from .artifacts import ArtifactIntegrityError, ArtifactStore
from .observations import observation_submission
from .presets import agent_draft, require_tools_ready
from .report_delivery import MAX_EVIDENCE_BYTES, artifact_display, render_html, validate_html
from .reporting import (
    REPORT_INPUT_TOKEN_BUDGET,
    assess_delivery,
    blocked_projection,
    evidence_kind,
    normalized_checked_at,
    projection_envelope,
    safe_artifact_id,
    safe_narrative,
    safe_node_id,
)
from .world import World, node_text


@dataclass(frozen=True)
class KernelCommand:
    tag: str
    project_id: str | None = None
    values: dict = field(default_factory=dict)


@dataclass(frozen=True)
class KernelQuery:
    tag: str
    project_id: str | None = None
    values: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RunLease:
    run_id: str
    project_id: str


class ResearchKernel:
    def __init__(
        self,
        world: World,
        *,
        projects_root: Path,
        runtime=None,
        agents=None,
        pipelines=None,
        admission=None,
    ):
        self._world = world
        self._projects_root = Path(projects_root)
        self._runtime = runtime
        self._agents = agents
        self._pipelines = pipelines
        self._admission: AdmissionPolicy = admission or PendingAdmissionPolicy()
        self._threads = _thread_manager(world, runtime, agents)
        if runtime is not None:
            runtime.bind_kernel(self)

    async def command(self, command: KernelCommand):
        handler = getattr(self, f"_command_{command.tag}", None)
        if handler is None:
            raise ValueError(f"unknown kernel command: {command.tag}")
        result = handler(command)
        return await result if isawaitable(result) else result

    async def query(self, query: KernelQuery):
        handler = getattr(self, f"_query_{query.tag}", None)
        if handler is None:
            raise ValueError(f"unknown kernel query: {query.tag}")
        result = handler(query)
        return await result if isawaitable(result) else result

    def run(self, run_id: str) -> dict:
        from .workflows import default_engine

        run = self._world.run(run_id)
        return default_engine(self._world, run["project_id"], self).run(run_id)

    def _command_create_project(self, command: KernelCommand) -> dict:
        _validate_project(command.values)
        workspace = _allocate_workspace(self._projects_root)
        return self._create_project(command.values, workspace)

    def _command_set_auto(self, command: KernelCommand) -> dict:
        return self._world.set_auto(
            _project_id(command), bool(command.values["enabled"])
        )

    def _command_submit_node(self, command: KernelCommand) -> dict:
        return self._submit_node(_project_id(command), command.values)

    def _command_resolve_admission(self, command: KernelCommand) -> dict:
        allowed = {"node_id", "decision", "reason", "rebuttal"}
        _validate_fields(command.values, allowed, {"node_id", "decision"})
        project_id = _project_id(command)
        node = self._project_node(project_id, command.values["node_id"])
        verdict = _admission_verdict(command.values)
        return self._apply_admission(node, verdict)

    def _command_add_edge(self, command: KernelCommand) -> dict:
        value, project_id = command.values, _project_id(command)
        _validate_fields(
            value, {"source", "target", "polarity"}, {"source", "target", "polarity"}
        )
        self._admitted_node(project_id, value["source"])
        self._admitted_node(project_id, value["target"])
        return self._world.add_edge(value["source"], value["target"], value["polarity"])

    def _command_start_run(self, command: KernelCommand) -> dict:
        value = command.values
        allowed = {"node_id", "pipeline_id", "payload"}
        _validate_fields(value, allowed, {"node_id", "pipeline_id"})
        project_id = _project_id(command)
        node = self._admitted_node(project_id, value["node_id"])
        payload = _run_payload(value.get("payload", {}))
        self._validate_run_context(project_id, payload)
        pipeline = self._require_pipelines().get(value["pipeline_id"])
        return self._world.create_run(project_id, node["id"], pipeline, payload)

    def _command_confirm_run(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"run_id"}, {"run_id"})
        return self._world.queue_run_signal(
            command.values["run_id"], {"kind": "confirm_step"}
        )

    def _command_resolve_run(self, command: KernelCommand) -> dict:
        fields = {"run_id", "decision", "reason"}
        _validate_fields(command.values, fields, fields)
        run = self._world.run(command.values["run_id"])
        gate = run["payload"].get("_pipeline", {}).get("gate") or {}
        signal = _resolution_signal(gate, command.values)
        return self._world.queue_run_signal(run["id"], signal)

    def _command_observation(self, command: KernelCommand) -> dict:
        if "lineage_id" in command.values:
            raise ValueError("observation rejects fields: lineage_id")
        submission = observation_submission(command.values)
        artifacts = ArtifactStore(self._world.artifacts_root, _project_id(command))
        for artifact_id in submission["payload"]["artifact_ids"]:
            artifacts.get(artifact_id)
        return self._submit_node(_project_id(command), submission)

    def _command_capture_artifact(self, command: KernelCommand) -> dict:
        project_id = _project_id(command)
        self._world.project(project_id)
        value = command.values
        _validate_fields(value, {"content", "media_type"}, {"content", "media_type"})
        if not isinstance(value["content"], bytes):
            raise TypeError("artifact content must be bytes")
        if not isinstance(value["media_type"], str) or not value["media_type"].strip():
            raise ValueError("artifact media_type must be non-empty text")
        artifacts = ArtifactStore(self._world.artifacts_root, project_id)
        record = artifacts.add(value["content"], value["media_type"].strip())
        return _artifact_view(record)

    def _command_thread_publish_report(self, command: KernelCommand) -> dict:
        values = command.values
        _validate_fields(values, {"thread_id", "title"}, {"thread_id", "title"})
        thread = self._thread_project(command)
        project_id = thread["project_id"]
        return self._publish_report(project_id, thread["id"], values["title"])

    def _command_runtime_publish_report(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"session_id", "title"}, {"session_id", "title"})
        project_id = _project_id(command)
        thread = self._world.thread_for_session(command.values["session_id"])
        if thread["project_id"] != project_id:
            raise PermissionError("runtime session belongs to another project")
        return self._publish_report(project_id, thread["id"], command.values["title"])

    def _publish_report(self, project_id: str, thread_id: str, title: str) -> dict:
        envelope = self._publication_projection(project_id)
        if envelope["status"] == "blocked":
            return _publication_failure("projection", [], _blocked_assessment(envelope))
        projection = envelope["projection"]
        stages = [{"name": "projection", "status": "completed"}]
        assessment = assess_delivery(projection)
        if not assessment["valid"]:
            return _publication_failure("citation_validation", stages, assessment)
        stages.append({"name": "citation_validation", "status": "completed"})
        return self._render_publication(project_id, thread_id, title, projection, assessment, stages)

    def _render_publication(self, project_id, thread_id, title, projection, assessment, stages):
        title, content = _report_title(title), render_html(title, projection, assessment)
        stages.append({"name": "rendering", "status": "completed"})
        gaps = validate_html(content)
        if gaps:
            return _publication_failure("output_validation", stages, {**assessment, "valid": False, "gaps": gaps})
        stages.append({"name": "output_validation", "status": "completed"})
        artifact = ArtifactStore(self._world.artifacts_root, project_id).add(content, "text/html")
        publication = self._world.publish_report(project_id, thread_id, title, artifact["id"])
        stages.append({"name": "persistence", "status": "completed"})
        return {"status": "published", "title": title, "publication": publication, "artifact": _artifact_view(artifact), "assessment": assessment, "stages": stages}

    def _command_save_report(self, command: KernelCommand) -> dict:
        values = command.values
        _validate_fields(values, {"title", "thread_id", "publication_id"}, {"title", "thread_id", "publication_id"})
        title = _report_title(values["title"])
        thread = self._thread_project(command)
        return self._world.save_report(thread["project_id"], thread["id"], title, values["publication_id"])

    def _command_claim(self, _command: KernelCommand) -> RunLease | None:
        run = self._world.claim_run()
        return RunLease(run["id"], run["project_id"]) if run else None

    def _command_heartbeat(self, command: KernelCommand) -> bool:
        return self._world.touch_run(command.values["run_id"])

    def _command_fail(self, command: KernelCommand) -> dict:
        from .workflows import fail_run

        return fail_run(self._world, command.values["run_id"], command.values["error"])

    async def _command_create_thread(self, command: KernelCommand) -> dict:
        value = command.values
        return await self._require_threads().create(
            _project_id(command),
            value.get("title", "新对话"),
            value.get("agent_id", "research-assistant"),
            value.get("node_ids", []),
        )

    async def _command_restart_thread(self, command: KernelCommand) -> dict:
        return await self._require_threads().restart(command.values["thread_id"])

    def _command_thread_prompt(self, command: KernelCommand):
        value = command.values
        return self._require_threads().prompt(value["thread_id"], value["message"])

    def _command_pin_thread(self, command: KernelCommand) -> dict:
        value = command.values
        return self._require_threads().pin(value["thread_id"], value["node_id"])

    def _command_unpin_thread(self, command: KernelCommand) -> dict:
        value = command.values
        return self._require_threads().unpin(value["thread_id"], value["node_id"])

    async def _command_create_agent(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"value"}, {"value"})
        value = command.values["value"]
        self._require_agents().validate_new(value)
        await self._require_runtime().validate_agent(value)
        catalog = await self._runtime_catalog(_project_id(command))
        require_tools_ready(catalog, value)
        return self._require_agents().create(value)

    async def _command_draft_agent(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"preset_id"}, {"preset_id"})
        catalog = await self._runtime_catalog(_project_id(command))
        return agent_draft(command.values["preset_id"], catalog)

    async def _runtime_catalog(self, project_id: str) -> dict:
        workspace = self._world.project(project_id)["root"]
        return await self._require_runtime().recognize(workspace)

    async def _command_save_agent(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"agent_id", "value"}, {"agent_id", "value"})
        value = command.values["value"]
        await self._require_runtime().validate_agent(value)
        catalog = await self._runtime_catalog(_project_id(command))
        require_tools_ready(catalog, value)
        return self._require_agents().save(
            command.values["agent_id"], value
        )

    def _command_save_pipeline(self, command: KernelCommand) -> dict:
        value = command.values
        return self._require_pipelines().save(value["pipeline_id"], value["value"])

    def _query_node(self, query: KernelQuery) -> dict:
        return self._project_node(query.project_id, query.values["node_id"])

    def _query_admitted_node(self, query: KernelQuery) -> dict:
        return self._admitted_node(_project_id(query), query.values["node_id"])

    def _query_nodes(self, query: KernelQuery) -> list[dict]:
        return self._world.nodes(_project_id(query))

    def _query_graph_search(self, query: KernelQuery) -> list[dict]:
        nodes = self._world.search(_project_id(query), query.values.get("text", ""))
        return [
            _node_summary(node) for node in nodes if node["life_state"] == "admitted"
        ]

    def _query_projects(self, _query: KernelQuery) -> list[dict]:
        return self._world.projects()

    def _query_project_by_name(self, query: KernelQuery) -> dict:
        return self._world.project_by_name(query.values["name"])

    def _query_workspace(self, query: KernelQuery) -> str:
        return self._world.project(_project_id(query))["root"]

    def _query_graph(self, query: KernelQuery) -> dict:
        project_id = _project_id(query)
        return {
            "nodes": self._world.nodes(project_id),
            "edges": self._world.edges(project_id),
        }

    def _query_runs(self, query: KernelQuery) -> list[dict]:
        return [self._run_view(run) for run in self._world.runs(_project_id(query))]

    def _query_run(self, query: KernelQuery) -> dict:
        run = self._world.run(query.values["run_id"])
        gate = run["payload"].get("_pipeline", {}).get("gate") or {}
        return {**self._run_view(run), "gate": gate}

    def _query_threads(self, query: KernelQuery) -> list[dict]:
        return self._world.threads(_project_id(query))

    async def _query_catalog(self, query: KernelQuery) -> dict:
        return await self._runtime_catalog(_project_id(query))

    async def _query_session(self, query: KernelQuery) -> dict:
        return await self._require_runtime().inspect(query.values["session_id"])

    def _query_agents(self, _query: KernelQuery) -> list[dict]:
        return self._require_agents().all()

    def _query_agent(self, query: KernelQuery) -> dict:
        return self._require_agents().get(query.values["agent_id"])

    def _query_pipelines(self, _query: KernelQuery) -> list[dict]:
        return self._require_pipelines().all()

    async def _query_thread(self, query: KernelQuery) -> dict:
        return await self._require_threads().detail(query.values["thread_id"])

    async def _query_embedding_dimensions(self, query: KernelQuery) -> int:
        value = query.values
        vectors = await self._require_runtime().embed(
            value["endpoint"], value["model"], ["orbit"]
        )
        return len(vectors[0])

    def _query_bootstrap(self, query: KernelQuery) -> dict:
        projects = self._project_cards()
        selected = query.project_id or (projects[0]["id"] if projects else None)
        return self._bootstrap(selected, projects)

    def _query_report_projection(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, set(), set())
        return self._report_projection(_project_id(query))

    def _query_report_validate(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, set(), set())
        envelope = self._publication_projection(_project_id(query))
        return assess_delivery(envelope["projection"]) if envelope["status"] == "ready" else _blocked_assessment(envelope)

    def _query_report_bibtex(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, {"artifact_id"}, {"artifact_id"})
        project_id = _project_id(query)
        artifact_id = query.values["artifact_id"]
        if artifact_id not in self._source_artifact_ids(project_id):
            raise PermissionError("artifact is not admitted report evidence")
        content = _bibtex(
            ArtifactStore(self._world.artifacts_root, project_id), artifact_id
        )
        return {"id": artifact_id, "content": content}

    def _query_report_content(self, query: KernelQuery) -> bytes:
        values = query.values
        _validate_fields(values, {"thread_id", "publication_id"}, {"thread_id", "publication_id"})
        thread = self._thread_project(query)
        project_id = thread["project_id"]
        publication = self._world.publication(project_id, values["publication_id"], values["thread_id"])
        return ArtifactStore(self._world.artifacts_root, project_id).read(publication["artifact_id"])

    def _query_report(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, {"report_id"}, {"report_id"})
        return self._world.report(_project_id(query), query.values["report_id"])

    def _submit_node(self, project_id: str, value: dict) -> dict:
        _validate_fields(value, {"kind", "payload", "parent_id"}, {"kind", "payload"})
        self._validate_parent(project_id, value.get("parent_id"))
        payload = _node_payload(value["payload"])
        state = {"parent_id": value["parent_id"]} if value.get("parent_id") else {}
        node = self._world.create_node(project_id, value["kind"], payload, **state)
        verdict = self._admission.review(node)
        return self._apply_admission(node, verdict) if verdict else node

    def _apply_admission(self, node, verdict) -> dict:
        if verdict.decision == "approve":
            validate_project_claim_ids(self._world, node)
        return self._world.apply_admission(node["id"], verdict)

    def _project_node(self, project_id: str | None, node_id: str) -> dict:
        node = self._world.node(_canonical_node_id(node_id))
        if project_id and node["project_id"] != project_id:
            raise PermissionError("node belongs to another project")
        return node

    def _thread_project(self, value: KernelCommand | KernelQuery) -> dict:
        thread = self._world.thread(value.values["thread_id"])
        if value.project_id and value.project_id != thread["project_id"]:
            raise PermissionError("thread belongs to another project")
        return thread

    def _admitted_node(self, project_id: str, node_id: str) -> dict:
        node = self._project_node(project_id, node_id)
        if node["life_state"] != "admitted":
            raise PermissionError("node is not admitted")
        return node

    def _validate_parent(self, project_id: str, parent_id: str | None) -> None:
        try:
            if parent_id:
                self._admitted_node(project_id, parent_id)
        except PermissionError as error:
            message = "node parent must be admitted and belong to the project"
            raise ValueError(message) from error

    def _validate_run_context(self, project_id: str, payload: dict) -> None:
        thread_id = payload.get("thread_id")
        if thread_id and self._world.thread(thread_id)["project_id"] != project_id:
            raise PermissionError("thread belongs to another project")
        for node_id in payload.get("pins", []):
            self._admitted_node(project_id, node_id)

    async def _endpoint_ready(self, project_id: str) -> bool:
        if self._runtime is None:
            return False
        workspace = self._world.project(project_id)["root"]
        catalog = await self._runtime.recognize(workspace)
        return any(
            item.get("available") is True for item in catalog.get("endpoints", [])
        )

    def _run_view(self, run: dict) -> dict:
        return {
            **run,
            "steps": self._world.steps(run["id"]),
            "events": self._world.run_events(run["id"]),
        }

    def _project_cards(self) -> list[dict]:
        return [self._project_card(project) for project in self._world.projects()]

    def _project_card(self, project: dict) -> dict:
        runs = self._world.runs(project["id"])
        active = {"queued", "running", "waiting_human"}
        return {
            **project,
            "title": project["name"],
            "node_count": len(self._world.nodes(project["id"])),
            "run_count": len(runs),
            "active_run_count": sum(run["status"] in active for run in runs),
        }

    def _bootstrap(self, project_id: str | None, projects: list[dict]) -> dict:
        if not project_id:
            return _empty_bootstrap()
        runs = [self._run_view(run) for run in self._world.runs(project_id)]
        return _bootstrap_value(self, project_id, projects, runs)

    def _report_projection(self, project_id: str) -> dict:
        return self._public_report_projection(*self._report_inputs(project_id))

    def _publication_projection(self, project_id: str) -> dict:
        project, nodes = self._report_inputs(project_id)
        envelope = self._public_report_projection(project, nodes)
        if envelope["status"] == "blocked":
            return envelope
        artifacts = self._publication_artifacts(project["id"], envelope["projection"]["artifacts"])
        return {**envelope, "projection": {**envelope["projection"], "artifacts": artifacts}}

    def _public_report_projection(self, project: dict, nodes: list[dict]) -> dict:
        tokens = _report_input_upper_bound(project, nodes)
        if tokens > REPORT_INPUT_TOKEN_BUDGET:
            return blocked_projection(tokens)
        return projection_envelope(self._report_view(project, nodes))

    def _report_inputs(self, project_id: str) -> tuple[dict, list[dict]]:
        nodes = [node for node in self._world.nodes(project_id) if node["life_state"] == "admitted"]
        return self._world.project(project_id), nodes

    def _report_view(self, project: dict, nodes: list[dict]) -> dict:
        claims = _report_claims(nodes)
        facts = [_claim_fact(claim) for claim in claims if claim["verdict"] == "supported"]
        sources = _report_sources(nodes, facts)
        artifacts = self._report_artifacts(project["id"], claims)
        question = safe_narrative(project["question"])
        return {"question": question, "facts": facts, "claims": claims, "sources": sources, "artifacts": artifacts}

    def _publication_artifacts(self, project_id: str, artifacts: list[dict]) -> list[dict]:
        store = ArtifactStore(self._world.artifacts_root, project_id)
        return [_publication_artifact(store, artifact) for artifact in artifacts]

    def _report_artifacts(self, project_id: str, claims: list[dict]) -> list[dict]:
        links = _artifact_links(claims)
        store = ArtifactStore(self._world.artifacts_root, project_id)
        return [_report_artifact(store, artifact_id, links[artifact_id]) for artifact_id in sorted(links)]

    def _source_artifact_ids(self, project_id: str) -> set[str]:
        sources = [
            node
            for node in self._world.nodes(project_id)
            if node["kind"] == "source" and node["life_state"] == "admitted"
        ]
        return {
            artifact_id
            for node in sources
            for artifact_id in node["payload"].get("artifact_ids", [])
        }

    def _create_project(self, value: dict, workspace: Path) -> dict:
        try:
            return self._world.create_project(
                value["name"], workspace, value["question"]
            )
        except Exception:
            workspace.rmdir()
            raise

    def _require_runtime(self):
        if self._runtime is None:
            raise RuntimeError("kernel runtime is unavailable")
        return self._runtime

    def _require_pipelines(self):
        if self._pipelines is None:
            raise RuntimeError("kernel pipelines are unavailable")
        return self._pipelines

    def _require_agents(self):
        if self._agents is None:
            raise RuntimeError("kernel agents are unavailable")
        return self._agents

    def _require_threads(self):
        if self._threads is None:
            raise RuntimeError("kernel threads are unavailable")
        return self._threads


def _bootstrap_value(kernel, project_id, projects, runs) -> dict:
    world = kernel._world
    return {
        "projects": projects,
        "active_project_id": project_id,
        "nodes": world.nodes(project_id),
        "edges": world.edges(project_id),
        "runs": runs,
        "pipelines": kernel._pipelines.all() if kernel._pipelines else [],
        "threads": world.threads(project_id),
        "slots": _slots(runs),
    }


def _thread_manager(world, runtime, agents):
    if runtime is None or agents is None:
        return None
    from .threads import ThreadManager

    return ThreadManager(world, runtime, agents)


def _project_id(value) -> str:
    if not value.project_id:
        raise ValueError("kernel operation requires project_id")
    return value.project_id


def _report_title(value) -> str:
    title = safe_narrative(value)
    if title is None:
        raise ValueError("report title must be safe non-empty text")
    return title


def _report_input_upper_bound(project: dict, nodes: list[dict]) -> int:
    values = [project.get("question"), *({"id": node["id"], "kind": node["kind"], "payload": node["payload"]} for node in nodes)]
    size = sum(len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) for value in values)
    return math.ceil(size / 4)


def _validate_project(value: dict) -> None:
    _validate_fields(value, {"name", "question"}, {"name", "question"})
    if not all(isinstance(value[key], str) and value[key].strip() for key in value):
        raise ValueError("project name and question cannot be empty")


def _allocate_workspace(projects_root: Path) -> Path:
    root = projects_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / secrets.token_hex(12)
    workspace.mkdir(mode=0o700)
    return workspace


def _resolution_signal(gate: dict, value: dict) -> dict:
    if not gate:
        raise ValueError("run has no human gate")
    return {**gate, "decision": value["decision"], "reason": value["reason"]}


def _artifact_view(record: dict) -> dict:
    fields = ("id", "sha256", "media_type", "size", "created_at")
    return {field: record[field] for field in fields}


def _artifact_ids(value) -> set[str]:
    if isinstance(value, str):
        return {value} if value.startswith("artifact:") else set()
    if isinstance(value, dict):
        return {item for child in value.values() for item in _artifact_ids(child)}
    if isinstance(value, list):
        return {item for child in value for item in _artifact_ids(child)}
    return set()


def _validate_fields(value: dict, allowed: set[str], required: set[str]) -> None:
    if not isinstance(value, dict):
        raise TypeError("kernel command values must be an object")
    if missing := required - set(value):
        raise ValueError(f"kernel command missing fields: {', '.join(sorted(missing))}")
    if unknown := set(value) - allowed:
        raise ValueError(f"kernel command rejects fields: {', '.join(sorted(unknown))}")


def _node_payload(value) -> dict:
    if not isinstance(value, dict):
        raise TypeError("node payload must be an object")
    return value


def _admission_verdict(value: dict) -> AdmissionVerdict:
    reason = value.get("reason", "")
    rebuttal = value.get("rebuttal")
    if not isinstance(reason, str):
        raise TypeError("admission reason must be text")
    if rebuttal is not None and not isinstance(rebuttal, dict):
        raise TypeError("admission rebuttal must be an object")
    return AdmissionVerdict(value["decision"], reason, rebuttal)


def _run_payload(value) -> dict:
    allowed = {"thread_id", "instruction", "mode", "pins"}
    _validate_fields(value, allowed, set())
    for key in ("thread_id", "instruction", "mode"):
        if key in value and not _nonempty_text(value[key]):
            raise ValueError(f"run payload {key} must be non-empty text")
    pins = value.get("pins", [])
    if not isinstance(pins, list) or not all(_nonempty_text(pin) for pin in pins):
        raise ValueError("run payload pins must be node ids")
    if len(pins) != len(set(pins)):
        raise ValueError("run payload pins must be unique")
    return {**value, "pins": list(pins)} if "pins" in value else dict(value)


def _nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _bibtex(store: ArtifactStore, artifact_id: str) -> str:
    record = store.get(artifact_id)
    if record["media_type"] not in {"application/x-bibtex", "text/x-bibtex"}:
        raise ValueError("report artifact must use a BibTeX media type")
    try:
        content = store.read(artifact_id).decode("utf-8")
        bibliography = parse_string(content, "bibtex")
    except (UnicodeDecodeError, PybtexError) as error:
        raise ValueError("report artifact contains invalid BibTeX") from error
    if not bibliography.entries:
        raise ValueError("report artifact contains no BibTeX entries")
    return content


def _canonical_node_id(value: str) -> str:
    node_id = value.lstrip("@")
    return node_id if node_id.startswith("node:") else f"node:{node_id}"


def _node_summary(node: dict) -> dict:
    return {
        "id": node["id"],
        "kind": node["kind"],
        "life_state": node["life_state"],
        "summary": node_text(node["payload"]),
    }


def _report_claims(nodes: list[dict]) -> list[dict]:
    index = {node["id"]: node for node in nodes}
    return [
        _claim_record(node, ordinal, claim, index)
        for node in nodes
        for ordinal, claim in enumerate(validate_claims(node["payload"].get("claims", [])), 1)
    ]


def _claim_record(node: dict, ordinal: int, claim: dict, index: dict) -> dict:
    evidence = [_claim_evidence(index[item]) for item in claim.get("evidence", []) if item in index]
    evidence = [item for item in evidence if item is not None]
    return {
        "id": _report_claim_id(node["id"], ordinal),
        "text": safe_narrative(claim["text"]),
        "life_state": node["life_state"],
        "verdict": claim["verdict"],
        "evidence": evidence,
        "evidence_ids": [item["id"] for item in evidence],
        "source_ids": [item["id"] for item in evidence if item["kind"] == "source"],
        "artifact_ids": sorted({artifact for item in evidence for artifact in item["artifact_ids"]}),
    }


def _report_claim_id(node_id: str, ordinal: int) -> str | None:
    node = safe_node_id(node_id)
    return f"claim:{node.removeprefix('node:')}:{ordinal}" if node else None


def _claim_fact(claim: dict) -> dict:
    return {
        "text": claim["text"],
        "claim_id": claim["id"],
        "source_ids": claim["source_ids"],
        "artifact_ids": claim["artifact_ids"],
    }


def _report_sources(nodes: list[dict], facts: list[dict]) -> list[dict]:
    needed = {source for fact in facts for source in fact["source_ids"]}
    return [_safe_source(node) for node in nodes if node["id"] in needed]


def _safe_source(node: dict) -> dict:
    payload = node["payload"]
    level = payload.get("source_level")
    return {"id": safe_node_id(node["id"]), "title": safe_narrative(payload.get("title")), "source_level": level if level in {"preprint", "conference", "published", "primary_data"} else None, "checked_at": normalized_checked_at(payload.get("checked_at"))}


def _claim_evidence(node: dict) -> dict | None:
    if node["kind"] not in {"source", "experiment"}:
        return None
    return {"id": safe_node_id(node["id"]), "kind": node["kind"], "artifact_ids": _direct_artifact_ids(node)}


def _artifact_links(claims: list[dict]) -> dict[str, list[dict]]:
    links = {}
    for claim in claims:
        if claim["verdict"] == "supported":
            _add_claim_links(links, claim)
    return links


def _add_claim_links(links: dict, claim: dict) -> None:
    for evidence in claim["evidence"]:
        for artifact_id in evidence["artifact_ids"]:
            link = _artifact_link(claim, evidence)
            if link is not None:
                links.setdefault(artifact_id, []).append(link)


def _artifact_link(claim: dict, evidence: dict) -> dict | None:
    if not claim["id"] or not evidence["id"]:
        return None
    link = {"claim_id": claim["id"], "evidence_id": evidence["id"]}
    return {**link, "source_id": evidence["id"]} if evidence["kind"] == "source" else link


def _report_artifact(store, artifact_id: str, links: list[dict]) -> dict:
    try:
        record = store.get(artifact_id)
    except (ArtifactIntegrityError, KeyError, OSError):
        record = {}
    return {"id": safe_artifact_id(record.get("id")), "kind": evidence_kind(record.get("media_type")), "size": record.get("size") if isinstance(record.get("size"), int) else None, "links": links}


def _publication_artifact(store, artifact: dict) -> dict:
    try:
        record = store.get(artifact["id"])
        display = _artifact_display(store, record, artifact)
    except (ArtifactIntegrityError, KeyError, OSError, TypeError):
        display = {"kind": "invalid"}
    return {**artifact, "display": display}


def _artifact_display(store, record: dict, artifact: dict) -> dict:
    if not _artifact_record_matches(record, artifact):
        return {"kind": "invalid"}
    try:
        return artifact_display(record, store.read(record["id"]))
    except (ArtifactIntegrityError, KeyError, OSError):
        return {"kind": "invalid"}


def _artifact_record_matches(record: dict, artifact: dict) -> bool:
    checks = (record.get("id") == artifact.get("id"), evidence_kind(record.get("media_type")) == artifact.get("kind"), record.get("size") == artifact.get("size"), isinstance(record.get("size"), int) and record["size"] <= MAX_EVIDENCE_BYTES)
    return all(checks)


def _blocked_assessment(envelope: dict) -> dict:
    return {"valid": False, "delivery_level": 0, "accepted_facts": [], "minimum_source_level": None, "gaps": envelope["gaps"], "contract": envelope["contract"]}


def _publication_failure(stage: str, stages: list[dict], assessment: dict) -> dict:
    return {"status": "failed", "assessment": assessment, "stages": [*stages, {"name": stage, "status": "failed"}]}


def _direct_artifact_ids(node: dict) -> list[str]:
    values = node["payload"].get("artifact_ids", [])
    return sorted({item for item in values if safe_artifact_id(item)}) if isinstance(values, list) else []


def _slots(runs: list[dict], count: int = 2) -> list[dict]:
    active = [
        run for run in runs if run["status"] in {"queued", "running", "waiting_human"}
    ]
    return [
        {"index": index + 1, "run": active[index] if index < len(active) else None}
        for index in range(count)
    ]


def _empty_bootstrap() -> dict:
    return {
        "projects": [],
        "active_project_id": None,
        "nodes": [],
        "edges": [],
        "runs": [],
        "pipelines": [],
        "threads": [],
        "slots": [],
    }


def default_kernel() -> ResearchKernel:
    from .agents import AgentRegistry
    from .config import load_settings
    from .pipelines import PipelineRegistry
    from .runtime_client import RuntimeClient

    settings = load_settings()
    world = World(settings.database, settings.artifacts)
    runtime = RuntimeClient(settings.runtime_url)
    agents = AgentRegistry(settings.agents_root)
    pipelines = PipelineRegistry(settings.pipelines_root, settings.pipeline_schema)
    return ResearchKernel(
        world,
        projects_root=settings.projects_root,
        runtime=runtime,
        agents=agents,
        pipelines=pipelines,
    )
