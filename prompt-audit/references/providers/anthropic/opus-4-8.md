<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Opus 4.8: model guidance

Applies only to Opus 4.8. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/opus-4-8.md §<section>]`.

## Thinking-depth lines

- How often the model thinks can be steered by the prompt. A line such as "Thinking adds latency … When in doubt, respond directly" reduces it, and at `low` effort a targeted line ("This task involves multistep reasoning. Think carefully through the problem before responding.") raises it. Effort is still the first lever. Don't flag such lines as no-ops; suggest measuring their effect.

## Subagent delegation

- Spawns fewer subagents by default and the prompt can steer it: give explicit guidance on when subagents are desirable (for example, not for work it can finish in one response; several at once when fanning out across items).

## Search and tool use

- Favors reasoning over tool calls. A prompt that depends on a tool being used (web search, for example) should say why and when to use it.
