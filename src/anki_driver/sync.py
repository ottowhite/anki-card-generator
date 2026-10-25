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
from pathlib import Path

from anki.collection import Collection
from anki.sync import SyncAuth

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION_PATH = PROJECT_ROOT / "data" / "collection.anki2"


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
    """Run one sync pass and return a human-readable result."""
    out = col.sync_collection(auth, sync_media=sync_media)
    return str(out.required)


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
