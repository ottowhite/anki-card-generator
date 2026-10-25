# anki-driver

Manages a personal Spanish-vocabulary Anki collection, synced with
AnkiWeb, via the official [`anki`](https://pypi.org/project/anki/) package
— the same collection/backend library that powers the desktop app.

Also: [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) for the internals,
and [`.claude/skills/add-spanish-card/SKILL.md`](.claude/skills/add-spanish-card/SKILL.md)
for what a good card looks like and how an agent adds one.

## Setup

```bash
uv sync                      # https://docs.astral.sh/uv/
cp .env.example .env.local   # then edit in your real AnkiWeb credentials
direnv allow .               # https://direnv.net/
```

`.envrc` loads `.env.local` (gitignored) whenever you `cd` here, so
`ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD` are always set. Edit that file
yourself — never paste real credentials into chat/AI tools.

## Usage

```bash
uv run anki-driver-sync      # sync data/collection.anki2 with AnkiWeb
uv run anki-driver           # demo: temp collection, add a note, print card count

uv run add-card cloze --text "...{{c1::palabra}}..." --grammar "..." [--definition/--synonyms/--note "..."]
uv run add-card picture --image-url "https://..." --word "la silla" --grammar "..." [--definition/--synonyms/--note "..."]
uv run add-card basic --front "..." --back "..." [--image-url URL]
```

One run adds any number of cards of one type: repeat the options, paired
by position (one `--text`, one `--image-url`+`--word`, or one
`--front`+`--back` per card). Optional options go once per card (`""` to
skip one) or not at all.

Each `add-card` run syncs, adds the note(s), then syncs again — waiting for
any image to finish uploading before it returns. `--deck` targets a deck
other than the default (`Vocabulario`).

Without direnv, export the two variables yourself first, or let it prompt
you (the password stays hidden).

### The collection file

Commands act on `data/collection.anki2`, a repo-local **copy** — no
file-lock conflict with the desktop app, no need to quit it first.
`--collection /path/to/other.anki2` overrides. To reseed it from the real
profile:

```bash
cp "$HOME/Library/Application Support/Anki2/User 1/collection.anki2" data/collection.anki2
```

## Layout

```
src/anki_driver/  sync.py (AnkiWeb sync) · cards.py (add-card) · images.py
                  (fetch/shrink) · __init__.py (demo)
data/             collection.anki2, gitignored
.claude/skills/   agent-facing card-adding workflow
docs/             implementation notes
```
