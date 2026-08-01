---
name: check-sources
description: Check whether the vendors' official prompting guides have changed since prompt-audit's reference files were last refreshed — reports what changed per family and whether a reference-refresh release is warranted. Read-only; writes nothing. USER-INVOKED ONLY — execute solely when the user explicitly names this skill ($prompt-audit skills in Codex, /prompt-audit:check-sources in Claude Code); never auto-trigger from natural-language inference.
disable-model-invocation: true
---

This skill is a thin wrapper around the plugin's canonical runbook so that
Codex CLI (which loads plugin skills, not plugin commands) can execute it.
Claude Code users can equivalently run the plugin-namespaced slash command
`/prompt-audit:check-sources`.

**Step 0 — invocation gate.** Whether and when to check reference
freshness is the user's decision, not yours. Proceed only if the user
explicitly invoked this skill by name in their message. If you arrived
here by inferring intent from conversation, stop and ask: "Run
check-sources?" — and proceed only on an explicit yes.

Then read and execute, exactly and in order, the runbook at:

- Codex CLI: `${PLUGIN_ROOT}/commands/check-sources.md`
- Claude Code: `${CLAUDE_PLUGIN_ROOT}/commands/check-sources.md`

Do not improvise beyond what the runbook specifies.
