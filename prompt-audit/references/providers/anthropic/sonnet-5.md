<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Sonnet 5: model guidance

Applies only to Sonnet 5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/sonnet-5.md §<section>]`.

## Thinking-depth lines

- How often the model thinks can be steered by the prompt. A line such as "Thinking adds latency … When in doubt, respond directly" reduces it, and at `low` effort a targeted line ("This task involves multistep reasoning. Think carefully through the problem before responding.") raises it. Effort is still the first lever. Don't flag such lines as no-ops; suggest measuring their effect.
