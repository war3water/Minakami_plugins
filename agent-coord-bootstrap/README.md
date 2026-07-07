# agent-coord-bootstrap

Scaffold or upgrade the agent-coordination doc layer — fresh init for new projects, content-preserving migration for existing ones. Works in Claude Code and Codex CLI from the same plugin source (Claude Code surfaces the `/init-agent-coord` slash command; Codex CLI surfaces the same runbook as a plugin skill, since Codex loads skills rather than commands). Beyond coordination, the scaffold seeds lightweight code-health practices that keep the codebase from decaying into a cleanup project.

## What it creates

```text
<your-project>/
├── AGENTS.md                              ← canonical routing + hard rules (~150 lines)
├── CLAUDE.md                              ← symlink or one-line pointer → AGENTS.md
├── GEMINI.md                              ← (if gemini target selected)
├── AGENT.md                               ← (if aider target selected)
├── README.md                              ← human onboarding stub (only if missing)
├── .gitignore                             ← appends .local/ and friends
├── .claude/settings.local.json            ← permission allowlist (chosen profile)
├── .claude/skills/.gitkeep                ← skill pointer dir
├── .agent/skills/.gitkeep                 ← Codex skill pointer dir (if codex target)
└── .agent_works/
    ├── conventions.md                     ← elaboration + examples, one hop from AGENTS.md
    ├── decisions.md                        ← full layout only; lean creates on first need
    ├── plans.md                            ← full layout only; lean creates on first need
    ├── project_requirements.md             ← full layout only; lean creates on first need
    ├── handoff/current_handoff.md          ← full layout only; lean creates on first need
    └── coordination/work_queue.md          ← full layout only; lean creates on first need
```

**Layout: `lean` (default) or `full`.** `lean` scaffolds only the prevention layer — `AGENTS.md`, the
README, and `conventions.md` — and lets the five process docs be born on first need from the routing table
in `AGENTS.md`. `full` writes them all upfront for an established or multi-agent project. The prevention
value (behavior nets, documented features, deletion care) lives in `AGENTS.md` + README and is identical in
both; the process docs are coordination scaffolding, so a new project starts clean and grows into them.

## Usage

**User-invoked only.** Scaffolding or restructuring a project's coordination docs is the user's call — the model is never allowed to trigger this on its own (`disable-model-invocation: true` on the Claude Code command and skill; `policy.allow_implicit_invocation: false` in the Codex skill policy).

In any project root:

```text
/agent-coord-bootstrap:init-agent-coord    # Claude Code (plugin-namespaced slash command)
$agent-coord-bootstrap                     # Codex CLI (type $ and pick agent-coord-bootstrap; also /skills)
```

You'll be asked five questions (project name, runtime targets, layout, permission profile, symlink strategy). All have sensible defaults — `layout` defaults to `lean` (see below).

### Existing projects — upgrade mode

If the project already has coordination files (`AGENTS.md`, `.agent_works/`, a content-bearing `CLAUDE.md`, etc.), the command does not refuse and does not silently overwrite. It inventories what exists and asks you to choose:

1. **Upgrade (recommended)** — it classifies your existing docs (template-duplicate / unique / conflicting), proposes a migration plan as a source→destination table, and executes only after your approval. Unique rules merge into the new `AGENTS.md`; content with no obvious home is parked in `.agent_works/upgrade_parking.md` for your review — never dropped. A divergent `CLAUDE.md` becomes an alias only after its unique content is merged.
2. **Pause** — nothing is written.

So the plugin serves both ends: initializing a fresh repo, and refactoring an existing project into an agent-ready handoff structure.

## What it seeds against decay

The scaffolded docs carry preventive counterparts of the repair rules in the companion `/code-cleanup` skill,
each backed by its measured evals (iterations 1–8, 2026-07):

- **Verification pins behavior** — a feature is done when a runnable check pins it, listed in README `### Verify`.
  Measured: with a stated net, 6/6 liveness traps survived cleanup agents; without one, an outward shim was deleted 3/3.
- **Documented features survive** — every real capability, dormant ones included, is listed in README `## Features`.
  Measured: a README-documented dormant capability was kept 3/3 by bare agents; its undocumented twin deleted 3/3.
- **Deletion care** — check README/docs/configs before deleting or renaming anything public-facing.
  Measured: this mechanical check bound agent behavior where prose warnings did not.
- **Indirection, duplication, dumping grounds** — layers must earn their existence; extend, don't fork; one
  nameable responsibility per module. From the repair skill's gates (agents over-produce indirection; duplicates drift).
- **Restore hatch** — no edits on an untracked tree. Measured: bare agents on untracked trees produced no real restore path.

Binding one-liners live inline in `AGENTS.md` (rules bind at the decision site); elaboration sits one hop away
in `conventions.md`; the evidence stays here, out of your repo.

## Design constraints

- **Run-once per project.** Bootstrap/upgrade is per-project, not per-session. No background hooks, no session-start checks.
- **Prompt-only.** No Python engine, no install-time dependencies. The slash command is the entire plugin logic.
- **Portable.** No drive letters, no `~`, no absolute paths in any scaffolded file. Aliases use relative symlink targets or bare-filename pointer files.
- **Dual-runtime.** Identical behavior in Claude Code and Codex CLI.

## After it runs

1. Fill in `.agent_works/project_requirements.md` with your product north star.
2. Read `AGENTS.md` once — it's the routing doc both you and any agent will consult.
3. Add real tickets to `.agent_works/coordination/work_queue.md` as work surfaces.
4. Put your real test/smoke commands in README `### Verify` and your capabilities in `## Features`.
