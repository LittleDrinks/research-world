import asyncio

from server.kernel import KernelCommand, ResearchKernel
from worker import __main__ as worker


class FailingKernel:
    def __init__(self):
        self.failed = []
        self.heartbeats = []

    def run(self, _run_id):
        raise RuntimeError("model unavailable")

    async def command(self, command):
        if command.tag == "fail":
            self.failed.append((command.values["run_id"], str(command.values["error"])))
        return True


def test_worker_delegates_failure_to_kernel():
    kernel = FailingKernel()

    worker.execute(kernel, "run:test")

    assert kernel.failed == [("run:test", "model unavailable")]


def test_kernel_claim_returns_domain_lease(world, project, tmp_path):
    root = world.nodes(project["id"])[0]
    world.create_run(
        project["id"], root["id"], {"id": "test", "name": "test", "stages": []}
    )

    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    lease = asyncio.run(kernel.command(KernelCommand("claim")))

    assert lease.project_id == project["id"]
    assert lease.run_id.startswith("run:")


def test_kernel_heartbeat_hides_run_storage(world, project, tmp_path):
    root = world.nodes(project["id"])[0]
    run = world.create_run(
        project["id"], root["id"], {"id": "test", "name": "test", "stages": []}
    )
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")

    values = {"run_id": run["id"]}
    assert (
        asyncio.run(kernel.command(KernelCommand("heartbeat", values=values))) is False
    )
    asyncio.run(kernel.command(KernelCommand("claim")))
    assert (
        asyncio.run(kernel.command(KernelCommand("heartbeat", values=values))) is True
    )
