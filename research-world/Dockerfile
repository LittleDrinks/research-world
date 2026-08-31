FROM python:3.12-slim AS penguin
RUN python - <<'PY'
import hashlib
import tarfile
from pathlib import Path
from urllib.request import urlopen

url, expected = (
    "https://github.com/Prism-Shadow/penguin-harness/releases/download/v0.2.9/penguin-linux-x64.tar.gz",
    "585f6885be6bbbd7eba5eca7308de4c8c4e0ab4990fb450726bdda50c0d268fe",
)
archive = Path("/tmp/penguin.tar.gz")
with urlopen(url) as source, archive.open("wb") as target:
    while chunk := source.read(1024 * 1024):
        target.write(chunk)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit("Penguin release checksum mismatch")
with tarfile.open(archive, "r:gz") as bundle:
    bundle.extract("./payload.tar.gz", "/tmp")
    bundle.extract("./payload.tar.gz.sha256", "/tmp")
payload = Path("/tmp/payload.tar.gz")
payload_expected = Path("/tmp/payload.tar.gz.sha256").read_text().split()[0]
if hashlib.sha256(payload.read_bytes()).hexdigest() != payload_expected:
    raise SystemExit("Penguin payload checksum mismatch")
with tarfile.open(payload, "r:gz") as program:
    program.extractall("/opt")
PY

FROM node:22-alpine AS web
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN pip install --no-cache-dir uv==0.8.13
COPY kernel-contract/ kernel-contract/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv UV_HTTP_TIMEOUT=120 uv sync --frozen --no-dev
COPY server/ server/
COPY worker/ worker/
COPY library/ library/
COPY agents/ agents/
COPY pipelines/ pipelines/
COPY schemas/ schemas/
COPY --from=web /build/web/dist web/dist
COPY --from=penguin /opt/penguin /opt/penguin
COPY penguin-readiness.mjs /opt/penguin-readiness.mjs
COPY --chmod=0755 penguin-entrypoint.sh /usr/local/bin/penguin-entrypoint
EXPOSE 8095
CMD ["rw", "serve", "--host", "0.0.0.0", "--port", "8095"]

FROM docker:29-cli AS docker_cli
FROM runtime AS runner
COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker
EXPOSE 8096
CMD ["uvicorn", "server.runner_controller:app", "--host", "0.0.0.0", "--port", "8096"]
