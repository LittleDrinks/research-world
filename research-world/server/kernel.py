from __future__ import annotations

from dataclasses import dataclass, field
from inspect import isawaitable
from pathlib import Path

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

from .admission import (
    AdmissionPolicy,
    AdmissionVerdict,
    PendingAdmissionPolicy,
    claim_id,
    validate_claims,
    validate_project_claim_ids,
)
from .artifacts import ArtifactStore
from .observations import observation_submission
from .presets import agent_draft, require_capabilities_ready
from .project_storage import ProjectStorage
from .reporting import assess_delivery
from .source_candidates import validate_candidate_artifact, validate_source_candidate
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
        self._projects = ProjectStorage(projects_root)
        self._projects.materialize(world.projects())
        self._runtime = runtime
        self._agents = agents
        self._pipelines = pipelines
        self._admission: AdmissionPolicy = admission or PendingAdmissionPolicy()
        self._threads = _thread_manager(world, runtime, agents, self._workspace)
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
        workspace = self._projects.allocate()
        return self._create_project(command.values, workspace)

    def _command_set_auto(self, command: KernelCommand) -> dict:
        return self._world.set_auto(
            _project_id(command), bool(command.values["enabled"])
        )

    def _command_submit_node(self, command: KernelCommand) -> dict:
        if command.values.get("kind") == "source":
            raise ValueError("source nodes must be submitted by a Pipeline")
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

    def _submit_source_candidate(
        self, project_id: str, run_id: str, index: int, direction_id: str, value: dict
    ) -> dict:
        candidate = validate_source_candidate(value)
        run = self._world.run(run_id)
        if run["project_id"] != project_id or run["node_id"] != direction_id:
            raise ValueError("SourceCandidate Pipeline context does not match Direction")
        direction = self._admitted_node(project_id, direction_id)
        if direction["kind"] != "direction":
            raise ValueError("SourceCandidate target must be a Direction")
        if candidate["relationship"]["direction_id"] != direction_id:
            raise ValueError("SourceCandidate relationship must target the Pipeline Direction")
        store = ArtifactStore(self._world.artifacts_root, project_id)
        workspace = self._workspace(project_id)
        validate_candidate_artifact(candidate, store, workspace)
        return self._source_submission(run_id, index, direction_id, candidate)

    def _source_submission(
        self, run_id: str, index: int, direction_id: str, candidate: dict
    ) -> dict:
        marker = {"run_id": run_id, "index": index}
        if existing := self._source_by_pipeline(marker):
            return existing
        payload = {**candidate, "pipeline": marker}
        project_id = self._world.run(run_id)["project_id"]
        value = {"kind": "source", "payload": payload, "parent_id": direction_id}
        return self._submit_node(project_id, value)

    def _source_by_pipeline(self, marker: dict) -> dict | None:
        project_id = self._world.run(marker["run_id"])["project_id"]
        return next(
            (
                node for node in self._world.nodes(project_id)
                if node["kind"] == "source" and node["payload"].get("pipeline") == marker
            ),
            None,
        )

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
        require_capabilities_ready(catalog, value)
        return self._require_agents().create(value)

    async def _command_draft_agent(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"preset_id"}, {"preset_id"})
        catalog = await self._runtime_catalog(_project_id(command))
        return agent_draft(command.values["preset_id"], catalog)

    async def _runtime_catalog(self, project_id: str) -> dict:
        return await self._require_runtime().recognize(str(self._workspace(project_id)))

    async def _command_save_agent(self, command: KernelCommand) -> dict:
        _validate_fields(command.values, {"agent_id", "value"}, {"agent_id", "value"})
        value = command.values["value"]
        await self._require_runtime().validate_agent(value)
        catalog = await self._runtime_catalog(_project_id(command))
        require_capabilities_ready(catalog, value)
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
        return [self._projects.project(project) for project in self._world.projects()]

    def _query_project_by_name(self, query: KernelQuery) -> dict:
        return self._projects.project(self._world.project_by_name(query.values["name"]))

    def _query_workspace(self, query: KernelQuery) -> str:
        return str(self._workspace(_project_id(query)))

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

    async def _query_report_projection(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, set(), set())
        project_id = _project_id(query)
        endpoint_ready = await self._endpoint_ready(project_id)
        return self._report_projection(project_id, endpoint_ready)

    async def _query_report_validate(self, query: KernelQuery) -> dict:
        _validate_fields(query.values, {"facts"}, {"facts"})
        projection = await self._query_report_projection(
            KernelQuery("report_projection", _project_id(query))
        )
        projection["facts"] = query.values["facts"]
        return assess_delivery(projection)

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
        relation = node["payload"].get("relationship", {})
        evidence = node["kind"] == "source" and "pipeline" in node["payload"]
        if not evidence or verdict.decision != "approve":
            return self._world.apply_admission(node["id"], verdict)
        if relation.get("use") not in {"supports", "refutes"}:
            return self._world.apply_admission(node["id"], verdict)
        target = self._admitted_node(node["project_id"], relation["direction_id"])
        if target["kind"] != "direction":
            raise ValueError("source relationship target must be a direction")
        return self._world.apply_source_admission(
            node["id"], verdict, target["id"], relation["use"]
        )

    def _project_node(self, project_id: str | None, node_id: str) -> dict:
        node = self._world.node(_canonical_node_id(node_id))
        if project_id and node["project_id"] != project_id:
            raise PermissionError("node belongs to another project")
        return node

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
        catalog = await self._runtime.recognize(str(self._workspace(project_id)))
        return any(
            item.get("available") is True for item in catalog.get("endpoints", [])
        )

    def _run_view(self, run: dict) -> dict:
        return {
            **run,
            "payload": self._current_source_payload(run["payload"]),
            "steps": self._world.steps(run["id"]),
            "events": self._world.run_events(run["id"]),
        }

    def _current_source_payload(self, payload: dict) -> dict:
        pipeline = payload.get("_pipeline")
        values = pipeline.get("values", {}) if isinstance(pipeline, dict) else {}
        sources = values.get("sources")
        if not isinstance(sources, list):
            return payload
        current = [self._world.node(source["id"]) for source in sources]
        updated = {**values, "sources": current}
        return {**payload, "_pipeline": {**pipeline, "values": updated}}

    def _project_cards(self) -> list[dict]:
        return [self._project_card(project) for project in self._world.projects()]

    def _project_card(self, project: dict) -> dict:
        runs = self._world.runs(project["id"])
        active = {"queued", "running", "waiting_human"}
        return {
            **self._projects.project(project),
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

    def _report_projection(self, project_id: str, endpoint_ready: bool) -> dict:
        nodes = [
            node
            for node in self._world.nodes(project_id)
            if node["life_state"] == "admitted"
        ]
        sources = [_source_record(node) for node in nodes if node["kind"] == "source"]
        claims = [claim for node in nodes for claim in _node_claims(node)]
        facts = [
            _claim_fact(claim) for claim in claims if claim["verdict"] == "supported"
        ]
        artifacts = self._report_artifacts(project_id, nodes)
        return {
            "endpoint_ready": endpoint_ready,
            "facts": facts,
            "claims": claims,
            "sources": sources,
            "artifacts": artifacts,
        }

    def _report_artifacts(self, project_id: str, nodes: list[dict]) -> list[dict]:
        evidence = [node for node in nodes if node["kind"] in {"source", "experiment"}]
        artifact_ids = sorted(
            {item for node in evidence for item in _artifact_ids(node["payload"])}
        )
        store = ArtifactStore(self._world.artifacts_root, project_id)
        return [_artifact_view(store.get(artifact_id)) for artifact_id in artifact_ids]

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

    def _workspace(self, project_id: str) -> Path:
        return self._projects.workspace(self._world.project(project_id))

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


def _thread_manager(world, runtime, agents, workspace):
    if runtime is None or agents is None:
        return None
    from .threads import ThreadManager

    return ThreadManager(world, runtime, agents, workspace)


def _project_id(value) -> str:
    if not value.project_id:
        raise ValueError("kernel operation requires project_id")
    return value.project_id


def _validate_project(value: dict) -> None:
    _validate_fields(value, {"name", "question"}, {"name", "question"})
    if not all(isinstance(value[key], str) and value[key].strip() for key in value):
        raise ValueError("project name and question cannot be empty")


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


def _source_record(node: dict) -> dict:
    return {
        **node["payload"],
        "id": node["id"],
        "kind": "source",
        "life_state": "admitted",
    }


def _node_claims(node: dict) -> list[dict]:
    claims = validate_claims(node["payload"].get("claims", []))
    return [_claim_record(node, index, claim) for index, claim in enumerate(claims, 1)]


def _claim_record(node: dict, index: int, claim: dict) -> dict:
    evidence = [
        item for item in claim.get("evidence", []) if str(item).startswith("node:")
    ]
    return {
        "id": claim_id(node, index, claim),
        "text": claim["text"],
        "life_state": "admitted",
        "verdict": claim["verdict"],
        "source_ids": evidence,
    }


def _claim_fact(claim: dict) -> dict:
    return {
        "text": claim["text"],
        "claim_id": claim["id"],
        "source_ids": claim["source_ids"],
    }


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
