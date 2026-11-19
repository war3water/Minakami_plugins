# Google (Gemini) — model-scoped guidance

Read this file only when the user named a specific model and it appears in the Models table of `providers/google.md`. Each entry starts with *Applies to*; use an entry only when it names the target model. Where an entry here disagrees with `providers/google.md` or `general.md`, this entry wins for the models it names. Cite as `[ref: providers/google-models.md §<section> · <model>]`.

## Current date and grounding

- *Applies to:* Gemini 3 Flash. For time-sensitive queries with search, the system instruction should give the current date and year and say to use it in search queries, and state the model's knowledge cutoff. For answers that must rest only on supplied context, the vendor gives a strict grounding clause (rely only on facts in the provided context; say when the answer isn't there).
