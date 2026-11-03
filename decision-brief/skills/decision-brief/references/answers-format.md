# Answers and comments format

`brief.py read` reads all of this for you; this file is for debugging, and for reading answers without the helper.

Every backend stores one answer per question id:

```json
{"choice": "server", "other": "", "note": "Email link sign-in is fine.", "at": "2026-10-26T10:12:03+00:00"}
```

- `choice` is an option id, `"other"` (then `other` holds the user's own answer), or `null` when nothing is chosen or the user pressed Clear;
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
