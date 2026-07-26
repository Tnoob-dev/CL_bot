## Summary

<!-- What does this PR change and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / internal (no behavior change)
- [ ] Documentation
- [ ] CI / build

## Checklist

- [ ] Branched off `dev` and targeting `dev`.
- [ ] `make lint` passes (ruff + basedpyright).
- [ ] `make test` passes.
- [ ] Existing bot commands still behave the same (unless this is an intended change).
- [ ] New configuration is read via `cinemalibrarybot.config.settings` (not `os.getenv`) and documented in `docs/configuration.md` + `.env.example`.
- [ ] No CWD-relative file paths (resolved via `settings.DATA_DIR` / `settings.ASSETS_DIR`).

## Notes for reviewers

<!-- Anything that needs special attention, manual testing steps, etc. -->
