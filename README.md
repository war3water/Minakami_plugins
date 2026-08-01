# Minakami Plugins

Personal marketplace of cross-runtime plugins for [Claude Code](https://claude.com/claude-code) and [Codex CLI](https://developers.openai.com/codex). One plugin source serves both runtimes.

## Plugins in this marketplace

| Plugin | Purpose |
|---|---|
| `agent-coord-bootstrap` | Scaffold or upgrade an agent-coordination doc layer (`AGENTS.md` + `.agent_works/` + cross-runtime aliases). Fresh init for new projects; content-preserving migration for existing ones. Seeds lightweight code-health practices that keep the codebase maintainable. |
| `prompt-audit` | Audit one prompt's effectiveness for a specific target coding model — token efficiency, goal clarity, confusion/hallucination triggers, capability limiting, and more. Evidence-cited findings tables, an honest verdict, prioritized refinement advice, and an optional approval-gated rewrite. |

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

### Manual

```bash
claude plugin marketplace add war3water/Minakami_plugins
claude plugin install agent-coord-bootstrap@minakami-plugins
claude plugin install prompt-audit@minakami-plugins

codex plugin marketplace add war3water/Minakami_plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
codex plugin add prompt-audit@minakami-plugins
```

Note the asymmetry: Claude Code uses `plugin install`, Codex CLI uses `plugin add`. Both take the `<plugin>@<marketplace>` form. The marketplace source is the bare `owner/repo` GitHub shorthand — `github:`-prefixed forms are rejected by both CLIs.

## Update

```bash
# Claude Code: refresh the marketplace, then update the plugins
claude plugin marketplace update minakami-plugins
claude plugin update agent-coord-bootstrap@minakami-plugins
claude plugin update prompt-audit@minakami-plugins

# Codex CLI: refresh the marketplace, then re-add the plugins
codex plugin marketplace upgrade minakami-plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
codex plugin add prompt-audit@minakami-plugins
```

## Known limitation — Codex headless mode

Codex CLI loads plugin skills in interactive sessions only. `codex exec` (verified on v0.145.0) does not load plugin skills at all — regardless of trusted directory or `--skip-git-repo-check` — so a `$<plugin>` invocation in a script falls back to the model improvising without the runbook. Invoke these plugins from an interactive `codex` session; re-test headless support after Codex CLI upgrades. Claude Code headless works normally (`claude -p "/<plugin>:<command> ..."`).

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
prompt-audit/                       Plugin source
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/audit-prompt.md        Slash command runbook (Claude Code surface)
    skills/audit-prompt/            Skill wrapper (Codex surface)
    references/                     Per-model-family durable prompt guidance the audit cites
```

The two `marketplace.json` files and the two `plugin.json` files are **duplicated, not symlinked** — Windows + Git symlinks are unreliable. Edit `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` as canonical, then run `bash scripts/sync-manifests.sh` before committing.

## Release process

- A plugin release bumps that plugin's `version` in four places at once: both of its `plugin.json` copies and its entry in both `marketplace.json` copies (via the canonical-then-sync flow above). `metadata.version` is the marketplace's own release train — bumped only for marketplace-level events (new plugin, installer changes), never for per-plugin releases.
- Ship criteria: `npx markdownlint-cli2 "**/*.md"` clean, manifest pairs in sync, no absolute paths in plugin content.
- `prompt-audit` releases additionally run its five-case eval sweep before shipping — see that plugin's README §Maintenance. Eval fixtures, expectations, and sweep results live in the maintainer's external test workspace, never in this repo.
- The commit log is the changelog: `<type>: v<x.y.z> — <summary>` for releases, scoped conventional style otherwise.
