---
name: init-agent-coord
description: Scaffold the agent-coordination doc layer (AGENTS.md + .agent_works/ + cross-runtime aliases) in the current project. One-shot per project.
---

You are executing `/init-agent-coord` for the `agent-coord-bootstrap` plugin.

Your job: scaffold the cross-runtime agent-coordination doc layer in the user's current working directory. Plugin root resolves via `${PLUGIN_ROOT}` (or `${CLAUDE_PLUGIN_ROOT}` as legacy alias). Templates live at `${PLUGIN_ROOT}/templates/`.

Follow the steps below **in order**. Do not skip steps. Do not invent additional files.

---

## Step 1 — Refuse if already initialized

Check whether any of these exist in the current working directory (NOT the plugin root):

- `AGENTS.md`
- `.agent_works/` (directory)
- `.claude/settings.local.json`

If **any** of these exist, STOP immediately. Print:

```
Already initialized. Found:
  - <list each marker that exists>
Re-running would risk overwriting your edits. To re-init, manually delete the markers above first.
```

Then exit. Do not write any files.

---

## Step 2 — Ask five questions

Use `AskUserQuestion` (if available) or plain prose. Collect all answers before doing anything else.

1. **project_name** — kebab-case slug. Default: basename of the current working directory.
2. **runtime_targets** — comma-separated subset of `{claude, codex, gemini, aider}`. Default: `claude, codex`. Determines which alias files get created in Step 4.
3. **layout** — `minimal` or `full`. Default: `full`.
   - `minimal` → only `handoff/current_handoff.md`, `decisions.md`, `coordination/work_queue.md`
   - `full` → also `plans.md` and `project_requirements.md`
4. **permission_profile** — `dev-local`, `dev-network`, or `read-only`. Default: `dev-local`.
5. **symlink_strategy** — `auto` or `pointer-only`. Default: `auto`.
   - `auto` → try real symlinks; on failure (Windows without Developer Mode, etc.) fall back to one-line pointer files
   - `pointer-only` → always write a one-line pointer file

Record the answers. They're referenced by name below as `{{project_name}}`, `{{runtime_targets}}`, etc.

Also resolve **{{date}}** to today's ISO date (e.g. `2026-05-19`).

---

## Step 3 — Write files from templates

For each template at `${PLUGIN_ROOT}/templates/<src>`, read the file, perform string substitution on the placeholders, and write it to the corresponding target path under the user's cwd.

Substitutions: `{{project_name}}` → answer 1; `{{date}}` → today's ISO date. No other substitutions exist.

### Always create:

| Template source | Target path |
|---|---|
| `AGENTS.md.tmpl` | `AGENTS.md` |
| `.agent_works/decisions.md.tmpl` | `.agent_works/decisions.md` |
| `.agent_works/handoff/current_handoff.md.tmpl` | `.agent_works/handoff/current_handoff.md` |
| `.agent_works/coordination/work_queue.md.tmpl` | `.agent_works/coordination/work_queue.md` |

### If `layout == full`, also create:

| Template source | Target path |
|---|---|
| `.agent_works/plans.md.tmpl` | `.agent_works/plans.md` |
| `.agent_works/project_requirements.md.tmpl` | `.agent_works/project_requirements.md` |

### Permission profile — pick exactly one:

| Profile | Template source | Target path |
|---|---|---|
| `dev-local` | `settings.local.json.dev-local.tmpl` | `.claude/settings.local.json` |
| `dev-network` | `settings.local.json.dev-network.tmpl` | `.claude/settings.local.json` |
| `read-only` | `settings.local.json.read-only.tmpl` | `.claude/settings.local.json` |

### README.md — only if missing

If `README.md` does NOT exist in the cwd, write `README.md.tmpl` → `README.md`. If it exists, leave it alone — do not overwrite the user's README.

### .gitignore — append, don't replace

Read `${PLUGIN_ROOT}/templates/gitignore.tmpl`. If `.gitignore` exists in the cwd, append the template content (skip lines already present). If `.gitignore` does not exist, write the template content as the new file.

### Skill pointer directories — empty

- Always create `.claude/skills/` with an empty `.gitkeep` file inside.
- If `codex` is in `{{runtime_targets}}`, also create `.agent/skills/` with an empty `.gitkeep` file inside.

---

## Step 4 — Create cross-runtime alias files

For each runtime in `{{runtime_targets}}` (excluding the canonical `AGENTS.md` itself), create the corresponding alias in the cwd root:

| Runtime | Alias filename |
|---|---|
| `claude` | `CLAUDE.md` |
| `gemini` | `GEMINI.md` |
| `aider` | `AGENT.md` |

(Codex reads `AGENTS.md` directly — no alias needed.)

### Symlink creation algorithm

If `{{symlink_strategy}} == auto`:

1. **Detect OS.**
2. **POSIX (Linux / macOS):** run `ln -s AGENTS.md <alias>`. Target must be the **bare filename** `AGENTS.md` (relative, same directory), never an absolute path.
3. **Windows:** run `cmd /c mklink <alias> AGENTS.md`. If exit code is non-zero (Developer Mode off or insufficient privilege), fall back to pointer file.
4. **Pointer file fallback:** write a file at `<alias>` containing exactly the literal text `AGENTS.md` followed by a single newline. Nothing else.

If `{{symlink_strategy}} == pointer-only`:

- Skip the symlink attempt entirely. Always write the pointer file as described above.

Record per-alias which strategy was used (symlink vs pointer) — you'll report this in Step 6.

---

## Step 5 — Verify portability

Scan every file you created in Steps 3 and 4 for forbidden patterns:

- Windows drive letters: `[A-Za-z]:\\`
- POSIX home expansions: `/Users/`, `/home/`, `~/`
- Windows home expansions: `%USERPROFILE%`, `$HOME`

Files to scan: `AGENTS.md`, `README.md` (if created), everything under `.agent_works/`, `.claude/settings.local.json`.

If any match is found and it is NOT inside a clearly-marked "DO NOT do this" example block, STOP and report:

```
Portability check failed:
  <file>:<line>: <matched pattern>
The template should not contain absolute paths. This is a plugin bug — report at https://github.com/war3water/Minakami_plugins/issues.
```

---

## Step 6 — Report

Print a single-screen summary:

```
agent-coord-bootstrap: initialized {{project_name}}

Created files:
  AGENTS.md                                    (canonical)
  <list each created file>

Cross-runtime aliases:
  CLAUDE.md      symlink → AGENTS.md           (or "pointer file")
  GEMINI.md      <as appropriate>
  AGENT.md       <as appropriate>

Permission profile: {{permission_profile}}
Layout: {{layout}}

Next steps:
  1. Fill in .agent_works/project_requirements.md with your product north star.
  2. Read AGENTS.md — it's the routing doc every agent will consult.
  3. Add real tickets to .agent_works/coordination/work_queue.md as work surfaces.
```

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.
