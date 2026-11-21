<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Sonnet 5.5: model guidance

Applies only to Sonnet 5.5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/sonnet-5-5.md §<section>]`.

## Thinking-depth lines

- For a JSON answer to a task that needs a few steps of working out, "Think the problem through before you answer." at the end of the system prompt makes the model think first more often and raises accuracy. Don't flag it as reasoning boilerplate in that use.
- With thinking disabled on Opus 5, or `between_tools` thinking on Sonnet 5.5, a rule telling the model not to think or reason makes it more likely to leak internal XML tags into its visible output: remove it.

## Subagent delegation

- At `xhigh` or `max` effort, after finishing, the model can start its own review rounds, sometimes with reviewer subagents. Where that isn't wanted: "When the work the user asked for is done and its checks pass, stop and report. Don't start extra rounds of review or hardening on your own, and don't launch reviewer subagents unless the user asked for a review."

## Verification

- These models can report a code change as done without running a check that exercises it — Sonnet 5.5 at `low` effort, Haiku 5.5 at `low` and `medium`. Both pages give the same paragraph to add when that happens: run a real check (the project's tests, type-checker, build, or the changed command) before reporting done; a syntax-only check or one that failed to start doesn't count; install missing declared dependencies with the project's own package manager, unless told not to; if no real check can run, say which and why. Because the install clause yields to "unless told not to", a deliberate approval rule that covers installs or commands outside the repository still wins: when both are present, say that the approval rule takes precedence rather than treating it as a defect. When a coding-agent prompt for these models has no concrete check, this paragraph is the fix to offer; rate the finding by the usual rules (when the user's success criterion depends on a check, such as tests passing, the missing check is a D1 gap on the main path).

## Carrying work through and staying in scope

- At low effort with a long coding-agent prompt, the model can stop early and hand the task back. The pages' fix is a two-paragraph pair: keep working until everything asked for is done, stopping only when blocked on the user or before a risky step; when done and checked, stop and report without adding features, tests, docs, or refactors nobody asked for. Risky-action rules stay beside it.
- Adds tests, docs, and small supporting files at every effort level. If the user wants changes limited to what was asked, the second paragraph of the pair alone does that. On open-ended requests ("show me what you can do") it can start building when the user wanted ideas; a prompt that wants ideas or a plan first should say so and say to wait for a go-ahead.
