# Claude family — prompt guidance

Family-level guidance, cited as `[ref: claude-family.md §<section>]`. Universal patterns are in `general.md`; guidance for tool-using agents is in `agentic.md`. Weight D4 and D5 up for this family: precise obedience makes over-constraint and unresolved collisions costly.

## Structure preferences

- Clear sectioning pays off — markdown headings and XML-style tags both work; what matters is that instructions, context, and data are visibly distinct regions.
- Role and standing constraints belong in the system prompt; the task and its data in the user turn.
- In long prompts, put critical constraints early and restate the output contract near the end — the two positions the model attends to most reliably.
- When the task depends on which model is running or on exact model identifiers (self-identification, a model string in generated code), state them in the prompt: the model doesn't reliably know its own version.

## Instruction-following profile

- Instruction-following is strong and precise, which cuts both ways: the model obeys a bad rule rather than quietly ignoring it, so over-constraint backfires fast.
- Colliding rules get over-complied with — the model may satisfy the letter of the wrong one. This applies only to a collision that passes the runbook's D5 test.
- Instructions are read literally and don't generalize from one item to the next; state the scope an instruction covers ("every section, not just the first"). Flag it when a realistic input makes the literal reading produce output the user would reject.
- A vague conservatism bar in a review or analysis prompt — "only report high-severity issues", "be conservative", "don't nitpick" — is obeyed by withholding: the model still finds issues and drops them, so recall falls while capability is unchanged. Ask for coverage in the finding pass and filter separately, or state the bar concretely. A bar that already names what qualifies is that fix, not the defect; flag it only when the user's goal or success criteria name a category the bar excludes.
- Stating why a rule exists improves adherence: a one-clause reason lets the model apply the rule sensibly at edges the author didn't foresee.
- Describing tools and when to use them works better than scripting exact call sequences.
- Generic prohibitions ("avoid a generic look", "don't use that color") move the model to a different fixed default; name the pattern to avoid and the concrete alternative.
- In conversational prompts, give the reason and the whole task up front; the same information spread over several turns costs tokens and quality.

## Known no-op and harmful patterns

Family additions to the list in `general.md`:

- **Instructed re-verification** — "double-check your answer", "add a final verification step", "verify with a subagent". Current Claude models verify and self-correct natively, so this compounds into over-verification: token cost with no quality gain. Removable; in high-frequency agentic prompts, actively harmful.
- **Forced narration scaffolding** — "after every N tool calls, summarize progress", "hold all findings for the final response", counted checkpoints. Current models calibrate updates on their own, so counted scaffolding forces noise or suppresses updates users want. Describe the cadence and content wanted, with one example.
- **Reasoning-echo instructions** (harmful) — prompts that tell the model to write out, transcribe, or explain its internal reasoning in the response, usually standing in for a thinking mode. Safeguarded models can decline such a request outright as reasoning extraction, so the prompt fails rather than degrades. Flag in any prompt role; the fix is to delete the instruction and read the runtime's summarized thinking instead.

## Token-efficiency notes

- Structure (headings, tags) is cheap and buys reliability; don't flag light structural markup as waste.
- Length contracts should say what to leave out rather than demand terseness. Told to "be concise", current models compress prose into fragments, abbreviations, and arrow chains — shorter and harder to read. Naming what to drop (details that don't change what the reader does next) and asking for complete sentences gets brevity and readability together.
- Mixed-language prompts (English instructions, native-language domain terms) are handled well and are often the practical optimum — a discussion option, not a prescription.
