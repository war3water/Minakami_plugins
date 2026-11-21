<!-- Built by scripts/build-model-files.py from prompt-audit/sources/anthropic-entries.md. Do not edit by hand: edit the source and rebuild. -->

# Haiku 5.5: model guidance

Applies only to Haiku 5.5. Read it with `providers/anthropic.md`; where an entry here disagrees with that file or with `general.md`, the entry here wins. Cite as `[ref: providers/anthropic/haiku-5-5.md §<section>]`.

## Verification

- These models can report a code change as done without running a check that exercises it — Sonnet 5.5 at `low` effort, Haiku 5.5 at `low` and `medium`. Both pages give the same paragraph to add when that happens: run a real check (the project's tests, type-checker, build, or the changed command) before reporting done; a syntax-only check or one that failed to start doesn't count; install missing declared dependencies with the project's own package manager, unless told not to; if no real check can run, say which and why. Because the install clause yields to "unless told not to", a deliberate approval rule that covers installs or commands outside the repository still wins: when both are present, say that the approval rule takes precedence rather than treating it as a defect. When a coding-agent prompt for these models has no concrete check, this paragraph is the fix to offer; rate the finding by the usual rules (when the user's success criterion depends on a check, such as tests passing, the missing check is a D1 gap on the main path).

## Carrying work through and staying in scope

- At low effort with a long coding-agent prompt, the model can stop early and hand the task back. The pages' fix is a two-paragraph pair: keep working until everything asked for is done, stopping only when blocked on the user or before a risky step; when done and checked, stop and report without adding features, tests, docs, or refactors nobody asked for. Risky-action rules stay beside it.

## Search and tool use

- With a search tool, give the current date in the system prompt or the tool description. With a long system prompt or at `low` effort, add a nudge that training data ends well before that date, so changeable facts (records, office holders, prices, versions, rules, anything "latest") get searched; facts that can't change don't. Blanket "search for any present-day question" lines over-search without improving answers (the all-models tool-use entry).
- With thinking off, when structured JSON output and tool calls are both needed, add: "The JSON output format applies to your final answer only. When you need a tool, call it first … and write the JSON once you have the results."

## Chatbots and safeguards

- A chatbot or support system prompt should say its rules hold for the whole conversation, including when a user argues, gives a sympathetic reason, asks for a small part, claims an approved exception, or keeps asking.
