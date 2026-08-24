import hashlib
import json

import httpx
import pytest
import respx

from runtime import literature


class CaptureClient:
    def __init__(self, failure=None):
        self.failure = failure
        self.calls = []

    async def ext_method(self, method, values):
        self.calls.append((method, values))
        if self.failure:
            raise self.failure
        digest = hashlib.sha256(values["content"].encode()).hexdigest()
        return {"id": f"artifact:{digest}", "sha256": digest,
                "media_type": values["media_type"]}


class Bound:
    def __init__(self, workspace, client):
        self.workspace = workspace
        self.client = client


@respx.mock
async def test_crossref_get_returns_verified_record():
    route = respx.get("https://api.crossref.org/works/10.1000%2Fevidence").mock(
        return_value=httpx.Response(200, json={"message": {"DOI": "10.1000/evidence"}})
    )

    value = json.loads(await literature.crossref({"action": "get", "doi": "10.1000/evidence"}))

    assert route.called
    assert value == {"DOI": "10.1000/evidence"}


async def test_project_files_captures_artifact_before_writing(tmp_path):
    client = CaptureClient()
    bound = Bound(tmp_path, client)

    value = json.loads(await literature.project_files(bound, {
        "action": "store", "path": "sources/paper.txt",
        "content": "Complete text", "media_type": "text/plain",
    }))

    assert tmp_path.joinpath("sources/paper.txt").read_text() == "Complete text"
    assert value["project_file"] == "sources/paper.txt"
    assert value["artifact"]["id"].startswith("artifact:")
    assert client.calls[0][0] == "research/capture_artifact"


async def test_project_files_does_not_write_when_capture_fails(tmp_path):
    bound = Bound(tmp_path, CaptureClient(RuntimeError("capture failed")))

    with pytest.raises(RuntimeError, match="capture failed"):
        await literature.project_files(bound, {
            "action": "store", "path": "sources/paper.txt",
            "content": "Complete text", "media_type": "text/plain",
        })

    assert not tmp_path.joinpath("sources/paper.txt").exists()
