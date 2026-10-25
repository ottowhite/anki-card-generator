# Spanish vocabulary card types

What a *good card* looks like in this collection — content only. Nothing
here is about how cards get added to Anki (see `docs/IMPLEMENTATION.md`
for that) or how to invoke anything (see the `add-spanish-card` skill).

**Every card is entirely in Spanish.** No English anywhere — not a
translation, not a gloss, nothing.

## 1. Cloze (sentence) card

Note type: **Cloze**. A full Spanish sentence with the target word or
phrase hidden behind a cloze deletion.

- `Text`: the sentence, e.g.
  `Para programar bien necesitas mucha {{c1::habilidad}} y práctica constante.`
- `Back Extra`: grammar info for the hidden word/phrase — see **Content
  conventions** below, e.g.
  `sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud.`

Best for words that are easiest to learn in context: verbs, idioms, words
whose meaning depends on usage.

## 2. Picture card

Note type: **Basic**, used in a specific way — image alone on the front.

- `Front`: **only** an image of the object/action. No text, no caption,
  no translation.
- `Back`: the Spanish word/phrase plus grammar info, e.g.
  `la silla. sustantivo, femenino.`

Best for concrete, picturable nouns (objects, animals, places).

Images never appear on Cloze cards. A picture card is always this
separate front=image / back=word shape — not an image bolted onto a
sentence card (this was tried once and is wrong — see `docs/IMPLEMENTATION.md`).

## 3. Basic card

Note type: **Basic**, plain front/back. For anything that doesn't fit the
other two shapes — e.g. a prompt/question in Spanish with the answer on
the back.

## Content conventions (apply to every card type)

The back of every card states, in Spanish, whichever of these apply to
the word being taught:

- **Tipo de palabra**: sustantivo, verbo, adjetivo, adverbio, preposición,
  pronombre, conjunción, artículo, interjección, etc.
- **Género**: masculino / femenino (for nouns/adjectives).
- **Infinitivo**: if the front shows a conjugated verb form, give the
  infinitive.
- **Preposición**: if the word/verb takes a fixed preposition that isn't
  already visible in the front sentence (e.g. *pensar en*, *soñar con*).
- Anything else useful (synonyms, a brief clarification) — also in
  Spanish.

Example back: `sustantivo, femenino. Sinónimos: destreza, capacidad, aptitud.`
