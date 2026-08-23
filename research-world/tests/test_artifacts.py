import pytest

from server.artifacts import ArtifactIntegrityError, ArtifactStore


def test_artifact_registration_is_content_addressed_and_idempotent(tmp_path):
    store = ArtifactStore(tmp_path)

    first = store.add(b"result", "text/plain")
    second = store.add(b"result", "text/plain")

    assert first == second
    assert first["id"] == f"artifact:{first['sha256']}"
    assert store.read(first["id"]) == b"result"


def test_artifact_read_detects_tampering(tmp_path):
    store = ArtifactStore(tmp_path)
    artifact = store.add(b"result", "text/plain")
    tmp_path.joinpath(artifact["sha256"][:2], artifact["sha256"]).write_bytes(b"bad")

    with pytest.raises(ArtifactIntegrityError) as captured:
        store.read(artifact["id"])

    assert captured.value.code == "content_hash_mismatch"

    with pytest.raises(ArtifactIntegrityError) as repeated:
        store.add(b"result", "text/plain")

    assert repeated.value.code == "content_hash_mismatch"


def test_duplicate_hash_rejects_conflicting_metadata(tmp_path):
    store = ArtifactStore(tmp_path)
    artifact = store.add(b"result", "text/plain")

    with pytest.raises(ArtifactIntegrityError) as captured:
        store.add(b"result", "application/json")

    assert captured.value.code == "metadata_conflict"
    assert store.get(artifact["id"])["media_type"] == "text/plain"
