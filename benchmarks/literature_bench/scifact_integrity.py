from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


DATA_SHA256 = "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be"
EVALUATOR_REVISION = "66feffc5b2cc9e28e3ce3b8c9e824c3c642981eb"
EXPECTED_COUNTS = {"train": 809, "dev": 300, "test": 300, "corpus": 5183}
SOURCE_REVISION = "68b98a56d93e0f9da0d2aab4e6c3294699a0f72e"


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def revision(path: Path) -> str:
    command = ["git", "-C", str(path), "rev-parse", "HEAD"]
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout.strip()


def validate_data(data_root: Path) -> dict:
    splits = _read_splits(data_root)
    corpus = read_jsonl(data_root / "corpus.jsonl")
    _validate_counts(splits, corpus)
    _validate_gold(splits, corpus)
    return {"counts": _counts(splits, corpus)}


def _read_splits(data_root: Path) -> dict[str, list[dict]]:
    return {name: read_jsonl(data_root / f"claims_{name}.jsonl") for name in ("train", "dev", "test")}


def _counts(splits: dict[str, list[dict]], corpus: list[dict]) -> dict[str, int]:
    return {**{name: len(rows) for name, rows in splits.items()}, "corpus": len(corpus)}


def _validate_counts(splits: dict[str, list[dict]], corpus: list[dict]) -> None:
    counts = _counts(splits, corpus)
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"unexpected SciFact counts: {counts}")
    if len({row["doc_id"] for row in corpus}) != len(corpus):
        raise ValueError("duplicate SciFact corpus document id")
    for name, rows in splits.items():
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError(f"duplicate SciFact {name} claim id")


def _validate_gold(splits: dict[str, list[dict]], corpus: list[dict]) -> None:
    documents = {row["doc_id"]: row for row in corpus}
    for name, rows in splits.items():
        for claim in rows:
            _validate_claim(name, claim, documents)


def _validate_claim(name: str, claim: dict, documents: dict[int, dict]) -> None:
    for raw_id, rationales in claim.get("evidence", {}).items():
        document = documents.get(int(raw_id))
        if document is None:
            raise ValueError(f"{name}:{claim['id']} references missing document {raw_id}")
        _validate_sentences(name, claim["id"], raw_id, rationales, document["abstract"])


def _validate_sentences(name: str, claim_id: int, doc_id: str, rationales: list[dict], abstract: list[str]) -> None:
    for rationale in rationales:
        for sentence in rationale["sentences"]:
            if not 0 <= sentence < len(abstract):
                raise ValueError(f"{name}:{claim_id} has invalid sentence {doc_id}:{sentence}")


def official_top_k(source: Path) -> int:
    if "--k 3" not in (source / "script/pipeline.sh").read_text():
        raise ValueError("official TF-IDF top-3 command is unavailable")
    return 3


def verify(data: Path, archive: Path, source: Path, evaluator: Path) -> dict:
    archive_hash = sha256(archive)
    if archive_hash != DATA_SHA256:
        raise ValueError(f"official data hash mismatch: {archive_hash}")
    source_revision, evaluator_revision = revision(source), revision(evaluator)
    if source_revision != SOURCE_REVISION or evaluator_revision != EVALUATOR_REVISION:
        raise ValueError("SciFact source or evaluator revision mismatch")
    return {**validate_data(data), "archive_sha256": archive_hash, "source_revision": source_revision, "evaluator_revision": evaluator_revision, "top_k": official_top_k(source)}
