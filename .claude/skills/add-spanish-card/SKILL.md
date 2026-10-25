---
name: add-spanish-card
description: Generate and add a new Spanish vocabulary flashcard (cloze, picture, or basic) to the Anki collection. Use whenever asked to make/add a card for a word or set of words.
---

# Add a Spanish card

You do not need to know how syncing, media upload, or the Python
internals work to do this. If something breaks, that's covered in
`docs/IMPLEMENTATION.md` — not needed for the normal case below.

1. Read `docs/CARD_TYPES.md` (if you haven't already this session) for
   the three card shapes and the Spanish-only content rules (tipo de
   palabra, género, infinitivo, preposición — no English, ever).

2. Pick the right shape for the word and compose the content in Spanish:
   - A verb, idiom, or word that's clearest in context → **cloze**.
   - A concrete, picturable noun (object/animal/place) → **picture**
     (find a low-res image via web search, pass its URL).
   - Anything else → **basic**.

3. Run it:

   ```bash
   uv run add-card cloze \
     --text "Para programar bien necesitas mucha {{c1::habilidad}} y práctica constante." \
     --extra "sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud."

   uv run add-card picture \
     --image-url "https://commons.wikimedia.org/wiki/Special:FilePath/Old-chair.jpg" \
     --word "la silla" \
     --extra "sustantivo, femenino."

   uv run add-card basic --front "..." --back "..."
   ```

   Add `--deck "Nombre"` to target a deck other than the default
   (`Vocabulario`). Repeat `--text`/`--extra` (cloze only) to add several
   cards in one run.

4. The command itself syncs before and after, so the card is live on
   AnkiWeb when it finishes. Report back what was added (the Spanish
   text/word, not just "done").
