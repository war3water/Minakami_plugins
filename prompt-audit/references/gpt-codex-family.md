# GPT–Codex family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: gpt-codex-family.md §<section>]`.

## Structure preferences

- Markdown headings and bullet lists are the reliable structuring idiom; keep instructions, context, and data in visibly separate sections.
- Front-load: the most important instructions go first, and long narrative prose risks being skimmed — prefer concise imperative bullets.
- State the output format literally and completely; this family honors format specs to the letter, so a wrong or incomplete output contract locks in wrong output.

## Instruction-following profile

- Literal and explicit. Unstated defaults get filled unpredictably — spell out defaults, stop conditions, and tie-breakers rather than assuming sensible inference.
- Agentic prompts must pick exactly one persistence stance — "keep going until resolved" or "stop and ask when uncertain" — and state it. Including both, or neither, produces erratic stopping behavior.
- Conflicting instructions degrade output disproportionately for this family; a single unresolved contradiction can dominate the run. Weight D5 up. Two differently-worded statements of the same rule can be read as two distinct rules — deduplicate aggressively.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged. Family addition: "be smart", "be creative", "use your best judgment" as standalone lines — filler unless paired with the concrete dimension the judgment applies to.

## Token-efficiency notes

- Concise imperative bullets carry more instruction per token than narrative paragraphs, and survive skimming.
- Boilerplate preamble before the first actionable instruction is pure cost — the model needs the task, not a warm-up.
- Repetition is occasionally load-bearing for critical constraints in very long prompts, but only for the one or two rules that truly are critical.

## Language notes

- The universal trade-offs in `general.md` apply unchanged; no family-specific delta is durable enough to record.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D1 Goal clarity | Up — explicit goals, defaults, and stop conditions are load-bearing |
| D5 Internal consistency | Up — contradictions degrade output disproportionately |
| D6 Structure and format | Up — format specs honored literally; the contract must be right |
| Others | Per `general.md` role-based weighting |
