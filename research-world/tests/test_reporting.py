import pytest

from server.reporting import assess_delivery


def test_checked_delivery_accepts_only_traced_facts():
    projection = report_projection(endpoint_ready=True)

    result = assess_delivery(projection)

    assert result["valid"] is True
    assert result["delivery_level"] == 4
    assert result["accepted_facts"] == projection["facts"]
    assert result["minimum_source_level"] == "published"
    assert result["gaps"] == []


def test_missing_endpoint_preserves_checked_report_at_level_two():
    result = assess_delivery(report_projection(endpoint_ready=False))

    assert result["valid"] is True
    assert result["delivery_level"] == 2
    assert result["gaps"] == [
        {"code": "endpoint_missing", "path": "endpoint_ready", "blocking": False}
    ]


def test_fact_citation_must_match_admitted_claim_and_source():
    projection = report_projection(endpoint_ready=True)
    projection["facts"][0]["source_ids"] = ["node:other"]

    result = assess_delivery(projection)

    assert result["valid"] is False
    assert result["delivery_level"] == 1
    assert result["accepted_facts"] == []
    assert [gap["code"] for gap in result["gaps"]] == ["source_missing"]


@pytest.mark.parametrize(
    ("change", "code", "level"),
    [
        ({"life_state": "pending"}, "source_not_admitted", 1),
        ({"source_level": "preprint"}, "source_not_final", 3),
        ({"checked_at": "2026-08-23"}, "source_checked_at_invalid", 3),
    ],
)
def test_delivery_reports_source_gaps(change, code, level):
    projection = report_projection(endpoint_ready=True)
    projection["sources"][0].update(change)

    result = assess_delivery(projection)

    assert result["valid"] is False
    assert result["delivery_level"] == level
    assert code in [gap["code"] for gap in result["gaps"]]


def test_claim_source_link_is_not_inferred_from_fact():
    projection = report_projection(endpoint_ready=True)
    projection["claims"][0]["source_ids"] = ["node:different"]

    result = assess_delivery(projection)

    assert result["valid"] is False
    assert result["gaps"][0]["code"] == "claim_source_mismatch"


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"life_state": "ghost"}, "claim_not_admitted"),
        ({"verdict": "uncertain"}, "claim_not_supported"),
    ],
)
def test_fact_requires_an_admitted_supported_claim(change, code):
    projection = report_projection(endpoint_ready=True)
    projection["claims"][0].update(change)

    result = assess_delivery(projection)

    assert result["valid"] is False
    assert code in [gap["code"] for gap in result["gaps"]]


def test_projection_shape_is_explicit():
    with pytest.raises(ValueError, match="facts list"):
        assess_delivery({"claims": [], "sources": []})


def report_projection(endpoint_ready=False):
    return {
        "endpoint_ready": endpoint_ready,
        "facts": [
            {
                "text": "The measured transition occurs at 42 K.",
                "claim_id": "claim:one",
                "source_ids": ["node:paper"],
            }
        ],
        "claims": [
            {
                "id": "claim:one",
                "text": "Transition at 42 K",
                "life_state": "admitted",
                "verdict": "supported",
                "source_ids": ["node:paper"],
            }
        ],
        "sources": [
            {
                "id": "node:paper",
                "kind": "source",
                "life_state": "admitted",
                "source_level": "published",
                "checked_at": "2026-08-23T12:00:00+08:00",
            }
        ],
    }
