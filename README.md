# Minakami Plugins

Personal marketplace of cross-runtime plugins for [Claude Code](https://claude.com/claude-code) and [Codex CLI](https://developers.openai.com/codex). One plugin source serves both runtimes.

## Plugins in this marketplace

| Plugin | Purpose |
|---|---|
| `agent-coord-bootstrap` | Scaffold or upgrade an agent-coordination doc layer (`AGENTS.md` + `.agent_works/` + cross-runtime aliases). Fresh init for new projects; content-preserving migration for existing ones. Seeds lightweight code-health practices that keep the codebase maintainable. |

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

The script detects which of Claude Code / Codex CLI you have installed, registers this marketplace with each, installs every plugin listed above, and reports any step that failed.

### Manual (4 commands)

```bash
claude plugin marketplace add war3water/Minakami_plugins
claude plugin install agent-coord-bootstrap@minakami-plugins

codex plugin marketplace add war3water/Minakami_plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
```

Note the asymmetry: Claude Code uses `plugin install`, Codex CLI uses `plugin add`. Both take the `<plugin>@<marketplace>` form. The marketplace source is the bare `owner/repo` GitHub shorthand — `github:`-prefixed forms are rejected by both CLIs.

## Update

```bash
# Claude Code: refresh the marketplace, then update the plugin
claude plugin marketplace update minakami-plugins
claude plugin update agent-coord-bootstrap@minakami-plugins

# Codex CLI: refresh the marketplace, then re-add the plugin
codex plugin marketplace upgrade minakami-plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
```

## Repository layout

```text
.agents/plugins/marketplace.json    Codex canonical
.claude-plugin/marketplace.json     Claude + Codex legacy (duplicate)
install.sh / install.ps1            One-command bootstrap
scripts/sync-manifests.sh           Copy canonical manifests over mirrors + parity check
agent-coord-bootstrap/              Plugin source
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/init-agent-coord.md    Slash command runbook (Claude Code surface)
    skills/init-agent-coord/        Skill wrapper (Codex surface; Codex loads plugin skills, not commands)
    templates/                      Files the command writes into the target project
```

The two `marketplace.json` files and the two `plugin.json` files are **duplicated, not symlinked** — Windows + Git symlinks are unreliable. Edit `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` as canonical, then run `bash scripts/sync-manifests.sh` before committing.
