from __future__ import annotations

import httpx


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
            "limits": step.get("limits", {"cpus": 1, "memory_mb": 512, "pids": 128}),
        }
        response = httpx.post(f"{self.url}/run", json=spec, timeout=360)
        response.raise_for_status()
        return response.json()
