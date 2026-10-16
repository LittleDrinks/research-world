#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.literature_bench.scifact_integrity import verify


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--evaluator", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify(args.data, args.archive, args.source, args.evaluator)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
