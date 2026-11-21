<!-- Built by scripts/build-model-files.py from prompt-audit/sources/google-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Gemini 3 Flash: model guidance

Applies only to Gemini 3 Flash. Read it with `providers/google.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/google/gemini-3-flash.md §<section>]`.

## Current date and grounding

- For time-sensitive queries with search, the system instruction should give the current date and year and say to use it in search queries, and state the model's knowledge cutoff. For answers that must rest only on supplied context, the vendor gives a strict grounding clause (rely only on facts in the provided context; say when the answer isn't there).
