# Gemini family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: gemini-family.md §<section>]`.

This file is deliberately thinner than its siblings — audits for this family lean more heavily on `general.md`.

## Structure preferences

- Concise, directive instructions work best; short labeled sections over long prose.
- In long contexts, repeat the critical constraints near the end — distance from the task erodes their weight.
- Request output structure explicitly (schema, headings, or field list) when the output is consumed downstream.
- Few-shot examples are a strong lever — patterns are picked up from a small number of examples; tune the count by experiment rather than defaulting to zero or many.
- Choose one delimiter style — XML-style tags or Markdown headings — and keep it consistent within a prompt; mixed styles blur the boundary between instruction and data.
- Define ambiguous terms and parameters explicitly; loaded words are not disambiguated on the model's own initiative.
- In long inputs, put the question after the material and anchor it ("based on the preceding information...") — the specific form of the end-of-context rule above.
- An agentic system instruction separates three things: the reasoning strategy (how deeply to analyze and plan before acting), execution rules (when to adapt the plan, how persistently to retry, which actions count as risky), and interaction rules (when to ask versus assume, how verbose to be while working).

## Instruction-following profile

- Direct imperatives are followed reliably; softly hedged instructions ("you might consider...") are treated as optional.
- Light persona scaffolding is tolerated and occasionally useful for tone, but capability still comes from concrete constraints.
- Precise, plain instructions outperform elaborate prompt engineering; verbose or persuasive phrasing makes current models over-analyze.
- Default output is direct and terse: detail, warmth, or a conversational tone must be requested explicitly. This is the family's inversion of the usual bias — an unstated preference for elaboration yields a short answer, not a long one.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged. Family addition — chain-of-thought scaffolds ("outline your plan first", "show your reasoning steps", worked reasoning templates): current models reason internally, and the vendor's migration advice is to drop them in favor of the runtime's thinking setting. Family exception to the universal no-op: a short, deliberate depth request ("think very hard about this") on a genuinely hard problem is a documented lever, at token cost — do not flag it as boilerplate.

## Token-efficiency notes

- The universal heuristics in `general.md` apply; the repeat-critical-constraints advice above is the one family-specific exception to "never repeat".

## Language notes

- Broad multilingual coverage; the universal trade-offs in `general.md` apply unchanged.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D6 Structure and format | Up — explicit output structure and end-of-prompt constraint placement |
| Others | Per `general.md` role-based weighting |
