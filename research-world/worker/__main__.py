from __future__ import annotations

import asyncio
import time
from threading import Event, Thread

from server.kernel import KernelCommand, default_kernel

HEARTBEAT_SECONDS = 5


def main() -> None:
    kernel = default_kernel()
    while True:
        lease = asyncio.run(kernel.command(KernelCommand("claim")))
        if lease:
            execute(kernel, lease.run_id)
        else:
            time.sleep(1)


def execute(kernel, run_id: str) -> None:
    stop = Event()
    heartbeat = Thread(target=_heartbeat, args=(kernel, run_id, stop), daemon=True)
    heartbeat.start()
    try:
        kernel.run(run_id)
    except Exception as error:  # noqa: BLE001 - worker persists terminal failures.
        values = {"run_id": run_id, "error": error}
        asyncio.run(kernel.command(KernelCommand("fail", values=values)))
    finally:
        stop.set()
        heartbeat.join()


def _heartbeat(kernel, run_id: str, stop: Event) -> None:
    while not stop.wait(HEARTBEAT_SECONDS):
        values = {"run_id": run_id}
        if not asyncio.run(kernel.command(KernelCommand("heartbeat", values=values))):
            return


if __name__ == "__main__":
    main()
