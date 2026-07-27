---
name: audit-prompt
description: Audit one prompt's effectiveness for a specific target coding model — token efficiency, goal clarity, confusion/hallucination triggers, capability limiting, and more. Evidence-cited findings tables, an honest verdict, prioritized refinement advice, and an optional approval-gated rewrite. USER-INVOKED ONLY — execute solely when the user explicitly names this skill ($prompt-audit mention in Codex, /prompt-audit:audit-prompt in Claude Code); never auto-trigger from natural-language inference.
disable-model-invocation: true
---

This skill is a thin wrapper around the plugin's canonical runbook so that
Codex CLI (which loads plugin skills, not plugin commands) can execute it.
Claude Code users can equivalently run the plugin-namespaced slash command
`/prompt-audit:audit-prompt`.

**Step 0 — invocation gate.** Whether and when to audit a prompt is the
user's decision, not yours. Proceed only if the user explicitly invoked
this skill by name in their message. If you arrived here by inferring
intent from conversation — for example, the user merely complained about
a prompt — stop and ask: "Run audit-prompt on it?" — and proceed only on
an explicit yes.

Then read and execute, exactly and in order, the runbook at:

- Codex CLI: `${PLUGIN_ROOT}/commands/audit-prompt.md`
- Claude Code: `${CLAUDE_PLUGIN_ROOT}/commands/audit-prompt.md`

Do not improvise beyond what the runbook specifies.
