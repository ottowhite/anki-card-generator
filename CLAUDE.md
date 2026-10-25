# anki-driver

Python project using the official `anki` PyPI package (the Anki
collection/backend library used by the desktop app and add-ons).

## Tooling

- Dependency/venv management: `uv` (not pip/poetry). Use `uv add <pkg>`,
  `uv sync`, `uv run <cmd>`.
- Python version pinned via `.python-version` (3.12).

## Structure

- `src/anki_driver/__init__.py` — package entry point. `demo()` opens/creates
  an Anki `Collection` at a given path and adds a sample note via the
  built-in "Basic" note type. `main()` runs `demo()` against a temp
  collection; wired up as the `anki-driver` console script in
  `pyproject.toml`.

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
