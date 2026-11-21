# Google (Gemini) — prompt guidance

Cite as `[ref: providers/google.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** Google publishes one prompting page for all Gemini models, with a few model-specific sections. The sections under "All Gemini models" apply to every Gemini model. When the user named a model in the table below, also read its model file and apply it.

Weight D6 up for these models: explicit output structure and end-of-prompt placement of constraints matter.

## Models

Status is the vendor's, checked on 2026-11-21.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| Gemini 3 Flash | `gemini-3-flash-preview` | Gemini 3 | `providers/google/gemini-3-flash.md` | Preview |

Every other Gemini model (Gemini 4 Argon, Carbon, Hydrogen, Neon; Gemini 3.8, 3.6, 3.5 and 3.1 Flash models) has no model-specific guidance; this file is its whole basis.

## All Gemini models

### Structure preferences

- Concise, directive instructions in short labeled sections work better than long prose.
- In long inputs, put the question after the material, anchor it ("based on the preceding information…"), and restate critical constraints near the end — distance from the task erodes their weight. This is the one exception to "don't repeat" for these models.
- Request output structure explicitly (schema, headings, or field list) when the output is consumed downstream.
- Few-shot examples are a strong lever: patterns are picked up from a small number of examples.
- Keep delimiting consistent: flag it only when the same kind of boundary is marked two different ways (some instruction sections as tags, others as headings). Headings for the instructions with a tag around the inserted data is the intended split, not a mix.
- Define ambiguous terms and parameters explicitly; loaded words are not disambiguated on the model's own initiative.

### Instruction-following profile

- Direct imperatives are followed reliably; softly hedged instructions ("you might consider…") are treated as optional.
- Precise, plain instructions outperform elaborate prompt engineering; verbose or persuasive phrasing makes current models over-analyze. Light persona scaffolding is tolerated, but capability comes from concrete constraints.
- Default output is direct and terse: detail, warmth, or a conversational tone must be requested. An unstated preference for elaboration yields a short answer — the inversion of the usual bias.

### Known no-op and harmful patterns

Addition to the list in `general.md`: chain-of-thought scaffolds ("outline your plan first", "show your reasoning steps", worked reasoning templates) — current models reason internally, and the vendor advises the runtime thinking setting instead. The exception: a short, deliberate depth request ("think very hard about this") on a genuinely hard problem is a documented lever, at token cost; don't flag it as boilerplate.

### Agentic prompts

- An agentic system instruction separates three things: the reasoning strategy (how deeply to analyze and plan before acting), execution rules (when to adapt the plan, how persistently to retry, which actions count as risky), and interaction rules (when to ask versus assume, how verbose to be while working).
