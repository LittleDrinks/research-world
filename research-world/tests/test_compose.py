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


def test_runtime_owns_endpoint_definitions_and_root_env():
    services = compose()["services"]
    assert services["runtime"]["env_file"] == ["../.env"]
    assert "RUNTIME_ENDPOINTS" in services["runtime"]["environment"]
    for name in ("control", "worker"):
        environment = services[name]["environment"]
        assert {"RW_EMBEDDING_ENDPOINT", "RW_EMBEDDING_MODEL"} <= set(environment)
        assert not {"RUNTIME_ENDPOINTS", "RUNTIME_API_KEY"} & set(environment)
        assert "env_file" not in services[name]


def test_obsolete_harness_is_not_in_compose():
    value = compose()
    assert "harness" not in value["services"]
    assert "HARNESS_URL" not in str(value)
    assert "MODEL_API_KEY" not in str(value)
