# anki-driver

Manages a personal Spanish-vocabulary Anki collection (official `anki`
PyPI package), synced with AnkiWeb.

- **Add a card** → `add-spanish-card` skill. Self-contained; read nothing else.
- **Change or debug the infra** → `docs/IMPLEMENTATION.md` (anki API
  gotchas that cost real debugging time).
- Human setup/usage → `README.md`.

## Tooling

- `uv`, not pip/poetry: `uv add <pkg>`, `uv sync`, `uv run <cmd>`. Python
  3.12 via `.python-version`.
- Credentials: `direnv` loads `.env.local` (gitignored, real
  `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD`) via `.envrc`. `.env.example` is the
  committed template. Never ask for credentials in chat; never commit
  `.env.local`.
