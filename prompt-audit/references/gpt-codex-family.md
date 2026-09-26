# GPT–Codex family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: gpt-codex-family.md §<section>]`.

## Structure preferences

- Markdown headings and bullet lists are the reliable structuring idiom; keep instructions, context, and data in visibly separate sections.
- Front-load: the most important instructions go first, and long narrative prose risks being skimmed — prefer concise imperative bullets.
- State the output format literally and completely; this family honors format specs to the letter, so a wrong or incomplete output contract locks in wrong output.
- Outcome first: describe the result and the stopping condition before any steps, and let the model choose the path — step-scripted prompts constrain current models without improving results. A durable shape for a complex prompt in this family: role, tone, goal, success criteria, constraints, tools (what, when, what not to use), output contract, stop rules.
- Standing rules go in the developer or system message, per-request material in the user turn — the vendor's own analogy is a function definition versus its arguments. Headed sections (identity, instructions, examples, context) in Markdown headings or XML tags mark the boundaries.

## Instruction-following profile

- Literal and explicit. Unstated defaults get filled unpredictably — spell out defaults, stop conditions, and tie-breakers rather than assuming sensible inference.
- Agentic prompts must pick exactly one persistence stance — "keep going until resolved" or "stop and ask when uncertain" — and state it. Including both, or neither, produces erratic stopping behavior. Pair the stance with completion criteria and autonomy boundaries: which actions are safe to take without asking (local, reversible) and which need confirmation (external writes, destructive actions, scope expansions). Over-restrictive approval or safety language makes current models stop early and ask; the cure is boundaries, not more caution. Say too whether an unclear request means ask or proceed under a stated assumption — left unspecified, the newest models lean toward asking.
- Tool descriptions carry the routing: say what each tool is for, when to use it, and when not to, and expose only task-relevant tools. A tool list without usage rules is routed unpredictably.
- Verbosity and update cadence respond to explicit targets — a length bound for answers, and a stated cadence for progress updates (a brief preamble before the first tool call, then sparse outcome-based updates at phase changes). Counted cadences work in this family; unstated, the model narrates routine steps or falls silent.
- When a prompt loads skills or agent-instruction files, say which wins on conflict — the vendor's guidance is that the user's instructions take precedence — or the model pauses on the contradiction.
- Conflicting instructions degrade output disproportionately for this family; a single unresolved contradiction can dominate the run. Weight D5 up. Two differently-worded statements of the same rule can be read as two distinct rules — deduplicate aggressively.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged. Family addition: "be smart", "be creative", "use your best judgment" as standalone lines — filler unless paired with the concrete dimension the judgment applies to.
- Family addition — legacy scaffolding: repeated rules, redundant examples, meta-commentary instructions that make the model announce a plan before acting (a cause of premature stopping), and required tests for trivial reversible changes. The vendor's first recommendation for an underperforming prompt is to strip these and re-measure.

## Token-efficiency notes

- Concise imperative bullets carry more instruction per token than narrative paragraphs, and survive skimming.
- Boilerplate preamble before the first actionable instruction is pure cost — the model needs the task, not a warm-up.
- Repetition is occasionally load-bearing for critical constraints in very long prompts, but only for the one or two rules that truly are critical.
- Blanket "read all the docs before starting" rules in agent-instruction files are pure cost on every run; make file references conditional on the task that needs them.

## Language notes

- The universal trade-offs in `general.md` apply unchanged; no family-specific delta is durable enough to record.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D1 Goal clarity | Up — explicit goals, defaults, and stop conditions are load-bearing |
| D5 Internal consistency | Up — contradictions degrade output disproportionately |
| D6 Structure and format | Up — format specs honored literally; the contract must be right |
| Others | Per `general.md` role-based weighting |
