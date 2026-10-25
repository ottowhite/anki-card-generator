"""Fetch an image from the web and re-encode it as a small, low-resolution
JPEG suitable for attaching to a flashcard (keeps the collection's media
size - and AnkiWeb's media quota - small).

The image URL itself is expected to be found by whoever is composing the
card (e.g. Claude doing a web image search) - this module only handles
downloading and shrinking it.
"""

from __future__ import annotations

import io

import requests
from PIL import Image

MAX_DIMENSION = 400  # px, on the longest side
JPEG_QUALITY = 70
REQUEST_TIMEOUT_SECONDS = 15


def fetch_and_resize(
    url: str,
    max_dimension: int = MAX_DIMENSION,
    quality: int = JPEG_QUALITY,
) -> bytes:
    """Download an image from `url` and return it as a small JPEG's bytes."""
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "anki-driver/0.1 (personal flashcard tool)"},
    )
    response.raise_for_status()

    image = Image.open(io.BytesIO(response.content))
    image = image.convert("RGB")
    image.thumbnail((max_dimension, max_dimension))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()
