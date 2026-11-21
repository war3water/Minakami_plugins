# Google (Gemini): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/google/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| Gemini 3 Flash | — |

## Current date and grounding

- *Applies to:* Gemini 3 Flash. For time-sensitive queries with search, the system instruction should give the current date and year and say to use it in search queries, and state the model's knowledge cutoff. For answers that must rest only on supplied context, the vendor gives a strict grounding clause (rely only on facts in the provided context; say when the answer isn't there).
