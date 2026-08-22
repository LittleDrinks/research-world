from __future__ import annotations

import pytest

from server.library import resolve_assembly
from server.workflows import AgentFacade, PipelineEngine, mmr


def pipeline(pipeline_id):
    return {
        "id": pipeline_id,
        "name": pipeline_id,
        "stages": [{"id": "run", "type": "tool", "tool": "test"}],
    }


class FakePipelines:
    def get(self, pipeline_id):
        return pipeline(pipeline_id)


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
    def __init__(self, candidates=None, decisions=None):
        self.candidates = candidates or []
        self.decisions = list(decisions or [])
        self.pairs = []
        self.brainstorm_contexts = []
        self.plan_contexts = []
        self.reflect_contexts = []

    def brainstorm(self, context, count):
        self.brainstorm_contexts.append(context)
        return {"candidates": self.candidates[:count]}

    def pairwise(self, left, right):
        self.pairs.append((left, right))
        return True

    def plan(self, direction):
        self.plan_contexts.append(direction)
        return {"steps": [{"image": "busybox:1.36", "command": ["true"]}]}

    def review(self, context, reviewer):
        decision = self.decisions.pop(0) if self.decisions else "approve"
        return {
            "decision": decision,
            "quality": 0.8,
            "diversity": 0.7,
            "rebuttal": reviewer,
        }

    def reflect(self, context):
        self.reflect_contexts.append(context)
        return {"text": "Reflected direction"}


class FakeRuntime:
    def __init__(self, value):
        self.value = value
        self.call = None

    def json(self, role, instruction, payload, tools=None, prompt_segments=None):
        self.call = (role, instruction, payload, tools or [], prompt_segments or [])
        return self.value


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


def test_brainstorm_agent_enforces_named_response_contract():
    runtime = FakeRuntime({"research_directions": []})
    with pytest.raises(ValueError, match="required field 'candidates'"):
        AgentFacade(runtime, []).brainstorm({"text": "Why?"}, 2)
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
        pipeline("brainstorm"),
        {"select": 2, "instruction": "只考虑长期稳定性"},
    )
    result = engine(world, agents, world.embedding).run(run["id"])
    directions = [
        node for node in world.nodes(project["id"]) if node["kind"] == "direction"
    ]
    assert result["status"] == "completed"
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


def test_gray_similarity_uses_pairwise_judge(world, project):
    admitted_direction(world, project)
    vectors = {"Existing direction": [1, 0], "Gray": [0.7, 0.714]}
    world.embedding = FakeEmbedding(vectors)
    agents = FakeAgents([{"text": "Gray", "quality": 0.7}])
    run = world.create_run(
        project["id"], world.nodes(project["id"])[0]["id"], pipeline("brainstorm")
    )
    engine(world, agents, world.embedding).run(run["id"])
    assert agents.pairs == [("Gray", "Existing direction")]


def test_manual_research_confirms_start_and_each_step(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(
        project["id"],
        direction["id"],
        pipeline("research"),
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
    assert world.node(direction["id"])["direction_status"] == "supported"
    assert agents.plan_contexts[0]["instruction"] == "先扫描步长敏感性"
    assert agents.reflect_contexts[0]["instruction"] == "先扫描步长敏感性"


def test_replan_adds_evidence_without_rewriting_terminal_direction(world, project):
    direction = admitted_direction(world, project)
    world.update_node(direction["id"], direction_status="refuted")
    run = world.create_run(
        project["id"],
        direction["id"],
        pipeline("research"),
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
    run = world.create_run(project["id"], direction["id"], pipeline("research"))
    result = engine(world, FakeAgents(), runner=FakeRunner()).run(run["id"])
    queued = [item for item in world.runs(project["id"]) if item["status"] == "queued"]
    assert result["status"] == "completed"
    assert len(queued) == 1


def test_two_rejections_pause_lineage(world, project):
    world.set_auto(project["id"], True)
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], pipeline("research"))
    service = engine(
        world,
        FakeAgents(decisions=["reject", "reject"]),
        runner=FakeRunner(exit_code=1),
    )
    result = service.run(run["id"])
    assert result["status"] == "paused"
    assert "连续 2 次" in result["payload"]["reason"]


def test_double_review_conflict_escalates_to_human(world, project):
    direction = admitted_direction(world, project)
    run = world.create_run(project["id"], direction["id"], pipeline("research"))
    service = engine(
        world, FakeAgents(decisions=["approve", "reject"]), runner=FakeRunner()
    )
    service.run(run["id"])
    result = service.confirm(run["id"])
    assert result["status"] == "waiting_human"
    assert result["payload"]["conflict_node"].startswith("node:")


def test_facade_maps_assembly_to_runtime_session():
    runtime = FakeRuntime({"candidates": [{"text": "x", "quality": 0.1}]})
    assembly = resolve_assembly(["fs", "graph-query"])
    AgentFacade(runtime, assembly).brainstorm({"text": "Why?"}, 1)
    _, _, _, tools, segments = runtime.call
    assert {"type": "fs"} in tools
    webhook = next(tool for tool in tools if tool["type"] == "webhook")
    assert webhook["name"] == "graph_query"
    assert webhook["parameters"]["required"] == ["action", "project_id"]
    assert segments == [package["prompt_segment"] for package in assembly]


def test_pins_inject_node_content_into_agent_context(world, project):
    pinned = world.create_node(
        project["id"], "source", {"title": "Kepler 1609"}, life_state="admitted"
    )
    world.embedding = FakeEmbedding({"Novel": [1, 0]})
    agents = FakeAgents([{"text": "Novel", "quality": 0.5}])
    run = world.create_run(
        project["id"],
        world.nodes(project["id"])[0]["id"],
        pipeline("brainstorm"),
        {"select": 1, "pins": [pinned["id"]]},
    )
    engine(world, agents, world.embedding).run(run["id"])
    context = agents.brainstorm_contexts[0]
    assert context["project_id"] == project["id"]
    assert context["pins"] == [
        {"id": pinned["id"], "kind": "source", "payload": {"title": "Kepler 1609"}}
    ]
