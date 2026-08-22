from worker import __main__ as worker


class FailingEngine:
    def run(self, _run_id):
        raise RuntimeError("model unavailable")


def test_worker_failure_preserves_run_context(world, project, monkeypatch):
    root = world.nodes(project["id"])[0]
    run = world.create_run(
        project["id"], root["id"], {"id": "test", "name": "test", "stages": []},
        {"thread_id": "thread:test"},
    )
    world.set_working(root["id"], True)
    monkeypatch.setattr(worker, "default_engine", lambda *_: FailingEngine())
    worker.execute(world, run)
    failed = world.run(run["id"])
    assert failed["status"] == "failed"
    assert failed["payload"]["thread_id"] == "thread:test"
    assert failed["payload"]["error"] == "model unavailable"
    assert world.node(root["id"])["working"] == 0
