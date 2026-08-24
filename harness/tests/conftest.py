import pytest
import respx
from fastapi.testclient import TestClient

from harness.app import create_app
from helpers import API, MODEL_URL


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def make_client(data_dir):
    def _make():
        app = create_app(data_dir=data_dir, api_base=API, api_key="k",
                         model="test-model", backoff=(0, 0, 0))
        return TestClient(app)
    return _make


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def model_route():
    with respx.mock(assert_all_called=False) as router:
        yield router.post(MODEL_URL)
