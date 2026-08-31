from pathlib import Path

import yaml

COMPOSE = Path(__file__).parents[1] / "compose.yaml"
RELEASE_COMPOSE = Path(__file__).parents[1] / "compose.release.yaml"
DOCKERFILE = Path(__file__).parents[1] / "Dockerfile"
PENGUIN_READINESS = Path(__file__).parents[1] / "penguin-readiness.mjs"
PENGUIN_ENTRYPOINT = Path(__file__).parents[1] / "penguin-entrypoint.sh"
PENGUIN_COMMAND = [
    "/opt/penguin/bin/penguin",
    "server",
    "--host",
    "0.0.0.0",
    "--port",
    "7364",
]
PENGUIN_HEALTHCHECK = [
    "CMD",
    "/opt/penguin/node/bin/node",
    "/opt/penguin-readiness.mjs",
]


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


def test_penguin_service_is_pinned_and_uses_a_private_data_root():
    service = compose()["services"]["penguin"]

    assert service["build"] == {"context": ".", "target": "runtime"}
    assert service["entrypoint"] == ["/usr/local/bin/penguin-entrypoint"]
    assert service["command"] == PENGUIN_COMMAND
    assert service["environment"]["PENGUIN_HOME"] == "/penguin-data"
    assert service["environment"]["PENGUIN_UPDATE_CHECK"] == "off"
    assert service["volumes"] == ["rw-penguin-data:/penguin-data"]
    assert service["healthcheck"]["test"] == PENGUIN_HEALTHCHECK


def test_penguin_does_not_receive_model_credentials():
    for value in (compose(), release_compose()):
        service = value["services"]["penguin"]
        assert "env_file" not in service
        assert not {"OPENAI_API_KEY", "OPENAI_BASE_URL"} & set(service.get("environment", {}))
        assert "PENGUIN_SEED_ADMIN_PASSWORD" not in service.get("environment", {})
        assert "apikey" not in str(service)
        assert "baseurl" not in str(service)


def test_release_compose_runs_the_pinned_penguin_image():
    service = release_compose()["services"]["penguin"]

    assert "build" not in service
    assert service["image"] == "${RW_IMAGE:-ghcr.io/littledrinks/research-world}:${RW_VERSION:-pre-alpha}"
    assert service["entrypoint"] == ["/usr/local/bin/penguin-entrypoint"]
    assert service["command"] == PENGUIN_COMMAND


def test_penguin_artifact_pin_is_the_public_linux_x64_release():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "https://github.com/Prism-Shadow/penguin-harness/releases/download/v0.2.9/penguin-linux-x64.tar.gz" in dockerfile
    assert "585f6885be6bbbd7eba5eca7308de4c8c4e0ab4990fb450726bdda50c0d268fe" in dockerfile
    assert "ARG PENGUIN_VERSION" not in dockerfile
    assert "ARG PENGUIN_SHA256" not in dockerfile


def test_penguin_entrypoint_keeps_seed_password_process_local():
    entrypoint = PENGUIN_ENTRYPOINT.read_text(encoding="utf-8")

    assert "export PENGUIN_SEED_ADMIN_PASSWORD=" in entrypoint
    assert "secrets.token_urlsafe(32)" in entrypoint
    assert 'exec "$@"' in entrypoint
    assert ".seed-admin-password" not in entrypoint
    assert "chmod" not in entrypoint
    assert "cat " not in entrypoint


def test_penguin_readiness_is_authenticated_exact_version_and_silent():
    readiness = PENGUIN_READINESS.read_text(encoding="utf-8")

    assert "api-token" in readiness
    assert "Authorization" in readiness
    assert 'version !== "0.2.9"' in readiness
    assert 'describe !== "v0.2.9"' in readiness
    assert "console." not in readiness
    assert "process.stdout" not in readiness
