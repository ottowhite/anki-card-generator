# anki-driver

A Python project built on the official [`anki`](https://pypi.org/project/anki/)
package — the same collection/backend library that powers the Anki desktop
app and its add-ons — to manage a personal Spanish-vocabulary collection
synced with AnkiWeb.

Docs are split by audience:

- **This file** — human setup/usage.
- [`docs/CARD_TYPES.md`](docs/CARD_TYPES.md) — what a good card looks like
  (card shapes, Spanish content conventions). No code.
- [`.claude/skills/add-spanish-card/`](.claude/skills/add-spanish-card/SKILL.md) —
  the minimal workflow an agent uses to actually add a card.
- [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) — how the scripts,
  sync, and media upload work internally; for maintaining the code itself.

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

By default it syncs `data/collection.anki2` — a repo-local **copy** of the
collection, decoupled from the Anki desktop app (no file-lock conflict, no
need to quit the app first). Override with `--collection /path/to/other.anki2`.
It was seeded once from `~/Library/Application Support/Anki2/User 1/collection.anki2`;
to refresh it from the real profile again later:

```bash
cp "$HOME/Library/Application Support/Anki2/User 1/collection.anki2" data/collection.anki2
```

### Adding cards

```bash
uv run add-card cloze --text "...{{c1::palabra}}..." --extra "..."
uv run add-card picture --image-url "https://..." --word "la silla" --extra "..."
uv run add-card basic --front "..." --back "..." [--image-url URL]
```

Each run syncs before adding, adds the note(s), then syncs again (waiting
for any image to actually finish uploading before it returns). `--deck`
targets a deck other than the default (`Vocabulario`).

For what to actually put in `--text`/`--extra`/`--word` (card shape,
Spanish content rules), see [`docs/CARD_TYPES.md`](docs/CARD_TYPES.md) —
or just use the `add-spanish-card` skill, which already knows all of this.

## Project layout

- `src/anki_driver/__init__.py` — demo: create/open a collection, add a note
- `src/anki_driver/sync.py` — AnkiWeb login + sync helpers (`anki-driver-sync`)
- `src/anki_driver/cards.py` — generic add-card mechanics (`add-card`)
- `src/anki_driver/images.py` — download + shrink a web image for attaching
  to a card
- `data/collection.anki2` — repo-local collection copy (gitignored)
- `.envrc` / `.env.example` / `.env.local` — direnv-managed credentials
- `.claude/skills/add-spanish-card/` — agent-facing card-adding workflow
- `docs/CARD_TYPES.md` — card content reference
- `docs/IMPLEMENTATION.md` — engineering/implementation notes
- `pyproject.toml` — dependencies (`anki`, `pillow`) and project metadata
