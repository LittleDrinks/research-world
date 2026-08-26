import asyncio

from server.kernel import KernelQuery, ResearchKernel
from server.report_delivery import render_html
from server.reporting import REPORT_INPUT_TOKEN_BUDGET, REPORT_SECTIONS, assess_delivery, input_tokens


SOURCE = "node:" + "a" * 24
DIRECTION = "node:" + "b" * 24
CLAIM = f"claim:{DIRECTION.removeprefix('node:')}:1"
ARTIFACT = "artifact:" + "c" * 64


def projection():
    evidence = {"id": SOURCE, "kind": "source", "artifact_ids": [ARTIFACT]}
    source = {"id": SOURCE, "title": "Validated source", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"}
    claim = {"id": CLAIM, "text": "The result is reproducible.", "life_state": "admitted", "verdict": "supported", "evidence": [evidence], "evidence_ids": [SOURCE], "source_ids": [SOURCE], "artifact_ids": [ARTIFACT]}
    fact = {"text": claim["text"], "claim_id": CLAIM, "source_ids": [SOURCE], "artifact_ids": [ARTIFACT]}
    link = {"claim_id": CLAIM, "evidence_id": SOURCE, "source_id": SOURCE}
    artifact = {"id": ARTIFACT, "kind": "code", "size": 10, "links": [link], "display": {"kind": "code", "text": "value = 42"}}
    return {"question": "Can the result be reproduced?", "facts": [fact], "claims": [claim], "sources": [source], "artifacts": [artifact]}


def test_report_skill_benchmark_checks_contract_and_sections():
    value = projection()
    result = assess_delivery(value)
    html = render_html("Benchmark", value, result).decode()
    assert result["valid"] is True
    assert result["contract"]["sections"] == list(REPORT_SECTIONS)
    assert result["contract"]["input_budget_tokens"] == REPORT_INPUT_TOKEN_BUDGET
    assert 0 < result["contract"]["input_tokens"] <= REPORT_INPUT_TOKEN_BUDGET
    assert all(f"<h2>{section}</h2>" in html for section in REPORT_SECTIONS)
    assert f'href="#evidence-{SOURCE}"' in html
    assert f'data-artifact="{ARTIFACT}"' in html


def test_report_skill_benchmark_ignores_unprojected_admitted_payload(world, project, tmp_path):
    marker = "bounded-evidence"
    payload = {"notes": marker * (REPORT_INPUT_TOKEN_BUDGET + 1)}
    world.create_node(project["id"], "experiment", payload, life_state="admitted")
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    envelope = asyncio.run(kernel.query(KernelQuery("report_projection", project["id"])))
    assert envelope["status"] == "blocked"
    assert "projection" not in envelope
    assert marker not in str(envelope)
    assert envelope["gaps"][0]["code"] == "facts_missing"


def test_report_skill_benchmark_keeps_the_exact_budget_boundary(world, project, tmp_path):
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    source = world.create_node(project["id"], "source", {"title": "Source", "source_level": "published", "checked_at": "2026-08-26T00:00:00+00:00"})
    world.admit_node(source["id"])
    direction = world.create_node(project["id"], "direction", {"claims": [{"text": "Finding", "verdict": "supported", "evidence": [source["id"]]}]})
    world.admit_node(direction["id"])
    set_admitted_input_tokens(world, kernel, project, source, direction, 2048)
    assert asyncio.run(kernel.query(KernelQuery("report_projection", project["id"]))) ["status"] == "ready"
    set_admitted_input_tokens(world, kernel, project, source, direction, 2049)
    result = asyncio.run(kernel.query(KernelQuery("report_projection", project["id"])))
    assert result["gaps"] == [{"code": "projection_budget_exceeded", "path": "projection", "value": 2049}]


def test_report_skill_benchmark_excludes_trace_payload(world, project, tmp_path):
    marker = "trace-only-marker"
    world.create_node(project["id"], "experiment", {"trace": marker}, life_state="admitted")
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    envelope = asyncio.run(kernel.query(KernelQuery("report_projection", project["id"])))
    assert marker not in str(envelope)


def set_admitted_input_tokens(world, kernel, project, source, direction, target):
    for words in range(1, 4097):
        text = "word " * words
        world.update_node(source["id"], {**source["payload"], "title": text})
        world.update_node(direction["id"], {"claims": [{"text": text, "verdict": "supported", "evidence": [source["id"]]}]})
        nodes = [world.node(source["id"]), world.node(direction["id"])]
        if input_tokens(kernel._report_view(project, nodes)) == target:
            return
    raise AssertionError(f"cannot create {target} admitted input tokens")
