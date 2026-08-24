import pytest

from server.observations import observation_submission

ARTIFACT = "artifact:" + "a" * 64


def test_human_observation_becomes_a_source_submission():
    record = observation_record()

    command = observation_submission(record)

    assert command == {
        "kind": "source",
        "payload": {
            "title": "Run 7 measurements",
            "provenance": {"actor": "researcher:li", "method": "four-probe"},
            "observed_at": "2026-08-23T09:30:00+08:00",
            "artifact_ids": [ARTIFACT],
        },
    }
    assert "life_state" not in command
    assert record["payload"] == {"title": "Run 7 measurements"}


def test_experiment_observation_preserves_parent_for_kernel():
    record = observation_record(kind="experiment", parent_id="node:direction")

    command = observation_submission(record)

    assert command["kind"] == "experiment"
    assert command["parent_id"] == "node:direction"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"kind": "direction"}, "source or experiment"),
        ({"provenance": {}}, "requires actor"),
        ({"observed_at": "2026-08-23T09:30:00"}, "requires a timezone"),
        ({"artifact_ids": ["artifact:not-a-hash"]}, "SHA-256 ids"),
        ({"artifact_ids": [{}]}, "SHA-256 ids"),
        ({"life_state": "admitted"}, "rejects fields: life_state"),
        ({"lineage_id": "lineage:external"}, "rejects fields: lineage_id"),
        ({"payload": {"pipeline": {"run_id": "run:x"}}}, "rejects fields: pipeline"),
    ],
)
def test_observation_rejects_invalid_or_internal_state(change, message):
    with pytest.raises(ValueError, match=message):
        observation_submission({**observation_record(), **change})


def test_observation_payload_cannot_shadow_provenance():
    record = observation_record(payload={"provenance": {"actor": "other"}})

    with pytest.raises(ValueError, match="payload rejects fields: provenance"):
        observation_submission(record)


def observation_record(**changes):
    value = {
        "kind": "source",
        "payload": {"title": "Run 7 measurements"},
        "provenance": {"actor": "researcher:li", "method": "four-probe"},
        "observed_at": "2026-08-23T09:30:00+08:00",
        "artifact_ids": [ARTIFACT],
    }
    return {**value, **changes}
