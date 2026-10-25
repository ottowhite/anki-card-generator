"""Add one or more cards to the collection, syncing before and after.

Mechanizes the repeatable workflow: sync (pull latest from AnkiWeb), add
the new note(s), sync again (push them back up). Not coupled to any one
note type - a `CardSpec` just names the note type and its field values, so
Cloze, Basic, picture cards, or anything else can be added the same way.

Composing the actual card content (the Spanish sentence/cloze, word type,
gender, infinitive, an image search query, etc.) is done by whoever calls
this (e.g. Claude) - this module only owns the sync/add/sync mechanics.

The back of cloze and picture cards is laid out by `format_back()` from
separate pieces (--grammar, --definition, --synonyms, --note), so every
card looks the same: big bold word, small grey grammar line, then
definition and synonyms on their own lines.

Usage:
    uv run add-card cloze \\
        --text "Para programar bien necesitas mucha {{c1::habilidad}} y practica." \\
        --grammar "sustantivo · femenino" --synonyms "destreza, capacidad"

    # Picture card: image alone on the front, word (+ info) on the back.
    # Not a Cloze card - images never go on Cloze cards.
    uv run add-card picture --image-url "https://..." --word "la silla" \\
        --grammar "sustantivo · femenino" --definition "Mueble para sentarse."

    # Repeat --front/--back (paired by position) for several cards in one run.
    uv run add-card basic --front "..." --back "..." [--image-url "https://..."] \\
        --front "..." --back "..."
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
from anki.notes import NoteId

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


def format_back(
    word: str = "",
    grammar: str = "",
    definition: str = "",
    synonyms: str = "",
    note: str = "",
) -> str:
    """The standard card-back layout; empty pieces are left out. Faded text
    uses opacity, not a fixed colour, so it reads in light and dark mode."""
    parts = []
    if word:
        parts.append(f'<div style="font-size:1.8em; font-weight:bold;">{word}</div>')
    if grammar:
        parts.append(f'<div style="font-style:italic; opacity:0.65; margin-top:4px;">{grammar}</div>')
    if definition:
        parts.append(f'<div style="margin-top:14px;">{definition}</div>')
    if synonyms:
        parts.append(f'<div style="margin-top:8px; opacity:0.8;"><b>Sinónimos:</b> {synonyms}</div>')
    if note:
        parts.append(f'<div style="margin-top:8px; opacity:0.8;">{note}</div>')
    return "".join(parts)


def cloze_card(text: str, extra: str = "") -> CardSpec:
    """A sentence with a {{c1::word}} cloze. Never carries an image - the
    picture goes on a separate picture_card() instead."""
    return CardSpec(notetype="Cloze", field_values={"Text": text, "Back Extra": extra})


def basic_card(
    front: str,
    back: str,
    image_url: str | None = None,
    image_field: str = "Front",
) -> CardSpec:
    return CardSpec(
        notetype="Basic",
        field_values={"Front": front, "Back": back},
        image_url=image_url,
        image_field=image_field,
    )


def picture_card(word: str, image_url: str, **info: str) -> CardSpec:
    """A picture-recall card: the front is *only* the image; the back is
    the Spanish word plus whatever info applies (see `format_back`) - all
    in Spanish, no English."""
    back = format_back(word, **info)
    return basic_card(front="", back=back, image_url=image_url, image_field="Front")


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


def add_card_note(col: Collection, deck_id: DeckId, card: CardSpec) -> NoteId:
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
    return note.id


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
        note_ids = []
        for card in cards:
            note_ids.append(add_card_note(col, deck_id, card))
            print(f"Added {card.notetype} card to {deck_name!r}: {card.field_values}")

        print("Syncing after changes...")
        print(f"  -> {sync_now(col, auth, sync_media=sync_media)}")
        _verify_uploaded(col, note_ids)
    finally:
        col.close()


def _verify_uploaded(col: Collection, note_ids: list[NoteId]) -> None:
    """A sync can "succeed" without uploading anything (e.g. when AnkiWeb
    wants a full sync), so check the server actually assigned a usn."""
    ids = ",".join(str(nid) for nid in note_ids)
    unsynced = col.db.list(f"select id from notes where id in ({ids}) and usn = -1")
    if unsynced:
        raise RuntimeError(f"Note(s) {unsynced} were added locally but did not reach AnkiWeb")


INFO_ARGS = {
    "grammar": "Grammar line, e.g. 'sustantivo · femenino' or 'verbo · infinitivo: tener'.",
    "definition": "Short Spanish definition.",
    "synonyms": "Comma-separated Spanish synonyms.",
    "note": "Anything else worth knowing (in Spanish).",
}


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
    for name, help_text in INFO_ARGS.items():
        cloze_parser.add_argument(
            f"--{name}",
            action="append",
            default=[],
            help=f"{help_text} Paired by position with --text; pass '' to skip one.",
        )

    picture_parser = subparsers.add_parser(
        "picture", help="Add a picture card: image alone on the front, word (+ info) on the back."
    )
    picture_parser.add_argument("--image-url", required=True, help="Image to show on the front.")
    picture_parser.add_argument("--word", required=True, help="The Spanish word/phrase for the back, e.g. 'la silla'.")
    for name, help_text in INFO_ARGS.items():
        picture_parser.add_argument(f"--{name}", default="", help=help_text)

    basic_parser = subparsers.add_parser("basic", help="Add a Basic (front/back) card.")
    basic_parser.add_argument(
        "--front", action="append", required=True, dest="fronts", help="Repeat for multiple cards."
    )
    basic_parser.add_argument(
        "--back", action="append", required=True, dest="backs", help="Paired by position with --front."
    )
    basic_parser.add_argument(
        "--image-url",
        action="append",
        default=[],
        dest="image_urls",
        help="Image URL to attach to the front. Paired by position with --front; pass '' to skip one.",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.kind == "cloze":
        n = len(args.texts)
        info = {}
        for name in INFO_ARGS:
            values = getattr(args, name)
            if values and len(values) != n:
                parser.error(f"--{name} must be given either zero times or once per --text")
            info[name] = values or [""] * n
        cards = [
            cloze_card(text, format_back(**{name: info[name][i] for name in INFO_ARGS}))
            for i, text in enumerate(args.texts)
        ]
    elif args.kind == "picture":
        info = {name: getattr(args, name) for name in INFO_ARGS}
        cards = [picture_card(args.word, args.image_url, **info)]
    elif args.kind == "basic":
        n = len(args.fronts)
        if len(args.backs) != n:
            parser.error("--back must be given once per --front")
        if args.image_urls and len(args.image_urls) != n:
            parser.error("--image-url must be given either zero times or once per --front")
        image_urls = args.image_urls or [""] * n
        cards = [
            basic_card(front, back, image_url=image_url or None)
            for front, back, image_url in zip(args.fronts, args.backs, image_urls)
        ]
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
