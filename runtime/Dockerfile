FROM node:22-slim AS agent-clis
RUN npm install --global \
    @openai/codex@0.149.1-linux-x64 \
    @earendil-works/pi-coding-agent@0.84.3

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN pip install --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --no-cache-dir uv==0.8.13
COPY --from=agent-clis /usr/local/lib/node_modules/@openai/codex/vendor/x86_64-unknown-linux-musl/bin/codex /usr/local/bin/codex
COPY --from=agent-clis /usr/local/bin/node /usr/local/bin/node
COPY --from=agent-clis /usr/local/lib/node_modules/@earendil-works/pi-coding-agent /usr/local/lib/node_modules/@earendil-works/pi-coding-agent
RUN ln -s /usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js /usr/local/bin/pi
COPY runtime/pyproject.toml runtime/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    sed -i 's#https://files.pythonhosted.org/packages/#https://mirrors.aliyun.com/pypi/packages/#g' uv.lock \
    && \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    UV_SYSTEM_CERTS=1 \
    UV_HTTP_TIMEOUT=600 uv sync --frozen --no-dev
COPY runtime/runtime/ runtime/
COPY runtime/schemas/ schemas/
COPY .agents/skills/ /app/skills/
ENV HOME=/home/runtime PI_CODING_AGENT_DIR=/home/runtime/.pi/agent
RUN groupadd --gid 1000 runtime \
    && useradd --uid 1000 --gid runtime --create-home runtime \
    && mkdir -p /runtime-data /home/runtime/.pi/agent \
    && chown -R runtime:runtime /runtime-data /home/runtime
USER 1000:1000
EXPOSE 8098
CMD ["python", "-m", "runtime"]
