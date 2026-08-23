from io import StringIO

from server.cli import main


def test_serve_reuses_the_cli_event_loop(monkeypatch):
    calls = []

    async def serve(server, **_kwargs):
        calls.append((server.config.host, server.config.port))

    monkeypatch.setattr("uvicorn.Server.serve", serve)
    output = StringIO()

    result = main(["serve", "--host", "127.0.0.1", "--port", "8095"], object(), output)

    assert result == 0
    assert calls == [("127.0.0.1", 8095)]
