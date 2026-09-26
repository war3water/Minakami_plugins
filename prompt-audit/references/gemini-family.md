# Gemini family — prompt guidance

Family-level guidance, cited as `[ref: gemini-family.md §<section>]`. Universal patterns are in `general.md`; guidance for tool-using agents is in `agentic.md`. Weight D6 up for this family: explicit output structure and end-of-prompt placement of constraints matter.

## Structure preferences

- Concise, directive instructions in short labeled sections work better than long prose.
- In long inputs, put the question after the material, anchor it ("based on the preceding information…"), and restate critical constraints near the end — distance from the task erodes their weight. This is the family's one exception to "don't repeat".
- Request output structure explicitly (schema, headings, or field list) when the output is consumed downstream.
- Few-shot examples are a strong lever: patterns are picked up from a small number of examples.
- Keep delimiting consistent: flag it only when the same kind of boundary is marked two different ways (some instruction sections as tags, others as headings). Headings for the instructions with a tag around the inserted data is the intended split, not a mix.
- Define ambiguous terms and parameters explicitly; loaded words are not disambiguated on the model's own initiative.

## Instruction-following profile

- Direct imperatives are followed reliably; softly hedged instructions ("you might consider…") are treated as optional.
- Precise, plain instructions outperform elaborate prompt engineering; verbose or persuasive phrasing makes current models over-analyze. Light persona scaffolding is tolerated, but capability comes from concrete constraints.
- Default output is direct and terse: detail, warmth, or a conversational tone must be requested. An unstated preference for elaboration yields a short answer — the family's inversion of the usual bias.

## Known no-op and harmful patterns

Family addition to the list in `general.md`: chain-of-thought scaffolds ("outline your plan first", "show your reasoning steps", worked reasoning templates) — current models reason internally, and the vendor advises the runtime thinking setting instead. The exception: a short, deliberate depth request ("think very hard about this") on a genuinely hard problem is a documented lever, at token cost; don't flag it as boilerplate.
