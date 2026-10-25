---
name: add-spanish-card
description: Generate and add a new Spanish vocabulary flashcard (cloze, picture, or basic) to the Anki collection. Use whenever asked to make/add a card for a word or set of words.
---

# Add a Spanish card

Everything needed is here. (Infra internals live in
`docs/IMPLEMENTATION.md` — only if a command actually breaks.)

**Every card is entirely in Spanish. No English anywhere — not a
translation, not a gloss, nothing.**

## 1. Pick the shape

| Word | Shape | Form |
|---|---|---|
| Verb, idiom, or clearest in context | **cloze** | Sentence with the target hidden: `...mucha {{c1::habilidad}}...` |
| Concrete, picturable noun (object/animal/place) | **picture** | Front = image *only*, no text. Back = word + grammar info. |
| Anything else | **basic** | Plain front/back, e.g. a Spanish prompt → answer |

Images never go on cloze cards. A picture card is always the separate
front=image / back=word shape, never an image bolted onto a sentence.

For a picture card, find a low-res image via web search and pass its URL.

## 2. Compose the back

State in Spanish whichever apply to the word being taught:

- **Tipo de palabra** — sustantivo, verbo, adjetivo, adverbio,
  preposición, pronombre, conjunción, artículo, interjección…
- **Género** — masculino / femenino (nouns, adjectives).
- **Infinitivo** — if the front shows a conjugated form.
- **Preposición** — if the verb takes a fixed one not already visible in
  the sentence (*pensar en*, *soñar con*).
- Anything else useful (synonyms, a brief clarification) — also Spanish.

Example: `sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud.`

## 3. Run it

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

`--deck "Nombre"` targets a deck other than the default (`Vocabulario`).
Repeat `--text`/`--extra` (cloze only) for several cards in one run.

The command syncs before and after, so the card is live on AnkiWeb when it
finishes. Report what was added (the actual Spanish text/word, not "done").
