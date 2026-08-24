from pathlib import Path
from secrets import token_hex


class ProjectStorage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def allocate(self) -> Path:
        workspace = self.root / token_hex(12)
        workspace.mkdir(mode=0o700)
        return workspace

    def workspace(self, project: dict) -> Path:
        key = Path(project["root"]).name
        if not key:
            raise ValueError("project workspace key is empty")
        workspace = self.root / key
        workspace.mkdir(mode=0o700, exist_ok=True)
        return workspace

    def project(self, project: dict) -> dict:
        return {**project, "root": str(self.workspace(project))}

    def materialize(self, projects: list[dict]) -> None:
        for project in projects:
            self.workspace(project)
