---
name: add-spanish-card
description: Generate and add a new Spanish vocabulary flashcard (cloze, picture, or basic) to the Anki collection. Use whenever asked to make/add a card for a word or set of words.
---

# Add a Spanish card

Everything needed is here. (Infra internals live in
`docs/IMPLEMENTATION.md` — only if a command actually breaks.)

**Every card is entirely in Spanish. No English anywhere — not a
translation, not a gloss, nothing.**

## Talk to the user in Spanish

The user is a Spanish student and this is practice. If anything needs
clarifying or agreeing before you add the card — which word, which shape,
which image, is the sentence right — **conduct that whole exchange in
Spanish**, including the final report of what you added. Stay in Spanish
even if they write to you in English; switch only if they ask you to.

Don't break their flow: no English translations or glosses alongside your
Spanish, and no commentary on their Spanish unless they ask. Keep your own
Spanish clear and natural rather than showing off — plain wording a learner
can follow, and if they seem stuck on a word, rephrase it in simpler
Spanish instead of reaching for English.

## Dialect: latinoamericano (boliviano / colombiano)

Prefer the word that is valid across Bolivian, Colombian, and general
Latin American Spanish. Only when no single word works everywhere, use
the one most common in those regions — not the peninsular form.

- `ustedes`, never `vosotros`; no `vos` conjugations.
- Latin American over Spain-specific: *carro*/*auto* (not *coche*),
  *computadora* (not *ordenador*), *celular* (not *móvil*), *jugo* (not
  *zumo*), *departamento*/*apartamento* (not *piso*), *papa* (not *patata*).
- Avoid words that are vulgar or mean something different in Bolivia or
  Colombia, even if neutral elsewhere.
- If a word is regional enough to be worth knowing, say so on the back
  (e.g. `coloquial en Colombia`).

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

Give each piece as its own option — the tool lays them out (big bold word,
small grey grammar line, definition and synonyms on their own lines).
Never cram them into one sentence. All in Spanish; omit what doesn't apply.

- `--grammar` — tipo de palabra · género, joined with ` · `. Add
  `infinitivo: …` if the front shows a conjugated form, and the fixed
  preposition if not visible in the sentence (`verbo · pensar en`).
  E.g. `sustantivo · femenino`.
- `--definition` — short, plain Spanish definition.
- `--synonyms` — comma-separated, without the label (the tool adds
  `Sinónimos:`).
- `--note` — anything else useful, e.g. `coloquial en Colombia`.

## 3. Run it

```bash
uv run add-card cloze \
  --text "Para programar bien necesitas mucha {{c1::habilidad}} y práctica constante." \
  --grammar "sustantivo · femenino" \
  --definition "Capacidad para hacer algo bien." \
  --synonyms "destreza, capacidad, aptitud"

uv run add-card picture \
  --image-url "https://commons.wikimedia.org/wiki/Special:FilePath/Old-chair.jpg" \
  --word "la silla" \
  --grammar "sustantivo · femenino" \
  --definition "Mueble con respaldo para que se siente una persona."

uv run add-card basic --front "..." --back "..."
```

`--deck "Nombre"` targets a deck other than the default (`Vocabulario`).
Repeat `--text` (cloze only) for several cards in one run; each info
option is then given once per `--text` (pass `""` to skip one) or not at all.

The command syncs before and after, so the card is live on AnkiWeb when it
finishes. Then report back **in Spanish**, quoting what you actually added
(the sentence or the word, not just "listo").
