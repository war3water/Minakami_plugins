---
name: init-agent-coord
description: Scaffold or upgrade a project's agent-coordination doc layer (AGENTS.md + .agent_works/ + cross-runtime aliases). Also seeds lightweight code-health practices (verification, documented features, deletion care) that keep the codebase maintainable. USER-INVOKED ONLY — execute solely when the user explicitly names this skill ($agent-coord-bootstrap mention in Codex, /agent-coord-bootstrap:init-agent-coord in Claude Code); never auto-trigger from natural-language inference.
disable-model-invocation: true
---

This skill is a thin wrapper around the plugin's canonical runbook so that
Codex CLI (which loads plugin skills, not plugin commands) can execute it.
Claude Code users can equivalently run the plugin-namespaced slash command
`/agent-coord-bootstrap:init-agent-coord`.

**Step 0 — invocation gate.** This action scaffolds or restructures the
project's coordination docs; whether and when to run it is the user's
decision, not yours. Proceed only if the user explicitly invoked this
skill by name in their message. If you arrived here by inferring intent
from conversation, stop and ask: "Run init-agent-coord on this project?"
— and proceed only on an explicit yes.

Then read and execute, exactly and in order, the runbook at:

- Codex CLI: `${PLUGIN_ROOT}/commands/init-agent-coord.md`
- Claude Code: `${CLAUDE_PLUGIN_ROOT}/commands/init-agent-coord.md`

Do not improvise beyond what the runbook specifies.
