# GPT–Codex family — prompt guidance

Family-level guidance, cited as `[ref: gpt-codex-family.md §<section>]`. Universal patterns are in `general.md`; guidance for tool-using agents, including this family's persistence and tool-routing behavior, is in `agentic.md`. Weight D1, D5, and D6 up for this family: explicit goals and defaults are load-bearing, contradictions degrade output disproportionately, and format specs are honored literally.

## Structure preferences

- Markdown headings and bullet lists are the reliable structuring idiom; keep instructions, context, and data in visibly separate sections.
- Front-load: the most important instructions go first, and long narrative prose risks being skimmed — prefer concise imperative bullets.
- State the output format literally and completely; this family honors format specs to the letter, so a wrong or incomplete output contract locks in wrong output.
- Outcome first: describe the result and the stopping condition before any steps, and let the model choose the path; step-scripted prompts constrain current models without improving results. A durable shape for a complex prompt: role, tone, goal, success criteria, constraints, tools, output contract, stop rules.
- Standing rules go in the developer or system message and per-request material in the user turn — the vendor's analogy is a function definition versus its arguments.

## Instruction-following profile

- Literal and explicit: unstated defaults get filled unpredictably. Spell out defaults, stop conditions, and tie-breakers rather than assuming sensible inference.
- Conflicting instructions degrade output disproportionately; a single unresolved contradiction can dominate the run, and two differently worded statements of one rule can be read as two rules.
- Repetition is occasionally load-bearing for the one or two truly critical constraints in a very long prompt; beyond that it is cost.

## Known no-op and harmful patterns

Family additions to the list in `general.md`:

- "Be smart", "be creative", "use your best judgment" as standalone lines — filler unless tied to the concrete decision the judgment applies to.
- Instructions to announce a plan before acting — meta-commentary that causes premature stopping.
- Required tests for trivial, reversible changes.
