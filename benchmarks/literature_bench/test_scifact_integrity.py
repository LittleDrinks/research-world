import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.literature_bench.scifact_integrity import EXPECTED_COUNTS, validate_data


class SciFactIntegrityTest(unittest.TestCase):
    def test_validates_expected_counts_and_gold_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_data(root)
            self.assertEqual(validate_data(root)["counts"], EXPECTED_COUNTS)

    def test_rejects_invalid_gold_sentence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_data(root, sentence=1)
            with self.assertRaisesRegex(ValueError, "invalid sentence"):
                validate_data(root)

    def test_rejects_duplicate_corpus_document_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_data(root)
            corpus = root / "corpus.jsonl"
            rows = [json.loads(line) for line in corpus.read_text().splitlines()]
            rows[-1]["doc_id"] = rows[0]["doc_id"]
            self._write_rows(corpus, rows)
            with self.assertRaisesRegex(ValueError, "duplicate SciFact corpus"):
                validate_data(root)

    def _write_data(self, root: Path, sentence: int = 0) -> None:
        corpus = [{"doc_id": index, "abstract": ["Sentence"]} for index in range(1, 5184)]
        for name, count in EXPECTED_COUNTS.items():
            if name == "corpus":
                self._write_rows(root / "corpus.jsonl", corpus)
                continue
            evidence = {"1": [{"sentences": [sentence]}]} if name == "dev" else {}
            rows = [{"id": index, "evidence": evidence} for index in range(count)]
            self._write_rows(root / f"claims_{name}.jsonl", rows)

    def _write_rows(self, path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
