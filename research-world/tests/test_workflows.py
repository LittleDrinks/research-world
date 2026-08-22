from __future__ import annotations

import pytest

from server.app import _run_action, run_view
from server.workflows import AgentFacade, PipelineEngine, fail_run, mmr


def brainstorm_pipeline(pipeline_id="brainstorm"):
    stages = [
        stage("generate", "prompt", "generate-directions", agent="assistant"),
        stage(
            "deduplicate", "tool", "deduplicate-directions", policy="cosine-threshold"
        ),
        stage("select", "tool", "select-directions", policy="mmr"),
        review_stage("review", "review-directions"),
    ]
    return {"id": pipeline_id, "name": pipeline_id, "stages": stages}


def research_pipeline(pipeline_id="research"):
    return {
        "id": pipeline_id,
        "name": pipeline_id,
        "stages": [
            stage("plan", "prompt", "plan-experiment", agent="assistant"),
            stage(
                "execute",
                "tool",
                "execute-experiment",
                policy="mechanical-audit",
            ),
            review_stage("review", "review-experiment"),
            stage("reflect", "prompt", "reflect-direction", agent="assistant"),
            review_stage("review-reflection", "review-directions"),
        ],
    }


def stage(stage_id, stage_type, primitive, **values):
    key = "prompt" if stage_type == "prompt" else "tool"
    return {"id": stage_id, "type": stage_type, key: primitive, **values}


def review_stage(stage_id, primitive):
    return {
        **stage(stage_id, "prompt", primitive, agent="reviewer"),
        "repeat": 2,
        "policy": "unanimous-review",
        "on": {
            "approve": {"action": "admit"},
            "reject": {"action": "ghost"},
            "conflict": {"action": "wait_human"},
        },
    }


class FakePipelines:
    def get(self, pipeline_id):
        if pipeline_id == "research":
            return research_pipeline()
        return brainstorm_pipeline(pipeline_id)


class FakeEmbedding:
    def __init__(self, vectors):
        self.vectors = vectors

    def __call__(self, text):
        return self.vectors[text]


class FakeRunner:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code
        self.calls = []

    def run(self, step):
        self.calls.append(step)
        return {
            "exit_code": self.exit_code,
            "stdout": "measured",
            "usage": {"wall_ms": 10},
        }


class FakeAgents:
    def __init__(self, candidates=None, decisions=None, steps=None):
        self.candidates = candidates or []
        self.decisions = list(decisions or [])
        self.steps = steps or [{"image": "busybox:1.36", "command": ["true"]}]
        self.pairs = []
        self.brainstorm_contexts = []
        self.plan_contexts = []
        self.reflect_contexts = []
        self.agent_ids = []

    def validate(self, pipeline):
        return None

    def brainstorm(self, context, count, agent=None, operation_id=None):
        self.brainstorm_contexts.append(context)
        self.agent_ids.append(("brainstorm", agent))
        return {"candidates": self.candidates[:count]}

    def pairwise(self, left, right, operation_id=None):
        self.pairs.append((left, right))
        return {"duplicate": True}

    def plan(self, direction, agent=None, operation_id=None):
        self.plan_contexts.append(direction)
        self.agent_ids.append(("plan", agent))
        return {"steps": self.steps}

    def review(self, context, reviewer, agent=None, operation_id=None):
        self.agent_ids.append(("review", agent))
        decision = self.decisions.pop(0) if self.decisions else "approve"
        return {
            "decision": decision,
            "quality": 0.8,
            "diversity": 0.7,
            "rebuttal": reviewer,
        }

    def reflect(self, context, agent=None, operation_id=None):
        self.reflect_contexts.append(context)
        self.agent_ids.append(("reflect", agent))
        return {"text": "Reflected direction"}


class FakeRuntime:
    def __init__(self, value):
        self.value = value
        self.call = None

    def json(self, agent_spec, instruction, payload, required, operation_id=None):
        self.call = (agent_spec, instruction, payload, required, operation_id)
        return self.value


class FakeAgentRegistry:
    def __init__(self, specs=None):
        self.specs = {"assistant": agent_spec("assistant")} if specs is None else specs

    def get(self, agent_id):
        if agent_id not in self.specs:
            raise KeyError(agent_id)
        return self.specs[agent_id]


def agent_spec(agent_id):
    return {
        "id": agent_id,
        "name": "Configured agent",
        "runtime": "codex",
        "model": "gpt-5.6-codex",
        "instructions": "Use the saved definition.",
        "skills": ["evidence-review"],
        "tools": ["read_skill"],
        "mcp_servers": ["zotero"],
        "options": {"reasoning_effort": "high"},
    }


def engine(world, agents, embedding=None, runner=None):
    return PipelineEngine(
        world,
        agents,
        embedding or FakeEmbedding({}),
        runner or FakeRunner(),
        FakePipelines(),
    )


def admitted_direction(world, project, text="Existing direction"):
    node = world.create_node(project["id"], "direction", {"text": text})
    return world.admit_node(node["id"])


def assert_brainstorm_result(world, project, run, agents):
    directions = [
        node for node in world.nodes(project["id"]) if node["kind"] == "direction"
    ]
    assert world.run(run["id"])["status"] == "completed"
    assert world.run_events(run["id"])[1]["actor"] == "brainstormer"
    assert any(
        node["life_state"] == "ghost" and "cos=1.00" in node["rejection_reason"]
        for node in directions
    )
    assert any(
        node["payload"]["text"] == "Novel" and node["life_state"] == "admitted"
        for node in directions
    )
    assert agents.brainstorm_contexts[0]["instruction"] == "只考虑长期稳定性"


def assert_reflection_reviewed(world, project, agents):
    reflected = next(
        node
        for node in world.nodes(project["id"])
        if node["payload"].get("text") == "Reflected direction"
    )
    assert reflected["life_state"] == "admitted"
    assert agents.agent_ids.count(("review", "reviewer")) == 4
    assert ("reflect", "assistant") in agents.agent_ids


def assert_research_result(world, project, direction, agents):
    assert world.node(direction["id"])["direction_status"] == "supported"
    assert agents.plan_contexts[0]["instruction"] == "先扫描步长敏感性"
    assert agents.reflect_contexts[0]["instruction"] == "先扫描步长敏感性"
    assert_reflection_reviewed(world, project, agents)


def test_arbitrary_pipeline_id_executes_registered_stages(world, project):
    world.embedding = FakeEmbedding({"Novel": [1, 0]})
    agents = FakeAgents([{"text": "Novel", "quality": 0.8}])
    run = world.create_run(
        project["id"],
        world.nodes(project["id"])[0]["id"],
        brainstorm_pipeline("custom-ideas"),
        {"select": 1},
    )
    result = engine(world, agents, world.embedding).run(run["id"])
    assert result["status"] == "completed"
    assert any(
        node["payload"].get("text") == "Novel" and node["life_state"] == "admitted"
        for node in world.nodes(project["id"])
    )
    assert ("brainstorm", "assistant") in agents.agent_ids


def test_pipeline_id_does_not_choose_implementation(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(
        project["id"], direction["id"], research_pipeline("brainstorm")
    )
    agents = FakeAgents()
    result = engine(world, agents, runner=FakeRunner()).run(run["id"])
    assert result["status"] == "waiting_human"
    assert len(agents.plan_contexts) == 1
    assert agents.brainstorm_contexts == []


def test_pipeline_execution_stops_after_last_defined_stage(world, project):
    definition = brainstorm_pipeline("generate-only")
    definition["stages"] = definition["stages"][:1]
    agents = FakeAgents([{"text": "Novel", "quality": 0.8}])
    run = world.create_run(
        project["id"], world.nodes(project["id"])[0]["id"], definition
    )
    result = engine(world, agents).run(run["id"])
    assert result["status"] == "completed"
    assert all(node["kind"] != "direction" for node in world.nodes(project["id"]))


def test_run_executes_definition_snapshot(world, project):
    definition = brainstorm_pipeline("snapshot")
    run = world.create_run(
        project["id"], world.nodes(project["id"])[0]["id"], definition
    )
    definition["stages"] = research_pipeline()["stages"]
    world.embedding = FakeEmbedding({"Novel": [1, 0]})
    agents = FakeAgents([{"text": "Novel", "quality": 0.8}])
    result = engine(world, agents, world.embedding).run(run["id"])
    assert result["status"] == "completed"
    assert len(agents.brainstorm_contexts) == 1
    assert agents.plan_contexts == []


def test_brainstorm_agent_enforces_named_response_contract():
    runtime = FakeRuntime({"research_directions": []})
    with pytest.raises(ValueError, match="required field 'candidates'"):
        AgentFacade(runtime, FakeAgentRegistry()).brainstorm(
            {"text": "Why?"}, 2, "assistant"
        )
    assert '"candidates"' in runtime.call[1]
    assert runtime.call[2] == {"text": "Why?", "count": 2}


def test_mmr_balances_quality_and_similarity():
    candidates = [
        {"text": "a", "quality": 0.9, "vector": [1, 0]},
        {"text": "b", "quality": 0.88, "vector": [0.99, 0.01]},
        {"text": "c", "quality": 0.8, "vector": [0, 1]},
    ]
    assert [item["text"] for item in mmr(candidates, 2)] == ["a", "c"]


def test_brainstorm_blocks_duplicates_and_admits_selected(world, project):
    existing = admitted_direction(world, project)
    world.embedding = FakeEmbedding(
        {"Existing direction": [1, 0], "Duplicate": [1, 0], "Novel": [0, 1]}
    )
    world.update_node(existing["id"], payload={"text": "Existing direction"})
    agents = FakeAgents(
        [{"text": "Duplicate", "quality": 0.9}, {"text": "Novel", "quality": 0.8}]
    )
    run = world.create_run(
        project["id"],
        world.nodes(project["id"])[0]["id"],
        brainstorm_pipeline(),
        {"select": 2, "instruction": "只考虑长期稳定性"},
    )
    engine(world, agents, world.embedding).run(run["id"])
    assert_brainstorm_result(world, project, run, agents)
    values = world.run(run["id"])["payload"]["_pipeline"]["values"]
    assert "candidates" not in values
    assert "pool" not in values
    assert all("vector" not in item for item in values["directions"])


def test_gray_similarity_uses_pairwise_judge(world, project):
    admitted_direction(world, project)
    vectors = {"Existing direction": [1, 0], "Gray": [0.7, 0.714]}
    world.embedding = FakeEmbedding(vectors)
    agents = FakeAgents([{"text": "Gray", "quality": 0.7}])
    run = world.create_run(
        project["id"],
        world.nodes(project["id"])[0]["id"],
        brainstorm_pipeline(),
    )
    engine(world, agents, world.embedding).run(run["id"])
    assert agents.pairs == [("Gray", "Existing direction")]
    event = next(
        item
        for item in world.run_events(run["id"])
        if item["actor"] == "deduplicator" and item["type"] == "agent_session"
    )
    assert event["payload"]["stage_id"] == "deduplicate"


def test_manual_research_confirms_start_and_each_step(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(
        project["id"],
        direction["id"],
        research_pipeline(),
        {"instruction": "先扫描步长敏感性"},
    )
    runner = FakeRunner()
    agents = FakeAgents()
    service = engine(world, agents, runner=runner)
    planned = service.run(run["id"])
    assert planned["status"] == "waiting_human"
    assert planned["payload"]["experiment_id"].startswith("node:")
    assert runner.calls == []
    completed = service.confirm(run["id"])
    assert completed["status"] == "completed"
    assert len(runner.calls) == 1
    assert_research_result(world, project, direction, agents)


def test_manual_research_confirms_every_planned_step(world, project):
    direction = admitted_direction(world, project)
    steps = [
        {"image": "busybox:1.36", "command": ["echo", "one"]},
        {"image": "busybox:1.36", "command": ["echo", "two"]},
    ]
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    runner, agents = FakeRunner(), FakeAgents(steps=steps)
    service = engine(world, agents, runner=runner)
    assert service.run(run["id"])["status"] == "waiting_human"
    assert service.confirm(run["id"])["status"] == "waiting_human"
    assert len(runner.calls) == 1
    assert service.confirm(run["id"])["status"] == "completed"
    assert len(runner.calls) == 2


def test_manual_research_can_reject_plan_without_refuting_direction(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    service = engine(world, FakeAgents(), runner=FakeRunner())
    planned = service.run(run["id"])
    experiment_id = planned["payload"]["experiment_id"]

    rejected = service.resolve(run["id"], "reject", "步骤之间错误共享文件")

    assert rejected["status"] == "paused"
    assert rejected["stage"] == "execute"
    assert rejected["payload"]["_pipeline"]["gate"] is None
    assert world.node(experiment_id)["life_state"] == "ghost"
    assert world.node(direction["id"])["direction_status"] == "proposed"
    assert world.node(direction["id"])["working"] == 0
    assert world.edges(project["id"]) == []


def test_replan_adds_evidence_without_rewriting_terminal_direction(world, project):
    direction = admitted_direction(world, project)
    world.update_node(direction["id"], direction_status="refuted")
    run = world.create_run(
        project["id"],
        direction["id"],
        research_pipeline(),
        {"instruction": "更换积分器后重新验证", "mode": "replan"},
    )
    service = engine(world, FakeAgents(), runner=FakeRunner())
    service.run(run["id"])
    result = service.confirm(run["id"])
    assert result["status"] == "completed"
    assert world.node(direction["id"])["direction_status"] == "refuted"
    assert any(edge["polarity"] == "supports" for edge in world.edges(project["id"]))


def test_auto_review_starts_next_iteration(world, project):
    world.set_auto(project["id"], True)
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    result = engine(world, FakeAgents(), runner=FakeRunner()).run(run["id"])
    queued = [item for item in world.runs(project["id"]) if item["status"] == "queued"]
    assert result["status"] == "completed"
    assert len(queued) == 1


def test_two_rejections_pause_lineage(world, project):
    world.set_auto(project["id"], True)
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    service = engine(
        world,
        FakeAgents(decisions=["reject", "reject"]),
        runner=FakeRunner(exit_code=1),
    )
    result = service.run(run["id"])
    assert result["status"] == "paused"
    assert result["stage"] == "review-reflection"
    assert "连续 2 次" in result["payload"]["reason"]


def test_rejected_experiment_keeps_double_review(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    agents = FakeAgents(decisions=["reject", "reject", "approve", "approve"])
    service = engine(world, agents, runner=FakeRunner())
    service.run(run["id"])
    service.confirm(run["id"])
    experiment = next(
        node for node in world.nodes(project["id"]) if node["kind"] == "experiment"
    )
    assert experiment["life_state"] == "ghost"
    assert experiment["rebuttal"]["reviewer_a"]["rebuttal"] == "A"


def test_double_review_conflict_escalates_to_human(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    service = engine(
        world, FakeAgents(decisions=["approve", "reject"]), runner=FakeRunner()
    )
    service.run(run["id"])
    result = service.confirm(run["id"])
    assert result["status"] == "waiting_human"
    assert result["payload"]["conflict_node"].startswith("node:")
    assert service.resolve(run["id"], "approve", "人工批准")["status"] == "completed"


def test_agent_session_event_names_owning_stage(world, project):
    world.embedding = FakeEmbedding({"Novel": [1, 0]})
    agents = FakeAgents([{"text": "Novel", "quality": 0.8}])
    run = world.create_run(
        project["id"], world.nodes(project["id"])[0]["id"], brainstorm_pipeline()
    )
    engine(world, agents, world.embedding).run(run["id"])
    view = run_view(world, world.run(run["id"]))
    event = next(item for item in view["events"] if item["type"] == "agent_session")
    assert event["payload"] == {
        "stage_id": "generate",
        "session_id": None,
        "turn_id": None,
        "usage": {},
    }


def test_facade_passes_saved_agent_spec_to_runtime():
    runtime = FakeRuntime({"candidates": [{"text": "x", "quality": 0.1}]})
    spec = agent_spec("assistant")
    AgentFacade(runtime, FakeAgentRegistry({"assistant": spec})).brainstorm(
        {"text": "Why?"}, 1, "assistant"
    )
    assert runtime.call[0] == spec
    assert runtime.call[3] == ("candidates",)


def test_pipeline_rejects_unknown_agent_before_writing_events(world, project):
    facade = AgentFacade(FakeRuntime({}), FakeAgentRegistry({}))
    run = world.create_run(
        project["id"], world.nodes(project["id"])[0]["id"], brainstorm_pipeline()
    )
    service = engine(world, facade)
    with pytest.raises(KeyError):
        service.run(run["id"])
    assert world.run_events(run["id"]) == []


def test_pins_inject_node_content_into_agent_context(world, project):
    pinned = world.create_node(
        project["id"], "source", {"title": "Kepler 1609"}, life_state="admitted"
    )
    world.embedding = FakeEmbedding({"Novel": [1, 0]})
    agents = FakeAgents([{"text": "Novel", "quality": 0.5}])
    run = world.create_run(
        project["id"],
        world.nodes(project["id"])[0]["id"],
        brainstorm_pipeline(),
        {"select": 1, "pins": [pinned["id"]]},
    )
    engine(world, agents, world.embedding).run(run["id"])
    context = agents.brainstorm_contexts[0]
    assert context["project_id"] == project["id"]
    assert context["pins"] == [
        {"id": pinned["id"], "kind": "source", "payload": {"title": "Kepler 1609"}}
    ]


def test_failed_run_preserves_payload_and_releases_nodes(world, project):
    direction = admitted_direction(world, project)
    world.set_working(direction["id"], True)
    run = world.create_run(
        project["id"], direction["id"], research_pipeline(), {"thread_id": "t-1"}
    )
    failed = fail_run(world, run["id"], RuntimeError("provider failed"))
    assert failed["payload"] == {"thread_id": "t-1", "error": "provider failed"}
    assert world.node(direction["id"])["working"] == 0
    assert world.run_events(run["id"])[-1]["type"] == "run_failed"


def test_background_run_failure_becomes_terminal(world, project):
    root = world.nodes(project["id"])[0]
    run = world.create_run(project["id"], root["id"], brainstorm_pipeline())
    world.set_working(root["id"], True)

    def fail():
        raise RuntimeError("review failed")

    _run_action(world, run["id"], fail, ())
    assert world.run(run["id"])["status"] == "failed"
    assert world.node(root["id"])["working"] == 0


def test_direction_review_resumes_from_persisted_node(world, project):
    root = world.nodes(project["id"])[0]
    run = world.create_run(project["id"], root["id"], brainstorm_pipeline())
    values = {
        "origin": root["id"],
        "directions": [{"text": "Stable candidate", "quality": 0.8}],
    }
    payload = {"_pipeline": {"cursor": 3, "values": values, "gate": None}}
    world.update_run(run["id"], "review", "running", payload)
    agents = FakeAgents(decisions=["approve", "approve"])
    service = engine(world, agents)
    stage_spec = brainstorm_pipeline()["stages"][3]

    service._review_direction(stage_spec, world.run(run["id"]), values, 0)
    result = service.run(run["id"])

    directions = [
        node for node in world.nodes(project["id"]) if node["kind"] == "direction"
    ]
    assert result["status"] == "completed"
    assert len(directions) == 1
    assert directions[0]["life_state"] == "admitted"
    assert agents.agent_ids.count(("review", "reviewer")) == 2


def test_direction_resolution_is_idempotent(world, project):
    node = world.create_node(project["id"], "direction", {"text": "candidate"})

    first = world.resolve_direction_review(node["id"], False, "rejected")
    second = world.resolve_direction_review(node["id"], False, "rejected")

    assert first["changed"] is True
    assert second["changed"] is False
    assert second["lineage"]["rejection_streak"] == 1


def test_plan_resume_reuses_checkpoint_and_partial_steps(
    world, project, monkeypatch
):
    direction = admitted_direction(world, project)
    steps = [
        {"image": "busybox:1.36", "command": ["echo", "one"]},
        {"image": "busybox:1.36", "command": ["echo", "two"]},
    ]
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    agents, service = FakeAgents(steps=steps), None
    service = engine(world, agents, runner=FakeRunner())
    add_step = world.add_step
    calls = 0

    def interrupted(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("worker stopped")
        return add_step(*args, **kwargs)

    monkeypatch.setattr(world, "add_step", interrupted)
    with pytest.raises(RuntimeError, match="worker stopped"):
        service.run(run["id"])
    monkeypatch.setattr(world, "add_step", add_step)

    result = service.run(run["id"])
    assert result["status"] == "waiting_human"
    assert len(world.steps(run["id"])) == 2
    assert len(agents.plan_contexts) == 1


def test_running_container_step_is_resumable(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], research_pipeline())
    runner = FakeRunner()
    service = engine(world, FakeAgents(), runner=runner)
    service.run(run["id"])
    step = world.steps(run["id"])[0]
    world.update_step(step["id"], "running")

    assert service.confirm(run["id"])["status"] == "completed"
    assert len(runner.calls) == 1
