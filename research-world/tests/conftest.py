import pytest
from server.kernel_interface import create_kernel

@pytest.fixture
def graph_kernel(tmp_path):
    return create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")
