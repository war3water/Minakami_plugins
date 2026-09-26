---
name: audit-prompt
description: Audit one prompt's effectiveness for a specific target coding model — token efficiency, goal clarity, confusion/hallucination triggers, capability limiting, and more. Evidence-cited findings, an honest verdict, prioritized fixes, and an optional approval-gated rewrite. Runs only when the user invokes it by name ($prompt-audit in Codex, /prompt-audit:audit-prompt in Claude Code).
disable-model-invocation: true
---

This skill carries the plugin's audit runbook to Codex CLI, which loads plugin skills rather than plugin commands. Claude Code runs the same runbook as `/prompt-audit:audit-prompt`.

Run it only when the user asked for it by name. If you arrived here by inferring intent — say, the user complained about a prompt — ask "Run audit-prompt on it?" and continue only on a yes.

Then read and follow the runbook at `${PLUGIN_ROOT}/commands/audit-prompt.md` (in Claude Code, `${CLAUDE_PLUGIN_ROOT}/commands/audit-prompt.md`). The user's instructions in this conversation — for example, report only — take precedence over its defaults.
