from __future__ import annotations

import base64
import hashlib
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="Research World Runner Controller")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/doctor")
def doctor() -> dict:
    checks = (
        "! wget -T 2 -q -O- https://example.com && ! touch /blocked && touch /tmp/ok"
    )
    spec = {
        "image": "busybox:1.36",
        "command": ["sh", "-c", checks],
        "network": "none",
        "read_only": True,
        "limits": {"cpus": 1, "memory_mb": 64, "pids": 32},
    }
    result = run_container(spec)
    return {
        "ok": result["exit_code"] == 0,
        "network": "none",
        "read_only": True,
        "result": result,
    }


@app.post("/run")
def run(spec: dict) -> dict:
    return run_container(spec)


@app.post("/build")
def build(spec: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="rw-build-") as value:
        tag, digest = build_image(Path(value), spec)
        lock = lock_image(tag)
    return {"image_digest": digest, "lock": lock}


def build_image(root: Path, spec: dict) -> tuple[str, str]:
    write_files(root, spec["files"])
    header = "FROM python:3.12-slim\nWORKDIR /workspace\nCOPY . .\n"
    dockerfile = header + "\n".join(f"RUN {item}" for item in spec["setup"])
    (root / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    tag = "rw-env-" + hashlib.sha256(dockerfile.encode()).hexdigest()[:16]
    command = ["docker", "build", "--network", "default", "-t", tag, str(root)]
    subprocess.run(command, check=True, timeout=900)
    inspect = ["docker", "image", "inspect", "--format", "{{.Id}}", tag]
    result = subprocess.run(inspect, capture_output=True, text=True, check=True)
    return tag, result.stdout.strip()


def lock_image(tag: str) -> str:
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        tag,
        "python",
        "-m",
        "pip",
        "freeze",
        "--all",
    ]
    return subprocess.run(
        command, capture_output=True, text=True, check=True, timeout=120
    ).stdout


def write_files(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(content))


def run_container(spec: dict) -> dict:
    if not spec.get("files"):
        return invoke_container(spec, None)
    with tempfile.TemporaryDirectory(prefix="rw-run-") as value:
        root = Path(value)
        write_files(root, spec["files"])
        volume = create_input_volume(root)
        try:
            return invoke_container(spec, volume)
        finally:
            subprocess.run(
                ["docker", "volume", "rm", "-f", volume],
                check=False,
                capture_output=True,
            )


def create_input_volume(root: Path) -> str:
    volume = "rw-input-" + secrets.token_hex(8)
    subprocess.run(
        ["docker", "volume", "create", volume], check=True, capture_output=True
    )
    mount = f"type=volume,src={volume},dst=/workspace"
    helper = subprocess.run(
        ["docker", "create", "--mount", mount, "busybox:1.36", "true"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    try:
        subprocess.run(
            ["docker", "cp", f"{root}/.", f"{helper}:/workspace"], check=True
        )
    finally:
        subprocess.run(["docker", "rm", "-f", helper], check=False, capture_output=True)
    return volume


def invoke_container(spec: dict, volume: str | None) -> dict:
    started = time.monotonic()
    command = docker_command(spec, volume)
    process = subprocess.run(
        command, capture_output=True, text=True, timeout=300, check=False
    )
    return {
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "usage": {"wall_ms": round((time.monotonic() - started) * 1000)},
    }


def docker_command(spec: dict, volume: str | None = None) -> list[str]:
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "--env",
        f"RW_RANDOM_SEED={spec.get('seed', 0)}",
        *docker_limits(spec["limits"]),
        *docker_mount(volume),
    ]
    return [*command, spec["image"], *spec["command"]]


def docker_limits(limits: dict) -> list[str]:
    return [
        "--cpus",
        str(limits["cpus"]),
        "--memory",
        f"{limits['memory_mb']}m",
        "--pids-limit",
        str(limits["pids"]),
    ]


def docker_mount(volume: str | None) -> list[str]:
    if not volume:
        return []
    mount = f"type=volume,src={volume},dst=/workspace,readonly"
    return ["--mount", mount, "--workdir", "/workspace"]
