FROM node:22-slim AS codex
RUN npm install --global @openai/codex@0.149.0

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN pip install --no-cache-dir uv==0.8.13
COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex
COPY runtime/pyproject.toml runtime/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv UV_HTTP_TIMEOUT=120 uv sync --frozen --no-dev
COPY runtime/runtime/ runtime/
COPY runtime/schemas/ schemas/
COPY .agents/skills/ /app/skills/
EXPOSE 8098
CMD ["python", "-m", "runtime"]
