# syntax=docker/dockerfile:1

# =============================================================================
# Builder — resolve & install dependencies + the project with uv
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (cached layer) using only the lockfile + manifest,
# so app source changes don't invalidate the dependency layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Now copy the source and install the project itself (provides the cl-bot script).
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# =============================================================================
# Runtime — slim image, non-root, with the cloudflared binary on PATH
# =============================================================================
FROM python:3.13-slim-bookworm AS runtime

# cloudflared is used by the streaming tunnel. Installing it on PATH means the
# app uses it directly instead of downloading it at runtime (see stream/tunnel.py).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && arch="$(dpkg --print-architecture)" \
    && case "$arch" in \
         amd64) cf_arch=amd64 ;; \
         arm64) cf_arch=arm64 ;; \
         armhf) cf_arch=arm ;; \
         *) cf_arch=amd64 ;; \
       esac \
    && curl -fsSL -o /usr/local/bin/cloudflared \
         "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${cf_arch}" \
    && chmod +x /usr/local/bin/cloudflared \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user.
RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

# Copy the built virtual environment and the app source from the builder.
COPY --from=builder --chown=app:app /app /app

# Runtime data (session file, cine.db, subtitle/translation working dirs) lives
# in the mounted data volume; ensure the non-root user owns it.
RUN mkdir -p /app/data && chown -R app:app /app/data

ENV PATH="/app/.venv/bin:$PATH" \
    DATA_DIR="/app/data"

USER app

EXPOSE 8080
VOLUME ["/app/data"]

CMD ["cl-bot"]
