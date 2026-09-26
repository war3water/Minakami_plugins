# Claude family — durable prompt guidance

Evergreen contract: family-level, durable guidance only. No model version numbers, no benchmarks, no pricing. If a claim holds for only one model version, it does not belong here. The audit runbook cites this file as `[ref: claude-family.md §<section>]`.

## Structure preferences

- Clear sectioning pays off — markdown headings and XML-style tags both work well; what matters is that instructions, context, and data are visibly distinct regions.
- Role and standing constraints belong in the system prompt; the task and its data belong in the user turn.
- In long prompts, put critical constraints early and restate the output contract near the end — the two positions the model attends to most reliably.
- Delimit any untrusted or variable content (file contents, user data, retrieved text) inside explicit fences or tags, with instructions outside, and declare the region inert as `general.md` describes.
- When the task depends on which model is running or on exact model identifiers — self-identification, choosing a model string in generated code — state them in the system prompt. The model does not reliably know its own version; a prompt that assumes it does invites a confident wrong answer (D3).
- For long-running agentic prompts, give the model a place to keep state — a checklist or notes file it updates — and say what must survive when context is summarized. The model tracks progress well when it has somewhere to track it, and an unattended run that ends a turn with open items resumes more reliably from a checklist than from prose.

## Instruction-following profile

- Instruction-following is strong and precise — which cuts both ways: over-constraint backfires fast, because the model will actually obey a bad rule rather than quietly ignoring it. Weight D4 up.
- Rigid rules get over-complied with. When two rules can collide, state which wins; otherwise the model may satisfy the letter of the wrong one.
- Stating *why* a rule exists improves adherence — a one-clause motivation lets the model apply the rule sensibly at edges the author did not foresee.
- Prefer describing tools and when to use them over scripting exact call sequences; the model handles conditional judgment well and scripts break on deviation.
- Task scope can expand under the model's own judgment — nearby fixes, extra tests, unrequested abstractions. For narrow tasks, state the intended scope explicitly — deliver what was asked, at the scope intended; report adjacent findings rather than acting on them — rather than assuming the task description bounds it.
- Instructions are read literally and do not generalize from one item to the next. State the scope an instruction applies to ("every section, not just the first") instead of expecting the model to infer breadth.
- A conservatism instruction in a review or analysis prompt — "only report high-severity issues", "be conservative", "don't nitpick" — is obeyed literally: the model still finds the issues and then withholds them, so measured recall drops while capability is unchanged. Ask for coverage in the finding pass and filter in a separate step, or state the bar concretely.
- Generic prohibitions swap one default for another. "Avoid a generic look", "don't use that color", "if in doubt, use the tool" move the model to a different fixed default rather than producing the intended variety or judgment. Name the specific pattern to avoid, specify the concrete alternative, or replace a blanket default with the condition under which it applies.
- Give the reason and the whole task up front. Intent, constraints, and who the output is for, stated in the first turn, let the model run autonomously; the same information conveyed piecemeal over several turns costs tokens and quality. A one-clause reason behind a request lets the model connect it to the relevant context instead of inferring intent.

## Known no-op and harmful patterns

- The universal list in `general.md` applies unchanged, with an emphasis delta: strong instruction-following means a harmful over-constraint outweighs a lingering no-op — a bad rule gets obeyed here, not ignored, so D4 findings deserve the scrutiny.
- Family addition — instructed re-verification: "double-check your answer", "add a final verification step", "verify with a subagent". Current Claude models verify and self-correct natively, so these instructions compound with native behavior into over-verification — token cost with no quality gain. Flag as removable; in high-frequency agentic prompts, flag as actively harmful.
- Family addition — forced narration scaffolding: "after every N tool calls, summarize progress", "hold all findings for the final response", counted checkpoints. Current models calibrate updates on their own, so counted scaffolding either forces noise or suppresses the updates users want. Describe the cadence and content you want, with one example, and let the model apply it.
- Family addition — reasoning-depth lines in chat prompts: "think carefully before answering", "reason at length first". Reasoning depth is a runtime setting on current models; the line adds latency to every reply without improving it. Removable.
- Family addition, harmful — reasoning-echo instructions: prompts that tell the model to write out, transcribe, or explain its internal reasoning in the response, usually as a stand-in for a thinking mode. Current models with safeguards can decline such a request outright as reasoning extraction, so the prompt fails rather than degrades. Flag as harmful in any prompt role; the fix is to delete the instruction and read the runtime's summarized thinking instead.
- Not a no-op, for contrast: an investigate-before-answering rule tied to a concrete action ("read the file before describing it") and a generality rule for coding ("solve the general case; do not hard-code to the test inputs; report incorrect tests instead of working around them") are levers the vendor recommends adding — do not flag them as restating baseline competence.

## Token-efficiency notes

- Structure (headings, tags) is cheap and buys reliability — do not flag light structural markup as waste.
- One canonical, rule-consistent example outperforms several near-duplicates; flag example sets that repeat a point.
- Long verbatim repetition of earlier rules is unnecessary — a short pointer back suffices within one prompt.
- Length contracts should say what to leave out, not demand terseness. Told to "be concise", current models compress prose into fragments, abbreviations, and arrow chains — shorter and harder to read. A contract that names what to drop (details that do not change what the reader does next) and asks for complete sentences gets brevity and readability together.

## Language notes

- The universal trade-offs in `general.md` apply. Family delta: mixed-language prompts (English instructions, native-language domain terms) are handled well and are often the practical optimum — surface as a discussion option, not a prescription.

## Dimension weighting

| Dimension | Weighting for this family |
|---|---|
| D4 Capability limiting | Up — precise obedience makes over-constraint expensive |
| D5 Internal consistency | Up — colliding rules get over-complied with; priority statements matter |
| D6 Structure and format | Standard — sectioning/tags help; placement rules above apply |
| Others | Per `general.md` role-based weighting |
