<!-- Built by scripts/build-model-files.py from prompt-audit/sources/openai-entries.md. Do not edit by hand: edit the source and rebuild. -->

# GPT-6 Sol: model guidance

Applies only to GPT-6 Sol. Read it with `providers/openai.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/openai/gpt-6-sol.md §<section>]`.

## Writing style

- Tends toward detailed, formatted answers (lists, tables, Markdown) and recurring stock phrases. A product that needs prose, or a particular structure, must say so; a missing style spec is a D6 gap when the output is read by people.

## Subagent delegation

- May delegate less often than a multi-agent harness wants, and responds well to being told when and how much to use subagents for parallel work. A multi-agent prompt with no delegation guidance is a D1 gap for these models.
