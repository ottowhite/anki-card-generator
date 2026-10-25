# anki-driver

Python project using the official `anki` PyPI package (the Anki
collection/backend library used by the desktop app and add-ons).

## Tooling

- Dependency/venv management: `uv` (not pip/poetry). Use `uv add <pkg>`,
  `uv sync`, `uv run <cmd>`.
- Python version pinned via `.python-version` (3.12).
- Env/credentials: `direnv`. `.envrc` runs `dotenv_if_exists .env.local`.
  `.env.example` (committed, placeholders) is the template; `.env.local`
  (gitignored, real `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD`) is the real one,
  copied from `.env.example` and edited locally — never ask the user to
  paste real credentials into chat, and never commit `.env.local`.

## Structure

- `src/anki_driver/__init__.py` — package entry point. `demo()` opens/creates
  an Anki `Collection` at a given path and adds a sample note via the
  built-in "Basic" note type. `main()` runs `demo()` against a temp
  collection; wired up as the `anki-driver` console script in
  `pyproject.toml`.
- `src/anki_driver/sync.py` — signs in to AnkiWeb and syncs the repo-local
  collection copy. Wired up as the `anki-driver-sync` console script. Reads
  `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD` from the environment (populated by
  direnv from `.env.local`, falls back to `input()`/`getpass` prompts) —
  credentials must never be hardcoded, passed as CLI args, or committed.
  `DEFAULT_COLLECTION_PATH` is `data/collection.anki2` (repo-relative, via
  `Path(__file__).resolve().parents[2]`), not the global Anki profile.
- `data/collection.anki2` — gitignored copy of the real collection (seeded
  once via `cp` from `~/Library/Application Support/Anki2/User 1/collection.anki2`).
  Operating on this copy instead of the global profile means no file-lock
  conflict with the Anki desktop app.
- `src/anki_driver/cards.py` — the repeatable "give me a card for word X"
  workflow: sync -> add one or more Cloze notes to the Vocabulario deck ->
  sync. Wired up as the `anki-driver-add-cloze` console script. `ClozeCard`
  holds `text` (full Spanish sentence with `{{c1::word}}`) and optional
  `extra` (Cloze note type's "Back Extra" field). `add_cloze_cards()` does
  login + sync-before + add-each + sync-after in one call; reuses
  `get_credentials`/`login`/`sync_now`/`open_default_collection` from
  `sync.py` rather than duplicating them. Composing the actual Spanish
  sentence per English word is done by the caller (e.g. Claude) — this
  module only owns the sync/add/sync mechanics.

## Key API notes (anki package)

- `anki.collection.Collection(path)` opens or creates a `.anki2` collection
  file at `path`.
- Note types ("models") are looked up via `col.models.by_name(...)`; the
  default profile ships with "Basic", "Basic (and reversed card)", "Cloze",
  etc.
- Create a note with `col.new_note(notetype)`, set its fields by name
  (`note["Front"] = ...`), then persist with
  `col.add_note(note, col.decks.id("Default", create=True))`.
- Always `col.close()` when done (demo uses `try/finally`).
- AnkiWeb sign-in/sync: `col.sync_login(username, password, endpoint)`
  returns a `SyncAuth` (session `hkey`); `col.sync_collection(auth,
  sync_media)` performs the actual sync. Both are methods on an open
  `Collection` (any open collection works for `sync_login`, since it just
  proxies to the Rust backend).
- `sync_collection(...).required` is an enum (`anki.sync.sync_pb2.
  SyncCollectionResponse.ChangesRequired`: `NO_CHANGES`/`NORMAL_SYNC`/
  `FULL_SYNC`/`FULL_DOWNLOAD`/`FULL_UPLOAD`), not a count. `0`
  (`NO_CHANGES`) after a successful call means the sync completed and both
  sides now match — that's the expected/good result, not "nothing
  happened." To verify a change actually reached the server, don't spin up
  a brand-new unrelated local collection and check if it's populated — an
  unrelated collection has no shared sync history, so pulling it requires
  an explicit full-sync negotiation (`full_upload_or_download`) that
  `sync_collection` alone won't perform, giving a false "it's not there"
  reading. Instead check each note/card's `usn` column directly (`col.db.all
  ("select id, usn from notes where ...")`) — a positive, server-assigned
  `usn` confirms the server has it; `-1` means still pending.
