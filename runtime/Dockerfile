FROM node:22-slim AS codex
RUN npm install --global @openai/codex@0.149.1-linux-x64

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN pip install --no-cache-dir uv==0.8.13
COPY --from=codex /usr/local/lib/node_modules/@openai/codex/vendor/x86_64-unknown-linux-musl/bin/codex /usr/local/bin/codex
COPY research-world/kernel-contract/ /research-world/kernel-contract/
COPY runtime/pyproject.toml runtime/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv UV_HTTP_TIMEOUT=120 uv sync --frozen --no-dev
COPY runtime/runtime/ runtime/
COPY runtime/schemas/ schemas/
COPY .agents/skills/ /app/skills/
EXPOSE 8098
CMD ["python", "-m", "runtime"]
