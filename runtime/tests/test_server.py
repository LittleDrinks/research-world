from fastapi.testclient import TestClient

from runtime.runtime import Runtime
from runtime.server import create_app


def test_app_serves_health(tmp_path):
    with TestClient(create_app(Runtime(tmp_path, {}))) as client:
        assert client.get("/health").json() == {"ok": True}
