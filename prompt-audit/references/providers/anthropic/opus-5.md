<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Opus 5: model guidance

Applies only to Opus 5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/opus-5.md §<section>]`.

## Thinking-depth lines

- With thinking disabled on Opus 5, or `between_tools` thinking on Sonnet 5.5, a rule telling the model not to think or reason makes it more likely to leak internal XML tags into its visible output: remove it.

## Subagent delegation

- Delegates more readily than earlier models, which multiplies cost and time on small tasks. A prompt for a harness with subagents should say which scenarios warrant delegation, or the harness should cap spawns. Claude Code adds its own delegation instruction only with its `claude_code` system prompt preset, so a custom system prompt needs one.

## Writing and output

- Documents the model writes to disk run long. A product with model-authored reports or summaries should calibrate their length to what the task needs. The model also narrates corrections to its earlier statements; a user-facing prompt can limit that to corrections that change the user's code, conclusions, or decisions.
