"""Add Cloze cards to the Vocabulario deck, syncing before and after.

This mechanizes the repeatable workflow: sync (pull latest from AnkiWeb),
add one or more new Cloze notes, sync again (push them back up). The
actual word -> Spanish-sentence-with-cloze authoring is done by whoever
calls this (e.g. Claude, composing a fully-Spanish sentence per word) -
this module just handles the sync/add/sync mechanics reliably.

Usage:
    uv run anki-driver-add-cloze \\
        --text "Para programar bien necesitas mucha {{c1::habilidad}} y practica." \\
        --extra "Sinonimos: destreza, capacidad, aptitud."

    # Multiple cards in one go - pair --text/--extra by position:
    uv run anki-driver-add-cloze \\
        --text "Primera {{c1::frase}}." --extra "nota 1" \\
        --text "Segunda {{c1::frase}}." --extra "nota 2"
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from anki.collection import Collection
from anki.decks import DeckId

from anki_driver.sync import (
    DEFAULT_COLLECTION_PATH,
    get_credentials,
    login,
    open_default_collection,
    sync_now,
)

DEFAULT_DECK = "Vocabulario"
CLOZE_NOTETYPE = "Cloze"


@dataclass
class ClozeCard:
    text: str  # e.g. 'Ella tiene mucha {{c1::habilidad}} para esto.'
    extra: str = ""  # optional "Back Extra" content (synonyms, notes, etc.)


def add_cloze_note(col: Collection, deck_id: DeckId, card: ClozeCard) -> None:
    notetype = col.models.by_name(CLOZE_NOTETYPE)
    if notetype is None:
        raise RuntimeError(f"Note type {CLOZE_NOTETYPE!r} not found in collection")
    if "{{c1::" not in card.text and "{{c" not in card.text:
        raise ValueError(f"Cloze text has no {{{{c1::...}}}} marker: {card.text!r}")

    note = col.new_note(notetype)
    note["Text"] = card.text
    note["Back Extra"] = card.extra
    col.add_note(note, deck_id)


def add_cloze_cards(
    cards: list[ClozeCard],
    deck_name: str = DEFAULT_DECK,
    collection_path=DEFAULT_COLLECTION_PATH,
    sync_media: bool = False,
) -> None:
    """Sync, add the given cloze cards to `deck_name`, then sync again."""
    if not cards:
        raise ValueError("No cards given")

    username, password = get_credentials()
    col = open_default_collection(collection_path)
    try:
        auth = login(col, username, password)

        print("Syncing before changes...")
        print(f"  -> {sync_now(col, auth, sync_media=sync_media)}")

        deck_id = col.decks.id(deck_name, create=True)
        for card in cards:
            add_cloze_note(col, deck_id, card)
            print(f"Added card to {deck_name!r}: {card.text}")

        print("Syncing after changes...")
        print(f"  -> {sync_now(col, auth, sync_media=sync_media)}")
    finally:
        col.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text",
        action="append",
        required=True,
        dest="texts",
        help="A fully-formed cloze sentence, e.g. 'Hoy tengo {{c1::prisa}}.' "
        "Repeat --text for multiple cards.",
    )
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        dest="extras",
        help="Optional 'Back Extra' content, paired by position with --text. "
        "Repeat alongside --text, or omit entirely for no extras.",
    )
    parser.add_argument("--deck", default=DEFAULT_DECK, help=f"Target deck (default: {DEFAULT_DECK}).")
    parser.add_argument(
        "--collection",
        type=type(DEFAULT_COLLECTION_PATH),
        default=DEFAULT_COLLECTION_PATH,
        help=f"Path to the .anki2 collection file (default: {DEFAULT_COLLECTION_PATH}).",
    )
    parser.add_argument("--sync-media", action="store_true", help="Also sync media files.")
    args = parser.parse_args()

    if args.extras and len(args.extras) != len(args.texts):
        parser.error("--extra must be given either zero times or once per --text")
    extras = args.extras or [""] * len(args.texts)

    cards = [ClozeCard(text=t, extra=e) for t, e in zip(args.texts, extras)]
    add_cloze_cards(
        cards,
        deck_name=args.deck,
        collection_path=args.collection,
        sync_media=args.sync_media,
    )


if __name__ == "__main__":
    main()
