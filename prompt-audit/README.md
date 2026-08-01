# prompt-audit

Audit one prompt's effectiveness for a specific target coding model. You supply the prompt (pasted or by file path) and name the model family it targets; the audit interviews you for the prompt's goal and success criteria, analyzes the text across eight fixed dimensions, and delivers an evidence-cited report — findings tables, an honest verdict, prioritized refinement advice — plus an optional approval-gated rewrite. Works in Claude Code and Codex CLI from the same plugin source (Claude Code surfaces the `/prompt-audit:audit-prompt` slash command; Codex CLI surfaces the same runbook as a plugin skill, since Codex loads skills rather than commands).

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

Per-family knowledge lives in `references/` (`claude-family.md`, `gpt-codex-family.md`, `gemini-family.md`, plus the universal `general.md`) — durable, family-level guidance only, no version trivia. The family files carry the `-family` suffix deliberately: bare `claude.md`/`gemini.md` collide case-insensitively with the `CLAUDE.md`/`GEMINI.md` instruction files those runtimes auto-load. Every model-specific claim in the report carries a basis tag: `[ref: <file> §<section>]`, `[general]`, `[user-stated]`, or `[hypothesis]`.

## Honesty rules

The auditor is a language model reading text — it cannot run your prompt, measure tokens, or A/B test. So the report:

- MAY count what the text shows (lines, words, duplicated blocks) and phrase reductions approximately.
- May NOT invent token counts, percentages, benchmarks, or improvement estimates.
- Tags speculation `[hypothesis]`, capped at Minor severity unless your own observed failures corroborate it.
- Ends with a "Not assessed" section stating what the audit could not check.

Verdict scale (no invented scores): `Effective as-is` / `Effective with revisions` / `Needs rework` / `Not fit for purpose`.

## Usage

**User-invoked only.** Whether and when to audit a prompt is your call — the model is never allowed to trigger this on its own (`disable-model-invocation: true` on the Claude Code command and skill; `policy.allow_implicit_invocation: false` in the Codex skill policy).

In any session:

```text
/prompt-audit:audit-prompt    # Claude Code (plugin-namespaced slash command)
$prompt-audit                 # Codex CLI (type $ and pick prompt-audit; also /skills)
```

Then paste the prompt or give its file path. The audit runs in this order:

1. **Acquire** — one prompt per run; mixed files get their prompt region confirmed with you, never guessed.
2. **Interview** — target model family, prompt role, intended goal and success criteria, usage context, known pain. A short audit contract is confirmed before any analysis. If you cannot state the goal, the audit stops and works it out with you first.
3. **Analyze** — the eight dimensions, against the loaded reference files.
4. **Clarify** — ambiguous-intent excerpts come back as batched questions instead of guessed findings.
5. **Report** — dimension summary table, findings table (evidence @ line, mechanism, fix), finding details, prioritized advice, "Not assessed".
6. **Rewrite (optional, gated)** — in chat, or to a file whose exact path you confirm first (default: sibling `<name>.revised.<ext>`; the original is never overwritten). Every change is traceable to a finding ID via a change map table.

Language: the report is written in your conversation's language; a rewrite keeps the prompt's original language unless the audit surfaced a language trade-off and you chose to switch.

## Design constraints

- **Prompt-only.** No Python engine, no install-time dependencies. The runbook is the entire plugin logic.
- **Single-pass and stateless.** One prompt per invocation; re-audit a revision by invoking again. No background hooks.
- **Read-only by default.** The only file this plugin ever writes is the Step 6 rewrite, at a path you explicitly confirm — never your original, never inside this repo.
- **Dual-runtime.** Identical behavior in Claude Code and Codex CLI.
- **Evidence-honest.** No fabricated metrics; every claim carries its basis tag.

## After it runs

1. Apply the prioritized advice — or take the gated rewrite and diff it against your original.
2. Re-invoke the command on the revised prompt to verify the findings are resolved.
3. The reference files under `references/` are refreshed by plugin version bumps as model capability evolves — update the plugin to keep the streamlining checks current.

## Maintenance

- **Eval sweep per release.** A standing five-case eval suite regression-tests every version bump: a seeded-defect prompt (must catch known Criticals), a polished prompt (must reach `Effective as-is`), a genuinely clean prompt (guards against manufactured findings), an injection-bait agent prompt (D8 coverage), and a Chinese-language prompt (language-discussion behavior). Fixtures, expected finding classes, and sweep results live in the maintainer's external test workspace — never in this repo — and expectations are kept out of the invocation payloads so the auditor never sees its answer key. Judged runs are pinned to one model per sweep: cross-model verdicts are not comparable (severity calibration differs), so a sweep is only diffable against a baseline made with the same model. An optional mid-tier canary run checks instruction robustness; it is labeled and never counted in the quality baseline.
- **Reference refresh.** The `references/` no-op and anti-pattern lists shift as model capability evolves. Refreshing them is a normal version bump, gated by the same eval sweep — a reference change should visibly move at least one expected finding's basis tag or severity, and regress nothing. Refresh from the vendors' official prompting guides, distilling only durable family-level claims (version-specific tips stay out, per the reference files' evergreen contract):
  - Claude family — Anthropic's [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) plus per-model pages such as [prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)
  - GPT–Codex family — OpenAI's [GPT-5 prompting guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) and successor guides in the [Cookbook](https://cookbook.openai.com/)
  - Gemini family — Google's [prompt design strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- **Codex headless limitation.** `codex exec` (verified on v0.145.0) does not load plugin skills, so this plugin cannot be scripted through Codex — invoke `$prompt-audit` in an interactive `codex` session instead. Claude Code headless works: `claude -p "/prompt-audit:audit-prompt ..."` with the interview answers supplied in the message (the zero-hop fast path).
