# prompt-audit

Audit one prompt's effectiveness for a specific target coding model. You supply the prompt (pasted or by file path) and name the model family it targets; the audit establishes the prompt's goal and success criteria (asking only what it can't read from your request), analyzes the text across eight dimensions, and delivers an evidence-cited report — an honest verdict, a findings table, and the order to apply the fixes in — plus an optional approval-gated rewrite. Works in Claude Code and Codex CLI from the same plugin source (Claude Code surfaces the `/prompt-audit:audit-prompt` slash command; Codex CLI surfaces the same runbook as a plugin skill, since Codex loads skills rather than commands).

`prompt-audit` is fully independent of the other plugins in this marketplace — it shares no content or logic with them, only the repo's packaging conventions.

## What it checks

| # | Dimension |
|---|---|
| D1 | Goal clarity and achievement — is there a definition of done the model can hit? |
| D2 | Token efficiency and streamlining — duplication, filler, and obsolete guidance modern models no longer need stated |
| D3 | Confusion and hallucination triggers — phantom files/tools, undefined jargon, presupposed false facts |
| D4 | Capability limiting — over-constraint, micromanaged steps, stale workarounds for old model weaknesses |
| D5 | Internal consistency — contradictions, colliding rules with no stated priority |
| D6 | Structure, format, and language fit for the target model — judged against a per-family reference file |
| D7 | Context completeness and assumptions — what the model needs but is not given |
| D8 | Robustness and edge handling — failure paths, escape hatches, injection surface in agent prompts |

Per-family knowledge lives in `references/` (`claude-family.md`, `gpt-codex-family.md`, `gemini-family.md`, plus the universal `general.md`, and `agentic.md`, which is read only when the prompt drives a tool-using agent) — durable, family-level guidance only, no version trivia; the test for what belongs there is in `SOURCES.md`. The family files carry the `-family` suffix deliberately: bare `claude.md`/`gemini.md` collide case-insensitively with the `CLAUDE.md`/`GEMINI.md` instruction files those runtimes auto-load. Every model-specific claim in the report carries a basis tag: `[ref: <file> §<section>]`, `[general]`, `[user-stated]`, or `[hypothesis]`.

## Honesty rules

The auditor is a language model reading text — it cannot run your prompt, measure tokens, or A/B test. So the report:

- Counts what the text shows (lines, words, duplicated blocks) and phrases reductions approximately.
- Never invents token counts, percentages, benchmarks, or improvement estimates.
- Tags speculation `[hypothesis]`, Minor by default unless your own observed failures corroborate it. A reference file shows that a tendency exists, not that your prompt triggers it: a finding whose trigger is an input you wouldn't expect stays `[hypothesis]` whatever it cites. A speculative finding rated above Minor is marked `(unverified)` and never sets the verdict on its own; the verdict paragraph names it as the open question that could move the verdict.
- Lists under "Not assessed" what the audit could not check on your prompt, when there is anything.

Verdict scale (no invented scores): `Effective as-is` / `Effective with revisions` / `Needs rework` / `Not fit for purpose`. `Not fit for purpose` is reserved for a design that no stated fix can rescue; severe but fixable defects are `Needs rework`.

**Safeguard refusals.** A prompt under audit that tells the model to write out, transcribe, or trace its internal reasoning in the response can be declined by safeguarded Claude models before the audit starts (refusal category `reasoning_extraction`, observed on Claude Fable 5 and Claude Opus 5.5 with two differently worded prompts on 2026-09-22, with and without this plugin; Claude Opus 4.8 audited them). The runbook cannot report a finding it never gets to run. Passing the prompt by file path does not help: the safeguard also inspects file contents the model reads, and those runs were refused too (2026-09-23). Audit such a prompt on a model without that classifier (Claude Opus 4.8 audited these cases fully), or redact the offending line, run the audit, and add the redacted line back as a finding by hand — the reference files already classify it as harmful for exactly this reason.

## Usage

**User-invoked only.** Whether and when to audit a prompt is your call — the model is never allowed to trigger this on its own (`disable-model-invocation: true` on the Claude Code command and skill; `policy.allow_implicit_invocation: false` in the Codex skill policy).

In any session:

```text
/prompt-audit:audit-prompt    # Claude Code (plugin-namespaced slash command)
$prompt-audit                 # Codex CLI (type $ and pick prompt-audit; also /skills)
```

A second, maintainer-facing command checks whether the vendors' official prompting guidance has moved ahead of the reference files. It lists each vendor's machine-readable page index, so a prompting page for a newly released model is found by listing rather than remembered; verifies and diffs every registered page; and ends with a registry patch ready to paste into `SOURCES.md` (needs a session with web tools; read-only):

```text
/prompt-audit:check-sources   # Claude Code
$prompt-audit  → check-sources  # Codex CLI
```

Then paste the prompt or give its file path. The audit runs in this order:

1. **Acquire** — one prompt per run; mixed files get their prompt region confirmed with you, never guessed.
2. **Contract** — target model family, prompt role, goal and success criteria, usage context, known pain, and the rules you declare deliberate. Anything already in your request is taken as stated; only what the audit had to infer comes back for confirmation. If you can't state the goal, the audit works it out with you first.
3. **Analyze** — the eight dimensions, with the reference files for your target read before the analysis starts. Intent questions that would change a severity or a fix come back to you, batched.
4. **Report** — verdict, what works (quoted), dimensions checked with no findings, a findings table (evidence @ line, mechanism, fix) with detail paragraphs only where a row can't carry it, the order to apply fixes in, and anything not assessed.
5. **Rewrite (optional, gated)** — in chat, or to a file whose exact path you confirm first (default: sibling `<name>.revised.<ext>`; the original is never overwritten). Every change is traceable to a finding ID via a change map.

**Report only / headless.** Say "report only" (or run it through `claude -p`, where no one can answer): intent questions become stated assumptions inside the findings they affect, those findings count as unverified, and the audit ends at the report.

Language: the report is written in your conversation's language; a rewrite keeps the prompt's original language unless the audit surfaced a language trade-off and you chose to switch.

## Design constraints

- **Prompt-only.** No Python engine, no install-time dependencies. The runbook is the entire plugin logic.
- **Single-pass and stateless.** One prompt per invocation; re-audit a revision by invoking again. No background hooks.
- **Read-only by default.** The only file this plugin ever writes is the Step 6 rewrite, at a path you explicitly confirm — never your original, never inside this repo.
- **Dual-runtime.** Identical behavior in Claude Code and Codex CLI.
- **Evidence-honest.** No fabricated metrics; every claim carries its basis tag.

## After it runs

1. Apply the fixes in the reported order — or take the gated rewrite and diff it against your original.
2. Run the audit again on the revised prompt to confirm the findings are resolved; each run is independent.
3. The reference files under `references/` are refreshed by plugin version bumps as model capability evolves — update the plugin to keep the streamlining checks current.

## Maintenance

- **Eval sweep per audit-affecting release.** A standing five-case eval suite regression-tests every version bump that changes `commands/audit-prompt.md` or `references/` content; releases that touch neither (new commands, docs, the source registry) ship on lint + manifest parity alone. The suite: a seeded-defect prompt (must catch known Criticals), a polished prompt (must reach `Effective as-is`), a genuinely clean prompt (guards against manufactured findings), an injection-bait agent prompt (D8 coverage), and a Chinese-language prompt (language-discussion behavior). Fixtures, expected finding classes, and sweep results live in the maintainer's external test workspace — never in this repo — and expectations are kept out of the invocation payloads so the auditor never sees its answer key. Judged runs are pinned to one model per sweep: cross-model verdicts are not comparable (severity calibration differs), so a sweep is only diffable against a baseline made with the same model. An optional mid-tier canary run checks instruction robustness; it is labeled and never counted in the quality baseline.
- **Reference refresh.** The `references/` no-op and anti-pattern lists shift as model capability evolves. Refreshing them is a normal version bump, gated by the same eval sweep — a reference change should visibly move at least one expected finding's basis tag or severity, and regress nothing. **Freshness self-check:** run `/prompt-audit:check-sources` periodically and after any vendor model launch. It lists each family's discovery index from `SOURCES.md` (Anthropic's docs `llms.txt`, the OpenAI Cookbook `registry.yaml`, the Gemini API docs `llms.txt`), diffs the matches against the known pages to surface new, moved, or retired model prompting pages, verifies every registered page against its recorded coverage notes and outline snapshot, and ends with a registry patch. A source moves through `found` → `distilled` (→ `retired`): pasting the patch registers a page as `found`; the refresh release that distills it updates its coverage notes, outline snapshot, status, and last-reviewed date in the same commit. Distill only durable family-level claims — the registry's evergreen test says a claim qualifies when the family-wide page states it or it holds across the family's current model pages; a contradiction between sibling model pages marks it version-specific, and excluded tips are named in the coverage notes so they are not re-raised. Index URLs, match rules, fallbacks, and markdown-variant conventions live in `SOURCES.md` under "Discovery indexes".
- **Codex headless limitation.** `codex exec` (verified on v0.145.0) does not load plugin skills, so this plugin cannot be scripted through Codex — invoke `$prompt-audit` in an interactive `codex` session instead. Claude Code headless works: `claude -p "/prompt-audit:audit-prompt ..."` with the contract answers and "report only" supplied in the message. Always use the namespaced name: current Claude Code versions do not register the bare `/audit-prompt`, and a bare name then reaches the model as plain text with no runbook loaded.
