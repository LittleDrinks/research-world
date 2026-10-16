import pytest

from server.kernel_interface import create_kernel
from server.world import World


@pytest.fixture
def world(tmp_path):
    return World(tmp_path / "world.db", tmp_path / "artifacts")


@pytest.fixture
def project(world, tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("orbit research", encoding="utf-8")
    return world.create_project("q049", root, "Why do planetary orbits remain stable?")


@pytest.fixture
def graph_kernel(tmp_path):
    return create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
