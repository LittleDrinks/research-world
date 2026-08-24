from __future__ import annotations

import httpx

from .execution_evidence import verify_evidence

DEFAULT_LIMITS = {"cpus": 1, "memory_mb": 512, "pids": 128, "wall_seconds": 300}


class RunnerClient:
    def __init__(self, url: str):
        self.url = url.rstrip("/")

    def run(self, step: dict) -> dict:
        spec = {
            "execution_id": step["execution_id"],
            "image": step["image"],
            "command": step["command"],
            "files": step.get("files", {}),
            "seed": step.get("seed", 0),
            "limits": step.get("limits", DEFAULT_LIMITS),
        }
        timeout = spec["limits"]["wall_seconds"] + 60
        response = httpx.post(f"{self.url}/run", json=spec, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if "failure" in result:
            return result
        check = verify_evidence(result)
        if check["ok"]:
            return result
        return invalid_evidence(step["execution_id"], check)

    def replay(self, step: dict) -> dict:
        replay = {**step, "execution_id": f"{step['execution_id']}:replay"}
        return self.run(replay)


def invalid_evidence(execution_id: str, check: dict) -> dict:
    return {
        "execution_id": execution_id,
        "exit_code": 2,
        "stdout": "",
        "stderr": check["code"],
        "failure": check,
    }
