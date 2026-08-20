from httpx import Response

from helpers import completion


def test_benchmark_run_two_cases(client, model_route):
    r = client.post("/benchmarks", json={"name": "b1", "cases": [
        {"id": "case-hit", "prompt": "p1", "expect": {"contains": "alpha"}},
        {"id": "case-miss", "prompt": "p2", "expect": {"contains": "MISS"}},
    ]})
    assert r.status_code == 200, r.text
    bid = r.json()["id"]
    model_route.mock(side_effect=[
        Response(200, json=completion("alpha result", pt=10, ct=4)),
        Response(200, json=completion("beta result", pt=20, ct=6))])
    run = client.post(f"/benchmarks/{bid}/runs", json={}).json()
    assert len(run["cases"]) == 2
    hit, miss = run["cases"]
    assert hit["case_id"] == "case-hit"
    assert hit["status"] == "completed"
    assert hit["contains_hit"] is True
    assert hit["rounds"] == 1
    assert hit["prompt_tokens"] == 10
    assert miss["case_id"] == "case-miss"
    assert miss["contains_hit"] is False
    assert hit["session_id"] != miss["session_id"]
    agg = run["aggregate"]
    assert agg["cases"] == 2
    assert agg["completion_rate"] == 1.0
    assert agg["avg_rounds"] == 1.0
    assert agg["avg_tokens"] == (14 + 26) / 2
    assert agg["total_wall_ms"] >= 0
    again = client.get(f"/benchmarks/{bid}/runs/{run['id']}").json()
    assert again["aggregate"] == agg
    assert [c["case_id"] for c in again["cases"]] == ["case-hit", "case-miss"]
