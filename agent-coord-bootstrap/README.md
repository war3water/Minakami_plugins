# agent-coord-bootstrap

One-shot scaffolding for the agent-coordination doc layer in a new project. Works in Claude Code and Codex CLI from the same plugin source.

## What it creates

```
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
    ├── decisions.md
    ├── plans.md
    ├── project_requirements.md
    ├── handoff/current_handoff.md
    └── coordination/work_queue.md
```

## Usage

In any fresh project root:

```
/init-agent-coord
```

You'll be asked five questions (project name, runtime targets, layout, permission profile, symlink strategy). All have sensible defaults.

### Existing projects — upgrade mode

If the project already has coordination files (`AGENTS.md`, `.agent_works/`, a content-bearing `CLAUDE.md`, etc.), the command does not refuse and does not silently overwrite. It inventories what exists and asks you to choose:

1. **Upgrade (recommended)** — it classifies your existing docs (template-duplicate / unique / conflicting), proposes a migration plan as a source→destination table, and executes only after your approval. Unique rules merge into the new `AGENTS.md`; content with no obvious home is parked in `.agent_works/upgrade_parking.md` for your review — never dropped. A divergent `CLAUDE.md` becomes an alias only after its unique content is merged.
2. **Pause** — nothing is written.

So the plugin serves both ends: initializing a fresh repo, and refactoring an existing project into an agent-ready handoff structure.

## Design constraints

- **Run-once per project.** Bootstrap/upgrade is per-project, not per-session. No background hooks, no session-start checks.
- **Prompt-only.** No Python engine, no install-time dependencies. The slash command is the entire plugin logic.
- **Portable.** No drive letters, no `~`, no absolute paths in any scaffolded file. Aliases use relative symlink targets or bare-filename pointer files.
- **Dual-runtime.** Identical behavior in Claude Code and Codex CLI.

## After it runs

1. Fill in `.agent_works/project_requirements.md` with your product north star.
2. Read `AGENTS.md` once — it's the routing doc both you and any agent will consult.
3. Add real tickets to `.agent_works/coordination/work_queue.md` as work surfaces.
