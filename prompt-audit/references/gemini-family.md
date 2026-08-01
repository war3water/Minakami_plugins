# Gemini family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: gemini-family.md §<section>]`.

This file is deliberately thinner than its siblings — audits for this family lean more heavily on `general.md`.

## Structure preferences

- Concise, directive instructions work best; short labeled sections over long prose.
- In long contexts, repeat the critical constraints near the end — distance from the task erodes their weight.
- Request output structure explicitly (schema, headings, or field list) when the output is consumed downstream.
- Few-shot examples are a strong lever — patterns are picked up from a small number of examples; tune the count by experiment rather than defaulting to zero or many.

## Instruction-following profile

- Direct imperatives are followed reliably; softly hedged instructions ("you might consider...") are treated as optional.
- Light persona scaffolding is tolerated and occasionally useful for tone, but capability still comes from concrete constraints.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged; no family-specific additions are durable enough to record here.

## Token-efficiency notes

- The universal heuristics in `general.md` apply; the repeat-critical-constraints advice above is the one family-specific exception to "never repeat".

## Language notes

- Broad multilingual coverage; the universal trade-offs in `general.md` apply unchanged.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D6 Structure and format | Up — explicit output structure and end-of-prompt constraint placement |
| Others | Per `general.md` role-based weighting |
