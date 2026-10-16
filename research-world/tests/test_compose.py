from pathlib import Path

import yaml

COMPOSE = Path(__file__).parents[1] / "compose.yaml"
RELEASE_COMPOSE = Path(__file__).parents[1] / "compose.release.yaml"
RUNTIME_DOCKERFILE = Path(__file__).parents[2] / "runtime" / "Dockerfile"


def compose():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def release_compose():
    return yaml.safe_load(RELEASE_COMPOSE.read_text(encoding="utf-8"))


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


def test_lean_is_not_installed_or_started_by_compose():
    assert "lean-sandbox" not in compose()["services"]


def test_runtime_delegates_lean_execution_to_runner_controller():
    service = compose()["services"]["runtime"]

    assert service["environment"]["RUNNER_CONTROLLER_URL"].startswith("http://runner-controller")


def test_release_compose_uses_only_ghcr_images():
    services = release_compose()["services"]
    assert all("build" not in service for service in services.values())
    assert all("ghcr.io" in service["image"] for service in services.values())


def test_release_compose_preserves_credential_boundary():
    services = release_compose()["services"]
    assert services["runtime"]["env_file"] == ["../.env"]
    for name in ("control", "worker", "runner-controller"):
        assert "env_file" not in services[name]


def test_runtime_image_pins_pi_and_runs_as_uid_1000():
    content = RUNTIME_DOCKERFILE.read_text(encoding="utf-8")
    assert "@earendil-works/pi-coding-agent@0.84.3" in content
    assert "USER 1000:1000" in content


def test_runtime_mounts_host_pi_agent_directory_read_write():
    for value in (compose(), release_compose()):
        runtime = value["services"]["runtime"]
        assert runtime["user"] == "1000:1000"
        assert runtime["environment"]["HOME"] == "/home/runtime"
        assert runtime["environment"]["PI_CODING_AGENT_DIR"] == "/home/runtime/.pi/agent"
        assert "${HOME}/.pi/agent:/home/runtime/.pi/agent" in runtime["volumes"]
