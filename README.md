# Minakami Plugins

Personal marketplace of cross-runtime plugins for [Claude Code](https://claude.com/claude-code), [Codex CLI](https://developers.openai.com/codex), Grok Build, and [pi](https://pi.dev). One plugin source serves every runtime.

## Plugins in this marketplace

| Plugin | Purpose |
|---|---|
| `agent-coord-bootstrap` | Scaffold or upgrade an agent-coordination doc layer (`AGENTS.md` + `.agent_works/` + cross-runtime aliases) that Claude Code, Codex CLI, and Gemini CLI all read. Fresh init for new projects; content-preserving migration for existing ones. A second skill, `review-readme`, checks a project's README against best practices for its type and proposes edits traced to the project's files. |
| `prompt-audit` | Audit one prompt's effectiveness for a specific target coding model — token efficiency, goal clarity, confusion/hallucination triggers, capability limiting, and more. Evidence-cited findings tables, an honest verdict, prioritized refinement advice, and an optional approval-gated rewrite. A second command, `check-sources`, lists the vendors' docs indexes to catch newly published model prompting pages and reports when the official guidance has moved ahead of the plugin's reference files. |
| `code-map` | Build an interactive, layered code map of a repository as one local HTML file — architecture overview, module dependency map, algorithm pipeline with typed data flow, and the functions inside each stage. Every node deep-links to your editor with typed inputs/outputs, hotspot flags, search, and notes; every edge cites its source line, and unconfirmed edges are marked inferred. |
| `code-cleanup` | Clean up a codebase so a maintainer can read, debug, and change it, without changing what it does — from one targeted change, to removing dead code and junk, to flattening call paths that jump through needless layers and splitting god functions, to a full overhaul, or a map and plan only. An empty or vague request gets a short survey and one question about the level. Its README lists the tested one-line requests for each need. |
| `decision-brief` | Put every open question of a task on one page a newcomer can answer in one pass: every short name and codename explained in a glossary with its source, then one card per question with plain-words background, a real example, options with what each changes, and a labelled recommendation, plus an Other answer and a note. Select any text to comment; the agent answers in the thread while it reads along, or a read-only headless agent answers on request. When you press I'm done, the agent reads every answer at once, acts, and updates the page. A local page served from 127.0.0.1 in every runtime, or a claude.ai Artifact when you pick one. |

## Install on a new device

### One command (recommended)

```bash
# macOS, Linux, or Git Bash on Windows
curl -fsSL https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.sh | bash
```

```powershell
# Windows PowerShell 5.1 or PowerShell 7
iwr -useb https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.ps1 | iex
```

The installer puts every plugin above into each agent runtime it finds on PATH, and reports any step that failed:

| Runtime | What the installer does |
|---|---|
| Claude Code | registers this marketplace, then installs or updates each plugin |
| Codex CLI | registers this marketplace, then installs or updates each plugin |
| Grok Build | skips each plugin Grok already loads from Claude Code (its Claude compatibility, on by default), and installs or updates the rest from this repository, so no skill loads twice |
| pi | installs or updates this repository as one pi package; its `package.json` points pi at every plugin's skills |

Re-running it brings every plugin to its latest version. It also warns about personal skill folders, such as `~/.claude/skills/code-cleanup`, that share a name with a plugin skill: a runtime may load those instead of the plugin, or both.

To install into some runtimes only, set `MINAKAMI_RUNTIMES` to a comma-separated list of `claude`, `codex`, `grok`, and `pi`:

```bash
curl -fsSL https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.sh | MINAKAMI_RUNTIMES=claude,pi bash
```

```powershell
$env:MINAKAMI_RUNTIMES = 'claude,pi'; iwr -useb https://raw.githubusercontent.com/war3water/Minakami_plugins/main/install.ps1 | iex
```

### Manual

```bash
claude plugin marketplace add war3water/Minakami_plugins
claude plugin install agent-coord-bootstrap@minakami-plugins
claude plugin install prompt-audit@minakami-plugins
claude plugin install code-map@minakami-plugins
claude plugin install code-cleanup@minakami-plugins
claude plugin install decision-brief@minakami-plugins

codex plugin marketplace add war3water/Minakami_plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
codex plugin add prompt-audit@minakami-plugins
codex plugin add code-map@minakami-plugins
codex plugin add code-cleanup@minakami-plugins
codex plugin add decision-brief@minakami-plugins

# Grok Build: only for plugins it doesn't already load from Claude Code
grok plugin install war3water/Minakami_plugins#agent-coord-bootstrap --trust
grok plugin install war3water/Minakami_plugins#prompt-audit --trust
grok plugin install war3water/Minakami_plugins#code-map --trust
grok plugin install war3water/Minakami_plugins#code-cleanup --trust
grok plugin install war3water/Minakami_plugins#decision-brief --trust

# pi: the whole repository is one package
pi install git:github.com/war3water/Minakami_plugins
```

Note the asymmetry: Claude Code uses `plugin install`, Codex CLI uses `plugin add`. Both take the `<plugin>@<marketplace>` form. The marketplace source is the bare `owner/repo` GitHub shorthand — `github:`-prefixed forms are rejected by both CLIs.

## Update

Re-run the one-command installer. By hand:

```bash
# Claude Code: refresh the marketplace, then update the plugins
claude plugin marketplace update minakami-plugins
claude plugin update agent-coord-bootstrap@minakami-plugins
claude plugin update prompt-audit@minakami-plugins
claude plugin update code-map@minakami-plugins
claude plugin update code-cleanup@minakami-plugins
claude plugin update decision-brief@minakami-plugins

# Codex CLI: refresh the marketplace, then re-add the plugins
codex plugin marketplace upgrade minakami-plugins
codex plugin add agent-coord-bootstrap@minakami-plugins
codex plugin add prompt-audit@minakami-plugins
codex plugin add code-map@minakami-plugins
codex plugin add code-cleanup@minakami-plugins
codex plugin add decision-brief@minakami-plugins

# Grok Build: plugins installed into Grok itself
grok plugin update

# pi
pi update git:github.com/war3water/Minakami_plugins
```

## Start a skill

Restart any running session after installing or updating. Each plugin's README describes its skills.

| Runtime | Form | Example |
|---|---|---|
| Claude Code | `/<plugin>:<skill>` | `/code-cleanup:code-cleanup` |
| Codex CLI | type `$` and pick the skill (interactive sessions only, see below) | `$code-cleanup` |
| Grok Build | `/<skill>`, or `/<plugin>:<skill>` when two skills share a name | `/code-cleanup` |
| pi | `/skill:<skill>` | `/skill:code-cleanup` |

## Known limitation — Codex headless mode

Codex CLI loads plugin skills in interactive sessions only. `codex exec` does not load plugin skills at all, regardless of trusted directory or `--skip-git-repo-check`. This was verified on v0.145.0, and re-verified on v0.162.1 (Windows) and v0.163.0 (Linux) on 2026-10-17.

A `$<skill>` mention in a script injects nothing. A capable model may then search the disk and find the skill in the plugin cache, but that is the model improvising its way to the file, not a guarantee. Invoke these plugins from an interactive `codex` session, and re-test headless support after Codex CLI upgrades.

Claude Code headless works normally: `claude -p "/<plugin>:<skill> ..."`.

## Repository layout

```text
.agents/plugins/marketplace.json    Codex canonical
.claude-plugin/marketplace.json     Claude + Codex legacy (duplicate)
package.json                        pi package manifest: loads every <plugin>/skills/ folder
install.sh / install.ps1            One-command installer for Claude Code, Codex CLI, Grok Build, and pi
scripts/sync-manifests.sh           Mirrors the canonical manifests, regenerates the installers' plugin lists, checks registration
.gitattributes                      Keeps shell scripts LF in every checkout
agent-coord-bootstrap/              Plugin source (skills only; one SKILL.md serves every runtime)
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    skills/init-agent-coord/        Scaffold/upgrade runbook; templates/ holds the files it writes into the project
    skills/review-readme/           README review runbook; references/readme-checklist.md is the per-type checklist
    skills/check-templates/         Maintainer skill; SOURCES.md registers each template claim and its source
prompt-audit/                       Plugin source
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/audit-prompt.md        Slash command runbook (Claude Code surface)
    commands/check-sources.md       Maintainer command: checks vendor docs indexes against the references
    skills/audit-prompt/            Skill wrapper (Codex, Grok, and pi surface)
    skills/check-sources/           Skill wrapper (Codex, Grok, and pi surface)
    references/                     Per-model-family durable prompt guidance the audit cites
    SOURCES.md                      Source registry: discovery indexes, registered pages, outline snapshots (read by check-sources)
code-map/                           Plugin source
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/code-map.md            Slash command runbook (Claude Code surface)
    skills/code-map/                Skill wrapper (Codex, Grok, and pi surface)
    references/                     Extraction method, data contract, editor link schemes
    templates/viewer.html           Reference viewer the run fills with data
code-cleanup/                       Plugin source (skills only; one SKILL.md serves every runtime)
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    skills/code-cleanup/            SKILL.md, plus references/ (campaign mode), assets/ (ledger template), scripts/ (helpers)
decision-brief/                     Plugin source (skills only; one SKILL.md serves every runtime)
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    skills/decision-brief/          SKILL.md, references/ (questions.json format), assets/ (page template, example), scripts/brief.py (build, local server with live comments, read-back)
```

The two `marketplace.json` files and the two `plugin.json` files are **duplicated, not symlinked** — Windows + Git symlinks are unreliable. Edit `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` as canonical, then run `bash scripts/sync-manifests.sh` before committing. The script also rewrites the generated plugin and skill lists in both installers, and fails when a plugin folder isn't registered in the marketplace.

## Release process

- **Adding a plugin:** create its folder with `.codex-plugin/plugin.json` and a `skills/` folder, register it in `.agents/plugins/marketplace.json`, and run `bash scripts/sync-manifests.sh`. The installers and the pi package pick it up with no other change.
- **Portable skills:** a skill finds its bundled files relative to its own `SKILL.md`. Where it names `${CLAUDE_PLUGIN_ROOT}` or `${PLUGIN_ROOT}`, it also says how to find the plugin root without them, because Grok Build and pi define neither.
- **Versions:** a plugin release bumps that plugin's `version` in four places at once: both of its `plugin.json` copies and its entry in both `marketplace.json` copies (via the canonical-then-sync flow above). `metadata.version` is the marketplace's own release train — bumped only for marketplace-level events (new plugin, installer changes), never for per-plugin releases.
- **Ship criteria:** `npx markdownlint-cli2 "**/*.md"` clean, `bash scripts/sync-manifests.sh` passes, no absolute paths in plugin content.
- `prompt-audit` releases that change its audit runbook or `references/` content additionally run its five-case eval sweep before shipping — see that plugin's README §Maintenance. Eval fixtures, expectations, and sweep results live in the maintainer's external test workspace, never in this repo. Its `/prompt-audit:check-sources` command lists the vendors' docs indexes for new model prompting pages, reports when the official guidance has moved ahead of the reference files, and emits the `SOURCES.md` patch a refresh release starts from.
- The commit log is the changelog: `<type>: v<x.y.z> — <summary>` for releases, scoped conventional style otherwise.
