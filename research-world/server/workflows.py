from __future__ import annotations

import math
import os
import secrets
from dataclasses import dataclass

from .admission import (
    validate_claims as validate_claim_records,
)
from .admission import validate_project_claim_ids
from .agents import AgentRegistry
from .artifacts import ArtifactStore
from .clients import RunnerClient
from .config import load_settings
from .execution_evidence import (
    compare_replay,
    persist_evidence_artifact,
    verify_evidence,
    verify_evidence_artifact,
)
from .pipelines import PipelineRegistry, StagePrimitiveRegistry
from .runtime_client import (
    AgentResultError,
    RuntimeCapabilityError,
    RuntimeClient,
    RuntimeEmbedding,
)
from .titles import TITLE_TOKEN_LIMIT, validate_title
from .world import World


def cosine(left: list[float], right: list[float]) -> float:
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(
        sum(x * x for x in right)
    )
    return (
        sum(x * y for x, y in zip(left, right, strict=True)) / denominator
        if denominator
        else 0.0
    )


def mmr(
    candidates: list[dict],
    count: int,
    query_vector: list[float],
    weight: float = 0.2,
) -> list[dict]:
    selected = []
    remaining = list(candidates)
    while remaining and len(selected) < count:
        score = lambda item: _mmr_score(item, selected, query_vector, weight)
        best = max(remaining, key=score)
        selected.append(best)
        remaining.remove(best)
    return selected


def _mmr_score(candidate, selected, query_vector, weight) -> float:
    relevance = cosine(candidate["vector"], query_vector)
    similarity = max(
        (cosine(candidate["vector"], item["vector"]) for item in selected), default=0
    )
    return relevance - weight * similarity


class AgentFacade:
    def __init__(self, runtime: RuntimeClient, agents: AgentRegistry):
        self.runtime = runtime
        self.agents = agents

    def validate(self, pipeline: dict) -> None:
        for agent_id in _pipeline_agents(pipeline):
            self.agents.get(agent_id)

    def _call(
        self,
        agent_id: str,
        instruction: str,
        payload: dict,
        required: tuple[str, ...],
        operation_id: str | None = None,
    ) -> dict:
        return self.runtime.json(
            self.agents.get(agent_id), instruction, payload, required, operation_id
        )

    def brainstorm(
        self, context: dict, count: int, agent: str, operation_id: str | None = None
    ) -> dict:
        value = self._call(
            agent,
            BRAINSTORM_PROMPT,
            {**context, "count": count},
            ("candidates",),
            operation_id,
        )
        candidates = self._validate(
            value, lambda: validate_candidates(required(value, "candidates"), count)
        )
        return {**value, "candidates": candidates}

    def pairwise(self, left: str, right: str, operation_id: str | None = None) -> dict:
        value = self._call(
            "independent-reviewer",
            PAIR_PROMPT,
            {"left": left, "right": right},
            ("duplicate",),
            operation_id,
        )
        duplicate = required(value, "duplicate")
        if not isinstance(duplicate, bool):
            raise TypeError("runtime field 'duplicate' must be boolean")
        return value

    def plan(
        self, direction: dict, agent: str, operation_id: str | None = None
    ) -> dict:
        value = self._call(
            agent, PLAN_PROMPT, direction, ("title", "action"), operation_id
        )
        return {**value, "title": self._validate(value, lambda: _plan_title(value))}

    def audit_action(self, context: dict, operation_id: str | None = None) -> dict:
        value = self._call(
            "independent-reviewer",
            ACTION_REVIEW_PROMPT,
            context,
            ("decision", "argument", "evidence"),
            operation_id,
        )
        return validate_verdict(value)

    def claims(
        self, context: dict, agent: str, operation_id: str | None = None
    ) -> dict:
        value = self._call(
            agent, CLAIM_AUDIT_PROMPT, context, ("claims",), operation_id
        )
        value["claims"] = validate_claims(value["claims"])
        return value

    def review(
        self,
        context: dict,
        subject: str,
        stance: str,
        agent: str,
        operation_id: str | None = None,
    ) -> dict:
        fields = ("decision", "argument", "evidence", "needs_experiment")
        value = self._call(
            agent,
            REVIEW_PROMPTS[subject],
            {**context, "stance": stance},
            fields,
            operation_id,
        )
        return {**validate_review_verdict(value), "stance": stance}

    def reconcile(
        self, context: dict, agent: str, operation_id: str | None = None
    ) -> dict:
        value = self._call(
            agent, RECONCILE_PROMPT, context, ("title", "text"), operation_id
        )
        return {
            **value,
            "title": self._validate(value, lambda: validate_title(required(value, "title"))),
        }

    def reflect(
        self, context: dict, agent: str, operation_id: str | None = None
    ) -> dict:
        value = self._call(
            agent, REFLECT_PROMPT, context, ("title", "text"), operation_id
        )
        return {
            **value,
            "title": self._validate(value, lambda: validate_title(required(value, "title"))),
        }

    def _validate(self, value: dict, validator):
        try:
            return validator()
        except (TypeError, ValueError) as error:
            raise AgentResultError(error, value) from error


@dataclass
class PipelineEngine:
    world: World
    agents: object
    embedding: object
    runner: object
    pipelines: object

    def __post_init__(self) -> None:
        handlers = {
            "generate-directions": self._generate_directions,
            "deduplicate-directions": self._deduplicate_directions,
            "select-directions": self._select_directions,
            "review-directions": self._review_directions,
            "plan-experiment": self._plan_experiment,
            "execute-experiment": self._execute_experiment,
            "review-experiment": self._review_experiment,
            "reflect-direction": self._reflect_direction,
        }
        self.primitives = StagePrimitiveRegistry(handlers)

    def run(self, run_id: str) -> dict:
        run = self.world.run(run_id)
        self.primitives.validate(run["definition_snapshot"])
        self.agents.validate(run["definition_snapshot"])
        event = "run_resumed" if self.world.run_events(run_id) else "run_started"
        self._event(run_id, "control", event, {"pipeline_id": run["pipeline_id"]})
        signal = run["payload"].get("_signal")
        if (
            signal
            and signal.get("decision") == "reject"
            and signal["kind"] == "confirm_step"
        ):
            return self._reject_plan(run, signal["reason"])
        return self._drive(run_id, signal)

    def _reject_plan(self, run: dict, reason: str) -> dict:
        frame = _frame(run)
        self.world.ghost_node(run["payload"]["experiment_id"], reason)
        self.world.set_working(run["node_id"], False)
        payload = _stage_payload(
            {**run["payload"], "reason": reason},
            frame["cursor"],
            frame["values"],
            None,
        )
        event = {
            "actor": "human",
            "type": "plan_rejected",
            "payload": {"reason": reason},
        }
        return self.world.transition_run(
            run["id"], run["stage"], "paused", payload, event
        )

    def _drive(self, run_id: str, signal: dict | None = None) -> dict:
        while True:
            run = self.world.run(run_id)
            spec, frame = run["definition_snapshot"], _frame(run)
            if frame["cursor"] >= len(spec["stages"]):
                return self._complete(run_id)
            stage = spec["stages"][frame["cursor"]]
            self.world.update_run(run_id, stage["id"], "running")
            context = {"run": self.world.run(run_id), "values": frame["values"]}
            result = self.primitives.execute(stage, {**context, "signal": signal})
            signal = None
            if self.world.run(run_id)["status"] == "paused":
                return self.world.run(run_id)
            saved = self._save_stage(stage, result)
            if saved["status"] != "running":
                return saved

    def _save_stage(self, stage: dict, result: dict) -> dict:
        run = self.world.run(result["run_id"])
        frame, values = _frame(run), dict(_frame(run)["values"])
        values.update(result.get("values", {}))
        for key in result.get("drop", ()):
            values.pop(key, None)
        cursor = _next_cursor(
            run["definition_snapshot"], frame["cursor"], stage, result
        )
        gate = result.get("gate")
        payload = _stage_payload(run["payload"], cursor, values, gate)
        status = "waiting_human" if gate else "running"
        event = "gate_waiting" if gate else "stage_completed"
        return self._transition_stage(run, stage, status, payload, event)

    def _transition_stage(self, run, stage, status, payload, event) -> dict:
        return self.world.transition_run(
            run["id"],
            stage["id"],
            status,
            payload,
            {"actor": "control", "type": event, "payload": {"stage": stage["id"]}},
        )

    def _generate_directions(self, stage: dict, context: dict) -> dict:
        run = context["run"]
        origin = self.world.set_working(run["node_id"], True)
        count = int(run["payload"].get("count", 8))
        context = self._agent_context(run, origin["payload"])
        operation = f"{run['id']}:{stage['id']}:brainstorm"
        result = self.agents.brainstorm(context, count, stage["agent"], operation)
        self._record_agent(run["id"], "brainstormer", result)
        values = {"origin": origin["id"], "candidates": result["candidates"]}
        return _stage_result(run, values)

    def _deduplicate_directions(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], context["values"]
        origin = self.world.node(values["origin"])
        try:
            params = _policy_params(stage)
            pool = self._deduplicate(run, origin, values["candidates"], params)
        except RuntimeCapabilityError as error:
            self._pause(run["id"], str(error))
            return _stage_result(run)
        return _stage_result(run, {"pool": pool})

    def _select_directions(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], context["values"]
        count = int(run["payload"].get("select", 4))
        weight = float(_policy_params(stage).get("weight", 0.2))
        origin = self.world.node(values["origin"])
        query = self.embedding(origin["payload"].get("text", ""))
        selected = mmr(values["pool"], count, query, weight)
        directions = [_without_vector(item) for item in selected]
        return _stage_result(
            run, {"directions": directions}, drop=("candidates", "pool")
        )

    def _deduplicate(
        self, run: dict, origin: dict, candidates: list[dict], params: dict
    ) -> list[dict]:
        existing = self._existing_directions(run["project_id"])
        pool = []
        for candidate in candidates:
            candidate["vector"] = self.embedding(candidate["text"])
            match, score = self._nearest(candidate, [*existing, *pool])
            if match and self._is_duplicate(run, candidate, match, score, params):
                reflected = self._blocked_direction(
                    run, origin, candidate, match, score
                )
                if reflected:
                    pool.append(reflected)
            else:
                pool.append(candidate)
        return pool

    def _existing_directions(self, project_id: str) -> list[dict]:
        values = []
        for node in self.world.nodes(project_id):
            if node["kind"] != "direction":
                continue
            vector = self.world.embedding_for(node["id"]) or self.embedding(
                node["payload"].get("text", "")
            )
            values.append(
                {
                    "text": node["payload"].get("text", ""),
                    "vector": vector,
                    "node_id": node["id"],
                    "life_state": node["life_state"],
                }
            )
        return values

    def _nearest(
        self, candidate: dict, others: list[dict]
    ) -> tuple[dict | None, float]:
        if not others:
            return None, 0.0
        match = max(
            others, key=lambda item: cosine(candidate["vector"], item["vector"])
        )
        return match, cosine(candidate["vector"], match["vector"])

    def _is_duplicate(self, run, candidate, match, score, params) -> bool:
        if score > float(params.get("block", 0.8)):
            return True
        review = float(params.get("review", 0.6))
        if score < review:
            return False
        operation = f"{run['id']}:deduplicate:{candidate['text']}:{match['text']}"
        result = self.agents.pairwise(candidate["text"], match["text"], operation)
        self._record_agent(run["id"], "deduplicator", result)
        return result["duplicate"]

    def _blocked_direction(self, run, origin, candidate, match, score) -> dict:
        reason = f"与“{match['text']}”重合（cos={score:.2f}）"
        node = self._blocked_node(run, origin, candidate)
        if not node["rejection_reason"]:
            node = self.world.ghost_node(node["id"], reason)
            self._event(
                run["id"],
                "deduplicator",
                "candidate_blocked",
                {
                    "node_id": node["id"],
                    "reason": reason,
                },
            )
        return self._reflect_blocked(run, node, candidate, match, reason)

    def _reflect_blocked(self, run, node, candidate, match, reason) -> dict:
        context = {
            "candidate": candidate["text"],
            "overlap": {
                "node_id": match.get("node_id"),
                "text": match["text"],
            },
            "blocker": reason,
        }
        operation = f"{run['id']}:deduplicate:{node['id']}:reflect"
        value = self.agents.reconcile(context, self._author_agent(run), operation)
        self._record_agent(run["id"], "reflector", value)
        return {
            "title": value["title"],
            "text": value["text"],
            "vector": self.embedding(value["text"]),
            "lineage_id": node["lineage_id"],
        }

    def _author_agent(self, run: dict) -> str:
        stages = run["definition_snapshot"]["stages"]
        return next(
            stage["agent"]
            for stage in stages
            if stage.get("prompt") == "generate-directions"
        )

    def _blocked_node(self, run, origin, candidate) -> dict:
        existing = next(
            (
                node
                for node in self.world.nodes(run["project_id"])
                if node["kind"] == "direction"
                and node["life_state"] == "ghost"
                and node["parent_id"] == origin["id"]
                and node["payload"].get("text") == candidate["text"]
            ),
            None,
        )
        return existing or self._candidate_node(run, origin, candidate)

    def _candidate_node(self, run, origin, candidate) -> dict:
        lineage = candidate.get("lineage_id") or f"lineage:{secrets.token_hex(12)}"
        return self.world.create_node(
            run["project_id"],
            "direction",
            {"title": candidate["title"], "text": candidate["text"]},
            parent_id=origin["id"],
            lineage_id=lineage,
        )

    def _review_directions(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], dict(context["values"])
        key = f"review_index:{stage['id']}"
        index = int(values.get(key, 0))
        if context.get("signal"):
            index = self._resume_direction_review(
                stage, run, values, index, context["signal"]
            )
        while index < len(values["directions"]):
            waiting = self._review_direction(stage, run, values, index)
            if waiting:
                return waiting
            index += 1
            values[key] = index
            self._checkpoint(run["id"], values)
        if values.get("origin"):
            self.world.set_working(values["origin"], False)
        return _stage_result(run, values)

    def _review_direction(self, stage, run, values, index) -> dict | None:
        item = values["directions"][index]
        node = self._direction_node(run, values, item)
        values["directions"][index] = {"node_id": node["id"]}
        self._checkpoint(run["id"], values)
        if node["life_state"] != "pending":
            return None
        found, outcome = _stored_review(node)
        if not found:
            outcome = self._admission_review(
                run, node, "direction", agent=stage["agent"]
            )
        if outcome is None:
            gate = {"kind": "review", "node_id": node["id"]}
            return _stage_result(run, values, "conflict", gate)
        action = _exit_action(stage, "approve" if outcome else "reject")
        self._apply_direction_review(run, node, outcome, action, "方向双审完成")
        return None

    def _resume_direction_review(self, stage, run, values, index, signal) -> int:
        node = self.world.node(signal["node_id"])
        approved = signal["decision"] == "approve"
        action = _exit_action(stage, signal["decision"])
        self._apply_direction_review(run, node, approved, action, signal["reason"])
        values[f"review_index:{stage['id']}"] = index + 1
        return index + 1

    def _direction_node(self, run, values, item) -> dict:
        if item.get("node_id"):
            return self.world.node(item["node_id"])
        origin = self.world.node(values["origin"])
        return self._candidate_node(run, origin, item)

    def _apply_direction_review(self, run, node, approved, action, reason) -> None:
        expected = "admit" if approved else "ghost"
        if action != expected:
            raise ValueError(f"direction review requires action {expected}")
        self._resolve_node(run, node, approved, reason)

    def _plan_experiment(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], dict(context["values"])
        direction = self.world.set_working(run["node_id"], True)
        values.update(self._plan(run, direction, stage["agent"], values))
        self._checkpoint(run["id"], values)
        experiment = self._experiment(run, direction, values)
        values["experiment"] = experiment["id"]
        self._checkpoint(run["id"], values)
        review = self._audit_action(run, values)
        if review["decision"] == "reject":
            return self._reject_action(run, direction, experiment, review)
        steps = self._ensure_step(run, values["action"])
        return _stage_result(
            run,
            {"experiment": experiment["id"], "steps": steps},
            drop=("action", "title"),
        )

    def _experiment(self, run, direction, values) -> dict:
        node_id = values.get("experiment") or run["payload"].get("experiment_id")
        if node_id:
            return self.world.node(node_id)
        experiment = self._new_experiment(run, direction, values["title"])
        self._event(
            run["id"], "control", "experiment_created", {"node_id": experiment["id"]}
        )
        return experiment

    def _new_experiment(self, run: dict, direction: dict, title: str) -> dict:
        experiment = self.world.create_node(
            run["project_id"],
            "experiment",
            {"title": title, "goal": direction["payload"].get("text", "")},
            parent_id=direction["id"],
            lineage_id=direction["lineage_id"],
            working=True,
        )
        payload = {**run["payload"], "experiment_id": experiment["id"]}
        self.world.update_run(run["id"], run["stage"], "running", payload)
        return experiment

    def _plan(self, run: dict, direction: dict, agent: str, values: dict) -> dict:
        if values.get("action") is not None:
            return {"action": values["action"], "title": values["title"]}
        context = self._agent_context(run, direction["payload"])
        plan = self.agents.plan(context, agent, f"{run['id']}:plan")
        self._record_agent(run["id"], "planner", plan)
        return {"action": plan["action"], "title": plan["title"]}

    def _audit_action(self, run: dict, values: dict) -> dict:
        if values.get("action_review"):
            return values["action_review"]
        operation = f"{run['id']}:action-review"
        review = self.agents.audit_action({"action": values["action"]}, operation)
        self._record_agent(run["id"], "action-reviewer", review)
        values["action_review"] = clean(review)
        self._checkpoint(run["id"], values)
        return review

    def _reject_action(self, run, direction, experiment, review) -> dict:
        reason = review["argument"]
        self.world.ghost_node(
            experiment["id"], reason, {"action_review": clean(review)}
        )
        self.world.set_working(direction["id"], False)
        self._pause(run["id"], f"行动审核驳回：{reason}")
        return _stage_result(run)

    def _ensure_step(self, run: dict, action: dict) -> list[str]:
        step = self.world.add_step(
            run["id"], 1, "execute", action, not bool(run["auto"])
        )
        return [step["id"]]

    def _execute_experiment(self, stage: dict, context: dict) -> dict:
        run, signal = context["run"], context.get("signal")
        pending = self._pending_steps(run["id"])
        if pending and not run["auto"] and not signal:
            return _stage_result(run, gate={"kind": "confirm_step"})
        selected = pending if run["auto"] else pending[:1]
        for step in selected:
            self._execute_step(run, step)
        if self._pending_steps(run["id"]):
            return _stage_result(run, gate={"kind": "confirm_step"})
        outputs = [step["output"] for step in self.world.steps(run["id"])]
        return _stage_result(run, {"outputs": outputs})

    def _pending_steps(self, run_id: str) -> list[dict]:
        return [
            step
            for step in self.world.steps(run_id)
            if step["status"] in {"pending", "running"}
        ]

    def _execute_step(self, run: dict, step: dict) -> None:
        self.world.update_step(step["id"], "running")
        payload = {**step["payload"], "execution_id": step["id"]}
        output = self._execute_with_replay(run["project_id"], payload)
        status = (
            "completed"
            if self._verified_execution(run["project_id"], output)
            else "failed"
        )
        self.world.update_step(step["id"], status, output)
        self._event(
            run["id"], "runner", "tool_result", {"step_id": step["id"], **output}
        )

    def _execute_with_replay(self, project_id: str, payload: dict) -> dict:
        artifacts = ArtifactStore(self.world.artifacts_root, project_id)
        evidence = self.runner.run(payload)
        if not verify_evidence(evidence)["ok"]:
            return evidence
        artifact_id = persist_evidence_artifact(evidence, artifacts)
        replay = self.runner.replay(payload)
        return {
            **evidence,
            "artifact_id": artifact_id,
            "replay": self._replay_record(evidence, replay, artifacts),
        }

    def _replay_record(self, evidence: dict, replay: dict, artifacts) -> dict:
        comparison = compare_replay(evidence, replay)
        if not verify_evidence(replay)["ok"]:
            return comparison
        artifact_id = persist_evidence_artifact(replay, artifacts)
        return {**comparison, "artifact_id": artifact_id}

    def _verified_execution(self, project_id: str, output: dict) -> bool:
        if output.get("exit_code") != 0 or not output.get("replay", {}).get("ok"):
            return False
        artifacts = ArtifactStore(self.world.artifacts_root, project_id)
        artifact = verify_evidence_artifact(
            output, output.get("artifact_id", ""), artifacts
        )
        replay = output["replay"]
        return artifact["ok"] and replay.get("artifact_id") == output["artifact_id"]

    def _review_experiment(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], context["values"]
        experiment = self.world.node(values["experiment"])
        if experiment["life_state"] != "pending":
            outcome = "approve" if experiment["life_state"] == "admitted" else "reject"
            return _stage_result(run, outcome=outcome)
        if signal := context.get("signal"):
            return self._resume_experiment_review(
                stage, run, experiment, values, signal
            )
        outputs = values["outputs"]
        outcome = self._experiment_review(run, experiment, outputs, stage["agent"])
        if outcome is None:
            gate = {"kind": "review", "node_id": experiment["id"]}
            return _stage_result(run, outcome="conflict", gate=gate)
        self._apply_experiment_review(stage, run, experiment, outcome, outputs)
        return _stage_result(run, outcome="approve" if outcome else "reject")

    def _experiment_review(self, run, experiment, outputs, agent):
        mechanical = all(
            output and self._verified_execution(run["project_id"], output)
            for output in outputs
        )
        extra = {"mechanical": mechanical, "outputs": outputs}
        found, outcome = _stored_review(experiment)
        return (
            outcome if found else self._review_evidence(run, experiment, extra, agent)
        )

    def _review_evidence(self, run, experiment, extra, agent):
        self._audit_claims(run, experiment, "experiment", extra, agent)
        if not extra["mechanical"]:
            verdict = {
                "decision": "reject",
                "stance": "mechanical",
                "argument": "执行退出码或凭据校验失败",
                "evidence": ["execution.exit_code"],
            }
            self.world.update_node(experiment["id"], rebuttal={"mechanical": verdict})
            return False
        return self._admission_review(run, experiment, "experiment", extra, agent)

    def _resume_experiment_review(self, stage, run, experiment, values, signal):
        approved = signal["decision"] == "approve"
        self._apply_experiment_review(
            stage, run, experiment, approved, values["outputs"]
        )
        return _stage_result(run, outcome=signal["decision"])

    def _apply_experiment_review(self, stage, run, experiment, approved, outputs):
        action = _exit_action(stage, "approve" if approved else "reject")
        expected = "admit" if approved else "ghost"
        if action != expected:
            raise ValueError(f"experiment review requires action {expected}")
        self._resolve_experiment(
            run, self.world.node(experiment["id"]), approved, outputs
        )

    def _admission_review(self, run, node, subject, extra=None, agent=None):
        claims = self._audit_claims(run, node, subject, extra, agent)
        context = {
            "subject": subject,
            "node": node["payload"],
            "claims": claims,
            "evidence_nodes": self._review_evidence_nodes(run),
            **(extra or {}),
        }
        reviews = self._review_pair(run, node, subject, context, agent)
        self._store_reviews(node, reviews)
        decisions = [review.get("decision") == "approve" for review in reviews]
        if decisions[0] != decisions[1]:
            return None
        return decisions[0]

    def _store_reviews(self, node: dict, reviews: list[dict]) -> None:
        rebuttal = {
            "reviewer_a": clean(reviews[0]),
            "reviewer_b": clean(reviews[1]),
        }
        self.world.update_node(node["id"], rebuttal=rebuttal)

    def _audit_claims(self, run, node, subject, extra, agent) -> list[dict]:
        if claims := node["payload"].get("claims"):
            return claims
        context = {"subject": subject, "node": node["payload"], **(extra or {})}
        operation = f"{run['id']}:{subject}:{node['id']}:claims"
        value = self.agents.claims(context, agent, operation)
        self._record_agent(run["id"], "claim-auditor", value)
        claims = value["claims"]
        self.world.update_node(
            node["id"], payload={**node["payload"], "claims": claims}
        )
        return claims

    def _review_pair(self, run, node, subject, context, agent) -> list[dict]:
        reviews = []
        for stance in ("support", "challenge"):
            operation = f"{run['id']}:{subject}:{node['id']}:{stance}"
            review = self.agents.review(context, subject, stance, agent, operation)
            self._validate_review_evidence(run, review)
            self._record_agent(run["id"], f"reviewer-{stance}", review)
            reviews.append(review)
        return reviews

    def _review_evidence_nodes(self, run: dict) -> list[dict]:
        node_ids = [run["node_id"], *run["payload"].get("pins", [])]
        nodes = [self.world.node(node_id) for node_id in dict.fromkeys(node_ids)]
        admitted = [
            node
            for node in nodes
            if node["project_id"] == run["project_id"]
            and node["life_state"] == "admitted"
        ]
        return [{"id": node["id"], "kind": node["kind"]} for node in admitted]

    def _validate_review_evidence(self, run: dict, review: dict) -> None:
        if not review["evidence"]:
            raise ValueError("review evidence must reference an admitted node")
        for node_id in review["evidence"]:
            try:
                node = self.world.node(node_id)
            except KeyError as error:
                raise ValueError(
                    "review evidence must reference an admitted node"
                ) from error
            if (
                node["project_id"] != run["project_id"]
                or node["life_state"] != "admitted"
            ):
                raise ValueError("review evidence must reference an admitted node")

    def _resolve_node(self, run, node, approved: bool, reason: str) -> None:
        if approved:
            validate_project_claim_ids(self.world, node)
        result = self.world.resolve_direction_review(node["id"], approved, reason)
        lineage, current = result["lineage"], result["node"]
        if approved:
            self._queue_auto_research(run, current, lineage)
        self._pause_lineage(run, lineage, "同一谱系连续 2 次 review 驳回，已升级人工。")

    def _queue_auto_research(self, run, node, lineage) -> None:
        should_queue = run["auto"] and node["kind"] == "direction"
        if should_queue and not lineage["auto_paused"]:
            spec = self.pipelines.get("research")
            self.world.create_run(run["project_id"], node["id"], spec)

    def _resolve_experiment(self, run, experiment, approved, outputs) -> None:
        direction = self.world.node(run["node_id"])
        payload = {**experiment["payload"], "outputs": outputs}
        if approved:
            validate_project_claim_ids(self.world, {**experiment, "payload": payload})
        result = self.world.resolve_experiment_review(
            experiment["id"], direction["id"], approved, payload
        )
        lineage = result["lineage"]
        self._pause_lineage(run, lineage, "同一谱系连续 2 次驳回")

    def _pause_lineage(self, run, lineage, reason) -> None:
        if lineage["auto_paused"]:
            payload = {**run["payload"], "reason": reason}
            self.world.update_run(run["id"], run["stage"], "paused", payload)

    def _reflect_direction(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], dict(context["values"])
        if values.get("directions"):
            return _stage_result(run, {"directions": values["directions"]})
        experiment = self.world.node(values["experiment"])
        prompt = {"experiment": experiment["payload"], "outputs": values["outputs"]}
        operation = f"{run['id']}:{stage['id']}:reflect"
        value = self.agents.reflect(
            self._agent_context(run, prompt), stage["agent"], operation
        )
        self._record_agent(run["id"], "reflector", value)
        node = self._reflection_node(run, experiment, value)
        directions = [{"node_id": node["id"]}]
        self._checkpoint(run["id"], {**values, "directions": directions})
        return _stage_result(run, {"directions": directions})

    def _reflection_node(self, run, experiment, value):
        return self.world.create_node(
            run["project_id"],
            "direction",
            {"title": value["title"], "text": value["text"]},
            parent_id=run["node_id"],
            lineage_id=experiment["lineage_id"],
        )

    def _complete(self, run_id: str) -> dict:
        run = self.world.run(run_id)
        event = {"actor": "control", "type": "run_completed", "payload": {}}
        return self.world.transition_run(
            run_id, "complete", "completed", run["payload"], event
        )

    def _pause(self, run_id: str, reason: str) -> dict:
        run = self.world.run(run_id)
        payload = {**run["payload"], "reason": reason}
        event = {
            "actor": "control",
            "type": "run_paused",
            "payload": {"reason": reason},
        }
        return self.world.transition_run(run_id, "paused", "paused", payload, event)

    def _record_agent(self, run_id: str, actor: str, value: dict) -> None:
        if self._agent_event_exists(run_id, actor, value.get("_session_id")):
            return
        payload = {
            "stage_id": self.world.run(run_id)["stage"],
            "session_id": value.get("_session_id"),
            "turn_id": value.get("_turn_id"),
            "usage": value.get("_usage", {}),
        }
        self._event(run_id, actor, "agent_session", payload)

    def _agent_event_exists(self, run_id, actor, session_id) -> bool:
        return bool(session_id) and any(
            item["actor"] == actor
            and item["type"] == "agent_session"
            and item["payload"].get("session_id") == session_id
            for item in self.world.run_events(run_id)
        )

    def _checkpoint(self, run_id: str, values: dict) -> dict:
        run = self.world.run(run_id)
        if run["status"] == "paused":
            return run
        frame = _frame(run)
        payload = _stage_payload(run["payload"], frame["cursor"], values, None)
        return self.world.update_run(run_id, run["stage"], "running", payload)

    def _agent_context(self, run: dict, context: dict) -> dict:
        pins = [self._pin(node_id) for node_id in run["payload"].get("pins", [])]
        return {
            **context,
            "project_id": run["project_id"],
            "instruction": run["payload"].get("instruction", ""),
            "mode": run["payload"].get("mode", ""),
            "pins": pins,
        }

    def _pin(self, node_id: str) -> dict:
        node = self.world.node(node_id)
        return {"id": node["id"], "kind": node["kind"], "payload": node["payload"]}

    def _event(self, run_id: str, actor: str, event_type: str, payload: dict) -> None:
        self.world.record_run_event(run_id, actor, event_type, payload)


def _stage_result(run, values=None, outcome="next", gate=None, drop=()) -> dict:
    return {
        "run_id": run["id"],
        "values": values or {},
        "outcome": outcome,
        "gate": gate,
        "drop": drop,
    }


def _frame(run: dict) -> dict:
    return run["payload"].get("_pipeline", {"cursor": 0, "values": {}, "gate": None})


def _stage_payload(payload, cursor, values, gate) -> dict:
    result = {key: value for key, value in payload.items() if key != "_signal"}
    result["_pipeline"] = {"cursor": cursor, "values": values, "gate": gate}
    if values.get("experiment"):
        result["experiment_id"] = values["experiment"]
    if gate and gate.get("node_id"):
        result["conflict_node"] = gate["node_id"]
    elif "conflict_node" in result:
        del result["conflict_node"]
    return result


def _next_cursor(spec, cursor, stage, result) -> int:
    if result.get("gate"):
        return cursor
    exit_value = stage.get("on", {}).get(result.get("outcome"))
    target = (
        exit_value if isinstance(exit_value, str) else (exit_value or {}).get("next")
    )
    if not target:
        return cursor + 1
    return next(i for i, item in enumerate(spec["stages"]) if item["id"] == target)


def _exit_action(stage: dict, outcome: str) -> str | None:
    value = stage.get("on", {}).get(outcome)
    return value.get("action") if isinstance(value, dict) else None


def _policy_params(stage: dict) -> dict:
    value = stage.get("policy")
    return value.get("params", {}) if isinstance(value, dict) else {}


def clean(value: dict) -> dict:
    return {key: item for key, item in value.items() if not key.startswith("_")}


def _without_vector(value: dict) -> dict:
    return {key: item for key, item in value.items() if key != "vector"}


def _stored_review(node: dict) -> tuple[bool, bool | None]:
    rebuttal = node.get("rebuttal") or {}
    if mechanical := rebuttal.get("mechanical"):
        return True, mechanical.get("decision") == "approve"
    reviews = [rebuttal.get("reviewer_a"), rebuttal.get("reviewer_b")]
    if not all(reviews):
        return False, None
    decisions = [review.get("decision") == "approve" for review in reviews]
    return True, decisions[0] if decisions[0] == decisions[1] else None


def required(value: dict, field: str):
    if field not in value:
        raise ValueError(f"runtime response missing required field '{field}'")
    return value[field]


def validate_verdict(value: dict) -> dict:
    if value.get("decision") not in {"approve", "reject"}:
        raise ValueError("runtime field 'decision' must be approve or reject")
    if not isinstance(value.get("argument"), str) or not value["argument"].strip():
        raise ValueError("runtime field 'argument' must be non-empty text")
    evidence = value.get("evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) for item in evidence
    ):
        raise ValueError("runtime field 'evidence' must be a string list")
    return value


def validate_review_verdict(value: dict) -> dict:
    validate_verdict(value)
    needed = required(value, "needs_experiment")
    if not isinstance(needed, bool):
        raise TypeError("runtime field 'needs_experiment' must be boolean")
    return value


def validate_candidates(value, count: int) -> list[dict]:
    if not isinstance(value, list) or len(value) < count:
        raise ValueError(
            f"runtime field 'candidates' must contain at least {count} items"
        )
    return [_validate_candidate(candidate) for candidate in value[:count]]


def _validate_candidate(candidate) -> dict:
    if not isinstance(candidate, dict):
        raise TypeError("each candidate requires title and text")
    title = validate_title(required(candidate, "title"))
    text = required(candidate, "text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("each candidate requires text")
    return {"title": title, "text": text.strip()}


def validate_claims(value) -> list[dict]:
    claims = validate_claim_records(value)
    if not claims:
        raise ValueError("runtime field 'claims' must be a non-empty list")
    return claims


def default_engine(world: World, project_id: str, kernel) -> PipelineEngine:
    settings = load_settings()
    runtime = RuntimeClient(settings.runtime_url, project_id)
    runtime.bind_kernel(kernel)
    agents = AgentFacade(runtime, AgentRegistry(settings.agents_root))
    endpoint = os.environ["RW_EMBEDDING_ENDPOINT"]
    model = os.getenv("RW_EMBEDDING_MODEL", "qwen3.7-text-embedding")
    embedding = RuntimeEmbedding(runtime, endpoint, model)
    runner = RunnerClient(
        os.getenv("RUNNER_CONTROLLER_URL", "http://runner-controller:8096")
    )
    pipelines = PipelineRegistry(settings.pipelines_root, settings.pipeline_schema)
    return PipelineEngine(world, agents, embedding, runner, pipelines)


def fail_run(world: World, run_id: str, error: Exception) -> dict:
    result = error.result if isinstance(error, AgentResultError) else None
    return world.fail_run(run_id, error, result)


def _plan_title(value: dict) -> str:
    if not isinstance(required(value, "action"), dict):
        raise TypeError("runtime field 'action' must be an object")
    return validate_title(required(value, "title"))


def _pipeline_agents(pipeline: dict) -> set[str]:
    return {stage["agent"] for stage in pipeline["stages"] if stage["type"] == "prompt"}


BRAINSTORM_PROMPT = (
    "输入节点内容与 instruction 是研究约束，count 是候选数。严格执行 instruction，生成恰好 count 个相互差异显著、"
    "可证伪的研究方向。每个候选的 title 是简洁标题，硬性不超过 12 token；text 是完整正文。"
    '严格返回 {"candidates":[{"title":"...","text":"..."}]}。'
)
PAIR_PROMPT = (
    "判断 left 与 right 是否在研究问题、方法和可证伪结论上实质重复。"
    '严格返回 {"duplicate":true}，duplicate 只能是布尔值。'
)
PLAN_PROMPT = (
    "严格执行 instruction，只提交当前最值得执行的一个原子行动，不规划后续步骤。执行契约：行动在独立的一次性容器中运行，"
    "不能依赖其他行动的文件或状态；容器文件系统只读，仅 /tmp 可写（64MB、noexec），同一行动内可用 /tmp 暂存；"
    "使用 python:3.12-slim 与 Python 标准库或 busybox，禁止网络和未内置包；脚本内嵌 command，files 默认空对象，"
    "非空文件内容必须是 base64。所有输入变量必须进入计算并与明确基线比较；不得硬编码判定、阈值或事实，"
    "阈值只能由相邻观测的真实状态转变推导，无转变时必须报告 no_transition。stdout 最后一行必须是含 evidence_scope、"
    "measurements 与 decision 的 JSON 对象；合成数据只能支持程序或模型内部结论。退出码 0 表示执行成功。"
    "title 是本实验的简洁标题，硬性不超过 12 token。严格返回 "
    '{"title":"...","action":{"image":"busybox:1.36","command":["sh","-lc","..."],'
    '"files":{},"seed":0,"limits":{"cpus":1,"memory_mb":512,"pids":128,'
    '"wall_seconds":300}}}。'
)
ACTION_REVIEW_PROMPT = (
    "独立检查单个 action 的输入边界、可证伪性、资源限制与结果契约；不得执行。严格返回 "
    '{"decision":"approve|reject","argument":"...","evidence":["字段路径或约束"]}。'
)
CLAIM_AUDIT_PROMPT = (
    "把 node 与 outputs 中的结论拆成互不复合的原子 claim，逐条按已有证据审计。严格返回 "
    '{"claims":[{"text":"...","verdict":"supported|refuted|uncertain",'
    '"evidence":["来源或产物引用"]}]}。不得用总分替代逐条结论。'
)
MECHANISM_REVIEW_PROMPT = (
    "审核 direction 的机制新颖性、任务适配与可证伪性。stance=support 时给最强支持论证，"
    "stance=challenge 时主动寻找重合、泄漏与反例。evidence 只能引用 evidence_nodes 中的 admitted node id；"
    "缺少决定性实验时 needs_experiment=true。严格返回 "
    '{"decision":"approve|reject","argument":"...","evidence":["node:id"],"needs_experiment":false}。'
)
EVIDENCE_REVIEW_PROMPT = (
    "审核 experiment 的输入边界、执行凭据、产物哈希与逐条 claim 证据。stance=support 时给最强支持论证，"
    "stance=challenge 时主动寻找不可复现、越界与反例。evidence 只能引用 evidence_nodes 中的 admitted node id；"
    "仍需补实验时 needs_experiment=true。严格返回 "
    '{"decision":"approve|reject","argument":"...","evidence":["node:id"],"needs_experiment":false}。'
)
REVIEW_PROMPTS = {
    "direction": MECHANISM_REVIEW_PROMPT,
    "experiment": EVIDENCE_REVIEW_PROMPT,
}
RECONCILE_PROMPT = (
    "候选被 blocker 阻断。只使用 candidate、overlap 的相关切片与最小理由，生成一个机制上明确不同且可证伪的方向；"
    "不得请求完整隔离内容。title 是简洁标题，硬性不超过 12 token；text 是完整正文。"
    '严格返回 {"title":"...","text":"..."}。'
)
REFLECT_PROMPT = (
    "严格执行 instruction，基于实验输出与失败边界生成一个可证伪的新方向。"
    "title 是简洁标题，硬性不超过 12 token；text 是完整正文。"
    '严格返回 {"title":"...","text":"..."}。'
)
