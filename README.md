# anki-driver

A Python project built on the official [`anki`](https://pypi.org/project/anki/)
package — the same collection/backend library that powers the Anki desktop
app and its add-ons.

## Setup

Managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### Environment / credentials

This project uses [direnv](https://direnv.net/) to load AnkiWeb credentials
automatically:

```bash
cp .env.example .env.local   # then edit .env.local with your real credentials
direnv allow .
```

- `.env.example` — committed template with placeholder values.
- `.env.local` — your real `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD`, gitignored,
  loaded automatically by `.envrc` whenever you `cd` into this directory.
  Edit it directly yourself; never paste real credentials into chat/AI tools.

## Usage

```bash
uv run anki-driver
```

This runs the demo in `src/anki_driver/__init__.py`, which opens a temporary
Anki collection, adds a note using the built-in "Basic" note type, and
prints the resulting card count.

### Signing in to AnkiWeb / syncing

With direnv set up (above), credentials load automatically:

```bash
uv run anki-driver-sync
```

Otherwise, export them yourself first (or you'll be prompted, with the
password hidden):

```bash
export ANKIWEB_USERNAME="you@example.com"
export ANKIWEB_PASSWORD="your-password"
uv run anki-driver-sync
```

This logs in to AnkiWeb via `Collection.sync_login` and syncs via
`Collection.sync_collection`. Credentials are never passed as CLI args or
committed anywhere.

By default it syncs `data/collection.anki2` — a repo-local **copy** of the
collection (seeded once from the real profile; see below), decoupled from
the Anki desktop app, so there's no file-lock conflict and no need to quit
the app first. Override with `--collection /path/to/other.anki2`.

`data/collection.anki2` is gitignored (personal data, binary, changes on
every sync) — it was copied once from
`~/Library/Application Support/Anki2/User 1/collection.anki2`. To refresh it
from the real profile again later:

```bash
cp "$HOME/Library/Application Support/Anki2/User 1/collection.anki2" data/collection.anki2
```

## Project layout

- `src/anki_driver/__init__.py` — demo: create/open a collection, add a note
- `src/anki_driver/sync.py` — AnkiWeb login + sync (`anki-driver-sync`)
- `data/collection.anki2` — repo-local collection copy (gitignored)
- `.envrc` / `.env.example` / `.env.local` — direnv-managed credentials
- `pyproject.toml` — dependencies (`anki`) and project metadata
