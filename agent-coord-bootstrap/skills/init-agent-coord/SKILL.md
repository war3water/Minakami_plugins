---
name: init-agent-coord
description: Scaffold or upgrade a project's agent-coordination doc layer (AGENTS.md + .agent_works/ + cross-runtime aliases). Use when the user asks to initialize agent docs, set up AGENTS.md, bootstrap or upgrade agent coordination in a project.
---

This skill is a thin wrapper around the plugin's canonical runbook so that
Codex CLI (which loads plugin skills, not plugin commands) can execute it.
Claude Code users can equivalently run the `/init-agent-coord` slash command.

Read and execute, exactly and in order, the runbook at:

- Codex CLI: `${PLUGIN_ROOT}/commands/init-agent-coord.md`
- Claude Code: `${CLAUDE_PLUGIN_ROOT}/commands/init-agent-coord.md`

Do not improvise beyond what the runbook specifies.
