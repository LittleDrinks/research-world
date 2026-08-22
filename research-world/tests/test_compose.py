from pathlib import Path

import yaml


def compose():
    path = Path(__file__).parents[1] / "compose.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_only_runtime_receives_model_credentials():
    services = compose()["services"]
    for name, service in services.items():
        environment = service.get("environment", {})
        if name == "runtime":
            assert {"RUNTIME_API_BASE", "RUNTIME_API_KEY"} <= set(environment)
        else:
            assert not {"RUNTIME_API_BASE", "RUNTIME_API_KEY"} & set(environment)


def test_obsolete_harness_is_not_in_compose():
    value = compose()
    assert "harness" not in value["services"]
    assert "HARNESS_URL" not in str(value)
    assert "MODEL_API_KEY" not in str(value)
