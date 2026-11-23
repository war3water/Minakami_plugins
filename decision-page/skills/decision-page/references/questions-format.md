# questions.json format

One JSON file per task drives the page. `page.py build` checks it and names every problem; `assets/example/questions.json` is a complete example to copy from.

The page sorts the cards into tabs. **Waiting for you** holds every question whose `state` is `open`, under a heading per `group`; a report's follow-up questions without a `group` get "From: `<report title>`". **Work status** holds the progress reports that are not `archived`. **Decided** holds the questions whose `state` is `answered` and the archived reports, under a heading per `round`, then the earlier rounds from `archive/`. **Glossary** holds the terms. A tab with nothing in it is left out, except Waiting for you.

`page.py mark` with a new `--round` moves older rounds out of this file into `archive/` next to it: `index.json` lists each round's decisions in one line each, and `<round>.json` keeps its full cards and reports. `page.py` writes those files, and `page.py history` prints them. `mark` also records the time in `marked_at`.

## Top level

| Field | Required | What it holds |
|---|---|---|
| `title` | yes | The page's name and heading: specific to the project and topic, such as "Pantry storage decisions", so it stands out in a browser tab or a list of pages |
| `project` | no | The project's name, shown above the title |
| `intro` | no | Replaces the default opening paragraph (markup allowed) |
| `lang` | no | The page's language code, such as `en` or `zh-CN` (default `en`). A code starting with `zh` also switches the page's own labels to Chinese |
| `ui` | no | Replacement interface text, by key (see "Interface text") |
| `style` | no | The page's look: `notebook` (the default: IBM Plex type on a grey-green paper), `ledger` (paper and navy, serif headings; sans-serif on Chinese, Japanese and Korean pages), `rose` (warm pink accent) or `slate` (cool grey and teal). Each has a light and a dark version |
| `density` | no | How cards open: `detailed` (the default: the card reads straight through, each effect on its own line) or `compact` (the question, its background and its options on one screen, each option on one line; the table, pictures, example and "More" open on a click). The reader can switch, and the page remembers the pick in that browser |
| `glossary` | no | Terms, in reading order |
| `questions` | yes, unless `progress` holds them | The open question cards |
| `progress` | no | Reports on decisions already made, each with optional follow-up questions |
| `questions_title`, `progress_title` | no | Replace the names of the Waiting for you and Work status tabs |

## Glossary entry

| Field | Required | What it holds |
|---|---|---|
| `term` | yes | The short name as readers meet it, such as `DEC-1 ... DEC-16` or `T6, T651` |
| `meaning` | yes | Its plain meaning (markup allowed) |
| `sources` | no | Where it comes from: a list of `{"label": ..., "url": "https://..."}` (each link checked before publishing), or `{"path": "docs/spec.md"}` for a file in the project; add `"note"` for text after it. Without `sources`, the page shows the project file the term first appears in, found when the page is built |
| `aka` | no | Other spellings the page uses, so the abbreviation check counts them as explained |

Each entry gets an anchor `g-` plus the term in lowercase with dashes, so a card can link to it: `[localStorage](#g-localstorage)`, `[WCAG 2.2 AA](#g-wcag-2-2-aa)`. The build warns when such a link points nowhere. A term written as `NFR-nnn` covers `NFR-001`, `NFR-002` and so on.

On the cards, the first use of each term (and of each `aka`) is underlined: pointing at it, or focusing it with the keyboard, shows its meaning in place, with a link to the Glossary tab.

## Question card

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | Lowercase letters, digits and dashes; unique across the page. Answers are stored by this id |
| `title` | yes | The question, in plain words |
| `ref` | no | The project's own number for the question, such as a ticket or decision id, shown after the title so the user can match the card to its source (explain the numbering in the glossary) |
| `group` | no | The heading the card sits under on Waiting for you, such as "New questions from the sync work" |
| `plain` | yes | The background in plain words, in as few sentences as tell it: what is true today, why, and why it needs a choice (markup) |
| `more` | no | What would push the card past one screen, folded under "More": the example's working, more cases, how an option is built, history. Nothing that could change the choice (markup) |
| `table` | no | `{"head": [...], "rows": [[...], ...]}`; cells take inline markup, and a column of numbers lines up on the right. A row that belongs to one option is `{"cells": [...], "option": "<option id>"}`: it stands out when that option is chosen |
| `figures` | no | Pictures shown after the background: images, drawings or live demos (see "Figures") |
| `example` | no | For a card whose background and options do not already make the choice plain: `{"text": ..., "source": ..., "label": ..., "table": ..., "figures": [...]}`. `source` says where the example comes from, in the page's language: a file and line, a ticket, a log, or that it was made up to illustrate; the build warns when an open question's example has none. `label` replaces the heading "Example" |
| `options` | yes | At least one; see below. The page adds Other, Clear, Add a note and Comment |
| `state` | no | `open` (default) or `answered`, which moves the card to Decided; `page.py mark` sets it |
| `round` | no | The heading the card sits under on Decided, such as "Round 1, decided 20 October"; `page.py mark --round` sets it |
| `outcome` | no | "What I did" after the answer, shown on answered cards (markup) |
| `read` | no | Written by `page.py mark`: the answer as you read it. The card shows it when no newer answer is stored, and says when the user changed it |

An option is `{"id": "...", "label": "...", "effect": "...", "recommended": true}`:

- `id`: lowercase letters, digits and dashes, unique within the card; `other` is reserved;
- `label`: the answer in a few words (inline markup);
- `effect`: one line on what choosing it changes from today for the people it touches: its gain and its catch, with direction and rough size; not how it is built (inline markup);
- `recommended`: `true` tags the option "Recommended"; a string also shows that string under it, such as why, or when another option fits better. At most one option per card;
- `figure` (optional): one picture of what this option looks like (see "Figures"). When options have pictures, the card shows a switch to compare them, opening on the recommended one, and choosing an option shows its picture. When every option's picture is a live demo, the card shows none of them: a button and a Try it link on each option open a floating window with one demo at a time, a switch over the options and Choose this, which answers the card.

## Progress report

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | Lowercase letters, digits and dashes; the card's anchor is `p-` plus the id |
| `title` | yes | What was built, such as "Family tree: your three answers, built" |
| `status` | no | The status label (default "built, please check") |
| `done` | no | `false` while the work is still in progress (a half-filled marker instead of a tick) |
| `text` | no | What changed, in two or three sentences (markup) |
| `more` | no | How it was checked and other detail, folded under "More" (markup) |
| `table`, `figures` | no | As on a question card; use before and after pairs |
| `action` | no | One thing the user has to do, shown highlighted after "One action for you:"; the Work status tab counts these |
| `archived` | no | `true` moves the report to Decided; `page.py mark --reports` sets it |
| `round` | no | The heading it sits under on Decided |
| `questions` | no | Follow-up question cards; they go on Waiting for you (or Decided, once answered) |

## Figures

A figure is `{"src": "shots/before.png", "alt": "...", "label": "Before", "caption": "..."}`.

- `src` is a path relative to questions.json, inside its folder: an image (png, jpg, gif, webp or avif), a drawing (`.svg`) or a live demo (`.html`). Web addresses are refused, because the local page loads nothing from outside.
- A drawing is placed into the page itself: it takes the page's colours in light and dark, and its parts marked `data-option="<option id>"` stand out when that option is chosen. A live demo runs in a sealed frame, with no network and no access to the page; the frame grows to fit it. `references/pictures.md` says how to make both, and `build` refuses a drawing that holds code or loads outside files.
- `alt` is required: what the picture shows, for a reader who cannot see it.
- `caption` is the point the picture makes, in one line; `build` warns when a drawing or demo has none.
- `height` (a demo only): its height in pixels until it loads (default 420).
- Two or more figures sit side by side on a wide screen and stack on a phone. Each has its own Comment button where comments work.
- Every image and drawing opens full size on a click (or Enter): the wheel or a pinch zooms, dragging pans, Esc closes. A demo in `figures` has Open large.

## Markup

Text fields take a small, safe subset; HTML is shown as text:

- a blank line starts a new paragraph; a single line break stays a line break;
- lines that all start with `- ` form a list, lines that start with `1. ` a numbered list;
- lines between two ```` ``` ```` lines form a text sketch, shown exactly as typed in a fixed-width font (a calculation, a small layout drawn in characters);
- `**bold**`, and `` `code` `` for names, paths and values;
- `[text](https://...)` opens in a new tab; `[text](#g-term)`, `[text](#q-id)` and `[text](#p-id)` jump within the page.

## Interface text

The page's labels come in English, and in Simplified Chinese when `lang` starts with `zh`. Every label has a key, and `ui` replaces any of them, for example to write the page in another language:

```json
"ui": {
  "plain": "Kurz erklärt",
  "recommended": "Empfohlen",
  "other": "Andere Antwort",
  "clear": "Löschen",
  "chip_need": "Offen"
}
```

The keys and their English text are at the top of the script in `assets/page.html` (the object `EN`). Keep the placeholders in braces, such as `{n}`, `{total}`, `{time}`, `{why}` and `{name}`.

## Answers and comments

`page.py read` reads every answer and comment thread for you. Their stored format is in `references/answers-format.md`, for debugging.
