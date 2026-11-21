<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Opus 5.5: model guidance

Applies only to Opus 5.5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/opus-5-5.md §<section>]`.

## Thinking-depth lines

- Lower effort first. After that, if time to first token still matters, "Answer directly without deliberating." can reduce thinking further; it can lower quality, so the prompt's owner should measure it. A rule telling the model not to think at all, carried over from a thinking-disabled setup, should be removed.

## Chat prompts: earlier answers

- Optional: "Once you have answered something, treat that answer as done. On later turns, focus your thinking on what the user is asking now …" at the end of a chat system prompt cuts re-examination of earlier answers and the latency it adds. Not a defect when absent.

## Search and tool use

- In agents that work across several connected apps (email, documents, spreadsheets, CRM), one line telling the model to explore the relevant sources before acting, including ones the task doesn't mention, raises task success. Since it acts on what it finds, untrusted content must stay out of those sources (D8).
