#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
bench_cache="$repo_root/.scratch/scifact"
output="${1:?Usage: benchmarks/scifact_product/run.sh OUTPUT [--limit N --split train|dev --model MODEL]}"
shift
mkdir -p "$bench_cache"
cd "$repo_root"
if [[ ! -d "$bench_cache/source/.git" ]]; then
  git clone -q https://github.com/allenai/scifact.git "$bench_cache/source"
  git -C "$bench_cache/source" checkout -q 68b98a56d93e0f9da0d2aab4e6c3294699a0f72e
fi
if [[ ! -d "$bench_cache/evaluator/.git" ]]; then
  git clone -q https://github.com/allenai/scifact-evaluator.git "$bench_cache/evaluator"
  git -C "$bench_cache/evaluator" checkout -q 66feffc5b2cc9e28e3ce3b8c9e824c3c642981eb
fi
if [[ ! -f "$bench_cache/data.tar.gz" ]]; then
  curl -fL --retry 2 --max-time 120 https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz -o "$bench_cache/data.tar.gz"
fi
uv sync --project benchmarks/scifact_product --frozen
if [[ ! -d "$bench_cache/data" ]]; then
  uv run --project benchmarks/scifact_product python - "$bench_cache" <<'PY'
import hashlib,sys,tarfile
from pathlib import Path
root=Path(sys.argv[1]); archive=root/'data.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be'
with tarfile.open(archive) as data:data.extractall(root,filter='data')
PY
fi
cat > "$bench_cache/compose.yaml" <<'YAML'
services:
  control:
    ports: !override
      - "127.0.0.1:18095:8095"
  runtime:
    ports: !override
      - "127.0.0.1:18098:8098"
YAML
cd "$repo_root/research-world"
docker compose -p rwbench -f compose.yaml -f "$bench_cache/compose.yaml" up --build -d --wait
docker compose -p rwbench -f compose.yaml -f "$bench_cache/compose.yaml" images --format json > "$bench_cache/images.json"
cd "$repo_root"
PYTHONDONTWRITEBYTECODE=1 uv run --project benchmarks/scifact_product python -m benchmarks.scifact_product.run \
  --data "$bench_cache/data" --archive "$bench_cache/data.tar.gz" \
  --source "$bench_cache/source" --evaluator "$bench_cache/evaluator" --output "$output" "$@"
