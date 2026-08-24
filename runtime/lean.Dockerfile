FROM debian:bookworm-slim AS build
ARG LEAN_VERSION=4.33.1
ARG LEAN_SHA256=890afd185370f85666025b883914ab4f4b339136f8c96167b69cfb62aecaf235
ARG MATHLIB_COMMIT=0df444a360eaa60ab8c11dca51a86af692955474
RUN apt-get update && apt-get install --yes --no-install-recommends aria2 ca-certificates git zstd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN aria2c --allow-overwrite=true --auto-file-renaming=false \
    --max-connection-per-server=16 --min-split-size=1M --split=16 \
    --dir=/opt --out=lean.tar.zst \
    "https://github.com/leanprover/lean4/releases/download/v${LEAN_VERSION}/lean-${LEAN_VERSION}-linux.tar.zst" \
    && echo "${LEAN_SHA256}  lean.tar.zst" | sha256sum --check \
    && tar --use-compress-program=unzstd --extract --file=lean.tar.zst \
    && mv "lean-${LEAN_VERSION}-linux" lean \
    && rm lean.tar.zst
ENV PATH=/opt/lean/bin:$PATH
RUN git clone --branch v${LEAN_VERSION} --depth 1 \
    https://github.com/leanprover-community/mathlib4.git /opt/mathlib \
    && test "$(git -C /opt/mathlib rev-parse HEAD)" = "${MATHLIB_COMMIT}"
WORKDIR /opt/mathlib
RUN git config --global http.version HTTP/1.1 \
    && for attempt in 1 2 3 4 5; do \
        lake exe cache get && break; \
        test "$attempt" -lt 5; \
    done \
    && rm -rf .git /root/.gitconfig

FROM debian:bookworm-slim
ENV HOME=/tmp PATH=/opt/lean/bin:$PATH
COPY --from=build /opt/lean /opt/lean
COPY --from=build /opt/mathlib /opt/mathlib
WORKDIR /opt/mathlib
RUN lake env lean --version | grep '4.33.1'
USER 65532:65532
CMD ["lake", "env", "lean", "--version"]
