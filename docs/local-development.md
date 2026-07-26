# Local development — run & test a dev bot

This guide walks you from zero to a **separate development bot** running on your
machine and answering commands in Telegram, **without touching production** and
**without needing the real movie-info API** (you can serve movie data from a
local fixture file).

There are two ways to run it locally:

- **Docker Compose** (recommended) — spins up PostgreSQL + the bot together.
- **Host + uv** — run the Python process directly against your own Postgres.

---

## 1. Create a dedicated dev bot

Never reuse the production token for local testing — create a throwaway bot.

1. In Telegram, open a chat with **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`, choose a name and a unique username (e.g. `myname_cl_dev_bot`).
3. Copy the **bot token** it gives you → this is `TELEGRAM_BOT_TOKEN`.

A bot token authenticates without a phone number — Pyrogram creates a bot
session directly, so there's no login code to enter.

## 2. Get your API credentials

1. Go to **https://my.telegram.org** → **API development tools**.
2. Create an app (any title). Copy:
   - **App api_id** → `TELEGRAM_API_ID`
   - **App api_hash** → `TELEGRAM_API_HASH`

## 3. Create throwaway chats and collect their IDs

The bot references several channels/groups by numeric ID. For dev, create a few
private test chats and use their IDs everywhere:

1. Create a **test channel** and a **test group**. Add your dev bot as an
   **admin** to both.
2. Get the numeric IDs: forward a message from each chat to
   **[@userinfobot](https://t.me/userinfobot)** or **[@RawDataBot](https://t.me/RawDataBot)**.
   Channel/supergroup IDs look like `-1001234567890`.
3. Get **your own user ID** the same way (send any message to the bot) → `OWNER_ID`.

You can point several of the ID variables at the same test chat to keep things
simple. Minimum to get the core commands working:

| Variable | Point it at |
|---|---|
| `OWNER_ID` | your user ID (makes you super-admin) |
| `CINEMA_ID`, `CHANNEL_ID` | your test channel |
| `GROUP_ID`, `ORDERS_ID`, `PAY_GROUP` | your test group |
| `STREAM_BIN_CHANNEL` | your test channel (only needed for `/stream`) |

## 4. Configure the environment

```bash
cp .env.example data/.env
```

Edit `data/.env` and fill in the values from steps 1–3. For an **offline** dev
session (no external API calls), set:

```dotenv
MOCK_MOVIE_DATA=1        # /info reads from local fixtures instead of IMDB_API_URL
```

Everything else (payments, subtitles, Groq) can stay blank until you need it —
those features simply won't be exercised.

> The `USER_DB` / `POSTGRE_DB_URL` defaults in `.env.example` already point at
> the `db` service used by Docker Compose, so you don't need to change them for
> the Compose flow.

## 5a. Run with Docker Compose (recommended)

```bash
make dev      # builds the image, starts Postgres + the bot
make seed     # inserts sample catalog + posts so /search returns results
make logs     # follow the bot logs
```

Compose starts PostgreSQL (with a healthcheck), waits for it, then starts the
bot with your `data/.env` and the source bind-mounted for quick iteration.

To stop: `make down`.

## 5b. Run on the host with uv

```bash
uv sync                              # install dependencies
# make sure USER_DB / POSTGRE_DB_URL point at a Postgres you control
uv run python scripts/seed_dev_data.py   # optional: sample data
uv run cl-bot                        # start the bot (== python -m cinemalibrarybot)
```

## 6. Simulate movie info from a local file (offline `/info`)

The `/info` command normally calls an IMDb-style API. For local testing you can
serve that data from JSON files instead — no network, no API key.

- With `MOCK_MOVIE_DATA=1`, the mock provider reads from `FIXTURES_DIR`
  (default `./tests/fixtures/movie_search`). Committed sample fixtures are
  included so `/info` works out of the box.
- To use **your own** data, create a private, gitignored folder and point
  `FIXTURES_DIR` at it:

  ```bash
  mkdir -p .fixtures/movie_search
  # copy the sample files and edit them:
  cp tests/fixtures/movie_search/*.json .fixtures/movie_search/
  ```

  ```dotenv
  FIXTURES_DIR=./.fixtures/movie_search
  ```

  `.fixtures/` is in `.gitignore`, so your personal data never gets committed.

The fixture shape mirrors the real API response (`id`, `primaryTitle`,
`startYear`, `rating.aggregateRating`, `runtimeSeconds`, `genres`, `plot`,
`primaryImage.url`, `type`). See the committed samples for the exact structure.

## 7. Test the bot in Telegram

Open a chat with your dev bot (and/or use your test group) and try:

| Command | Expected |
|---|---|
| `/start` | Welcome message. |
| `/help` | Help text. |
| `/search <name>` | Matching seeded posts (run `make seed` first). |
| `/info <title>` | A movie card built from the fixture (with `MOCK_MOVIE_DATA=1`). |
| `/profile` | Your profile panel. |
| `#cine` + photo (in the group) | Creates a movie request. |

**Streaming (`/stream`)** additionally needs `STREAM_BIN_CHANNEL` and a public
URL. With `STREAM_URL` blank, the bot auto-starts a **Cloudflare tunnel** and
prints the public URL in the logs. To skip streaming during dev, simply don't
call `/stream`.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `database "..." does not exist` / connection refused | Postgres isn't up/ready. With Compose, `make down && make dev`; on host, check `USER_DB`/`POSTGRE_DB_URL`. |
| `The session file ... is already in use` | Another instance is running with the same `NAME`. Stop it, or change `NAME`. |
| Config error at startup naming a variable | A **required** var is missing in `data/.env`. See [configuration.md](configuration.md). |
| `/search` returns nothing | Run `make seed` to insert sample posts. |
| `/info` errors or hangs | Ensure `MOCK_MOVIE_DATA=1` (offline) or a valid `IMDB_API_URL`. |
| Files/session written to the wrong place | Paths resolve from `DATA_DIR` (default `./data`). Run from the repo root or set `DATA_DIR`. |
