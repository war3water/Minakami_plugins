# questions.json format

One JSON file per task drives the page. `brief.py build` checks it and names every problem; `assets/example/questions.json` is a complete example to copy from.

## Top level

| Field | Required | What it holds |
|---|---|---|
| `title` | yes | The page's name and heading: specific to the project and topic, such as "Pantry storage decisions", so it stands out in a browser tab or a list of pages |
| `project` | no | The project's name, shown above the title |
| `intro` | no | Replaces the default opening paragraph (markup allowed) |
| `lang` | no | The page's language code, such as `en` or `zh-CN` (default `en`). A code starting with `zh` also switches the page's own labels to Chinese |
| `ui` | no | Replacement interface text, by key (see "Interface text") |
| `glossary` | no | Terms, in reading order |
| `questions` | yes, unless `progress` holds them | The open question cards |
| `progress` | no | Reports on decisions already made, each with optional follow-up questions |
| `questions_title`, `progress_title` | no | Replace the two section headings |

## Glossary entry

| Field | Required | What it holds |
|---|---|---|
| `term` | yes | The short name as readers meet it, such as `OD-1 ... OD-16` or `T6, T651` |
| `meaning` | yes | Its plain meaning (markup allowed) |
| `sources` | no | Where it comes from: a list of `{"label": ..., "url": "https://..."}`, each one checked before publishing; add `"note"` for text after the link |
| `aka` | no | Other spellings the page uses, so the abbreviation check counts them as explained |

Each entry gets an anchor `g-` plus the term in lowercase with dashes, so a card can link to it: `[localStorage](#g-localstorage)`, `[WCAG 2.2 AA](#g-wcag-2-2-aa)`. The build warns when such a link points nowhere. A term written as `NFR-nnn` covers `NFR-001`, `NFR-002` and so on.

## Question card

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | Lowercase letters, digits and dashes; unique across the page. Answers are stored by this id |
| `title` | yes | The question, in plain words |
| `ref` | no | A short tag shown after the title, such as a ticket number (explain it in the glossary) |
| `plain` | yes | The "in plain words" background (markup) |
| `table` | no | `{"head": [...], "rows": [[...], ...]}`; cells take inline markup |
| `figures` | no | Images shown after the background (see "Figures") |
| `example` | no | Text, or `{"label": "WHEN IT HAPPENS", "text": ..., "table": ..., "figures": [...]}` |
| `options` | yes | At least one; see below. The page adds Other, Clear choice, the note and Comment on this |
| `state` | no | `open` (default) or `answered`; `brief.py mark` sets it |
| `outcome` | no | "What I did" after the answer, shown on answered cards (markup) |
| `read` | no | Written by `brief.py mark`: the answer as you read it, so later changes show |

An option is `{"id": "...", "label": "...", "effect": "...", "recommended": true}`:

- `id`: lowercase letters, digits and dashes, unique within the card; `other` is reserved;
- `label`: the answer in a few words (inline markup);
- `effect`: what choosing it changes (inline markup);
- `recommended`: `true` shows "I recommend this."; a string shows that string instead. At most one option per card.

## Progress report

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | Lowercase letters, digits and dashes; the card's anchor is `p-` plus the id |
| `title` | yes | What was built, such as "Family tree: your three answers, built" |
| `status` | no | The chip text (default "built, please check") |
| `done` | no | `false` while the work is still in progress (amber instead of green) |
| `text` | no | What changed and how it was checked (markup) |
| `table`, `figures` | no | As on a question card; use before and after pairs |
| `action` | no | One thing the user has to do, shown highlighted after "One action for you:" |
| `questions` | no | Follow-up question cards, shown right after the report |

## Figures

A figure is `{"src": "shots/before.png", "alt": "...", "label": "Before", "caption": "..."}`.

- `src` is a path relative to questions.json, inside its folder: png, jpg, gif, webp, svg or avif. Web addresses are refused, because the local page loads nothing from outside.
- `alt` is required: what the image shows, for a reader who cannot see it.
- Two or more figures sit side by side on a wide screen and stack on a phone.

## Markup

Text fields take a small, safe subset; HTML is shown as text:

- a blank line starts a new paragraph; a single line break stays a line break;
- lines that all start with `- ` form a list, lines that start with `1. ` a numbered list;
- `**bold**`, and `` `code` `` for names, paths and values;
- `[text](https://...)` opens in a new tab; `[text](#g-term)`, `[text](#q-id)` and `[text](#p-id)` jump within the page.

## Interface text

The page's labels come in English, and in Simplified Chinese when `lang` starts with `zh`. Every label has a key, and `ui` replaces any of them, for example to write the page in another language:

```json
"ui": {
  "plain": "Kurz erklärt",
  "recommended": "Das empfehle ich.",
  "other": "Andere Antwort",
  "clear": "Auswahl löschen",
  "chip_need": "wartet auf Sie"
}
```

The keys and their English text are at the top of the script in `assets/page.html` (the object `EN`). Keep the placeholders in braces, such as `{n}`, `{total}`, `{time}`, `{why}` and `{name}`.

## Answers and comments

Every backend stores one answer per question id:

```json
{"choice": "server", "other": "", "note": "Email link sign-in is fine.", "at": "2026-10-26T10:12:03+00:00"}
```

- `choice` is an option id, `"other"` (then `other` holds the user's own answer), or `null` when nothing is chosen or the user pressed Clear choice;
- `note` is the free note; the Artifact backend adds `by`, the user's id.

The local server writes `answers.json`; the static page's download has the same shape:

```json
{
  "app": "decision-brief",
  "format": 2,
  "rev": 14,
  "title": "Decisions waiting for you",
  "answers": {"storage": {"choice": "server", "other": "", "note": "", "at": "..."}},
  "comments": [
    {"id": "c1", "target": "q-storage", "quote": "clearing the browser's data deletes every list", "by": "user", "text": "Does this happen on phones too?", "at": "..."},
    {"id": "c2", "target": "q-storage", "parent": "c1", "by": "agent", "name": "Claude", "text": "Yes: ...", "at": "..."}
  ],
  "done": {"at": "...", "note": ""}
}
```

- `rev` goes up with every change; open pages wait on it, so updates show within a second.
- A comment without `parent` starts a thread; a reply names the thread's first comment. `by` is `user` or `agent`; `name` is the agent's name on the page. `quote` is the text the user selected, if any. A comment the user sent with Ask now has `ask`: `pending`, then `answered` or `failed`.
- `target` is where the thread sits: `q-` plus a question id, `p-` plus a report id, `g-` plus a glossary anchor, or `page`.
- `done` is set when the user presses I'm done.

An Artifact keeps answers in its `answers` collection and comments in the platform's own threads. `brief.py read --answers` takes what an agent saved from it: the folder ArtifactData `list` writes with `out_dir` (one `<question id>.json` per answer), or the listing's text in a file (one `{"id": ..., "data": {...}}` object per line).
