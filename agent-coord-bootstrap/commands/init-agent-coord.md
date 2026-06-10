---
name: init-agent-coord
description: Scaffold or upgrade the agent-coordination doc layer (AGENTS.md + .agent_works/ + cross-runtime aliases) in the current project. Fresh repos get a clean init; existing projects get a content-preserving migration.
---

You are executing `/init-agent-coord` for the `agent-coord-bootstrap` plugin.

Your job: scaffold (or upgrade to) the cross-runtime agent-coordination doc layer in the user's current working directory. Plugin root resolves via `${PLUGIN_ROOT}` (or `${CLAUDE_PLUGIN_ROOT}` as legacy alias). Templates live at `${PLUGIN_ROOT}/templates/`.

Follow the steps below **in order**. Do not skip steps. Do not invent additional files.

---

## Step 1 — Detect project state

Check for existing coordination markers in the current working directory (NOT the plugin root):

- `AGENTS.md`
- `CLAUDE.md`, `GEMINI.md`, `AGENT.md` — note for each whether it is a symlink, a one-line pointer file, or a real file with its own content
- `.agent_works/` or legacy `agent_works/` (directory)
- `.claude/settings.local.json`
- `README.md` (note only — never modified beyond the fresh-init "only if missing" rule)

**If NONE of the markers exist** (README.md alone does not count): this is a fresh project → go to **Mode A — Fresh init**.

**If ANY marker exists**: this is an existing project. Print a short inventory of what was found (one line per marker, with its type), then ask the user to decide. Use `AskUserQuestion` if available:

> This project already has agent-coordination files. How should I proceed?
>
> 1. **Upgrade (recommended)** — I will inventory your existing docs, propose a migration plan that reorganizes them into this plugin's layout, and execute it only after your approval. Unique content and project-specific rules are preserved, never dropped.
> 2. **Pause** — stop now; nothing is written.

If the user picks **Pause**, exit immediately without writing any files. If the user picks **Upgrade**, go to **Mode B — Upgrade**.

---

# Mode A — Fresh init

## Step A2 — Ask five questions

Use `AskUserQuestion` (if available) or plain prose. Collect all answers before doing anything else.

1. **project_name** — kebab-case slug. Default: basename of the current working directory.
2. **runtime_targets** — comma-separated subset of `{claude, codex, gemini, aider}`. Default: `claude, codex`. Determines which alias files get created in Step A4.
3. **layout** — `minimal` or `full`. Default: `full`.
   - `minimal` → only `handoff/current_handoff.md`, `decisions.md`, `coordination/work_queue.md`
   - `full` → also `plans.md` and `project_requirements.md`
4. **permission_profile** — `dev-local`, `dev-network`, or `read-only`. Default: `dev-local`.
5. **symlink_strategy** — `auto` or `pointer-only`. Default: `auto`.
   - `auto` → try real symlinks; on failure (Windows without Developer Mode, etc.) fall back to one-line pointer files
   - `pointer-only` → always write a one-line pointer file

Record the answers. They're referenced by name below as `{{project_name}}`, `{{runtime_targets}}`, etc.

Also resolve **{{date}}** to today's ISO date (e.g. `2026-06-02`).

## Step A3 — Write files from templates

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

## Step A4 — Create cross-runtime alias files

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

Record per-alias which strategy was used (symlink vs pointer) — you'll report this in Step A6.

## Step A5 — Verify portability

Scan every file you created in Steps A3 and A4 for forbidden patterns:

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

## Step A6 — Report

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

---

# Mode B — Upgrade (existing project)

Goal: reorganize the project's existing coordination docs into this plugin's layout **without losing any unique content or project-specific rules**. Hard rules for this entire mode:

- **Never delete unique content.** Anything that has no obvious home goes to `.agent_works/upgrade_parking.md`, flagged in the final report — not dropped.
- **Never overwrite `README.md`.**
- **No writes before the user approves the migration plan (Step B4).**

## Step B1 — Safety gate

Run `git status`. Three cases:

- **Clean working tree** → proceed.
- **Dirty tree** → tell the user: "Your working tree has uncommitted changes. I recommend committing first so the upgrade is a clean, revertable diff." Ask whether to proceed anyway or pause. Respect the answer.
- **Not a git repo** → warn that there is no undo mechanism, recommend `git init` + initial commit first, and ask whether to proceed anyway.

## Step B2 — Inventory and classify

Read each existing coordination artifact found in Step 1. Also check these common locations for coordination-like docs (do not crawl the whole repo): `docs/`, `.github/`, repo root `*.md` files.

Classify every content block (a section, a rule list, a table) into one of three buckets:

1. **matches-plugin-layout** — content that duplicates what the plugin's templates already provide (e.g. a generic "don't commit secrets" rule). The template version wins; the duplicate is dropped from the merged doc (this is the ONLY case where existing text is not carried over, and only because the meaning is preserved by the template).
2. **unique-preserve** — project-specific rules, decisions, status, domain knowledge, custom workflows. These MUST appear in the migrated layout.
3. **conflict** — existing content that contradicts a template rule (e.g. an existing doc says "always work in base environment"). Flag for the user in the migration plan; the user's existing rule wins unless they say otherwise.

Special cases:

- **`CLAUDE.md` (or `GEMINI.md`/`AGENT.md`) is a real file with its own content** → its unique content merges into the new `AGENTS.md`; the file itself then becomes an alias (symlink or pointer).
- **Legacy `agent_works/` (non-dot)** → contents migrate to `.agent_works/`; the old directory is removed only after every file inside has been moved or parked.
- **Existing `.claude/settings.local.json`** → preserved as-is. Optionally offer to append missing safety `deny` entries from the chosen profile template; never remove the user's existing `allow` entries.

## Step B3 — Ask the five questions

Same five questions as Step A2, but pre-fill defaults from the inventory:

- `project_name` — from existing docs if stated, else cwd basename.
- `runtime_targets` — infer from which alias files already exist (e.g. `CLAUDE.md` present → `claude` is a target); default to adding `codex`.
- `layout` — `full` if the project already has plan/requirement docs to migrate, else ask.
- `permission_profile` — if `.claude/settings.local.json` exists, default is `keep-existing` (see B2 special case).
- `symlink_strategy` — `auto`.

## Step B4 — Migration plan (approval gate)

Present a migration plan as a table — every row is one action:

```
| # | Source | Action | Destination |
|---|--------|--------|-------------|
| 1 | CLAUDE.md §"Project rules" (7 unique rules) | merge into | AGENTS.md §1 Hard Rules |
| 2 | CLAUDE.md (file itself, after merge) | convert to alias | pointer → AGENTS.md |
| 3 | docs/handoff_notes.md | move | .agent_works/handoff/current_handoff.md |
| 4 | agent_works/decisions.md (legacy dir) | move | .agent_works/decisions.md |
| 5 | (template) | create | .agent_works/coordination/work_queue.md |
| 6 | CLAUDE.md §"deployment checklist" (no obvious home) | park | .agent_works/upgrade_parking.md |
| ...| | | |
```

List every conflict from B2 explicitly below the table with a recommendation. Then ask the user to approve, amend, or pause. **Do not write anything until approval.**

## Step B5 — Execute

In this order:

1. Build the new `AGENTS.md`: start from `AGENTS.md.tmpl` (with substitutions as in Step A3), then fold every `unique-preserve` block into its best-matching section. Project-specific rules go into §1 Hard Rules or §5 Working Principles as appropriate; domain terms into the Glossary.
2. Create / move the `.agent_works/` files per the approved plan. Existing content fills the same role as the template would (e.g. an existing handoff doc replaces `current_handoff.md.tmpl` content, not the other way around).
3. Write `.agent_works/upgrade_parking.md` if any content was parked, with one section per parked block and a one-line note on where it came from.
4. Convert alias files (per B2 special case) using the Step A4 symlink algorithm — only AFTER their unique content is confirmed merged.
5. Append `.gitignore` entries and create skill pointer dirs as in Step A3.
6. Remove the legacy `agent_works/` directory only if it is now empty.

## Step B6 — Verify and report

Run the Step A5 portability scan over everything written. Then report:

```
agent-coord-bootstrap: upgraded {{project_name}}

Migrated:
  <source> → <destination>     (one line per executed plan row)

Preserved verbatim:
  <files left untouched>

Parked (needs your review):
  .agent_works/upgrade_parking.md — <n> blocks

Conflicts resolved:
  <rule> — kept your existing version / replaced per your choice

Next steps:
  1. Review .agent_works/upgrade_parking.md and re-home or delete each block.
  2. Read the merged AGENTS.md once end-to-end — confirm the folded-in rules read correctly.
  3. Commit the upgrade as a single revertable commit.
```

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.
