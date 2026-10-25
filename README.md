# anki-driver

A Python project built on the official [`anki`](https://pypi.org/project/anki/)
package — the same collection/backend library that powers the Anki desktop
app and its add-ons.

## Setup

Managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
uv run anki-driver
```

This runs the demo in `src/anki_driver/__init__.py`, which opens a temporary
Anki collection, adds a note using the built-in "Basic" note type, and
prints the resulting card count.

### Signing in to AnkiWeb / syncing

```bash
export ANKIWEB_USERNAME="you@example.com"
export ANKIWEB_PASSWORD="your-password"   # or omit and get prompted (hidden input)
uv run anki-driver-sync
```

This logs in to AnkiWeb via `Collection.sync_login` and syncs your local
collection via `Collection.sync_collection`. Credentials are read from your
shell environment or a hidden terminal prompt — never pass them as CLI args
or commit them anywhere.

By default it targets the current profile's `collection.anki2` under
`~/Library/Application Support/Anki2/` (override with `--collection`).
**Close the Anki desktop app first** — it holds a lock on the same file.

## Project layout

- `src/anki_driver/__init__.py` — demo: create/open a collection, add a note
- `src/anki_driver/sync.py` — AnkiWeb login + sync (`anki-driver-sync`)
- `pyproject.toml` — dependencies (`anki`) and project metadata
