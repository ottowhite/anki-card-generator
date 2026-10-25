"""Add one or more cards to the collection, syncing before and after.

Mechanizes the repeatable workflow: sync (pull latest from AnkiWeb), add
the new note(s), sync again (push them back up). Not coupled to any one
note type - a `CardSpec` just names the note type and its field values, so
Cloze, Basic, or anything else can be added the same way. Optionally
attaches a web image (fetched and shrunk to a low-res JPEG) to a chosen
field.

Composing the actual card content (the Spanish sentence/cloze, word type,
gender, infinitive, an image search query, etc.) is done by whoever calls
this (e.g. Claude) - this module only owns the sync/add/sync mechanics.

Usage:
    uv run add-card cloze \\
        --text "Para programar bien necesitas mucha {{c1::habilidad}} y practica." \\
        --extra "sustantivo, femenino. Sinonimos: destreza, capacidad."

    uv run add-card basic --front "..." --back "..." --image-url "https://..."
"""

from __future__ import annotations

import argparse
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from anki.collection import Collection
from anki.decks import DeckId

from anki_driver.images import fetch_and_resize
from anki_driver.sync import (
    DEFAULT_COLLECTION_PATH,
    get_credentials,
    login,
    open_default_collection,
    sync_now,
)

DEFAULT_DECK = "Vocabulario"


@dataclass
class CardSpec:
    """A note to add: which note type, its field values, and an optional
    image to attach to one of those fields."""

    notetype: str
    field_values: dict[str, str] = field(default_factory=dict)
    image_url: str | None = None
    image_field: str = ""  # required if image_url is set

    def __post_init__(self) -> None:
        if self.image_url and not self.image_field:
            raise ValueError("image_field is required when image_url is set")

    def resolve_fields(self, col: Collection) -> dict[str, str]:
        """Field values with the image (if any) downloaded, shrunk, added to
        the collection's media, and embedded as an <img> tag."""
        fields = dict(self.field_values)
        if self.image_url:
            filename = _attach_image(col, self.image_url)
            img_tag = f'<img src="{filename}">'
            existing = fields.get(self.image_field, "")
            fields[self.image_field] = f"{existing} {img_tag}".strip()
        return fields


def cloze_card(
    text: str,
    extra: str = "",
    image_url: str | None = None,
    image_field: str = "Back Extra",
) -> CardSpec:
    return CardSpec(
        notetype="Cloze",
        field_values={"Text": text, "Back Extra": extra},
        image_url=image_url,
        image_field=image_field,
    )


def basic_card(
    front: str,
    back: str,
    image_url: str | None = None,
    image_field: str = "Back",
) -> CardSpec:
    return CardSpec(
        notetype="Basic",
        field_values={"Front": front, "Back": back},
        image_url=image_url,
        image_field=image_field,
    )


def _slug_from_url(url: str) -> str:
    """A readable base filename derived from the URL, e.g. 'old-chair' from
    .../Special:FilePath/Old-chair.jpg - falls back to 'image' if nothing
    usable is found."""
    last_segment = urlsplit(url).path.rsplit("/", 1)[-1]
    stem = Path(last_segment).stem or "image"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return slug or "image"


def _attach_image(col: Collection, url: str) -> str:
    """Download+shrink the image at `url` and add it to the collection's
    media folder, returning the (deduplicated) stored filename."""
    data = fetch_and_resize(url)
    slug = _slug_from_url(url)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / f"{slug}.jpg"
        tmp_path.write_bytes(data)
        return col.media.add_file(str(tmp_path))


def add_card_note(col: Collection, deck_id: DeckId, card: CardSpec) -> None:
    notetype = col.models.by_name(card.notetype)
    if notetype is None:
        raise RuntimeError(f"Note type {card.notetype!r} not found in collection")

    note = col.new_note(notetype)
    field_names = set(note.keys())
    resolved = card.resolve_fields(col)
    unknown = set(resolved) - field_names
    if unknown:
        raise ValueError(
            f"Note type {card.notetype!r} has no field(s) {sorted(unknown)}; "
            f"it has {sorted(field_names)}"
        )
    for name, value in resolved.items():
        note[name] = value
    col.add_note(note, deck_id)


def add_cards(
    cards: list[CardSpec],
    deck_name: str = DEFAULT_DECK,
    collection_path: Path = DEFAULT_COLLECTION_PATH,
    sync_media: bool = True,
) -> None:
    """Sync, add the given cards to `deck_name`, then sync again."""
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
            add_card_note(col, deck_id, card)
            print(f"Added {card.notetype} card to {deck_name!r}: {card.field_values}")

        print("Syncing after changes...")
        print(f"  -> {sync_now(col, auth, sync_media=sync_media)}")
    finally:
        col.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="add-card",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--deck", default=DEFAULT_DECK, help=f"Target deck (default: {DEFAULT_DECK}).")
    parser.add_argument(
        "--collection",
        type=Path,
        default=DEFAULT_COLLECTION_PATH,
        help=f"Path to the .anki2 collection file (default: {DEFAULT_COLLECTION_PATH}).",
    )
    parser.add_argument("--no-media", action="store_true", help="Skip media sync.")

    subparsers = parser.add_subparsers(dest="kind", required=True)

    cloze_parser = subparsers.add_parser("cloze", help="Add Cloze card(s).")
    cloze_parser.add_argument(
        "--text",
        action="append",
        required=True,
        dest="texts",
        help="A cloze sentence, e.g. 'Hoy tengo {{c1::prisa}}.' Repeat for multiple cards.",
    )
    cloze_parser.add_argument(
        "--extra",
        action="append",
        default=[],
        dest="extras",
        help="'Back Extra' content, paired by position with --text.",
    )
    cloze_parser.add_argument("--image-url", help="Image URL to attach (only valid with a single --text).")

    basic_parser = subparsers.add_parser("basic", help="Add a Basic (front/back) card.")
    basic_parser.add_argument("--front", required=True)
    basic_parser.add_argument("--back", required=True)
    basic_parser.add_argument("--image-url", help="Image URL to attach to the back.")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.kind == "cloze":
        if args.extras and len(args.extras) != len(args.texts):
            parser.error("--extra must be given either zero times or once per --text")
        extras = args.extras or [""] * len(args.texts)
        if args.image_url and len(args.texts) != 1:
            parser.error("--image-url can only be used with a single --text")
        cards = [
            cloze_card(text, extra, image_url=args.image_url if i == 0 else None)
            for i, (text, extra) in enumerate(zip(args.texts, extras))
        ]
    elif args.kind == "basic":
        cards = [basic_card(args.front, args.back, image_url=args.image_url)]
    else:  # pragma: no cover - argparse enforces valid choices
        raise AssertionError(f"Unhandled kind: {args.kind!r}")

    add_cards(
        cards,
        deck_name=args.deck,
        collection_path=args.collection,
        sync_media=not args.no_media,
    )


if __name__ == "__main__":
    main()
