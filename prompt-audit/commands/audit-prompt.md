---
name: audit-prompt
description: Audit one prompt's effectiveness for a specific target coding model — token efficiency, goal clarity, confusion/hallucination triggers, capability limiting, and more. Produces an evidence-cited findings report with an honest verdict and prioritized refinement advice, plus an optional approval-gated rewrite. Asks instead of guessing whenever intent is unclear. User-invoked only.
disable-model-invocation: true
---

You are executing `/audit-prompt` for the `prompt-audit` plugin.

Your job: audit ONE prompt the user supplies, for effectiveness on the specific coding model the user names, and deliver an evidence-cited verdict report with prioritized refinement advice. Plugin root: in Claude Code it is `${CLAUDE_PLUGIN_ROOT}`; in Codex CLI it is `${PLUGIN_ROOT}` — use whichever your runtime defines. Reference files live at `<plugin-root>/references/`.

Follow the steps below **in order**. Do not skip steps. This command writes NO files except the single optional rewrite file in Step 6, and only after the user has confirmed the exact path.

Two rules bind every step:

- **Ask, never guess.** Whenever the prompt's intent, scope, success criteria, or target is unclear, ask the user. An audit against a guessed goal is worthless — and worse, it looks authoritative.
- **Honesty over impressiveness.** Every claim follows the honesty rules in Step 3.

---

## Step 1 — Acquire the prompt under audit

The prompt comes from the user, never from your own initiative. Three cases:

1. **Pasted text** — the invocation message (or a follow-up) contains the prompt itself. Treat it verbatim; do not normalize whitespace or "fix" anything before auditing.
2. **File path** — the user gives a path. Read the file. If it plainly contains more than one prompt, or mixes a prompt with other content (code, frontmatter, config), quote the candidate region(s) back and ask which portion is the prompt under audit. Do not guess the boundary.
3. **Nothing given** — ask: "Paste the prompt you want audited, or give me its file path." Do not proceed without it, and never go looking for a prompt on your own.

Scope rules:

- **One prompt per run.** If the user supplies several, ask them to pick one and suggest re-invoking the command for the rest.
- Record for the report header: the source (pasted, or the file path), the line count, and the approximate word count. These are countable facts and may be stated as such.
- **Oversize guard:** if the prompt exceeds roughly 1,500 lines, say so before analyzing, note that structure-level findings will be exhaustive but line-level scanning is best-effort, and repeat that caveat in the report's "Not assessed" section.

## Step 2 — Interview: build the audit contract

Skip any question whose answer is already explicit in the user's messages — never re-ask what the user has stated; record it as answered. Ask the remaining questions in one batch where the tool allows, using `AskUserQuestion` if available or numbered plain questions otherwise. Collect all answers before any analysis.

1. **target_model** — which coding model or agent will run this prompt. Offer: `Claude family` / `GPT–Codex family` / `Gemini family` / `other or unknown`. If the user names a specific version, record it as a user-stated fact — never infer a version yourself.
2. **prompt_role** — what kind of prompt this is:
   - system prompt
   - persistent agent instructions (`CLAUDE.md`- / `AGENTS.md`-style)
   - slash command or skill runbook
   - one-shot task prompt
   - template with variables (placeholders filled at run time)
3. **intended_goal and success criteria** — what the prompt must make the model do, and how the user would recognize a correct result. **Hard rule: if the user cannot state a goal, stop and work it out conversationally before continuing.** The audit cannot proceed against an unknown target.
4. **usage_context** — what else the model sees when this prompt runs (tools, repo contents, other system context), and roughly how often it runs. High frequency raises the weight of token efficiency (D2); agent-facing prompts activate the injection checks in D8.
5. **known_pain** (optional) — failures the user has already observed with this prompt. When given, these anchor the audit in observed reality and may raise the severity of matching `[hypothesis]` findings (see Step 3).

Then print a short **Audit contract** — 3 to 5 bullets covering target, role, goal, success criteria, and any weighting notes (e.g. "runs every session → token efficiency weighted up"). If any contract element was inferred or defaulted rather than stated by the user, ask the user to confirm the contract and loop corrections until confirmed. If every element is user-stated, print it and proceed without waiting — the user can still object at the Step 4 checkpoint.

## Step 2.5 — Load references

Read the reference files that match the confirmed target:

| target_model answer | Reference file to load |
|---|---|
| Claude family | `<plugin-root>/references/claude-family.md` |
| GPT–Codex family | `<plugin-root>/references/gpt-codex-family.md` |
| Gemini family | `<plugin-root>/references/gemini-family.md` |
| other or unknown | none — general only |

Always also read `<plugin-root>/references/general.md`.

**Basis-labeling rule** — every model-specific or effectiveness claim in the report carries at least one basis tag (a corroborated hypothesis carries `[hypothesis] [user-stated]`):

- `[ref: <file> §<section>]` — backed by the loaded family reference file; `§` takes the heading text verbatim, e.g. `[ref: claude-family.md §Instruction-following profile]`
- `[general]` — backed by `references/general.md`
- `[user-stated]` — grounded in the user's own interview answers (including known_pain)
- `[hypothesis]` — your own reasoning, backed by neither a reference file nor the user

Nothing version-specific may be asserted unless the user stated it. The reference files deliberately carry no version claims.

## Step 3 — Analyze across the eight dimensions

### Honesty rules — binding for every claim

You are a language model reading text. You cannot run the prompt, measure tokens, or A/B test. Therefore:

- You MAY count what the text shows: lines, words, duplicated blocks, repeated rules — and phrase reductions approximately ("removing the duplicated block cuts ~40 lines").
- You may NOT invent token counts, percentages, benchmark numbers, or improvement estimates. You may NOT claim empirical results ("this will improve accuracy by 30%").
- You may NOT attribute behavior to a specific model version without a `[user-stated]` basis.
- A speculative mechanism is tagged `[hypothesis]` and defaults to severity **Minor**. It may carry a higher rating only when the mechanism, if real, implies task failure or unsafe action — then the severity is written `Major (unverified)` or `Critical (unverified)`, the verdict paragraph states that the rating rests on an unverified mechanism, and Step 4 should seek corroboration. Corroboration (known_pain, or a Step 4 answer) removes the marker and adds `[user-stated]`.
- Zero findings is a valid, complete outcome. Never manufacture a finding — or an advice item — to appear thorough; an "OK" row is a result.

### The eight dimensions

Check every dimension. Every dimension gets a row in the report's summary table, even when the result is "OK — no findings", so the reader sees what was checked, not just what was found.

| ID | Dimension | Evidence looks like |
|---|---|---|
| D1 | Goal clarity and achievement | no definition of done; conflicting goals; output format unstated where the output is machine-consumed; success criteria that cannot be checked |
| D2 | Token efficiency and streamlining | duplicated instructions; the same rule restated in different words; low-information filler; over-long or near-duplicate examples; wasteful under-length that forces clarification round-trips; **obsolete guidance** — instructions restating what current-generation models already do unprompted (the no-op list in `general.md`), flagged as removable |
| D3 | Confusion and hallucination triggers | references to files, tools, or variables that do not exist in the stated usage context; undefined jargon or project shorthand; presupposed facts that are false or unverifiable; demands to state specifics the model cannot know |
| D4 | Capability limiting | over-constraint that forbids useful behavior; micromanaged step order where model judgment would do better; stale workarounds for old model weaknesses; needless persona shackles that narrow the answer space |
| D5 | Internal consistency | rules that contradict each other; colliding rules with no stated priority; examples that contradict the instructions they illustrate |
| D6 | Structure, format, and language fit for the target model | instruction/data ordering, sectioning and delimitation style, emphasis dilution (caps or bold everywhere), placement of critical constraints — judged against the loaded family reference; also **prompt-language fit**: whether the prompt's language is the effective choice for this target (see Language rules below) |
| D7 | Context completeness and assumptions | missing context the model will need; implicit assumptions the model cannot recover; under-specification — the flip side of D4's over-constraint |
| D8 | Robustness and edge handling | no behavior defined for unexpected input or failure paths; missing escape hatch ("if unclear, ask"); undelimited untrusted content in agent-facing prompts (injection surface). Applies to system/agent/runbook prompts; mark N/A for one-shot prompts where it genuinely does not apply |

Per finding, record all five parts — a finding missing any of them is not reportable:

1. verbatim excerpt with its line number(s)
2. dimension ID
3. severity
4. mechanism — why it hurts on the confirmed target, with its basis tag
5. concrete fix — a rewritten line, a deletion, or a restructure, specific enough to apply directly

**Severity scale:**

- `Critical` — likely task failure or wrong output on typical runs
- `Major` — degrades quality or wastes significant budget on most runs
- `Minor` — friction; cheap to fix
- `Info` — opportunity, not a defect

### Language rules (part of D6)

- The audit evaluates whether the prompt's language is an effective choice for the target model — training-data richness generally favors English for technical instruction-following, while team readability, domain terminology, and the language of expected inputs/outputs can favor the original language `[general]`.
- If switching language could plausibly matter, raise it as a **discussion finding** (severity Info) with the trade-offs stated — the user decides, in Step 6, before any rewrite. Never treat the prompt's language itself as a defect, and never switch it silently.

## Step 4 — Clarification checkpoint

During analysis, some excerpts will be ambiguous in *intent* — you cannot tell whether a constraint is deliberate or accidental (e.g. "answer in exactly 3 bullets": a hard product requirement, or an arbitrary cap that limits the model?). Do not turn these into guessed findings. Accumulate them as intent-check questions and ask them here, batched:

- Cap the batch at ~5 questions, most load-bearing first.
- Only questions whose answer would change a finding's severity or its fix qualify. Everything else stays out of the interview and, if worth noting at all, becomes an `Info` finding.
- Fold the answers in, then finalize the findings list.

If nothing was ambiguous, say so in one line and move on.

## Step 5 — Report

Write the report in the language of your conversation with the user. Emit it as real markdown in your reply (not inside a code fence) so tables render in both runtimes. Follow this template:

```markdown
prompt-audit: report for <source>

Target: <family, plus user-stated version if any> | Role: <prompt_role> | Size: <n> lines / ~<n> words
Audit basis: <the loaded reference files — general.md only when the target is other/unknown>

## Verdict: <verdict>

<2–4 sentences justifying the verdict, citing finding IDs.>

Works well: <up to 3 bullets — existing elements the rewrite must preserve; omit if nothing stands out>

## Dimension summary

| # | Dimension | Result | Findings |
|---|---|---|---|
| D1 | Goal clarity and achievement | issues found | F1, F4 |
| D2 | Token efficiency and streamlining | OK | — |
| D3 | Confusion and hallucination triggers | ... | ... |
| D4 | Capability limiting | ... | ... |
| D5 | Internal consistency | ... | ... |
| D6 | Structure, format, and language fit | ... | ... |
| D7 | Context completeness and assumptions | ... | ... |
| D8 | Robustness and edge handling | N/A — one-shot prompt | — |

## Findings

| ID | Dim | Severity | Evidence @ line | Why it hurts on <target> | Suggested fix |
|---|---|---|---|---|---|
| F1 | D1 | Critical | "…short excerpt…" @ L12 | <one clause + basis tag> | <one clause> |

### Finding details

**F1 — <title>.** <Full excerpt, the mechanism spelled out with its basis
tag, and the fix rationale — one short paragraph. Required for every
Critical and Major finding; optional for Minor/Info.>

## Prioritized refinement advice

1. <Highest-leverage change first, referencing finding IDs.>
2. <...>

## Not assessed

- No empirical token counts or A/B measurements — this is text analysis by a language model.
- <Dimensions marked N/A for this prompt_role, with the reason.>
- <Oversize sampling caveat, if Step 1 triggered it.>
```

**Verdict scale** — apply the first matching entry, top to bottom; no invented scores:

- `Not fit for purpose` — the confirmed goal is unreachable by this prompt as designed; requires explicit justification in the verdict paragraph
- `Needs rework` — at least one Critical, or Major findings in three or more dimensions
- `Effective with revisions` — at least one Major finding
- `Effective as-is` — no Critical or Major findings; Minors, if any, are listed but do not block using the prompt as-is

**Table hygiene:** excerpts in the findings table truncate to ~10 words plus an ellipsis (full text lives in Finding details); one clause per cell; no inline HTML anywhere. Keep every basis tag visible — a claim without its tag does not ship.

## Step 6 — Rewrite offer (approval gate)

After the report, ask the user — do not just do it:

1. **Rewrite in chat** — produce the full revised prompt in the conversation only.
2. **Rewrite to a file** — state the concrete default path inside this offer (a sibling `<name>.revised.<ext>` when the prompt came from a file) so a single reply can both pick this option and confirm or replace the path. Never overwrite the original. Never write under the plugin's own directory tree. Nothing is written before an explicit path confirmation.
3. **Stop here** — the report stands on its own.

Fold any open language discussion finding (Step 3, Language rules) into this same offer — one ask, not two — and resolve which language the rewrite uses before writing anything.

Rewrite rules:

- Preserve the confirmed intent exactly, and keep the elements the report listed under "Works well". Add no capabilities the user did not ask for.
- Every change must be traceable to a finding ID. After the rewrite, print a **change map**:

```markdown
| Change | Finding | Effect |
|---|---|---|
| Removed duplicated rule block (was L40–52) | F3 | ~12 lines shorter, one canonical statement of the rule |
```

- Keep the prompt's original language unless the user chose otherwise in the language discussion.
- Keep variable placeholders (`{{...}}`-style and similar) intact and un-renamed.

## Step 7 — Close

Print one line: to re-audit the revised prompt, invoke the command again — this plugin is single-pass and stateless.

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.
