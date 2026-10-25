"""Sign in to AnkiWeb and sync the repo-local collection, using the `anki`
package.

Credentials are never hardcoded or passed on the command line. Set them via
a direnv-managed .env.local (see .env.example), or export them yourself:

    export ANKIWEB_USERNAME="you@example.com"
    export ANKIWEB_PASSWORD="your-password"
    uv run anki-driver-sync

If `ANKIWEB_PASSWORD` is unset, you'll be prompted via a hidden terminal
prompt (`getpass`) instead - it is never echoed or logged.

By default this syncs data/collection.anki2, a repo-local copy of the
collection, decoupled from the one open in the Anki desktop app - no need
to close the app first.

The `get_credentials`/`login`/`sync_now` helpers here are shared with other
scripts (e.g. `cards.py`) that need to sync before/after making changes.
"""

from __future__ import annotations

import argparse
import getpass
import os
import time
from pathlib import Path

from anki.collection import Collection
from anki.sync import SyncAuth
from anki.sync_pb2 import SyncCollectionResponse

ChangesRequired = SyncCollectionResponse.ChangesRequired
FULL_SYNC_REQUIRED = {
    ChangesRequired.FULL_SYNC,
    ChangesRequired.FULL_DOWNLOAD,
    ChangesRequired.FULL_UPLOAD,
}
PENDING_CHANGE_TABLES = ("notes", "cards", "revlog", "graves", "decks", "notetypes")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION_PATH = PROJECT_ROOT / "data" / "collection.anki2"
MEDIA_SYNC_TIMEOUT_SECONDS = 120
MEDIA_SYNC_POLL_INTERVAL_SECONDS = 0.5


def get_credentials() -> tuple[str, str]:
    """Read AnkiWeb credentials from the environment, prompting if unset."""
    username = os.environ.get("ANKIWEB_USERNAME")
    if not username:
        username = input("AnkiWeb username/email: ")
    password = os.environ.get("ANKIWEB_PASSWORD")
    if not password:
        password = getpass.getpass("AnkiWeb password: ")
    return username, password


def login(col: Collection, username: str, password: str) -> SyncAuth:
    """Exchange AnkiWeb credentials for a SyncAuth (session key)."""
    return col.sync_login(username=username, password=password, endpoint=None)


def sync_now(col: Collection, auth: SyncAuth, sync_media: bool = True) -> str:
    """Run one sync pass and return a human-readable result.

    `sync_collection(sync_media=True)` only *starts* media upload/download
    in the background and returns immediately - it does not wait for it to
    finish. Without waiting here, a just-added image can get silently left
    behind (still `dirty` locally) if the collection is closed right after,
    which is exactly what happened the first time this was tried: the note
    synced, but its image never reached AnkiWeb ("image is missing").
    """
    out = col.sync_collection(auth, sync_media=sync_media)
    if out.HasField("new_endpoint"):
        # AnkiWeb moved the account to another shard; full syncs must use it.
        auth.endpoint = out.new_endpoint
    result = ChangesRequired.Name(out.required)
    if out.required in FULL_SYNC_REQUIRED:
        _full_download(col, auth, out, sync_media)
        result += " (resolved: downloaded from AnkiWeb)"
    if sync_media:
        _wait_for_media_sync(col)
    return result


def pending_change_count(col: Collection) -> int:
    """Rows changed locally but not yet on AnkiWeb (usn -1)."""
    return sum(
        col.db.scalar(f"select count() from {table} where usn = -1")
        for table in PENDING_CHANGE_TABLES
    )


def _full_download(col: Collection, auth: SyncAuth, out, sync_media: bool) -> None:
    """Resolve a "full sync required" result by replacing the local copy
    with AnkiWeb's - AnkiWeb (and the phone) is the source of truth here.

    A normal `sync_collection` silently does nothing in this state: it
    returns FULL_SYNC/FULL_DOWNLOAD and leaves new notes at usn -1, so a
    card "added and synced" never reaches other devices. Downloading would
    discard local-only changes, so refuse if there are any, and never
    auto-upload (that would overwrite AnkiWeb).
    """
    name = ChangesRequired.Name(out.required)
    if out.required == ChangesRequired.FULL_UPLOAD:
        raise RuntimeError(f"AnkiWeb requires {name}; refusing to overwrite AnkiWeb automatically")
    pending = pending_change_count(col)
    if pending:
        raise RuntimeError(
            f"AnkiWeb requires {name}, but {pending} local change(s) are unsynced "
            "and would be lost by a download. Resolve manually."
        )
    print(f"  AnkiWeb requires {name}; downloading the full collection...")
    col.close_for_full_sync()
    col.full_upload_or_download(
        auth=auth,
        server_usn=out.server_media_usn if sync_media else None,
        upload=False,
    )
    col.reopen(after_full_sync=True)


def _wait_for_media_sync(
    col: Collection,
    timeout: float = MEDIA_SYNC_TIMEOUT_SECONDS,
    poll_interval: float = MEDIA_SYNC_POLL_INTERVAL_SECONDS,
) -> None:
    deadline = time.monotonic() + timeout
    while col.media_sync_status().active:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Media sync did not finish within {timeout}s")
        time.sleep(poll_interval)


def open_default_collection(collection_path: Path = DEFAULT_COLLECTION_PATH) -> Collection:
    collection_path.parent.mkdir(parents=True, exist_ok=True)
    return Collection(str(collection_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection",
        type=Path,
        default=DEFAULT_COLLECTION_PATH,
        help=f"Path to the .anki2 collection file to sync (default: {DEFAULT_COLLECTION_PATH}).",
    )
    parser.add_argument(
        "--no-media",
        action="store_true",
        help="Skip media sync (faster, collection data only).",
    )
    args = parser.parse_args()

    username, password = get_credentials()

    print(f"Opening collection: {args.collection}")
    col = open_default_collection(args.collection)
    try:
        print("Logging in to AnkiWeb...")
        auth = login(col, username, password)
        print("Login succeeded. Syncing collection...")
        result = sync_now(col, auth, sync_media=not args.no_media)
        print(f"Sync finished: {result}")
    finally:
        col.close()


if __name__ == "__main__":
    main()
