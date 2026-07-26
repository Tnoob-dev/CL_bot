# Configuration reference

All configuration is provided through environment variables, loaded from
`data/.env` at startup (see [`.env.example`](../.env.example) for a copy-ready
template). In production the same variables are injected into the container
environment.

Variables are validated at startup by the central settings module
(`src/cinemalibrarybot/config.py`). Missing **required** variables cause an
immediate, explicit error instead of a confusing failure deep inside a handler.

## Telegram — core credentials

| Variable | Required | Default | Description |
|---|---|---|---|
| `NAME` | no | `cinemalibrarybot` | Pyrogram session name. The session file is created at `<DATA_DIR>/<NAME>.session`. |
| `TELEGRAM_API_ID` | **yes** | — | App API ID from https://my.telegram.org. |
| `TELEGRAM_API_HASH` | **yes** | — | App API hash from https://my.telegram.org. |
| `TELEGRAM_BOT_TOKEN` | **yes** | — | Bot token from @BotFather. A bot token logs in without a phone number. |

## Telegram — channels, groups & people

Numeric Telegram IDs (channel/group IDs are usually negative, e.g. `-100…`).

| Variable | Required | Description |
|---|---|---|
| `CINEMA_ID` | **yes** | Main cinema channel. |
| `CHANNEL_ID` | **yes** | Posts channel. |
| `GROUP_ID` | **yes** | Community group (handles `#cine` movie requests). |
| `ORDERS_ID` | **yes** | Chat where movie requests are routed. |
| `PAY_GROUP` | **yes** | Admin chat that receives payment screenshots for approval. |
| `SENDER_BOT` | no | Username/ID of the delivery bot used for file sending. |
| `OWNER_ID` | **yes** | Your Telegram user ID (super-admin). |
| `DELETE_MESSAGE_DELAY` | no (`30`) | Seconds before some throwaway messages self-delete. |

## Databases

| Variable | Required | Description |
|---|---|---|
| `USER_DB` | **yes** | SQLAlchemy URL for the users DB (Postgres in prod & dev-compose). |
| `POSTGRE_DB_URL` | **yes** | SQLAlchemy URL for the posts DB (Postgres). |
| `CINE_DB_URL` | no (`sqlite:///<DATA_DIR>/cine.db`) | SQLAlchemy URL for the SQLite movie catalog (`Game` table). |

## External APIs

| Variable | Required | Description |
|---|---|---|
| `IMDB_API_URL` | for `/info` | Base URL of the IMDb-style JSON API (`/search/titles`, `/titles/{id}`). Leave blank and set `MOCK_MOVIE_DATA=1` to run offline from fixtures. |
| `GROQ_KEY` | for translation | Groq API key (LLM title/synopsis translation). |
| `OPENSUBTITLES_KEYS` | for `/srt` | Comma-separated OpenSubtitles API keys. |
| `OPENSUBTITLE_USERNAME` | for `/srt` | OpenSubtitles account username. |
| `OPENSUBTITLE_PASSWORD` | for `/srt` | OpenSubtitles account password. |

## Payments & pricing

Plain-text values shown to users during the manual VIP payment flow.

| Variable | Description |
|---|---|
| `VIP_PRICE_CUP` / `VIP_PRICE_MLC` / `VIP_PRICE_USD` | VIP subscription prices per currency. |
| `PRICE1` / `PRICE2` / `PRICE3` | Publicity/other price tiers. |
| `CUP_CARD` / `CUP_CARD2` / `MLC_CARD` | Cuban payment card numbers. |
| `MOBILE` | Mobile-payment contact. |
| `Wallet_BEP` | Crypto wallet address (BEP-20). |
| `QVAPAY_LINK` | QvaPay / PayPal "PayMe" link. |

## Streaming server (aiohttp)

All optional; defaults shown.

| Variable | Default | Description |
|---|---|---|
| `STREAM_PORT` | `8080` | Port the stream server binds. |
| `STREAM_BIND` | `0.0.0.0` | Bind address. |
| `STREAM_BIN_CHANNEL` | — (**required for streaming**) | Channel used as a temporary bin for files being streamed. |
| `STREAM_URL` | auto | Public base URL. Blank ⇒ a Cloudflare tunnel is started automatically in dev. |
| `STREAM_HASH_LENGTH` | `6` | Length of the signed link hash. |
| `STREAM_MAX_CACHE_BYTES` | `209715200` | In-memory chunk cache cap (bytes). |
| `STREAM_PREFETCH_COUNT` | `15` | Chunks prefetched ahead of playback. |
| `STREAM_SLEEP_THRESHOLD` | `30` | Pyrogram sleep threshold. |
| `STREAM_MAX_RETRIES` | `1` | Per-chunk Telegram retry attempts. |
| `STREAM_RETRY_DELAY` | `0.5` | Base retry backoff (seconds). |
| `STREAM_MAX_CONCURRENT_DOWNLOADS` | `8` | Max simultaneous Telegram chunk downloads. |

## Local development / testing

Not used in production.

| Variable | Default | Description |
|---|---|---|
| `MOCK_MOVIE_DATA` | `0` | When truthy, `/info` reads from `FIXTURES_DIR` instead of `IMDB_API_URL`. |
| `FIXTURES_DIR` | `./tests/fixtures/movie_search` | JSON fixtures for the mock movie provider. Point at a private `.fixtures/` dir to use your own data. |
| `DATA_DIR` | `./data` | Runtime directory for the session file and `cine.db`. |
