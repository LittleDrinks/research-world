from fastapi.testclient import TestClient

from runtime.server import create_app


class ClosingRuntime:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def test_app_lifespan_awaits_runtime_close():
    runtime = ClosingRuntime()
    with TestClient(create_app(runtime)) as client:
        assert client.get("/health").json() == {"ok": True}
    assert runtime.closed
