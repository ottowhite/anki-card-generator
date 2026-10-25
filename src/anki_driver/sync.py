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
"""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from anki.collection import Collection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION_PATH = PROJECT_ROOT / "data" / "collection.anki2"


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

    username = os.environ.get("ANKIWEB_USERNAME")
    if not username:
        username = input("AnkiWeb username/email: ")
    password = os.environ.get("ANKIWEB_PASSWORD")
    if not password:
        password = getpass.getpass("AnkiWeb password: ")

    collection_path: Path = args.collection
    collection_path.parent.mkdir(parents=True, exist_ok=True)

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
