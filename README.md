# anki-driver

A Python project built on the official [`anki`](https://pypi.org/project/anki/)
package — the same collection/backend library that powers the Anki desktop
app and its add-ons.

## Setup

Managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
uv run anki-driver
```

This runs the demo in `src/anki_driver/__init__.py`, which opens a temporary
Anki collection, adds a note using the built-in "Basic" note type, and
prints the resulting card count.

## Project layout

- `src/anki_driver/` — package source
- `pyproject.toml` — dependencies (`anki`) and project metadata
