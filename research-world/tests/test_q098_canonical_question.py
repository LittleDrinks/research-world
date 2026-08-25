import asyncio
import json
from pathlib import Path

from server.kernel import KernelCommand, KernelQuery, ResearchKernel


ROOT = Path(__file__).parents[2]
FOREIGN_MEMORY_TEXT = "copying our memories onto a thumb drive"


def q098() -> dict:
    entries = json.loads((ROOT / "docs/questions.json").read_text(encoding="utf-8-sig"))
    return next(entry for entry in entries if entry["id"] == 98)


def create_project(kernel, seed) -> dict:
    return asyncio.run(
        kernel.command(
            KernelCommand(
                "create_project",
                values={key: seed[key] for key in ("name", "title", "question")},
            )
        )
    )


def test_q098_question_attribution_reaches_project_bootstrap(world, tmp_path):
    entry = q098()
    canonical = f'{entry["title"]}\n{entry["full_text"]}'
    project_seed = json.loads(
        (ROOT / "research-world/projects/q098/project.json").read_text()
    )
    kernel = ResearchKernel(world, projects_root=tmp_path / "projects")
    project = create_project(kernel, project_seed)
    bootstrap = asyncio.run(kernel.query(KernelQuery("bootstrap", project["id"])))

    question = next(node for node in bootstrap["nodes"] if node["kind"] == "question")
    visible = [
        entry["full_text"], project_seed["question"],
        bootstrap["projects"][0]["question"], question["payload"]["text"],
    ]
    assert all(FOREIGN_MEMORY_TEXT not in value for value in visible)
    assert project_seed["question"] == canonical
    assert bootstrap["projects"][0]["question"] == canonical
    assert question["payload"]["text"] == canonical
