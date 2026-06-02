# Minakami Plugins

Personal marketplace of cross-runtime plugins for [Claude Code](https://claude.com/claude-code) and [Codex CLI](https://developers.openai.com/codex). One plugin source serves both runtimes.

## Plugins in this marketplace

| Plugin | Purpose |
|---|---|
| `agent-coord-bootstrap` | One-shot scaffold of an agent-coordination doc layer (`AGENTS.md` + `agent_works/` + cross-runtime aliases) in a new project. |

## Install on a new device

### One-command (recommended)

```bash
# POSIX (macOS / Linux / Git Bash on Windows)
curl -fsSL https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.sh | bash
```

```powershell
# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.ps1 | iex
```

The script detects which of Claude Code / Codex CLI you have installed, registers this marketplace with each, and installs every plugin listed above.

### Manual (4 commands, runtime-agnostic)

```bash
claude plugin marketplace add github:war3water/Minakami_plugins
claude plugin install agent-coord-bootstrap@minakami-plugins

codex plugin marketplace add github:war3water/Minakami_plugins
codex plugin install agent-coord-bootstrap
```

## Update

```bash
claude plugin marketplace upgrade
codex plugin marketplace upgrade
```

Then reinstall plugins with `--upgrade` if needed.

## Repository layout

```
.agents/plugins/marketplace.json    Codex canonical
.claude-plugin/marketplace.json     Claude + Codex legacy (duplicate)
install.sh / install.ps1            One-command bootstrap
agent-coord-bootstrap/              Plugin source
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/init-agent-coord.md    Slash command body
    templates/                      Files the command writes into the target project
```

The two `marketplace.json` files and the two `plugin.json` files are **duplicated, not symlinked** — Windows + Git symlinks are unreliable. Edit `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` as canonical; copy the other side before commit (or run `scripts/sync-manifests.sh` if it exists).
