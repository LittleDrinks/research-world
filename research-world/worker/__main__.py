from __future__ import annotations

import time

from server.cli import default_world
from server.workflows import default_engine


def main() -> None:
    world = default_world()
    while True:
        run = world.claim_run()
        if run:
            execute(world, run)
        else:
            time.sleep(1)


def execute(world, run) -> None:
    try:
        default_engine(world, run["project_id"]).run(run["id"])
    except Exception as error:  # noqa: BLE001 - worker persists terminal failures.
        world.record_run_event(
            run["id"], "control", "run_failed", {"error": str(error)}
        )
        world.update_run(run["id"], "failed", "failed", {"error": str(error)})


if __name__ == "__main__":
    main()
