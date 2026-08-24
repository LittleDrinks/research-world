from __future__ import annotations

import json

from .config import ROOT


LIBRARY_DIR = ROOT / "library"
DEFAULT_ASSEMBLY = ["fs", "graph-query"]


def list_packages() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(LIBRARY_DIR.glob("*.json"))]


def resolve_assembly(names: list[str] | None) -> list[dict]:
    packages = {package["name"]: package for package in list_packages()}
    selected = DEFAULT_ASSEMBLY if names is None else names
    unknown = [name for name in selected if name not in packages]
    if unknown:
        raise ValueError(f"unknown capability packages: {unknown}")
    return [packages[name] for name in selected]


def assembly_names(names: list[str] | None) -> list[str]:
    return [package["name"] for package in resolve_assembly(names)]
