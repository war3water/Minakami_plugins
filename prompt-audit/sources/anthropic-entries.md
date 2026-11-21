# Anthropic (Claude): model entries (source)

The one place each model-specific entry is written. Audits never read this file. `scripts/build-model-files.py` copies every entry into the built file of each model its *Applies to* names (one file per model name, named by the rule in the script), under `references/providers/anthropic/`, and its check fails when a built file is out of date. Edit here, then rebuild; never edit a built file.

An entry starts with `- *Applies to:* <model>, <model>.` using names from the table below, and says everything it needs on its own: a built file shows it without the other models' entries. Conditions such as an effort level go in the entry text, not in the *Applies to* list.

## Models

| Model | Also covers |
|---|---|
| Opus 4.8 | — |
| Opus 5 | — |
| Opus 5.5 | — |
| Sonnet 5 | — |
| Sonnet 5.5 | — |
| Haiku 5.5 | — |
| Fable 5 | — |
| Fable 5.1 | Mythos 5.1 |
| Fable 5.2 | Mythos 5.2 |

## Thinking-depth lines

- *Applies to:* Opus 4.8, Sonnet 5. How often the model thinks can be steered by the prompt. A line such as "Thinking adds latency … When in doubt, respond directly" reduces it, and at `low` effort a targeted line ("This task involves multistep reasoning. Think carefully through the problem before responding.") raises it. Effort is still the first lever. Don't flag such lines as no-ops; suggest measuring their effect.
- *Applies to:* Opus 5.5. Lower effort first. After that, if time to first token still matters, "Answer directly without deliberating." can reduce thinking further; it can lower quality, so the prompt's owner should measure it. A rule telling the model not to think at all, carried over from a thinking-disabled setup, should be removed.
- *Applies to:* Fable 5.1, Mythos 5.1. The model usually follows "answer directly without deliberating": the line works.
- *Applies to:* Sonnet 5.5. For a JSON answer to a task that needs a few steps of working out, "Think the problem through before you answer." at the end of the system prompt makes the model think first more often and raises accuracy. Don't flag it as reasoning boilerplate in that use.
- *Applies to:* Opus 5, Sonnet 5.5. With thinking disabled on Opus 5, or `between_tools` thinking on Sonnet 5.5, a rule telling the model not to think or reason makes it more likely to leak internal XML tags into its visible output: remove it.

## Subagent delegation

- *Applies to:* Opus 4.8. Spawns fewer subagents by default and the prompt can steer it: give explicit guidance on when subagents are desirable (for example, not for work it can finish in one response; several at once when fanning out across items).
- *Applies to:* Opus 5. Delegates more readily than earlier models, which multiplies cost and time on small tasks. A prompt for a harness with subagents should say which scenarios warrant delegation, or the harness should cap spawns. Claude Code adds its own delegation instruction only with its `claude_code` system prompt preset, so a custom system prompt needs one.
- *Applies to:* Fable 5. Dispatches parallel subagents readily; say when delegation is appropriate and let the lead keep working while subagents run rather than blocking on each one.
- *Applies to:* Fable 5.2, Mythos 5.2. Leave the subagent tool's description alone unless the model starts more subagents than the task needs. If it does, look first for standing "delegate" lines in the system prompt, skills, and agent files, and make the tool description say what a subagent costs and when delegation is worth it.
- *Applies to:* Sonnet 5.5. At `xhigh` or `max` effort, after finishing, the model can start its own review rounds, sometimes with reviewer subagents. Where that isn't wanted: "When the work the user asked for is done and its checks pass, stop and report. Don't start extra rounds of review or hardening on your own, and don't launch reviewer subagents unless the user asked for a review."

## Verification

- *Applies to:* Fable 5. Exception to "Instructed re-verification": for long-running tasks, fresh-context verifier subagents beat self-critique, and the page recommends a line asking the model to establish a way of checking its work and to run it at an interval, verifying with subagents against the specification. Don't flag such a line as removable in a long-run prompt.
- *Applies to:* Sonnet 5.5, Haiku 5.5. These models can report a code change as done without running a check that exercises it — Sonnet 5.5 at `low` effort, Haiku 5.5 at `low` and `medium`. Both pages give the same paragraph to add when that happens: run a real check (the project's tests, type-checker, build, or the changed command) before reporting done; a syntax-only check or one that failed to start doesn't count; install missing declared dependencies with the project's own package manager, unless told not to; if no real check can run, say which and why. Because the install clause yields to "unless told not to", a deliberate approval rule that covers installs or commands outside the repository still wins: when both are present, say that the approval rule takes precedence rather than treating it as a defect. When a coding-agent prompt for these models has no concrete check, this paragraph is the fix to offer; rate the finding by the usual rules (when the user's success criterion depends on a check, such as tests passing, the missing check is a D1 gap on the main path).

## Carrying work through and staying in scope

- *Applies to:* Sonnet 5.5, Haiku 5.5. At low effort with a long coding-agent prompt, the model can stop early and hand the task back. The pages' fix is a two-paragraph pair: keep working until everything asked for is done, stopping only when blocked on the user or before a risky step; when done and checked, stop and report without adding features, tests, docs, or refactors nobody asked for. Risky-action rules stay beside it.
- *Applies to:* Sonnet 5.5. Adds tests, docs, and small supporting files at every effort level. If the user wants changes limited to what was asked, the second paragraph of the pair alone does that. On open-ended requests ("show me what you can do") it can start building when the user wanted ideas; a prompt that wants ideas or a plan first should say so and say to wait for a go-ahead.

## Chat prompts: earlier answers

- *Applies to:* Opus 5.5. Optional: "Once you have answered something, treat that answer as done. On later turns, focus your thinking on what the user is asking now …" at the end of a chat system prompt cuts re-examination of earlier answers and the latency it adds. Not a defect when absent.
- *Applies to:* Fable 5.2, Mythos 5.2. Chat-prompt lines telling the model to treat an earlier answer as done and focus on the new message make it far less likely to point out mistakes in its earlier answers. Flag them where the product needs the model to keep re-examining its answers; elsewhere, say to test that it still corrects itself.

## Code ownership

- *Applies to:* Fable 5.2, Mythos 5.2. The model pays close attention to who owns the code. Told the code base is its own ("You are the owner and long-term maintainer of this codebase …"), it consolidates duplicated code and makes related changes nobody asked for, at much higher output cost; told nothing, it adds to the existing structure. A scope-limiting rule ("no drive-by refactors") does not cancel the ownership sentence. Flag the pair as a D5 collision when both appear; suggest the sentence only when the user wants structural improvement.

## Writing and output

- *Applies to:* Opus 5. Documents the model writes to disk run long. A product with model-authored reports or summaries should calibrate their length to what the task needs. The model also narrates corrections to its earlier statements; a user-facing prompt can limit that to corrections that change the user's code, conclusions, or decisions.
- *Applies to:* Fable 5.1, Mythos 5.1. Under-formats rather than over-formats: anti-formatting rules written for earlier models push it further. Replace them with a rule for when lists and other formatting help.
- *Applies to:* Fable 5.1, Mythos 5.1. When summarizing documents, more likely to reproduce source passages without marking them as quotes. A summarizing prompt should include one complete example of a correct response (request, response, and why it's correct).
- *Applies to:* Fable 5.1, Mythos 5.1. Tends to rewrite whole files for small edits. If that matters, add a line saying to edit files surgically when it won't change the result.
- *Applies to:* Fable 5.2, Mythos 5.2. Follows writing style rules closely, so a hard limit ("one instruction per sentence, 20 words or fewer") makes prose choppy. Flag hard numeric style limits; prefer a description of the reader and the style.
- *Applies to:* Fable 5.2, Mythos 5.2. A token budget written into the prompt changes how much the model spends; a large one raised cost with no gain in Anthropic's tests. Suggest removing it and testing.

## Search and tool use

- *Applies to:* Opus 4.8. Favors reasoning over tool calls. A prompt that depends on a tool being used (web search, for example) should say why and when to use it.
- *Applies to:* Haiku 5.5. With a search tool, give the current date in the system prompt or the tool description. With a long system prompt or at `low` effort, add a nudge that training data ends well before that date, so changeable facts (records, office holders, prices, versions, rules, anything "latest") get searched; facts that can't change don't. Blanket "search for any present-day question" lines over-search without improving answers (the all-models tool-use entry).
- *Applies to:* Fable 5.1, Mythos 5.1. At `low` effort it searches less and answers from memory more. A prompt nudge helps: a name it doesn't confidently recognize, or one from a fast-moving field, is the thing to verify, so search it as the user wrote it.
- *Applies to:* Opus 5.5. In agents that work across several connected apps (email, documents, spreadsheets, CRM), one line telling the model to explore the relevant sources before acting, including ones the task doesn't mention, raises task success. Since it acts on what it finds, untrusted content must stay out of those sources (D8).
- *Applies to:* Haiku 5.5. With thinking off, when structured JSON output and tool calls are both needed, add: "The JSON output format applies to your final answer only. When you need a tool, call it first … and write the JSON once you have the results."

## Chatbots and safeguards

- *Applies to:* Haiku 5.5. A chatbot or support system prompt should say its rules hold for the whole conversation, including when a user argues, gives a sympathetic reason, asks for a small part, claims an approved exception, or keeps asking.
- *Applies to:* Fable 5.1, Mythos 5.1. Safeguard false positives are likelier with compile-check phrasing ("Does this program compile without errors?" — ask "Are there any bugs in this program?") and with lesser-known programming languages (give context on the language).
