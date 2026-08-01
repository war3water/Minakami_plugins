# General reference — universal failure modes and evidence rubric

Evergreen contract: this file carries durable, family-independent guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file with the `[general]` basis tag.

## Evidence rubric

What qualifies as a finding:

- All five parts the runbook enumerates — a finding missing any of them is not reportable.
- The mechanism must be causal, not aesthetic. "This sentence is redundant with L12, and duplicate rules drift apart over edits" is a finding; "I would phrase this differently" is not.

What does not qualify:

- Stylistic taste with no failure mechanism.
- Speculation presented as fact — speculation is allowed only under the runbook's `[hypothesis]` honesty rules.
- Anything the auditor cannot support from the text plus the loaded references plus the user's answers.

## Severity calibration

| Severity | Calibration examples |
|---|---|
| Critical | Two rules directly contradict on the main task path; the goal or output contract is absent and the output is machine-consumed; the prompt presupposes a file or tool that does not exist in the stated usage context |
| Major | The same rule appears three times in different wordings; a persistent prompt spends a large block on guidance the model follows unprompted; no stop condition on an open-ended agentic task |
| Minor | Filler phrases; one redundant courtesy sentence; emphasis on a low-stakes rule; a single stale example |
| Info | An available improvement that is not a defect — an escape hatch to add, a language trade-off to discuss, a restructure that would help future maintenance |

## Universal anti-patterns

- **Contradictory rules.** The model resolves the conflict unpredictably; different runs resolve it differently.
- **Duplicate rules.** Restating a rule in new words reads as two rules; over edits the copies drift apart and start to conflict.
- **Vague success criteria.** "Make it good", "be thorough" — the model optimizes for its own reading of "good", which may not be the user's.
- **Negation-heavy rule lists.** Long chains of "don't X, never Y" leave the desired behavior unstated; say what to do instead.
- **Emphasis dilution.** When everything is bold, capitalized, or marked IMPORTANT, nothing is; critical constraints lose their signal.
- **Examples that contradict instructions.** The model tends to follow the example, silently overriding the stated rule.
- **Unbounded asks.** "Be comprehensive", "cover everything" with no stop condition or budget invites overlong output and rambling.
- **Presupposed context.** Referencing files, tools, variables, or prior decisions that do not exist in the stated usage context sends the model chasing phantoms — a direct hallucination trigger.
- **Undelimited or spoofable untrusted content.** In agent-facing prompts, external text (file contents, web results, user data) mixed with instructions without clear delimitation is an instruction-injection surface. Delimitation alone is not enough: substituted content can embed text that imitates the closing delimiter or inserts new-looking rules, so the prompt must declare the delimited region inert — data, never instructions — and state that only the outermost harness-inserted delimiters count.
- **Micromanaged step order.** Scripting every micro-step where judgment would do better both limits the model and breaks when the situation deviates from the script.
- **Stale workarounds.** Instructions that compensate for a weakness earlier models had; on current models they cost tokens and can actively fight the model's better default behavior.

## Universal good patterns

- **Goal first.** State the goal and the definition of done before the constraints.
- **Explicit output contract.** Format, length bounds, and audience — stated once, precisely.
- **Positive phrasing.** Describe desired behavior; reserve prohibitions for real hard limits.
- **Stated rule priority.** When rules can collide, say which wins.
- **Escape hatch.** "If the input is unclear or a constraint cannot be met, say so and ask" — cheap insurance against confident wrong output.
- **Delimit data from instructions.** Fences, tags, or clearly labeled sections; instructions outside, material inside.
- **One canonical example.** A single worked example that agrees with the rules beats three near-duplicates.
- **Explicit length contract.** State the desired length of responses and written deliverables outright; models do not reliably infer length preferences, and an unstated preference yields the model's own calibration — usually longer than wanted.

## Known no-op patterns — streamlining candidates

These instructions restate what current-generation coding models already do unprompted. They spend tokens without changing behavior, and some actively narrow it. This list shifts as model capability evolves — refreshing it is what a version bump of this plugin is for. A streamlining claim not covered here may still be made, tagged `[hypothesis]`.

- "Do not hallucinate" / "be accurate" / "make sure your answer is correct" — aspiration, not instruction; no behavioral lever.
- "Think step by step" and similar reasoning boilerplate — reasoning-capable models do this on their own; the phrase adds nothing and dates the prompt.
- Generic expert personas — "you are the world's best programmer" adds no capability; a persona earns its place only when it carries real constraints (audience, tone, domain).
- Threats, bribes, tips, and emotional appeals — no durable effect on modern models; noise.
- Repeated courtesy — one "please" costs nothing; a pattern of them is filler.
- Restating baseline competence — "write clean code", "follow best practices", "use meaningful variable names" without project-specific content; the model's defaults already cover this.

## Token-efficiency heuristics

All countable from the text — these support approximate, honest claims ("removing the duplicate block cuts ~40 lines"):

- Duplicated or near-duplicated blocks and rules.
- Example weight: examples that dwarf the rules they illustrate, or several examples making the same point.
- Boilerplate preamble before the first actionable instruction.
- Run frequency multiplies cost: a persistent prompt (system, agent instructions) pays its token cost on every run, so D2 findings weigh heavier there — the interview's usage_context answer sets this.
- Under-length is also waste: a prompt so sparse the model must ask follow-ups (or guess) spends the saved tokens on round-trips or rework.

## Language notes

- Training-data richness is generally highest in English for coding models; technical instructions in English tend to be interpreted most precisely.
- Against that: team readability and maintainability, domain terminology that resists translation, and the language of the inputs/outputs the model will actually handle.
- The trade-off is real and situational — surface it for discussion with the user; never present one language as objectively correct, and never switch a prompt's language without the user's decision.

## Role-based dimension weighting

| prompt_role | Weight up |
|---|---|
| System prompt / persistent agent instructions | D2 (paid every run), D5 (long-lived rule sets accumulate conflicts), D8 (injection surface) |
| Slash command / skill runbook | D1 (determinism of outcome), D5, D8 |
| One-shot task prompt | D1, D7 (all context must be in-prompt); D8 often N/A |
| Template with variables | D3 (placeholders must be defined), D7 (holes must be fillable) |
