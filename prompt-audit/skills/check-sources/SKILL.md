---
name: check-sources
description: Check whether the vendors' official prompting guidance has moved ahead of prompt-audit's reference files — lists each vendor's page index to find newly published model prompting pages, diffs every registered page against its recorded coverage and outline, and reports what changed per family, whether a reference-refresh release is warranted, and a ready-to-paste registry patch. Read-only; writes nothing. Runs only when the user invokes it by name ($prompt-audit skills in Codex, /prompt-audit:check-sources in Claude Code).
disable-model-invocation: true
---

This skill carries the plugin's source-check runbook to Codex CLI, which loads plugin skills rather than plugin commands. Claude Code runs the same runbook as `/prompt-audit:check-sources`.

Run it only when the user asked for it by name. If you arrived here by inferring intent, ask "Run check-sources?" and continue only on a yes.

Then read and follow the runbook at `${PLUGIN_ROOT}/commands/check-sources.md` (in Claude Code, `${CLAUDE_PLUGIN_ROOT}/commands/check-sources.md`). The user's instructions in this conversation take precedence over its defaults.
