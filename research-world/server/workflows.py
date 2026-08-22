from __future__ import annotations

import math
import os
import secrets
from dataclasses import dataclass

from .clients import RunnerClient
from .config import load_settings
from .library import resolve_assembly
from .pipelines import PipelineRegistry
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
    def __init__(self, runtime: RuntimeClient, assembly: list[dict]):
        self.runtime = runtime
        self.assembly = assembly

    def _call(self, role: str, instruction: str, payload: dict) -> dict:
        return self.runtime.json(
            role,
            instruction,
            payload,
            tools=runtime_tools(self.assembly),
            prompt_segments=prompt_segments(self.assembly),
        )

    def brainstorm(self, context: dict, count: int) -> dict:
        value = self._call(
            "科研构思助手", BRAINSTORM_PROMPT, {**context, "count": count}
        )
        candidates = required(value, "candidates")
        if not isinstance(candidates, list) or len(candidates) < count:
            raise ValueError(
                f"runtime field 'candidates' must contain at least {count} items"
            )
        return {**value, "candidates": candidates[:count]}

    def pairwise(self, left: str, right: str) -> bool:
        value = self._call(
            "科研新颖性裁决者", PAIR_PROMPT, {"left": left, "right": right}
        )
        return bool(required(value, "duplicate"))

    def plan(self, direction: dict) -> dict:
        value = self._call("科研实验规划者", PLAN_PROMPT, direction)
        required(value, "steps")
        return value

    def review(self, context: dict, reviewer: str) -> dict:
        value = self._call(f"独立审查者 {reviewer}", REVIEW_PROMPT, context)
        for field in ("decision", "quality", "diversity", "rebuttal"):
            required(value, field)
        return value

    def reflect(self, context: dict) -> dict:
        value = self._call("科研反思助手", REFLECT_PROMPT, context)
        required(value, "text")
        return value


def runtime_tools(packages: list[dict]) -> list[dict]:
    tools = []
    for package in packages:
        if package["name"] == "fs":
            tools.append({"type": "fs"})
        for tool in package.get("tools", []):
            tools.append(
                {
                    "type": "webhook",
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters")
                    or {"type": "object", "properties": {}},
                }
            )
    return tools


def prompt_segments(packages: list[dict]) -> list[str]:
    return [
        package["prompt_segment"]
        for package in packages
        if package.get("prompt_segment")
    ]


@dataclass
class PipelineEngine:
    world: World
    agents: object
    embedding: object
    runner: object
    pipelines: object

    def run(self, run_id: str) -> dict:
        run = self.world.run(run_id)
        self._event(
            run_id, "control", "run_started", {"pipeline_id": run["pipeline_id"]}
        )
        handlers = {"brainstorm": self._brainstorm, "research": self._research}
        handler = handlers.get(run["pipeline_id"])
        if handler is None:
            raise ValueError(f"pipeline has no executor: {run['pipeline_id']}")
        return handler(run)

    def confirm(self, run_id: str) -> dict:
        run = self.world.run(run_id)
        if run["status"] != "waiting_human":
            raise ValueError("run is not waiting for confirmation")
        if run["stage"] == "created":
            return self.run(run_id)
        step = next(
            (item for item in self.world.steps(run_id) if item["status"] == "pending"),
            None,
        )
        return self._execute_confirmed(run, step)

    def resolve(self, run_id: str, decision: str, reason: str) -> dict:
        run = self.world.run(run_id)
        node_id = run["payload"].get("conflict_node")
        if run["status"] != "waiting_human" or not node_id:
            raise ValueError("run has no review conflict")
        node = self.world.node(node_id)
        approved = decision == "approve"
        if node["kind"] == "experiment":
            outputs = [step["output"] for step in self.world.steps(run_id)]
            self._resolve_experiment(run, node, approved, outputs)
            return self._reflect(run, node, outputs)
        self._resolve_node(run, node, approved, reason)
        return self._finish_unless_paused(run_id)

    def _brainstorm(self, run: dict) -> dict:
        origin = self.world.set_working(run["node_id"], True)
        self.world.update_run(run["id"], "brainstorm", "running")
        count = int(run["payload"].get("count", 8))
        result = self.agents.brainstorm(
            self._agent_context(run, origin["payload"]), count
        )
        self._record_agent(run["id"], "brainstormer", result)
        candidates = result["candidates"]
        try:
            pool = self._deduplicate(run, origin, candidates)
        except RuntimeCapabilityError as error:
            return self._pause(run["id"], str(error))
        selected = mmr(pool, int(run["payload"].get("select", 4)))
        return self._review_brainstorm(run, origin, selected)

    def _deduplicate(
        self, run: dict, origin: dict, candidates: list[dict]
    ) -> list[dict]:
        existing = self._existing_directions(run["project_id"])
        pool = []
        for candidate in candidates:
            candidate["vector"] = self.embedding(candidate["text"])
            match, score = self._nearest(candidate, [*existing, *pool])
            if match and self._is_duplicate(candidate, match, score):
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

    def _is_duplicate(self, candidate: dict, match: dict, score: float) -> bool:
        if score > 0.8:
            return True
        return score >= 0.6 and self.agents.pairwise(candidate["text"], match["text"])

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

    def _review_brainstorm(self, run, origin, selected) -> dict:
        for candidate in selected:
            node = self._candidate_node(run, origin, candidate)
            outcome = self._double_review(run, node, "direction")
            if outcome is None:
                self.world.set_working(origin["id"], False)
                return self.world.run(run["id"])
            self._resolve_node(run, node, outcome, "方向双审完成")
        self.world.set_working(origin["id"], False)
        return self._complete(run["id"])

    def _research(self, run: dict) -> dict:
        direction = self.world.set_working(run["node_id"], True)
        experiment = self._new_experiment(run, direction)
        payload = {**run["payload"], "experiment_id": experiment["id"]}
        self.world.update_run(run["id"], "plan", "running", payload)
        self._event(
            run["id"],
            "control",
            "experiment_created",
            {"node_id": experiment["id"]},
        )
        self._plan_steps(run, direction)
        status = "running" if run["auto"] else "waiting_human"
        self.world.update_run(run["id"], "execute", status, payload)
        current = self.world.run(run["id"])
        return self._execute_all(current) if run["auto"] else current

    def _new_experiment(self, run: dict, direction: dict) -> dict:
        experiment = self.world.create_node(
            run["project_id"],
            "experiment",
            {"title": "待执行实验", "goal": direction["payload"].get("text", "")},
            parent_id=direction["id"],
            lineage_id=direction["lineage_id"],
            working=True,
        )
        return experiment

    def _plan_steps(self, run: dict, direction: dict) -> None:
        plan = self.agents.plan(self._agent_context(run, direction["payload"]))
        self._record_agent(run["id"], "planner", plan)
        for ordinal, step in enumerate(plan["steps"], 1):
            self.world.add_step(
                run["id"], ordinal, "execute", step, not bool(run["auto"])
            )

    def _execute_all(self, run: dict) -> dict:
        for step in self.world.steps(run["id"]):
            self._execute_step(run, step)
        return self._review_experiment(run)

    def _execute_confirmed(self, run: dict, step: dict | None) -> dict:
        if step:
            self._execute_step(run, step)
        remaining = any(
            item["status"] == "pending" for item in self.world.steps(run["id"])
        )
        if remaining:
            return self.world.update_run(run["id"], "execute", "waiting_human")
        return self._review_experiment(run)

    def _execute_step(self, run: dict, step: dict) -> None:
        self.world.update_step(step["id"], "running")
        output = self.runner.run(step["payload"])
        status = "completed" if output.get("exit_code") == 0 else "failed"
        self.world.update_step(step["id"], status, output)
        self._event(
            run["id"], "runner", "tool_result", {"step_id": step["id"], **output}
        )

    def _review_experiment(self, run: dict) -> dict:
        experiment = self.world.node(run["payload"]["experiment_id"])
        outputs = [step["output"] for step in self.world.steps(run["id"])]
        mechanical = all(output and output.get("exit_code") == 0 for output in outputs)
        outcome = (
            self._double_review(
                run,
                experiment,
                "experiment",
                {"mechanical": mechanical, "outputs": outputs},
            )
            if mechanical
            else False
        )
        if outcome is None:
            return self.world.run(run["id"])
        self._resolve_experiment(run, experiment, bool(outcome), outputs)
        return self._reflect(run, experiment, outputs)

    def _double_review(self, run, node, subject, extra=None) -> bool | None:
        context = {"subject": subject, "node": node["payload"], **(extra or {})}
        reviews = [self.agents.review(context, name) for name in ("A", "B")]
        for name, review in zip(("A", "B"), reviews, strict=True):
            event = {**review, "node_id": node["id"], "subject": subject}
            self._record_agent(run["id"], f"reviewer-{name.lower()}", event)
        self.world.update_node(
            node["id"],
            rebuttal={"reviewer_a": clean(reviews[0]), "reviewer_b": clean(reviews[1])},
        )
        decisions = [review.get("decision") == "approve" for review in reviews]
        if decisions[0] != decisions[1]:
            payload = {**run["payload"], "conflict_node": node["id"]}
            self.world.update_run(run["id"], "review", "waiting_human", payload)
            return None
        return decisions[0]

    def _resolve_node(self, run, node, approved: bool, reason: str) -> None:
        lineage = self.world.register_review(node["lineage_id"], approved)
        if approved:
            self.world.admit_node(node["id"])
            if (
                run["auto"]
                and node["kind"] == "direction"
                and not lineage["auto_paused"]
            ):
                self.world.create_run(
                    run["project_id"], node["id"], self.pipelines.get("research")
                )
        else:
            self.world.ghost_node(node["id"], reason, node.get("rebuttal"))
        if lineage["auto_paused"]:
            payload = {
                **run["payload"],
                "reason": "同一谱系连续 2 次 review 驳回，已升级人工。",
            }
            self.world.update_run(run["id"], "review", "paused", payload)

    def _resolve_experiment(self, run, experiment, approved, outputs) -> None:
        direction = self.world.node(run["node_id"])
        payload = {**experiment["payload"], "outputs": outputs}
        if approved:
            self.world.admit_node(experiment["id"], payload)
            self.world.add_edge(experiment["id"], direction["id"], "supports")
        else:
            self.world.ghost_node(
                experiment["id"], "机械证据审计或双审未通过", experiment.get("rebuttal")
            )
            self.world.add_edge(experiment["id"], direction["id"], "refutes")
        self._resolve_direction(direction, approved)
        lineage = self.world.register_review(direction["lineage_id"], approved)
        if lineage["auto_paused"]:
            self.world.update_run(
                run["id"],
                "review",
                "paused",
                {**run["payload"], "reason": "同一谱系连续 2 次驳回"},
            )

    def _resolve_direction(self, direction: dict, approved: bool) -> None:
        if direction["direction_status"] == "proposed":
            state = "supported" if approved else "refuted"
            self.world.update_node(
                direction["id"], direction_status=state, working=False
            )
        else:
            self.world.set_working(direction["id"], False)

    def _reflect(self, run, experiment, outputs) -> dict:
        if self.world.run(run["id"])["status"] == "paused":
            return self.world.run(run["id"])
        context = {"experiment": experiment["payload"], "outputs": outputs}
        value = self.agents.reflect(self._agent_context(run, context))
        self._record_agent(run["id"], "reflector", value)
        node = self.world.create_node(
            run["project_id"],
            "direction",
            {"text": value["text"]},
            parent_id=experiment["id"],
            lineage_id=experiment["lineage_id"],
        )
        outcome = self._double_review(run, node, "direction")
        if outcome is None:
            return self.world.run(run["id"])
        self._resolve_node(run, node, outcome, "反思方向双审未通过")
        return self._finish_unless_paused(run["id"])

    def _finish_unless_paused(self, run_id: str) -> dict:
        if self.world.run(run_id)["status"] == "paused":
            return self.world.run(run_id)
        return self._complete(run_id)

    def _complete(self, run_id: str) -> dict:
        self._event(run_id, "control", "run_completed", {})
        return self.world.update_run(run_id, "complete", "completed")

    def _pause(self, run_id: str, reason: str) -> dict:
        self._event(run_id, "control", "run_paused", {"reason": reason})
        return self.world.update_run(run_id, "paused", "paused", {"reason": reason})

    def _record_agent(self, run_id: str, actor: str, value: dict) -> None:
        payload = {
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


def clean(value: dict) -> dict:
    return {key: item for key, item in value.items() if not key.startswith("_")}


def required(value: dict, field: str):
    if field not in value:
        raise ValueError(f"runtime response missing required field '{field}'")
    return value[field]


def default_engine(world: World, project_id: str) -> PipelineEngine:
    settings = load_settings()
    assembly = resolve_assembly(world.project(project_id)["assembly"])
    runtime = RuntimeClient(settings.runtime_url, world, project_id)
    agents = AgentFacade(runtime, assembly)
    model = os.getenv("RW_EMBEDDING_MODEL", "qwen3.7-text-embedding")
    embedding = RuntimeEmbedding(runtime, model)
    runner = RunnerClient(
        os.getenv("RUNNER_CONTROLLER_URL", "http://runner-controller:8096")
    )
    pipelines = PipelineRegistry(settings.pipelines_root, settings.pipeline_schema)
    return PipelineEngine(world, agents, embedding, runner, pipelines)


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
