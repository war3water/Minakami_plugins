<!-- Built by scripts/build-model-files.py from prompt-audit/sources/meta-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Muse Glimmer: model guidance

Applies only to Muse Glimmer. Read it with `providers/meta.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/meta/muse-glimmer.md §<section>]`.

## System prompt structure

- Be specific about the task ("You are a Python code reviewer" outperforms "You are a helpful assistant") and state output format, length and tone up front. Avoid instructions about how the model works internally.

## Tools and reasoning

- A reasoning model: its private chain of thought is built into the format, so prompts asking it to think step by step are unnecessary (D2).
