# Deployment

Production runs the bot as a single Docker container. Dependencies are managed
with **uv** and pinned via `uv.lock` for reproducible builds.

## Build the production image

```bash
docker build -t cl-bot:latest .
```

The image is multi-stage:

- A builder stage runs `uv sync --frozen --no-dev` into a virtual environment.
- The final stage is slim, runs as a **non-root** user, bundles the
  `cloudflared` binary (used by the streaming tunnel), and starts the bot via
  the `cl-bot` console script.

## Run the container

Mount a data directory (holding `data/.env`, the Pyrogram session, and
`cine.db`) and expose the stream port:

```bash
docker run -d --name cl-bot \
  --env-file data/.env \
  -v "$PWD/data:/app/data" \
  -p 8080:8080 \
  cl-bot:latest
```

- `data/` persists the session file and the SQLite catalog across restarts.
- Postgres (`USER_DB`, `POSTGRE_DB_URL`) is expected to be an external managed
  database in production; point the URLs at it in `data/.env`.
- The stream server listens on `STREAM_PORT` (default 8080). Set `STREAM_URL`
  to your public URL, or leave it blank to use the auto Cloudflare tunnel.

## Configuration

All configuration is environment-based — see
[configuration.md](configuration.md). Required variables are validated at
startup and fail fast with a clear message if missing.

## Releases

Releases are automated by pushing a Git tag. CI runs lint + tests and publishes
a GitHub Release with auto-generated notes. **No image is pushed and no server
is deployed automatically** — pull and run the image yourself.

### Cutting a release

```bash
# from an up-to-date main (or the branch you release from)
git tag -a v1.2.0 -m "v1.2.0"
git push origin v1.2.0
```

This triggers `.github/workflows/release.yml`, which:

1. Runs the full CI suite (ruff, basedpyright, pytest).
2. Creates a GitHub Release named after the tag with notes generated from the
   merged pull requests since the previous tag.

Use [semantic versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

## Continuous integration

Every push and pull request runs `.github/workflows/ci.yml`:

- `ruff check` + `ruff format --check` (lint & formatting)
- `basedpyright` (type checking)
- `pytest` (unit + smoke tests)

Keep CI green before merging into `dev` or `main`.
