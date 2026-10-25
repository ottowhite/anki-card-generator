# Implementation notes

For changing or debugging the infra. Each module's docstring covers its
own contract — this file holds only what the code *can't* tell you: the
layout at a glance, and the `anki` API behaviours that cost real
debugging time.

## Modules

- `sync.py` — AnkiWeb login + sync (`anki-driver-sync`). Owns
  `get_credentials`/`login`/`sync_now`/`open_default_collection`, shared
  by `cards.py`. `DEFAULT_COLLECTION_PATH` = `data/collection.anki2`,
  repo-relative, *not* the global Anki profile.
- `cards.py` — sync → add → sync, generalized over note types
  (`add-card`, subcommands `cloze`/`picture`/`basic`). A new shape = a
  subparser + a `*_card()` constructor; the sync mechanics don't change.
  Card *content* is the caller's job (the `add-spanish-card` skill).
- `images.py` — `fetch_and_resize(url)`: download, re-encode as JPEG
  capped at 400px/quality 70, keeping AnkiWeb's media quota and sync time
  low. Finding the URL is the caller's job.
- `__init__.py` — `demo()`, wired as `anki-driver`. Not used by the card
  workflow.
- `data/collection.anki2` — gitignored copy of the real collection, seeded
  once from `~/Library/Application Support/Anki2/User 1/collection.anki2`.
  Working on a copy means no file-lock conflict with the desktop app.

## anki API notes

Basics: `Collection(path)` opens or creates; note types via
`col.models.by_name(...)` ("Basic", "Cloze", … ship with the default
profile); `col.new_note(nt)` → `note["Front"] = ...` →
`col.add_note(note, col.decks.id(name, create=True))`; always
`col.close()` in a `finally`.

Sign-in/sync: `col.sync_login(user, pass, endpoint)` returns a `SyncAuth`
(session `hkey`); `col.sync_collection(auth, sync_media)` syncs. Both are
methods on an *open* collection — any open one works for `sync_login`,
since it just proxies to the Rust backend.

Three traps:

1. **`sync_collection(sync_media=True)` does not wait for media.** It only
   *starts* the transfer and returns; `col.media_sync_status().active` is
   still `True`. Close the collection then and a pending image is silently
   dropped — its `media` row in `collection.media.db2` stays `dirty=1`
   forever and other devices report "image is missing". `sync_now()` polls
   until `active` is `False` (`_wait_for_media_sync`). Always go through
   `sync_now()`, never `sync_collection` directly, when media is involved.

2. **`.required` is an enum, not a count**
   (`SyncCollectionResponse.ChangesRequired`:
   `NO_CHANGES`/`NORMAL_SYNC`/`FULL_SYNC`/`FULL_DOWNLOAD`/`FULL_UPLOAD`).
   `0` (`NO_CHANGES`) after a successful call means both sides now match —
   the good result, not "nothing happened". The `FULL_*` values mean the
   call did **nothing** — new notes stay at `usn -1` and never reach other
   devices, though no error is raised (this shipped a "synced" card that
   never arrived). `sync_now()` resolves them with a full *download*
   (AnkiWeb wins) when nothing local is pending, and raises otherwise; it
   never auto-uploads. Full syncs must use `out.new_endpoint` (the
   account's shard, e.g. `sync3.ankiweb.net`) or AnkiWeb answers HTTP 400
   "missing original size". `add-card` also checks its new notes got a
   server `usn` after the final sync.

3. **Don't verify a sync with a fresh collection.** An unrelated new
   collection shares no sync history, so pulling it needs an explicit
   `full_upload_or_download` negotiation that `sync_collection` won't
   perform — giving a false "it's not there". Check the server-assigned
   `usn` instead: `col.db.all("select id, usn from notes where ...")`.
   Positive means the server has it; `-1` means still pending.
