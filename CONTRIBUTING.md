# Contributing

Thanks for helping improve CinemaLibraryBot. This guide covers the branch flow,
local setup, and the checks to run before opening a pull request.

## Branch flow

- `main` — production. Only updated via PRs from `dev`.
- `dev` — integration branch. **Branch your work off `dev`** and open PRs back
  into `dev`.
- Feature branches: `feat/...`, `fix/...`, `refactor/...`, `docs/...`.

## Getting set up

```bash
uv sync --dev            # install runtime + dev dependencies
cp .env.example data/.env # fill in credentials (see docs/configuration.md)
```

See [`docs/local-development.md`](docs/local-development.md) for the full
guide, including how to create and test a dev bot on Telegram and run the bot
fully offline with mocked movie data.

## Before you push

Run the same checks CI runs:

```bash
make lint    # ruff check + ruff format --check + basedpyright
make test    # pytest
```

Or individually: `uv run ruff check .`, `uv run ruff format .`,
`uv run basedpyright`, `uv run pytest`.

## Guidelines

- **Behavior parity.** Unless a change is explicitly a feature/bugfix, existing
  bot commands must behave identically. The smoke test asserts all handlers
  still register.
- **Config, not `os.getenv`.** Read configuration through
  `cinemalibrarybot.config.settings`, never `os.getenv` directly.
- **No CWD-relative paths.** Resolve files via `settings.DATA_DIR`,
  `settings.ASSETS_DIR`, or package resources — never assume the process's
  working directory.
- **Mock external calls in tests.** New external boundaries belong in
  `services/` and should be mockable like `services/movie_search.py`.

## Commits

Write descriptive commit messages explaining *what* changed and *why*.

## Releases

Releases are cut by pushing a `vX.Y.Z` tag; CI runs lint + tests and publishes
a GitHub Release with generated notes. See
[`docs/deployment.md`](docs/deployment.md).
