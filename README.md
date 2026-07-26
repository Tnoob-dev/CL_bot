# CinemaLibraryBot (cl-bot)

A Telegram bot for a Cuban movie/series library channel. It lets users search
the catalog, look up rich movie info, request titles, fetch subtitles, and
(for VIP users) **stream files directly in the browser** through a co-hosted
media server. It also runs a lightweight, human-verified VIP subscription flow.

Built on [kurigram](https://github.com/KurimuzonAkuma/pyrogram) (a Pyrogram
fork, MTProto) with an [aiohttp](https://docs.aiohttp.org/) streaming server,
[SQLModel](https://sqlmodel.tiangolo.com/) over PostgreSQL + SQLite, and managed
with [uv](https://docs.astral.sh/uv/).

## Features

- **Catalog search** — `/search`, inline queries, and `#cine` requests in the group.
- **Rich movie info** — `/info` pulls titles from an IMDb-style API and renders a card (poster, rating, runtime, genres, translated synopsis).
- **Subtitles** — `/srt` via OpenSubtitles.
- **In-browser streaming** — `/stream` serves Telegram files through the aiohttp player, exposed via a Cloudflare tunnel when needed.
- **VIP subscriptions** — manual, screenshot-verified payment flow (Cuban cards, QvaPay/PayPal, crypto).
- **Admin tooling** — posting, fusion, publicity, broadcasts, stats (`/count`, `/top10`), bulk collection.

## Tech stack

| Concern | Choice |
|---|---|
| Telegram | kurigram (Pyrogram fork), MTProto long-polling |
| Streaming | aiohttp + Cloudflare tunnel |
| Data | SQLModel / SQLAlchemy 2 — PostgreSQL (users, posts) + SQLite (catalog) |
| Translation / AI | Groq LLM + deep-translator |
| Packaging | uv + `pyproject.toml` (single source of truth) |
| Runtime | Python 3.12, Docker |

## Quick start (local dev)

```bash
# 1. Copy the env template and fill it in (see docs/configuration.md)
cp .env.example data/.env

# 2. Bring up Postgres + the bot in Docker (offline-friendly)
make dev

# 3. Seed sample catalog/posts so /search returns results
make seed
```

Prefer running on the host with uv? `uv sync && uv run cl-bot`.

👉 **Full step-by-step guide (creating a dev bot on Telegram, IDs, mock data,
testing each command):** [`docs/local-development.md`](docs/local-development.md)

## Documentation

- [`docs/local-development.md`](docs/local-development.md) — run & test a dev bot, step by step.
- [`docs/configuration.md`](docs/configuration.md) — every environment variable.
- [`docs/architecture.md`](docs/architecture.md) — how the pieces fit together.
- [`docs/deployment.md`](docs/deployment.md) — production build & release process.

## Repository layout

```
src/cinemalibrarybot/   application package (handlers, services, repositories, stream)
assets/                 static media
docs/                   documentation
tests/                  pytest suite + fixtures
scripts/                dev utilities (e.g. seed_dev_data.py)
data/                   runtime dir — .env, session, cine.db (gitignored)
```

See [`docs/architecture.md`](docs/architecture.md) for the full module map.

## Contributing

Branch off `dev`, keep changes behavior-preserving unless intended, run
`make lint` and `make test` before pushing. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).
