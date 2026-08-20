"""Science 125 题批驱动：生成 project.json、建 project、发起 brainstorm、汇总轻量结果。"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "docs" / "questions.json"
PROJECTS = ROOT / "research-world" / "projects"
CONTAINER_PROJECTS = "/projects"  # compose.yaml 把 projects/ 挂载到容器 /projects
API = "http://127.0.0.1:8095"
TERMINAL = {"completed", "paused", "waiting_human", "failed"}


def load_questions() -> list[dict]:
    return json.loads(QUESTIONS.read_text(encoding="utf-8-sig"))


def spec_for(index: int, item: dict) -> dict:
    name = f"q{index:03d}"
    return {"name": name, "root": name,
            "question": f"{item['title']}\n{item['full_text']}"}


def write_project_files(specs: list[dict]) -> None:
    for spec in specs:
        directory = PROJECTS / spec["name"]
        if directory.exists():
            continue
        directory.mkdir(parents=True)
        path = directory / "project.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_projects(client: httpx.Client, specs: list[dict]) -> dict[str, str]:
    cards = client.get("/api/v1/projects").json()
    ids = {card["name"]: card["id"] for card in cards}
    for spec in specs:
        if spec["name"] in ids:
            continue
        body = {**spec, "root": f"{CONTAINER_PROJECTS}/{spec['name']}"}
        response = client.post("/api/v1/projects", json=body)
        assert response.status_code == 201, response.text
        ids[spec["name"]] = response.json()["id"]
        print(f"created {spec['name']}")
    return {spec["name"]: ids[spec["name"]] for spec in specs}


def question_node(client: httpx.Client, project_id: str) -> dict:
    data = client.get("/api/v1/bootstrap", params={"project_id": project_id}).json()
    return next(node for node in data["nodes"] if node["kind"] == "question")


def start_brainstorm(client: httpx.Client, project_id: str, question: str) -> dict:
    body = {"node_id": question_node(client, project_id)["id"], "kind": "brainstorm",
            "payload": {"instruction": question}}
    response = client.post(f"/api/v1/projects/{project_id}/workflows", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def finished(client: httpx.Client, project_id: str) -> bool:
    workflows = client.get(f"/api/v1/projects/{project_id}/workflows").json()
    return bool(workflows) and all(item["status"] in TERMINAL for item in workflows)


def wait_batch(client: httpx.Client, ids: dict[str, str], timeout: int) -> list[str]:
    pending = dict(ids)
    deadline = time.monotonic() + timeout
    while pending and time.monotonic() < deadline:
        time.sleep(5)
        pending = {name: pid for name, pid in pending.items() if not finished(client, pid)}
    return sorted(pending)


def report(client: httpx.Client, name: str, project_id: str) -> None:
    data = client.get("/api/v1/bootstrap", params={"project_id": project_id}).json()
    directions = [node for node in data["nodes"] if node["kind"] == "direction"]
    admitted = sum(node["life_state"] == "admitted" for node in directions)
    ghost = sum(node["life_state"] == "ghost" for node in directions)
    statuses = ",".join(item["status"] for item in data["workflows"])
    print(f"{name}: nodes={len(data['nodes'])} directions={len(directions)} "
          f"admitted={admitted} ghost={ghost} workflows={statuses}")


def main() -> int:
    args = parser().parse_args()
    specs = [spec_for(index, item)
             for index, item in enumerate(load_questions()[: args.limit], 1)]
    write_project_files(specs)
    with httpx.Client(base_url=API, timeout=60) as client:
        ids = ensure_projects(client, specs)
        for spec in specs:
            start_brainstorm(client, ids[spec["name"]], spec["question"])
        print(f"started {len(specs)} brainstorm workflows")
        if not args.wait:
            return 0
        pending = wait_batch(client, ids, args.timeout)
        for spec in specs:
            report(client, spec["name"], ids[spec["name"]])
    if pending:
        print(f"timeout, still pending: {pending}")
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="batch_125")
    parser.add_argument("--limit", type=int, default=None, help="只处理前 N 题")
    parser.add_argument("--wait", action="store_true", help="轮询直到本批 workflow 收敛")
    parser.add_argument("--timeout", type=int, default=3600, help="--wait 的超时秒数")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
