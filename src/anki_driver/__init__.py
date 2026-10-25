"""anki-driver: a small example project built on the official `anki` package.

The `anki` package is the same collection/backend library that powers the
Anki desktop app and its add-ons. This module demonstrates the basics:
opening (or creating) a collection file, adding a note, and querying it.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from anki.collection import Collection


def demo(collection_path: str | Path) -> None:
    """Open/create a collection at `collection_path` and add a sample note."""
    col = Collection(str(collection_path))
    try:
        basic_notetype = col.models.by_name("Basic")
        if basic_notetype is None:
            raise RuntimeError("Could not find the built-in 'Basic' note type")

        note = col.new_note(basic_notetype)
        note["Front"] = "What package does anki-driver use?"
        note["Back"] = "The official `anki` Python package."
        col.add_note(note, col.decks.id("Default", create=True))

        card_count = col.card_count()
        print(f"Collection at {collection_path} now has {card_count} card(s).")
    finally:
        col.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        demo(Path(tmp_dir) / "collection.anki2")


if __name__ == "__main__":
    main()
