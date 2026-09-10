---
name: code-map
description: Build an interactive, layered code map of the current repository as a local HTML file — architecture overview, module dependency map, algorithm pipeline with typed data flow, and the functions inside each stage — every node deep-linked to the editor, with typed inputs/outputs, hotspot flags, search, and per-node notes. USER-INVOKED ONLY — execute solely when the user explicitly names this skill ($code-map mention in Codex, /code-map:code-map in Claude Code); never auto-trigger from natural-language inference.
disable-model-invocation: true
---

This skill is a thin wrapper around the plugin's canonical runbook so that
Codex CLI (which loads plugin skills, not plugin commands) can execute it.
Claude Code users can equivalently run the plugin-namespaced slash command
`/code-map:code-map`.

**Step 0 — invocation gate.** This action reads the whole repository in
scope and writes a file into it; whether and when to run it is the user's
decision, not yours. Proceed only if the user explicitly invoked this skill
by name in their message. If you arrived here by inferring intent from
conversation — for example, the user merely asked how some code fits
together — stop and ask: "Run code-map on this repository?" — and proceed
only on an explicit yes.

Then read and execute, exactly and in order, the runbook at:

- Codex CLI: `${PLUGIN_ROOT}/commands/code-map.md`
- Claude Code: `${CLAUDE_PLUGIN_ROOT}/commands/code-map.md`

Do not improvise beyond what the runbook specifies.
