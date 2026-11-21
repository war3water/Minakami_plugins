# OpenAI (GPT, Codex) — prompt guidance

Cite as `[ref: providers/openai.md §<section>]`. Universal patterns are in `general.md`; universal guidance for tool-using agents is in `agentic.md`.

**How to read this file.** The sections under "All OpenAI models" apply to every OpenAI model unless an entry names an exception. When the user named a model in the table below, also read its model file and apply it; it holds that model's own advice and nothing about other models. When the user named only "GPT" or "Codex", or a model the table doesn't list, this file is the whole provider-specific basis.

Weight D1, D5, and D6 up for these models: explicit goals and defaults are load-bearing, contradictions degrade output disproportionately, and format specs are honored literally.

## Models

OpenAI publishes prompting guidance per generation; one page covers several series (Astra, Sol, Terra, Luna), so models of one generation share a model file. Status is the vendor's, checked on 2026-11-21; "newest" marks the newest model of its series. A model the vendor has shut down is not listed.

| Model | Id | Series | Model file | Status |
|---|---|---|---|---|
| GPT-6.2 Astra | `gpt-6.2-astra` | Astra | `providers/openai/gpt-6-2-astra.md` | Active, newest |
| GPT-6.2 Sol | `gpt-6.2-sol` | Sol | `providers/openai/gpt-6-2-sol.md` | Active, newest |
| GPT-6.1 Sol | `gpt-6.1-sol` | Sol | `providers/openai/gpt-6-1-sol.md` | Active |
| GPT-6.1 Terra | `gpt-6.1-terra` | Terra | `providers/openai/gpt-6-1-terra.md` | Active, newest |
| GPT-6 Astra | `gpt-6-astra` | Astra | `providers/openai/gpt-6-astra.md` | Active |
| GPT-6 Sol | `gpt-6-sol` | Sol | `providers/openai/gpt-6-sol.md` | Active |
| GPT-6 Luna | `gpt-6-luna` | Luna | `providers/openai/gpt-6-luna.md` | Active, newest |

GPT-5.x and GPT-5.x Codex models have no current per-model page; this file is their whole basis. Several are deprecated, with shutdowns between 2026-12-11 and 2027-04-01.

## All OpenAI models

### Structure preferences

- Markdown headings and bullet lists are the reliable structuring idiom; keep instructions, context, and data in visibly separate sections.
- Front-load: the most important instructions go first, and long narrative prose risks being skimmed — prefer concise imperative bullets.
- State the output format literally and completely; these models honor format specs to the letter, so a wrong or incomplete output contract locks in wrong output.
- Outcome first: describe the result and the stopping condition before any steps, and let the model choose the path; step-scripted prompts constrain current models without improving results. A durable shape for a complex prompt: role, tone, goal, success criteria, constraints, tools, output contract, stop rules.
- Standing rules go in the developer or system message and per-request material in the user turn — the vendor's analogy is a function definition versus its arguments.

### Instruction-following profile

- Literal and explicit: unstated defaults get filled unpredictably. Spell out defaults, stop conditions, and tie-breakers rather than assuming sensible inference.
- Conflicting instructions degrade output disproportionately; a single unresolved contradiction can dominate the run, and two differently worded statements of one rule can be read as two rules.
- Repetition is occasionally load-bearing for the one or two truly critical constraints in a very long prompt; beyond that it is cost.

### Known no-op and harmful patterns

Additions to the list in `general.md`:

- "Be smart", "be creative", "use your best judgment" as standalone lines — filler unless tied to the concrete decision the judgment applies to.
- Instructions to announce a plan before acting — meta-commentary that causes premature stopping.
- Required tests for trivial, reversible changes.

### Agentic prompts

- **One persistence stance.** Agentic prompts must pick exactly one — "keep going until resolved" or "stop and ask when uncertain" — and state it; both or neither produces erratic stopping. Over-restrictive approval or safety language makes current models stop early and ask; the cure is autonomy boundaries, not more caution. Left unspecified, the newest models lean toward asking. An ending that hands the work back — a plan, a suggested next step, a request for a routine decision — is stopping early too; when the run should finish on its own, name the only reasons to stop: a significant scope change, a concrete block, a decision only the user can make, an irreversible action.
- **Tool routing.** Tool descriptions carry the routing: say what each tool is for, when to use it, and when not to, and expose only task-relevant tools. A tool list without usage rules is routed unpredictably.
- **Update cadence.** Progress updates respond to an explicit cadence (a brief preamble before the first tool call, then sparse outcome-based updates at phase changes); counted cadences work for these models. Unstated, the model narrates routine steps or falls silent.
- **Instruction precedence.** When a prompt loads skills or agent-instruction files, say which wins on conflict — the vendor's guidance is that the user's instructions take precedence — or the model pauses on the contradiction.
- **Per-run reading cost.** Blanket "read all the docs before starting" rules in agent-instruction files are paid on every run; make file references conditional on the task that needs them.
