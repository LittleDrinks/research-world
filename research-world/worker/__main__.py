from __future__ import annotations

import time
from threading import Event, Thread

from server.cli import default_world
from server.workflows import default_engine, fail_run

HEARTBEAT_SECONDS = 5


def main() -> None:
    world = default_world()
    while True:
        run = world.claim_run()
        if run:
            execute(world, run)
        else:
            time.sleep(1)


def execute(world, run) -> None:
    stop = Event()
    heartbeat = Thread(target=_heartbeat, args=(world, run["id"], stop), daemon=True)
    heartbeat.start()
    try:
        default_engine(world, run["project_id"]).run(run["id"])
    except Exception as error:  # noqa: BLE001 - worker persists terminal failures.
        fail_run(world, run["id"], error)
    finally:
        stop.set()
        heartbeat.join()


def _heartbeat(world, run_id: str, stop: Event) -> None:
    while not stop.wait(HEARTBEAT_SECONDS):
        if not world.touch_run(run_id):
            return


if __name__ == "__main__":
    main()
