"""Sign in to AnkiWeb and sync a local collection, using the `anki` package.

Credentials are never hardcoded or passed on the command line. Set them in
your own shell before running this script:

    export ANKIWEB_USERNAME="you@example.com"
    export ANKIWEB_PASSWORD="your-password"
    uv run anki-driver-sync

If `ANKIWEB_PASSWORD` is unset, you'll be prompted via a hidden terminal
prompt (`getpass`) instead - it is never echoed or logged.

By default this targets your real local profile's collection, which is
normally open inside the Anki desktop app. Close Anki Desktop first, or
sync will fail to acquire the file lock / your changes may not round-trip.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

from anki.collection import Collection

DEFAULT_ANKI2_DIR = Path.home() / "Library" / "Application Support" / "Anki2"


def find_default_collection() -> Path | None:
    """Best-effort guess at the current profile's collection.anki2."""
    if not DEFAULT_ANKI2_DIR.is_dir():
        return None
    candidates = sorted(DEFAULT_ANKI2_DIR.glob("*/collection.anki2"))
    return candidates[0] if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection",
        type=Path,
        default=None,
        help="Path to the .anki2 collection file to sync (default: auto-detect "
        "the current profile under ~/Library/Application Support/Anki2).",
    )
    parser.add_argument(
        "--no-media",
        action="store_true",
        help="Skip media sync (faster, collection data only).",
    )
    args = parser.parse_args()

    username = os.environ.get("ANKIWEB_USERNAME")
    if not username:
        username = input("AnkiWeb username/email: ")
    password = os.environ.get("ANKIWEB_PASSWORD")
    if not password:
        password = getpass.getpass("AnkiWeb password: ")

    collection_path = args.collection or find_default_collection()
    if collection_path is None:
        print(
            "Could not auto-detect a collection.anki2. Pass --collection /path/to/collection.anki2.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"Opening collection: {collection_path}")
    col = Collection(str(collection_path))
    try:
        print("Logging in to AnkiWeb...")
        auth = col.sync_login(username=username, password=password, endpoint=None)
        print("Login succeeded. Syncing collection...")
        out = col.sync_collection(auth, sync_media=not args.no_media)
        print(f"Sync finished: {out.required}")
    finally:
        col.close()


if __name__ == "__main__":
    main()
