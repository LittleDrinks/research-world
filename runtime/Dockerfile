FROM node:22-slim AS agent-clis
RUN npm install --global \
    @earendil-works/pi-coding-agent@1.2.0

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN pip install --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --no-cache-dir uv==0.8.13
COPY --from=agent-clis /usr/local/bin/node /usr/local/bin/node
COPY --from=agent-clis /usr/local/lib/node_modules/@earendil-works/pi-coding-agent /usr/local/lib/node_modules/@earendil-works/pi-coding-agent
RUN ln -s /usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js /usr/local/bin/pi
COPY research-world/kernel-contract/ /research-world/kernel-contract/
COPY runtime/pyproject.toml runtime/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    sed -i 's#https://files.pythonhosted.org/packages/#https://mirrors.aliyun.com/pypi/packages/#g' uv.lock \
    && \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    UV_SYSTEM_CERTS=1 \
    UV_HTTP_TIMEOUT=600 uv sync --frozen --no-dev
RUN ln -s /usr/local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules /app/node_modules
COPY runtime/runtime/ runtime/
COPY .agents/skills/ /app/skills/
ENV HOME=/home/runtime PI_CODING_AGENT_DIR=/home/runtime/.pi/agent
RUN groupadd --gid 1000 runtime \
    && useradd --uid 1000 --gid runtime --create-home runtime \
    && mkdir -p /runtime-data /home/runtime/.pi/agent \
    && chown -R runtime:runtime /runtime-data /home/runtime
EXPOSE 8098
CMD ["python", "-m", "runtime.bootstrap"]
