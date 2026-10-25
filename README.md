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

### Adding cards (sync -> add -> sync)

The repeatable workflow for "give me a card for word X": sync, add one or
more notes, sync again. Not coupled to any single note type — `cloze`,
`picture`, and `basic` subcommands exist today, more can be added later.

```bash
uv run add-card cloze \
  --text "Para programar bien necesitas mucha {{c1::habilidad}} y práctica constante." \
  --extra "sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud."
```

- `--text` is a complete Spanish sentence with the target word wrapped in
  `{{c1::...}}` — repeat `--text` for multiple cards in one run.
- `--extra` (optional) fills the Cloze note type's "Back Extra" field;
  pair it positionally with `--text`, once per card, or omit entirely. See
  **Card content conventions** below for what goes in here.
- `--deck` overrides the target deck (default: `Vocabulario`).
- Cloze cards never carry an image — use `picture` for that (below).

```bash
uv run add-card picture \
  --image-url "https://commons.wikimedia.org/wiki/Special:FilePath/Old-chair.jpg" \
  --word "la silla" \
  --extra "sustantivo, femenino."
```

A picture card is a plain `Basic` note where the **front is the image
alone** (nothing else) and the **back is the word plus grammar info** —
see an object, recall the word, flip to check. `--image-url` is downloaded
and shrunk to a small low-res JPEG (see below); finding that URL (e.g. via
a web image search for a concrete object) is done by whoever calls
`add-card`, not by this code.

```bash
uv run add-card basic --front "..." --back "..." [--image-url URL]
```

`basic` is the general front/back escape hatch (e.g. for a non-picture,
non-cloze card); `picture` is just a convenience wrapper around it with
`front=""` and `image_field="Front"`.

Each run: logs in, syncs (pulls latest), adds the note(s), syncs again
(pushes them up) — **and actually waits for any attached image to finish
uploading** before closing the collection (see `sync.py`'s `sync_now`;
`sync_collection(sync_media=True)` only starts the media transfer in the
background, so skipping this wait silently drops images — this bit us
once already, see git history). Composing the actual card content
(sentence, word type, image search query, etc.) is a judgment call made by
whoever invokes this (e.g. Claude) — this script only handles the
sync/add/sync mechanics, plus the image download/resize/attach plumbing.

#### Card content conventions (Spanish vocab cards)

All cards are entirely in Spanish — no English anywhere on the card. The
back (Cloze "Back Extra") includes, in Spanish, whatever of these apply:

- **Tipo de palabra**: sustantivo, verbo, adjetivo, adverbio, preposición,
  pronombre, conjunción, artículo, interjección, etc.
- **Género**: masculino / femenino (for nouns/adjectives).
- **Infinitivo**: if the front shows a conjugated verb form, give the
  infinitive.
- **Preposición**: if the word/verb takes a fixed preposition that isn't
  already visible in the front sentence (e.g. *pensar en*, *soñar con*).
- Anything else useful (synonyms, a brief Spanish clarification), also in
  Spanish.

Example: `sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud.`

#### Images

`anki_driver.images.fetch_and_resize(url)` downloads an image and
re-encodes it as a JPEG capped at 400px on the long side — "low resolution"
is deliberate, to keep the collection and AnkiWeb's media quota small.
Finding a suitable image URL (e.g. via a web image search for a concrete
object) is done by whoever calls `add-card`, not by this code.

## Project layout

- `src/anki_driver/__init__.py` — demo: create/open a collection, add a note
- `src/anki_driver/sync.py` — AnkiWeb login + sync helpers (`anki-driver-sync`)
- `src/anki_driver/cards.py` — generic add-card mechanics: sync-before,
  add note(s) of any note type, sync-after (`add-card`)
- `src/anki_driver/images.py` — download + shrink a web image for attaching
  to a card
- `data/collection.anki2` — repo-local collection copy (gitignored)
- `.envrc` / `.env.example` / `.env.local` — direnv-managed credentials
- `pyproject.toml` — dependencies (`anki`, `pillow`) and project metadata
