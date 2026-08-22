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


def test_claim_recovers_only_expired_running_run(world, project):
    root = world.nodes(project["id"])[0]
    run = world.create_run(
        project["id"], root["id"], {"id": "test", "name": "test", "stages": []}
    )
    assert world.claim_run()["id"] == run["id"]
    assert world.claim_run() is None
    with world.db.connect() as connection:
        connection.execute(
            "UPDATE pipeline_runs SET updated_at='2000-01-01T00:00:00+00:00' WHERE id=?",
            (run["id"],),
        )
    assert world.claim_run()["id"] == run["id"]


def test_touch_only_renews_running_run(world, project):
    root = world.nodes(project["id"])[0]
    run = world.create_run(
        project["id"], root["id"], {"id": "test", "name": "test", "stages": []}
    )
    assert world.touch_run(run["id"]) is False
    world.claim_run()
    assert world.touch_run(run["id"]) is True
