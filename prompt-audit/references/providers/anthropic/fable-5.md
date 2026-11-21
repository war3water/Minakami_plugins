<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Fable 5: model guidance

Applies only to Fable 5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/fable-5.md §<section>]`.

## Subagent delegation

- Dispatches parallel subagents readily; say when delegation is appropriate and let the lead keep working while subagents run rather than blocking on each one.

## Verification

- Exception to "Instructed re-verification": for long-running tasks, fresh-context verifier subagents beat self-critique, and the page recommends a line asking the model to establish a way of checking its work and to run it at an interval, verifying with subagents against the specification. Don't flag such a line as removable in a long-run prompt.
