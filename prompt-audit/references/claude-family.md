# Claude family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: claude-family.md §<section>]`.

## Structure preferences

- Clear sectioning pays off — markdown headings and XML-style tags both work well; what matters is that instructions, context, and data are visibly distinct regions.
- Role and standing constraints belong in the system prompt; the task and its data belong in the user turn.
- In long prompts, put critical constraints early and restate the output contract near the end — the two positions the model attends to most reliably.
- Delimit any untrusted or variable content (file contents, user data, retrieved text) inside explicit fences or tags, with instructions outside.

## Instruction-following profile

- Instruction-following is strong and precise — which cuts both ways: over-constraint backfires fast, because the model will actually obey a bad rule rather than quietly ignoring it. Weight D4 up.
- Rigid rules get over-complied with. When two rules can collide, state which wins; otherwise the model may satisfy the letter of the wrong one.
- Stating *why* a rule exists improves adherence — a one-clause motivation lets the model apply the rule sensibly at edges the author did not foresee.
- Prefer describing tools and when to use them over scripting exact call sequences; the model handles conditional judgment well and scripts break on deviation.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged. The family delta is emphasis, not new items: strong instruction-following means a harmful over-constraint outweighs a lingering no-op — a bad rule gets obeyed here, not ignored, so D4 findings deserve the scrutiny.

## Token-efficiency notes

- Structure (headings, tags) is cheap and buys reliability — do not flag light structural markup as waste.
- One canonical, rule-consistent example outperforms several near-duplicates; flag example sets that repeat a point.
- Long verbatim repetition of earlier rules is unnecessary — a short pointer back suffices within one prompt.

## Language notes

- The universal trade-offs in `general.md` apply. Family delta: mixed-language prompts (English instructions, native-language domain terms) are handled well and are often the practical optimum — surface as a discussion option, not a prescription.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D4 Capability limiting | Up — precise obedience makes over-constraint expensive |
| D5 Internal consistency | Up — colliding rules get over-complied with; priority statements matter |
| D6 Structure and format | Standard — sectioning/tags help; placement rules above apply |
| Others | Per `general.md` role-based weighting |
