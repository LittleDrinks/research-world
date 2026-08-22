from __future__ import annotations

import math
import os
import secrets
from dataclasses import dataclass

from .agents import AgentRegistry
from .clients import RunnerClient
from .config import load_settings
from .pipelines import PipelineRegistry, StagePrimitiveRegistry
from .runtime_client import RuntimeCapabilityError, RuntimeClient, RuntimeEmbedding
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


def mmr(candidates: list[dict], count: int, weight: float = 0.2) -> list[dict]:
    selected = []
    remaining = list(candidates)
    while remaining and len(selected) < count:
        best = max(remaining, key=lambda item: _mmr_score(item, selected, weight))
        selected.append(best)
        remaining.remove(best)
    return selected


def _mmr_score(candidate: dict, selected: list[dict], weight: float) -> float:
    similarity = max(
        (cosine(candidate["vector"], item["vector"]) for item in selected), default=0
    )
    return float(candidate.get("quality", 0)) - weight * similarity


class AgentFacade:
    def __init__(self, runtime: RuntimeClient, agents: AgentRegistry):
        self.runtime = runtime
        self.agents = agents

    def validate(self, pipeline: dict) -> None:
        for agent_id in _pipeline_agents(pipeline):
            self.agents.get(agent_id)

    def _call(
        self, agent_id: str, instruction: str, payload: dict, required: tuple[str, ...]
    ) -> dict:
        return self.runtime.json(
            self.agents.get(agent_id), instruction, payload, required
        )

    def brainstorm(self, context: dict, count: int, agent: str) -> dict:
        value = self._call(
            agent, BRAINSTORM_PROMPT, {**context, "count": count}, ("candidates",)
        )
        candidates = required(value, "candidates")
        if not isinstance(candidates, list) or len(candidates) < count:
            raise ValueError(
                f"runtime field 'candidates' must contain at least {count} items"
            )
        return {**value, "candidates": candidates[:count]}

    def pairwise(self, left: str, right: str) -> dict:
        value = self._call(
            "independent-reviewer",
            PAIR_PROMPT,
            {"left": left, "right": right},
            ("duplicate",),
        )
        duplicate = required(value, "duplicate")
        if not isinstance(duplicate, bool):
            raise ValueError("runtime field 'duplicate' must be boolean")
        return value

    def plan(self, direction: dict, agent: str) -> dict:
        value = self._call(agent, PLAN_PROMPT, direction, ("steps",))
        required(value, "steps")
        return value

    def review(self, context: dict, reviewer: str, agent: str) -> dict:
        fields = ("decision", "quality", "diversity", "rebuttal")
        value = self._call(
            agent, REVIEW_PROMPT, {**context, "reviewer": reviewer}, fields
        )
        return value

    def reflect(self, context: dict, agent: str) -> dict:
        return self._call(agent, REFLECT_PROMPT, context, ("text",))


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
        self._event(
            run_id, "control", "run_started", {"pipeline_id": run["pipeline_id"]}
        )
        return self._drive(run_id)

    def confirm(self, run_id: str) -> dict:
        run = self.world.run(run_id)
        gate = _frame(run).get("gate")
        if run["status"] != "waiting_human" or not gate:
            raise ValueError("run is not waiting for confirmation")
        if gate["kind"] != "confirm_step":
            raise ValueError("run is not waiting for step confirmation")
        return self._drive(run_id, {"kind": "confirm_step"})

    def resolve(self, run_id: str, decision: str, reason: str) -> dict:
        run = self.world.run(run_id)
        gate = _frame(run).get("gate")
        if run["status"] != "waiting_human" or not gate:
            raise ValueError("run has no review conflict")
        if gate["kind"] != "review" or decision not in {"approve", "reject"}:
            raise ValueError("run has no matching review decision")
        signal = {"kind": "review", "decision": decision, "reason": reason, **gate}
        return self._drive(run_id, signal)

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
        self._event(run["id"], "control", event, {"stage": stage["id"]})
        return self.world.update_run(run["id"], stage["id"], status, payload)

    def _generate_directions(self, stage: dict, context: dict) -> dict:
        run = context["run"]
        origin = self.world.set_working(run["node_id"], True)
        count = int(run["payload"].get("count", 8))
        context = self._agent_context(run, origin["payload"])
        result = self.agents.brainstorm(context, count, stage["agent"])
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
        selected = mmr(values["pool"], count, weight)
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
                self._blocked_direction(run, origin, candidate, match, score)
            else:
                pool.append(candidate)
        return pool

    def _existing_directions(self, project_id: str) -> list[dict]:
        values = []
        for node in self.world.nodes(project_id):
            if node["kind"] != "direction" or node["life_state"] == "ghost":
                continue
            vector = self.world.embedding_for(node["id"]) or self.embedding(
                node["payload"].get("text", "")
            )
            values.append(
                {
                    "text": node["payload"].get("text", ""),
                    "vector": vector,
                    "node_id": node["id"],
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
        result = self.agents.pairwise(candidate["text"], match["text"])
        self._record_agent(run["id"], "deduplicator", result)
        return result["duplicate"]

    def _blocked_direction(self, run, origin, candidate, match, score) -> None:
        reason = (
            f"与“{match['text']}”重合（cos={score:.2f}），已阻断并转入 reflect/合并。"
        )
        node = self._candidate_node(run, origin, candidate, "ghost")
        self.world.update_node(node["id"], rejection_reason=reason)
        self._event(
            run["id"],
            "deduplicator",
            "candidate_blocked",
            {"node_id": node["id"], "reason": reason},
        )

    def _candidate_node(self, run, origin, candidate, life_state="pending") -> dict:
        lineage = f"lineage:{secrets.token_hex(12)}"
        payload = {
            "text": candidate["text"],
            "quality": float(candidate.get("quality", 0)),
        }
        return self.world.create_node(
            run["project_id"],
            "direction",
            payload,
            parent_id=origin["id"],
            lineage_id=lineage,
            life_state=life_state,
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
        if values.get("origin"):
            self.world.set_working(values["origin"], False)
        return _stage_result(run, values)

    def _review_direction(self, stage, run, values, index) -> dict | None:
        item = values["directions"][index]
        node = self._direction_node(run, values, item)
        values["directions"][index] = {"node_id": node["id"]}
        outcome = self._double_review(run, node, "direction", agent=stage["agent"])
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
        run = context["run"]
        direction = self.world.set_working(run["node_id"], True)
        experiment = self._new_experiment(run, direction)
        self._event(
            run["id"],
            "control",
            "experiment_created",
            {"node_id": experiment["id"]},
        )
        steps = self._plan_steps(run, direction, stage["agent"])
        values = {"experiment": experiment["id"], "steps": steps}
        return _stage_result(run, values)

    def _new_experiment(self, run: dict, direction: dict) -> dict:
        experiment = self.world.create_node(
            run["project_id"],
            "experiment",
            {"title": "待执行实验", "goal": direction["payload"].get("text", "")},
            parent_id=direction["id"],
            lineage_id=direction["lineage_id"],
            working=True,
        )
        payload = {**run["payload"], "experiment_id": experiment["id"]}
        self.world.update_run(run["id"], run["stage"], "running", payload)
        return experiment

    def _plan_steps(self, run: dict, direction: dict, agent: str) -> list[str]:
        context = self._agent_context(run, direction["payload"])
        plan = self.agents.plan(context, agent)
        self._record_agent(run["id"], "planner", plan)
        ids = []
        for ordinal, step in enumerate(plan["steps"], 1):
            saved = self.world.add_step(
                run["id"], ordinal, "execute", step, not bool(run["auto"])
            )
            ids.append(saved["id"])
        return ids

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
            step for step in self.world.steps(run_id) if step["status"] == "pending"
        ]

    def _execute_step(self, run: dict, step: dict) -> None:
        self.world.update_step(step["id"], "running")
        output = self.runner.run(step["payload"])
        status = "completed" if output.get("exit_code") == 0 else "failed"
        self.world.update_step(step["id"], status, output)
        self._event(
            run["id"], "runner", "tool_result", {"step_id": step["id"], **output}
        )

    def _review_experiment(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], context["values"]
        experiment = self.world.node(values["experiment"])
        if signal := context.get("signal"):
            return self._resume_experiment_review(
                stage, run, experiment, values, signal
            )
        outputs = values["outputs"]
        mechanical = all(output and output.get("exit_code") == 0 for output in outputs)
        extra = {"mechanical": mechanical, "outputs": outputs}
        outcome = self._review_evidence(run, experiment, extra, stage["agent"])
        if outcome is None:
            gate = {"kind": "review", "node_id": experiment["id"]}
            return _stage_result(run, outcome="conflict", gate=gate)
        self._apply_experiment_review(stage, run, experiment, outcome, outputs)
        return _stage_result(run, outcome="approve" if outcome else "reject")

    def _review_evidence(self, run, experiment, extra, agent):
        if not extra["mechanical"]:
            return False
        return self._double_review(run, experiment, "experiment", extra, agent)

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
        self._resolve_experiment(run, experiment, approved, outputs)

    def _double_review(self, run, node, subject, extra=None, agent=None) -> bool | None:
        context = {"subject": subject, "node": node["payload"], **(extra or {})}
        reviews = [self.agents.review(context, name, agent) for name in ("A", "B")]
        for name, review in zip(("A", "B"), reviews, strict=True):
            event = {**review, "node_id": node["id"], "subject": subject}
            self._record_agent(run["id"], f"reviewer-{name.lower()}", event)
        self.world.update_node(
            node["id"],
            rebuttal={"reviewer_a": clean(reviews[0]), "reviewer_b": clean(reviews[1])},
        )
        decisions = [review.get("decision") == "approve" for review in reviews]
        if decisions[0] != decisions[1]:
            return None
        return decisions[0]

    def _resolve_node(self, run, node, approved: bool, reason: str) -> None:
        lineage = self.world.register_review(node["lineage_id"], approved)
        if approved:
            self.world.admit_node(node["id"])
            self._queue_auto_research(run, node, lineage)
        else:
            current = self.world.node(node["id"])
            self.world.ghost_node(node["id"], reason, current.get("rebuttal"))
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
            self.world.admit_node(experiment["id"], payload)
            self.world.add_edge(experiment["id"], direction["id"], "supports")
        else:
            reason = "机械证据审计或双审未通过"
            current = self.world.node(experiment["id"])
            self.world.ghost_node(experiment["id"], reason, current.get("rebuttal"))
            self.world.add_edge(experiment["id"], direction["id"], "refutes")
        self._resolve_direction(direction, approved)
        lineage = self.world.register_review(direction["lineage_id"], approved)
        self._pause_lineage(run, lineage, "同一谱系连续 2 次驳回")

    def _pause_lineage(self, run, lineage, reason) -> None:
        if lineage["auto_paused"]:
            payload = {**run["payload"], "reason": reason}
            self.world.update_run(run["id"], run["stage"], "paused", payload)

    def _resolve_direction(self, direction: dict, approved: bool) -> None:
        if direction["direction_status"] == "proposed":
            state = "supported" if approved else "refuted"
            self.world.update_node(
                direction["id"], direction_status=state, working=False
            )
        else:
            self.world.set_working(direction["id"], False)

    def _reflect_direction(self, stage: dict, context: dict) -> dict:
        run, values = context["run"], context["values"]
        experiment = self.world.node(values["experiment"])
        outputs = values["outputs"]
        context = {"experiment": experiment["payload"], "outputs": outputs}
        value = self.agents.reflect(self._agent_context(run, context), stage["agent"])
        self._record_agent(run["id"], "reflector", value)
        node = self.world.create_node(
            run["project_id"],
            "direction",
            {"text": value["text"]},
            parent_id=experiment["id"],
            lineage_id=experiment["lineage_id"],
        )
        return _stage_result(run, {"directions": [{"node_id": node["id"]}]})

    def _complete(self, run_id: str) -> dict:
        self._event(run_id, "control", "run_completed", {})
        return self.world.update_run(run_id, "complete", "completed")

    def _pause(self, run_id: str, reason: str) -> dict:
        self._event(run_id, "control", "run_paused", {"reason": reason})
        return self.world.update_run(run_id, "paused", "paused", {"reason": reason})

    def _record_agent(self, run_id: str, actor: str, value: dict) -> None:
        payload = {
            "stage_id": self.world.run(run_id)["stage"],
            "session_id": value.get("_session_id"),
            "turn_id": value.get("_turn_id"),
            "usage": value.get("_usage", {}),
        }
        self._event(run_id, actor, "agent_session", payload)

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
    result = {
        **payload,
        "_pipeline": {"cursor": cursor, "values": values, "gate": gate},
    }
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


def required(value: dict, field: str):
    if field not in value:
        raise ValueError(f"runtime response missing required field '{field}'")
    return value[field]


def default_engine(world: World, project_id: str) -> PipelineEngine:
    settings = load_settings()
    runtime = RuntimeClient(settings.runtime_url, world, project_id)
    agents = AgentFacade(runtime, AgentRegistry(settings.agents_root))
    model = os.getenv("RW_EMBEDDING_MODEL", "qwen3.7-text-embedding")
    embedding = RuntimeEmbedding(runtime, model)
    runner = RunnerClient(
        os.getenv("RUNNER_CONTROLLER_URL", "http://runner-controller:8096")
    )
    pipelines = PipelineRegistry(settings.pipelines_root, settings.pipeline_schema)
    return PipelineEngine(world, agents, embedding, runner, pipelines)


def fail_run(world: World, run_id: str, error: Exception) -> dict:
    run = world.run(run_id)
    _release_run_nodes(world, run)
    payload = {**run["payload"], "error": str(error)}
    world.record_run_event(run_id, "control", "run_failed", {"error": str(error)})
    return world.update_run(run_id, "failed", "failed", payload)


def _release_run_nodes(world: World, run: dict) -> None:
    node_ids = {run["node_id"], run["payload"].get("experiment_id")}
    for node_id in node_ids - {None}:
        world.set_working(node_id, False)


def _pipeline_agents(pipeline: dict) -> set[str]:
    return {stage["agent"] for stage in pipeline["stages"] if stage["type"] == "prompt"}


BRAINSTORM_PROMPT = (
    "输入节点内容与 instruction 是研究约束，count 是候选数。严格执行 instruction，生成恰好 count 个相互差异显著、"
    '可证伪的研究方向。严格返回 {"candidates":[{"text":"...","quality":0.0}]}，quality 范围 0-1。'
)
PAIR_PROMPT = (
    "判断 left 与 right 是否在研究问题、方法和可证伪结论上实质重复。"
    '严格返回 {"duplicate":true}，duplicate 只能是布尔值。'
)
PLAN_PROMPT = (
    "严格执行 instruction，把输入方向拆为可独立确认的最小实验步骤。执行契约：每个步骤都是独立的一次性容器，"
    "步骤之间不共享任何文件或状态，必须各自自包含；容器文件系统只读，仅 /tmp 可写（64MB、noexec），同一步骤内可用 /tmp 暂存；"
    "输入数据放 files（base64，挂载于只读 /workspace）；一切结论经 stdout 输出，退出码 0 表示成功。严格返回 "
    '{"steps":[{"image":"busybox:1.36","command":["sh","-lc","..."],'
    '"files":{},"seed":0,"limits":{"cpus":1,"memory_mb":512,"pids":128}}]}。'
)
REVIEW_PROMPT = (
    "机械审计优先，再独立评价质量与多样性。严格返回 "
    '{"decision":"approve","quality":0.0,"diversity":0.0,"rebuttal":"..."}；'
    "decision 只能是 approve 或 reject，分数范围 0-1。"
)
REFLECT_PROMPT = '严格执行 instruction，基于实验输出与失败边界生成一个可证伪的新方向。严格返回 {"text":"..."}。'
