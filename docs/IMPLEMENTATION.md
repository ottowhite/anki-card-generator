# Implementation notes

How this codebase works, for whoever is maintaining or extending it —
not needed to just add a card (see the `add-spanish-card` skill for
that) and not about what makes good card content (see `CARD_TYPES.md`).

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
  workflow, generalized across note types (not coupled to Cloze). Wired up
  as the `add-card` console script with `cloze`/`picture`/`basic`
  subcommands (add more by adding a subparser + a `*_card()` constructor,
  no changes to the sync mechanics needed). `CardSpec` holds `notetype`,
  `field_values`, and an optional `image_url`/`image_field`. `cloze_card()`
  takes no image params at all - **images never go on Cloze cards**;
  `picture_card(word, image_url, extra)` builds a `Basic` note with the
  image alone on `Front` and the word+info on `Back` (a real picture-recall
  card, not an image bolted onto a sentence card - got this wrong once,
  see git history). `add_cards()` does login + sync-before + add-each +
  sync-after in one call; reuses
  `get_credentials`/`login`/`sync_now`/`open_default_collection` from
  `sync.py` rather than duplicating them. Composing the actual card content
  per word (Spanish sentence, word type, image search query, etc.) is done
  by the caller (e.g. the `add-spanish-card` skill) — this module only owns
  the sync/add/sync mechanics plus image attachment plumbing.
- `src/anki_driver/images.py` — `fetch_and_resize(url)` downloads an image
  and re-encodes it as a JPEG capped at 400px/quality 70 (`Pillow`), small
  enough to keep AnkiWeb's media quota and sync time low. `add-card
  --image-url` wires it to `col.media.add_file()`, which dedups by content
  hash; the stored filename is derived from the URL's last path segment
  (see `_slug_from_url`) rather than a random tempfile name, so media files
  stay recognizable. Finding the image URL itself (e.g. via a web image
  search for a concrete noun) is the caller's job, not this module's.

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
- **`sync_collection(auth, sync_media=True)` does NOT wait for media.** It
  only *starts* the media upload/download as a background task and returns
  immediately - `col.media_sync_status().active` is `True` right after it
  returns. If you close the collection then, a pending image is silently
  dropped (its row in `collection.media.db2`'s `media` table stays
  `dirty=1` forever, and AnkiWeb reports "image is missing" on other
  devices). `sync.py`'s `sync_now()` polls `media_sync_status()` until
  `active` is `False` (see `_wait_for_media_sync`) - always go through
  `sync_now()`, never call `sync_collection` directly when media might be
  involved.
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
