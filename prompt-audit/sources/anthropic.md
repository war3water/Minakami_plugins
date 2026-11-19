# Anthropic — source detail

Read by `check-sources` when it compares Anthropic's pages. Each page section states what is distilled now, at which scope, and what is excluded; it is rewritten, never appended to, when the page changes (see "Keeping the registry bounded" in `SOURCES.md`). "All models" means `references/providers/anthropic.md`; "scoped" means an entry in `references/providers/anthropic-models.md`, named by its section.

## Known matches at last discovery (2026-11-17)

All under `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/`: `overview`, `claude-prompting-best-practices`, `prompting-claude-fable-5`, `prompting-claude-fable-5-1`, `prompting-claude-fable-5-2`, `prompting-claude-haiku-5-5`, `prompting-claude-opus-4-8`, `prompting-claude-opus-5`, `prompting-claude-opus-5-5`, `prompting-claude-sonnet-5`, `prompting-claude-sonnet-5-5`. The hub table on the best-practices page lists the same nine model guides.

## Seen, not registered

- `overview` — the hub page for prompt engineering; no guidance of its own.

## Claude prompting best practices

The provider-wide page: its claims apply to all models.

- **Distilled (all models):** structure and tags; rule priority for collisions; motivation improves adherence; describe tools rather than scripting call order; model self-knowledge (state model identity and ids when the task depends on them); blanket defaults replaced by targeted conditions; overeagerness and scope; autonomy boundaries (confirm destructive, irreversible, or visible actions); long-horizon state tracking; investigate-before-answering and general-solution rules are real levers, not no-ops; reasoning boilerplate is a no-op; asking for reasoning in `<thinking>` or similar tags can trigger the reasoning-extraction refusal (the reasoning-echo entry covers tag scaffolds); multishot examples presented as problem, method, and expected answer (consistent with the references, no entry needed). A prompt rule guides but does not enforce, so money-moving or irreversible tools need a person approving each call or a tool that queues the action for release, and a rule that narrows an earlier permission says it overrides it (§Agentic prompts, "Text guides; tools enforce"). "Say a check was done only if a tool result showed it" corroborates evidence-backed status in `agentic.md`.
- **Excluded:** effort and thinking parameters, thinking-on-by-default API notes, prefill migration, LaTeX and document creation, vision and computer-use specifics, the Sonnet 5.5 migration subsection, and the verbatim text of the medication-dosing and payments blocks.
- **Outline (H2 › H3):**
  - Model-specific guidance
  - General principles › Be clear and direct; Add context to improve performance; Use examples effectively; Structure prompts with XML tags; Give Claude a role; Long context prompting; Model self-knowledge
  - Output and formatting › Communication style and verbosity; Control the format of responses; LaTeX output; Document creation; Migrating away from prefilled responses
  - Tool use › Tool usage; Optimize parallel tool calling
  - Thinking and reasoning › Overthinking and excessive thoroughness; Leverage thinking and interleaved thinking capabilities
  - Agentic systems › Long-horizon reasoning and state tracking; Balancing autonomy and safety; Payments, account numbers, and financial records; Research and information gathering; Subagent orchestration; Chain complex prompts; Reduce file creation in agentic coding; Overeagerness; Avoid focusing on passing tests and hardcoding; Minimizing hallucinations in agentic coding
  - Capability-specific tips › Improved vision capabilities; Frontend design; Medication dosing
  - Migration considerations › Migrating to Claude Sonnet 5.5
  - Next steps

## Prompting Claude Opus 5

- **Distilled (all models):** generic instructed re-verification is a no-op (with Sonnet 5 and Sonnet 5.5, which report self-started verification); scope-expansion bounds; explicit length contract; narration cadence via positive examples; conservatism wording in review prompts lowers recall; full task specification up front; its "Reasoning in the response" section corroborates the reasoning-echo entry and its outlet.
- **Distilled (scoped, Opus 5):** §Subagent delegation (say when to delegate, or cap it; a custom system prompt needs its own delegation line); §Writing and output (written-deliverable length, correction narration); §Thinking-depth lines (with thinking disabled, a no-think rule increases internal-tag leakage).
- **Excluded:** the combined thinking-disabled instruction (tool calls as text, internal tags), the Claude Code and Agent SDK spawn caps (harness settings), effort recommendations.
- **Outline (H2):** Capability improvements; Response length and verbosity; User-facing progress updates; Written deliverable length; Task scope and over-verification; Controlling subagent spawning; Self-correction; Running with thinking disabled; Reasoning in the response

## Prompting Claude Fable 5.1

Also covers Mythos 5.1.

- **Distilled (all models):** forced narration scaffolding ("hold all findings for the final response") replaced by a described cadence; finish-the-whole-task and autonomous-run instructions as completion criteria; writing density over compression; keep changes and tests to what the task asks for; say what a compaction summary must preserve; the reasoning-extraction note with its outlet (corroboration).
- **Distilled (scoped, Fable 5.1 and Mythos 5.1):** §Writing and output (anti-formatting rules; one complete example for quoting retrieved sources; the targeted-edit line); §Search and tool use (name-verification nudge at low effort); §Chatbots and safeguards (compile-check phrasing, context for lesser-known languages). Its think-less entry comes from the Fable 5.2 page.
- **Excluded:** effort levels, append-only history, thinking-block and prefix-binding rules (API), the tool-call batching nudge (harness message), base64 in tool output (harness), long-output token notes, the asynchronous subagent harness, vision tools, cache pricing.
- **Outline (H2):** Consider all effort levels; Ask for user-facing progress updates; Batch independent tool calls in agent loops; Keep the conversation history append-only; Writing density; Formatting in chat; Quoting retrieved sources; Finish the whole task; Tell the model what to preserve in compaction summaries; Keep changes and tests to what the task asks for; Search triggering at low effort; Reduce safeguard false positives; Prefer targeted edits over whole-file rewrites; Leave room for long outputs at xhigh and max effort; Let the lead agent keep working while subagents run; Give vision work tools to crop and zoom

## Prompting Claude Fable 5

- **Distilled (all models):** give the reason, not only the request; ground progress claims in tool results; state the boundaries; a brief instruction beats enumerating behaviors (older skills are too prescriptive); a notes or memory file as a place for state; reasoning-echo instructions trigger the reasoning-extraction refusal, and a short explanation is the outlet. Its final-summary readability (complete sentences, no working shorthand) is, with Fable 5.2 and Using GPT-6.2, the basis of `agentic.md` "A final report for a cold reader".
- **Distilled (scoped, Fable 5):** §Subagent delegation (say when; keep working while subagents run); §Verification (fresh-context verifier subagents in long runs, the exception to instructed re-verification).
- **Excluded:** effort, longer turns, the early-stopping reminder (corroborates `agentic.md` persistence), the context-budget reassurance (a harness countdown), the send-to-user tool, the memory bootstrapping prompt, fallback retry rules for `reasoning_extraction`.
- **Outline (H2):** Capability improvements; Longer turns by default; Consider all effort levels; Strong instruction following; Ground progress claims during long runs; State the boundaries; Parallel subagents; Construct a memory system; Rare cases of early stopping; Rare cases of context-budget concern; Give the reason, not only the request; Readability when communicating with the user; Create a send-to-user tool; Recommended scaffolding changes

## Prompting Claude Sonnet 5

- **Distilled (all models):** literal instruction following (state an instruction's scope); positive examples over negative instructions for verbosity; forced interim status scaffolding removed; review harnesses ask for coverage, not filtering; task specification up front in interactive coding; generic design prohibitions swap one default for another.
- **Distilled (scoped, Sonnet 5):** §Thinking-depth lines (thinking frequency is steerable; a respond-directly line reduces it, a targeted multistep line at low effort raises it).
- **Excluded:** effort calibration, tokenizer and token-limit notes, sampling parameters, the tool-use nudge with thinking off, the design example prompts, computer use.
- **Outline (H2):** Response length and verbosity; Calibrating effort and thinking depth; Tool use triggering; User-facing progress updates; More literal instruction following; Tone and writing style; Design and frontend defaults; Interactive coding products; Code review harnesses; Computer use

## Prompting Claude Opus 4.8

- **Distilled (all models):** corroborates the Sonnet 5 page section for section (literal following, verbosity via positive examples, review-harness coverage, task specification up front, generic design prohibitions).
- **Distilled (scoped, Opus 4.8):** §Subagent delegation (spawns fewer; say when subagents are desirable); §Thinking-depth lines (same as Sonnet 5); §Search and tool use (favors reasoning over tool calls; say why and when to use a tool).
- **Excluded:** effort, thinking-off default, tone specifics, the house design style, computer-use and browser tool versions.
- **Outline (H2):** Response length and verbosity; Calibrating effort and thinking depth; Tool use triggering; User-facing progress updates; More literal instruction following; Tone and writing style; Controlling subagent spawning; Design and frontend defaults; Interactive coding products; Code review harnesses; Computer use

## Prompting Claude Opus 5.5

- **Distilled (all models):** unattended runs need a completion checklist and evidence-based end-of-turn handling; reasoning-depth lines in chat prompts are removable (with Fable 5.2, Sonnet 5.5, and Haiku 5.5, the no-op entry in `general.md`); the reasoning-echo refusal; generic prohibitions swap one default for another, so name the pattern; random-id tags for pasted text corroborate the delimiter rule in `general.md`; asking for an opening line and a recap corroborates narration cadence.
- **Distilled (scoped, Opus 5.5):** §Thinking-depth lines ("answer directly without deliberating" after lowering effort, measured; remove a carried-over no-think rule); §Chat prompts: earlier answers (the optional treat-as-done lines); §Search and tool use (the multiapp exploration line).
- **Excluded:** medium effort default, thinking always on, time-budget signals (harness), progress-update display settings and the harness reminder, safeguard categories, visual-input tools, the frontend snippet.
- **Outline (H2):** Capabilities relevant to prompting; Calibrate effort; Prompts written for thinking disabled; Unattended agentic runs; Safeguard refusals; User-facing progress updates; Explore context in multiapp workflows; Time signals for multiagent harnesses; Thinking instructions in chat system prompts; Mark pasted text in user messages; Tools for complex visual inputs; Frontend design defaults

## Prompting Claude Fable 5.2

Also covers Mythos 5.2.

- **Distilled (all models):** approval rules apply as written, so name the actions they cover; a rule containing "never" is read as absolute, so write the exception into the rule as an ask-first rule; a general "act more freely" is too vague, so list the routine steps the agent may take; narrow the stop conditions in validation steps; delete cautions that outlived their reason (all in `agentic.md`, "Approval and absolute rules, as written"). Persistence text separates ordinary obstacles from deliberate blockers and keeps the risky-action confirmation. Final-report readability (`agentic.md`, with Fable 5 and Using GPT-6.2); the reasoning-echo refusal (corroboration); asking for an opening line, updates, and a recap corroborates narration cadence.
- **Distilled (scoped, Fable 5.2 and Mythos 5.2):** §Thinking-depth lines (think-less lines are no-ops here, and Fable 5.1 followed them); §Subagent delegation (leave the tool description alone unless it over-delegates; check standing delegate lines); §Chat prompts: earlier answers (treat-as-done lines suppress self-correction); §Code ownership; §Writing and output (hard numeric style limits; a token budget written into the prompt).
- **Excluded:** test numbers, effort calibration, the harness reminder and display settings for progress updates, preserved thinking and harness edits to earlier turns, the API task-budget feature.
- **Outline (H2 › H3):** Calibrate effort; Finish the whole task › Approvals; Say who owns the code; Keep users informed during long turns › Modify your harness; Signal intent; Update system prompt instructions; Set expectations for subagents; Keep caution from piling up; Review prompts and harnesses designed for earlier models; Make reports easy to follow; Safeguard refusals; Where to start

## Prompting Claude Sonnet 5.5

- **Distilled (all models):** blanket tool-discouraging wording suppresses needed checks; the reasoning-echo outlet; removing "hold all findings for the final response" (corroborates forced narration); self-started review rounds (corroborates instructed re-verification).
- **Distilled (scoped, Sonnet 5.5):** §Verification (the concrete check paragraph at low effort, with Haiku 5.5); §Carrying work through and staying in scope (the keep-working pair, with Haiku 5.5; unrequested additions; ideas first on open requests); §Subagent delegation (reviewer subagents at xhigh and max); §Thinking-depth lines (think-less lines unreliable; "Think the problem through before you answer." for JSON reasoning tasks; no-think rules leak tags under `between_tools`).
- **Excluded:** last-JSON-value parsing (harness), `between_tools` settings, mid-turn user-message placement (API), tolerant tool-call handling (harness), effort.
- **Outline (H2):** Calibrate effort; Steer initiative and scope; Running without up-front thinking; Reasoning tasks with JSON output; User-facing progress updates; Tool use in chat and knowledge work; Mid-turn user messages; Verification on coding tasks; Tolerant tool-call handling; Tools for complex visual inputs; Safeguard refusals

## Prompting Claude Haiku 5.5

- **Distilled (all models):** blanket search instructions over-trigger (with Sonnet 5.5, the tool-wording entry).
- **Distilled (scoped, Haiku 5.5):** §Verification (the concrete check paragraph at low and medium effort, with Sonnet 5.5); §Carrying work through and staying in scope (the keep-working pair, with Sonnet 5.5); §Search and tool use (the current date and the training-data nudge; the JSON-with-tools line with thinking off); §Chatbots and safeguards (rules hold for the whole conversation); §Thinking-depth lines ("answer directly" doesn't stop thinking, agreeing with `general.md`).
- **Excluded:** mid-turn user-message placement (API), thinking-off and effort settings, switching settings to keep reasoning out of replies.
- **Outline (H2):** Use effort to control thinking; Accurate search results; Use adaptive thinking with JSON output and your own tools; Prevent early stopping in long agent prompts; Tell coding agents to verify their changes; Mid-turn user messages; Keep chatbots to their system prompt; Keep reasoning out of user-facing text; Safeguard refusals
