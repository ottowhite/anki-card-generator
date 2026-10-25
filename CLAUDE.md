# anki-driver

Python project using the official `anki` PyPI package to manage a
personal Spanish-vocabulary Anki collection, synced with AnkiWeb.

This file is intentionally short — it loads into *every* session
automatically, including one whose only job is generating a card. Detail
lives in separate docs, read only when relevant:

- **Adding a card** → use the `add-spanish-card` skill. It's the whole
  workflow for that one task; nothing else here is needed for it.
- **What a good card looks like** (card types, Spanish content
  conventions) → `docs/CARD_TYPES.md`. Content only, no code.
- **How the scripts/sync/media actually work, API gotchas** →
  `docs/IMPLEMENTATION.md`. Needed only when changing or debugging the
  infra itself.

## Tooling

- Dependency/venv management: `uv` (not pip/poetry). Use `uv add <pkg>`,
  `uv sync`, `uv run <cmd>`. Python version pinned via `.python-version`
  (3.12).
- Env/credentials: `direnv`. `.envrc` runs `dotenv_if_exists .env.local`.
  `.env.example` (committed, placeholders) is the template; `.env.local`
  (gitignored, real `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD`) is the real one,
  copied from `.env.example` and edited locally — never ask the user to
  paste real credentials into chat, and never commit `.env.local`.
