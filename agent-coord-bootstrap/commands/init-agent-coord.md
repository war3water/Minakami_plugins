---
name: init-agent-coord
description: Scaffold or upgrade the agent-coordination doc layer (AGENTS.md + .agent_works/ + cross-runtime aliases) in the current project. Fresh repos get a clean init; existing projects get a content-preserving migration. Also seeds lightweight code-health practices (verification, documented features, deletion care) that keep the codebase maintainable. User-invoked only.
disable-model-invocation: true
---

You are executing `/init-agent-coord` for the `agent-coord-bootstrap` plugin.

Your job: scaffold (or upgrade to) the cross-runtime agent-coordination doc layer in the user's current working directory. Plugin root: in Claude Code it is `${CLAUDE_PLUGIN_ROOT}`; in Codex CLI it is `${PLUGIN_ROOT}` — use whichever your runtime defines. Templates live at `<plugin-root>/templates/`.

Follow the steps below **in order**. Do not skip steps. Do not invent additional files.

---

## Step 1 — Detect project state

Check for existing coordination markers in the current working directory (NOT the plugin root):

- `AGENTS.md` — note whether it is a **symlink**, a **one-line pointer file** (a single line `@AGENTS.md`-style import or a bare filename), or a **real file** with its own content
- `CLAUDE.md`, `GEMINI.md`, `AGENT.md` — same three-way type note for each
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
3. **layout** — `lean` or `full`. Default: `lean`.
   - `lean` → creates `AGENTS.md` + `.agent_works/conventions.md` and the README only. The five process
     docs (`decisions.md`, `plans.md`, `project_requirements.md`, `handoff/current_handoff.md`,
     `coordination/work_queue.md`) are **not** created now — they are born on first need from the routing
     table in `AGENTS.md`. Right for a new or small project: the prevention layer (AGENTS.md + README) is
     fully present; process ceremony waits until the project earns it.
   - `full` → also creates all five process docs upfront. Right for an established or multi-agent project
     that will use the coordination structure immediately.
4. **permission_profile** — `dev-local`, `dev-network`, or `read-only`. Default: `dev-local`. Asked only when `claude` is in `runtime_targets` — without a Claude Code target no `.claude/` artifacts are created and this question is skipped.
5. **symlink_strategy** — `auto` or `pointer-only`. Default: `auto`.
   - `auto` → try real symlinks; on failure (Windows without Developer Mode, etc.) fall back to one-line pointer files
   - `pointer-only` → always write a one-line pointer file

Record the answers. They're referenced by name below as `{{project_name}}`, `{{runtime_targets}}`, etc.

Also resolve **{{date}}** to today's ISO date (e.g. `2026-06-02`).

## Step A2.5 — Inspect before writing

If the directory already contains code, read its build/test manifests
(e.g. `package.json`, `pyproject.toml`, `Makefile`) and note the real
install / run / test commands. Use them in Step A3 in place of the
README template's placeholder commands, and resolve **{{initial_state}}**
to a one-line factual summary (e.g. "existing codebase — Node CLI, 9
source files"). Fill only what inspection supports: README template
sections that don't apply (env vars, debug table, project structure) are
deleted or kept as clearly-marked placeholders — never asserted as fact.
An empty or docs-only directory keeps the placeholders and resolves
{{initial_state}} to "fresh project — no work started".

## Step A2.6 — Version-control gate (only when code is present)

If the directory contains code but is not a git repository (or has
uncommitted changes), pause and recommend `git init` + a baseline commit
first — the same rule the scaffold itself seeds (AGENTS.md §1 rule 4).
Ask whether to proceed anyway; respect the answer. An empty directory
skips this gate.

## Step A3 — Write files from templates

For each template at `<plugin-root>/templates/<src>`, read the file, perform string substitution on the placeholders, and write it to the corresponding target path under the user's cwd.

Substitutions: `{{project_name}}` → answer 1; `{{date}}` → today's ISO date; `{{initial_state}}` → the Step A2.5 summary (handoff template only). No other substitutions exist.

**Do NOT write `.claude/settings.local.json` in this step** — the permission profile is written last (Step A6), so a restrictive profile (e.g. `read-only`, which denies the Write/Edit tools) cannot lock out the remainder of the scaffold.

### Always create (both layouts):

| Template source | Target path |
|---|---|
| `AGENTS.md.tmpl` | `AGENTS.md` |
| `.agent_works/conventions.md.tmpl` | `.agent_works/conventions.md` |

### If `layout == full`, also create (lean defers all five to first need):

| Template source | Target path |
|---|---|
| `.agent_works/decisions.md.tmpl` | `.agent_works/decisions.md` |
| `.agent_works/handoff/current_handoff.md.tmpl` | `.agent_works/handoff/current_handoff.md` |
| `.agent_works/coordination/work_queue.md.tmpl` | `.agent_works/coordination/work_queue.md` |
| `.agent_works/plans.md.tmpl` | `.agent_works/plans.md` |
| `.agent_works/project_requirements.md.tmpl` | `.agent_works/project_requirements.md` |

Under `lean`, a later agent creates any of these five the first time it needs to write that kind of
content, following its routing-table row in `AGENTS.md` — the row carries the path and the file's shape;
the plugin's templates are NOT assumed available after bootstrap. This is the plugin's own "grow on need"
principle applied to itself.

### README.md — only if missing

If `README.md` does NOT exist in the cwd, write `README.md.tmpl` → `README.md`, substituting any real commands found in Step A2.5 for the placeholder commands. If it exists, leave it alone — do not overwrite the user's README; instead suggest in the Step A7 report adding `## Features` and `### Verify` sections (see the template for their shape).

### .gitignore — append, don't replace

Read `<plugin-root>/templates/gitignore.tmpl`. If `.gitignore` exists in the cwd, append the template content (skip lines already present). If `.gitignore` does not exist, write the template content as the new file. Omit the `.claude/settings.local.json` line when `claude` is not in `{{runtime_targets}}`. If `.gitignore` is a symlink, do not append through it — flag it and ask.

### Skill pointer directories — empty

- If `claude` is in `{{runtime_targets}}`, create `.claude/skills/` with an empty `.gitkeep` file inside.
- If `codex` is in `{{runtime_targets}}`, also create `.agent/skills/` with an empty `.gitkeep` file inside.

## Step A4 — Create cross-runtime alias files

For each runtime in `{{runtime_targets}}`, wire up its access mechanism in the cwd root:

| Runtime | Mechanism |
|---|---|
| `claude` | `CLAUDE.md` alias — symlink or `@AGENTS.md` pointer |
| `gemini` | `GEMINI.md` alias — symlink or `@AGENTS.md` pointer |
| `aider` | no alias file works (aider has no auto-discovery) — append `read: AGENTS.md` to `.aider.conf.yml` (create it if missing; if it is a symlink, flag and ask), and note the `aider --read AGENTS.md` alternative in the A7 report |

(Codex CLI and Cursor read `AGENTS.md` directly — no alias needed.)

### Symlink creation algorithm

If `{{symlink_strategy}} == auto`:

1. **Detect OS.**
2. **POSIX (Linux / macOS):** run `ln -s AGENTS.md <alias>`. Target must be the **bare filename** `AGENTS.md` (relative, same directory), never an absolute path. If the command fails for any reason, fall back to the pointer file (step 4).
3. **Windows:** run `cmd /c mklink <alias> AGENTS.md`. If exit code is non-zero (Developer Mode off or insufficient privilege), fall back to the pointer file (step 4).
4. **Pointer file fallback:** write a file at `<alias>` containing exactly the literal text `@AGENTS.md` followed by a single newline. Nothing else. (The `@` prefix is the import syntax Claude Code and Gemini CLI resolve mechanically, so the alias actually loads the canonical doc instead of being a one-word memo.)

If `{{symlink_strategy}} == pointer-only`:

- Skip the symlink attempt entirely. Always write the pointer file as described above.

Record per-alias which strategy was used (symlink vs pointer) — you'll report this in Step A7.

## Step A5 — Verify portability

Scan every file you created in Steps A3 and A4 for forbidden patterns:

- Windows drive letters: `[A-Za-z]:\\` — and the forward-slash form (a SINGLE letter + `:/`, i.e. not preceded by another letter; URL schemes like `https://` are NOT drive letters)
- UNC shares: `\\server\share`-style paths
- POSIX home expansions: `/Users/`, `/home/`, `~/`
- POSIX system roots — enumerated; do NOT flag every leading slash: `/opt/`, `/srv/`, `/etc/`, `/usr/`, `/var/`, `/tmp/`
- Windows home expansions: `%USERPROFILE%`, `$HOME`

Files to scan: `AGENTS.md`, `README.md` (if created), everything under `.agent_works/`, `.gitignore`, `.aider.conf.yml` (if written), and every pointer-file alias created in Step A4.

**Exemptions — skip a match when any of these apply:**

1. It sits in `AGENTS.md` §1 rule 3 (the path-discipline rule itself) or in a clearly-marked "DO NOT do this" example.
2. The line carries a `(local-env)` tag — the documented marker for deliberately environment-bound references (another local repo, a system service, a tool install location). Those are allowed by rule 3; the scan only polices *undeclared* absolute paths.

If any other match is found, STOP and report:

```text
Portability check failed:
  <file>:<line>: <matched pattern>
The template should not contain absolute paths. This is a plugin bug — report at https://github.com/war3water/Minakami_plugins/issues.
```

## Step A6 — Write the permission profile (last write)

Skip this step entirely when `claude` is not in `{{runtime_targets}}` — no `.claude/` exists; note the skip in A7. Otherwise, as the final write of the scaffold, pick exactly one:

| Profile | Template source | Target path |
|---|---|---|
| `dev-local` | `settings.local.json.dev-local.tmpl` | `.claude/settings.local.json` |
| `dev-network` | `settings.local.json.dev-network.tmpl` | `.claude/settings.local.json` |
| `read-only` | `settings.local.json.read-only.tmpl` | `.claude/settings.local.json` |

This runs after everything else so that a restrictive profile takes effect only when there is nothing left to write.

## Step A6.5 — Re-scan the last write

Run the Step A5 patterns over the settings file just written (it did not exist at A5 time). Same failure protocol as A5.

## Step A7 — Report

Print a single-screen summary:

```text
agent-coord-bootstrap: initialized {{project_name}}

Created files:
  AGENTS.md                                    (canonical)
  <list each created file>

Cross-runtime access:
  CLAUDE.md       symlink → AGENTS.md          (or "pointer file"; only if claude targeted)
  GEMINI.md       <as appropriate>
  .aider.conf.yml read: AGENTS.md              (aider target; or run `aider --read AGENTS.md`)
  Codex CLI / Cursor: read AGENTS.md directly — nothing created

Permission profile: {{permission_profile}}    (or "skipped — no Claude Code target")
Layout: {{layout}}

Next steps (match the layout):
  1. Read AGENTS.md — it's the routing doc every agent will consult.
  2. Put your real test/smoke commands in README ### Verify and list
     capabilities in ## Features.
  3. full layout: fill .agent_works/project_requirements.md and add real
     tickets to work_queue.md.
     lean layout: those docs are created on first need from the AGENTS.md
     routing table — nothing to fill now.
```

If `README.md` already existed (and was therefore not written), add one line to the report: `README.md: left untouched — consider adding ## Features and ### Verify sections yourself.`

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.

---

# Mode B — Upgrade (existing project)

Goal: reorganize the project's existing coordination docs into this plugin's layout **without losing any unique content or project-specific rules**. Hard rules for this entire mode:

- **Never delete unique content.** Anything inventoried that has no obvious home goes to `.agent_works/upgrade_parking.md`, flagged in the final report — not dropped. The inventory covers the locations listed in Step B2; the B6 report names what was NOT searched, so the user can point the upgrade at anything it missed.
- **Never overwrite `README.md`.** The only permitted change is an append-only addition the user approved as an explicit B4 plan row (e.g. `## Features` / `### Verify` stubs); existing README content is never modified.
- **No writes before the user approves the migration plan (Step B4).**
- **Never write through a link.** If a target path is currently a symlink or pointer file, unlink/delete it first and write a fresh regular file — writing "through" a symlink modifies the file it points at, which may be a merge source you still need.

## Step B1 — Safety gate

Run `git status`. Three cases:

- **Clean working tree** → proceed.
- **Dirty tree** → tell the user: "Your working tree has uncommitted changes. I recommend committing first so the upgrade is a clean, revertable diff." Ask whether to proceed anyway or pause. Respect the answer.
- **Not a git repo** → warn that there is no undo mechanism, recommend `git init` + initial commit first, and ask whether to proceed anyway.

## Step B2 — Inventory and classify

Read each existing coordination artifact found in Step 1. Also check these common locations for coordination-like docs (do not crawl the whole repo): `docs/`, `.github/`, repo root `*.md` files, tool rule files (`.cursorrules`, `.windsurfrules`, `.cursor/rules/`, `.windsurf/`, `.aider.conf.yml`), and nested `AGENTS.md` / `CLAUDE.md` files listed via `git ls-files` (tracked files only; if not a git repo, check just the top two directory levels).

Classify every content block (a section, a rule list, a table) into one of three buckets:

1. **matches-plugin-layout** — content that duplicates what the plugin's templates already provide (e.g. a generic "don't commit secrets" rule). Classify here ONLY when the match is near-exact — same rule, same scope, no project-specific detail; **when in doubt, use bucket 2 and merge**. The template version wins; the duplicate is dropped from the merged doc. This is the ONLY case where existing text is not carried over — and because it is the only destructive classification, **every bucket-1 block gets its own row in the B4 plan with the dropped text quoted verbatim**, so the user sees exactly what is dropped and approves it.
2. **unique-preserve** — project-specific rules, decisions, status, domain knowledge, custom workflows. These MUST appear in the migrated layout.
3. **conflict** — existing content that contradicts a template rule (e.g. an existing doc says "always work in base environment"). Flag for the user in the migration plan; the user's existing rule wins unless they say otherwise.

Special cases:

- **`AGENTS.md` is itself a symlink or pointer** (e.g. pointing at a content-bearing `CLAUDE.md` — the reverse of this plugin's layout) → the link's TARGET holds the real content; inventory the target. In B5, the link is unlinked before the new `AGENTS.md` is written (see the "never write through a link" hard rule).
- **`CLAUDE.md` (or `GEMINI.md`/`AGENT.md`) is a real file with its own content** → its unique content merges into the new `AGENTS.md`; the file itself then becomes an alias (symlink or pointer).
- **`CLAUDE.md` (or other alias) is already a correct symlink/pointer to `AGENTS.md`** → leave it untouched; verify the target resolves and note "already correct" in the plan.
- **Legacy `agent_works/` (non-dot)** → contents migrate to `.agent_works/`; the old directory is removed only after every file inside has been moved or parked.
- **Style-guide / debug-notes / communication-guideline content** (conventions elaboration rather than binding rules) → merges into `.agent_works/conventions.md`, not into `AGENTS.md`.
- **Existing `.claude/settings.local.json`** → preserved as-is. Optionally offer to append missing **safety `ask`/`deny` entries** from the chosen profile template — but check overlap first: Claude applies `deny → ask → allow`, so an offered entry whose pattern intersects an existing `allow` (same command family, or one pattern is a prefix/glob of the other) would silently weaken that allow. **Overlapping entries become B4 conflict rows** — the user decides; only non-overlapping entries may be offered as an append. Never remove or edit existing entries, and never append tool-level `Write`/`Edit` denies.

## Step B3 — Ask the five questions

Same five questions as Step A2, but pre-fill defaults from the inventory:

- `project_name` — from existing docs if stated, else cwd basename.
- `runtime_targets` — infer from which access mechanisms already exist (`CLAUDE.md` present → `claude`; `.aider.conf.yml` present → `aider`); default to adding `codex`. Every selected target gets its alias **created or verified** in B5 — including targets with no existing file.
- `layout` — `full` if the project already has plan/requirement/decision docs to migrate; else `lean`
  (create only the docs that receive migrated content, plus AGENTS.md + conventions.md — never empty
  process docs).
- `permission_profile` — if `.claude/settings.local.json` exists, default is `keep-existing` (see B2 special case). If it does NOT exist, ask normally; the chosen profile is written in B5.
- `symlink_strategy` — `auto`.

## Step B4 — Migration plan (approval gate)

Present a migration plan as a table — every row is one action. Allowed actions: `merge into`, `move`, `create`, `convert to alias`, `verify (already correct)`, `park`, `drop (duplicate of template §X)`, `append`, `write`.

```text
| # | Source | Action | Destination |
|---|--------|--------|-------------|
| 1 | CLAUDE.md §"Project rules" (7 unique rules) | merge into | AGENTS.md §1 Hard Rules |
| 2 | CLAUDE.md (file itself, after merge) | convert to alias | pointer → AGENTS.md |
| 3 | CLAUDE.md §"never commit secrets" — quoted: "Never commit secrets or .env files" | drop (duplicate of template §1.1) | — |
| 4 | docs/handoff_notes.md | move | .agent_works/handoff/current_handoff.md |
| 5 | agent_works/decisions.md (legacy dir) | move | .agent_works/decisions.md |
| 6 | (template) | create | .agent_works/coordination/work_queue.md |
| 7 | (template) | create | .agent_works/conventions.md |
| 8 | GEMINI.md (new runtime target) | create | symlink → AGENTS.md |
| 9 | gitignore.tmpl lines (.local/, models/, ...) | append | .gitignore |
| 10 | settings.local.json.dev-local.tmpl | write | .claude/settings.local.json (none exists) |
| 11 | CLAUDE.md §"deployment checklist" (no obvious home) | park | .agent_works/upgrade_parking.md |
| ...| | | |
```

The plan MUST include: one row per bucket-1 drop **with the dropped text quoted verbatim in the row**, one row per alias (created, converted, or verified), one create-row per template file the layout is missing (including `.agent_works/conventions.md`), the exact `.gitignore` lines to append, and a settings row (write chosen profile / append approved non-overlapping safety entries / keep-existing untouched; overlapping entries appear under Conflicts instead). Include as a **recommended default** — the user can strike the row — an append-only row adding `## Features` / `### Verify` stubs to an existing `README.md`: those sections carry the scaffold's verification and documented-features practices.

List every conflict from B2 explicitly below the table with a recommendation. Then ask the user to approve, amend, or pause. **Do not write anything until approval.**

## Step B5 — Execute

In this order:

1. **Unlink first if needed:** if `AGENTS.md` is currently a symlink or pointer (per the B2 special case), delete the link now — its target's content is already inventoried. Never write through it.
2. Build the new `AGENTS.md` as a fresh regular file: start from `AGENTS.md.tmpl` (with substitutions as in Step A3), then fold every `unique-preserve` block into its best-matching section. Project-specific rules go into §1 Hard Rules or §4 Working Principles as appropriate; conventions elaboration into `.agent_works/conventions.md`; domain terms into the Glossary.
3. Create / move the `.agent_works/` files per the approved plan. Existing content fills the same role as the template would (e.g. an existing handoff doc replaces `current_handoff.md.tmpl` content, not the other way around).
4. Write `.agent_works/upgrade_parking.md` if any content was parked, with one section per parked block and a one-line note on where it came from.
5. Ensure every alias for every runtime in `{{runtime_targets}}`:
   - **Already a correct symlink/pointer to AGENTS.md** → leave untouched.
   - **Real file with content** (merge confirmed in step 2) → delete the original file first, then run the Step A4 algorithm on the now-empty path.
   - **Missing** (newly added runtime target) → run the Step A4 algorithm directly.
6. Append `.gitignore` entries (exactly the lines approved in the plan), create skill pointer dirs as in Step A3, and — only if the plan included the approved row — append the `## Features` / `### Verify` stubs to `README.md`. Before appending to any file in this step, confirm the target is a regular file — if it is a symlink or pointer, do not write through it; flag and ask.
7. Remove the legacy `agent_works/` directory only if it is now empty.
8. **Settings (last write, mirroring Step A6):** per the approved plan row — write the chosen profile if no settings file existed; append the approved safety entries if the user accepted the offer; otherwise leave untouched.

## Step B6 — Verify and report

Run the Step A5 portability scan (including its exemptions) **only over template-derived text** (the skeleton sections of the new `AGENTS.md`, files created from templates). For **migrated or parked user content** (folded-in unique blocks, `upgrade_parking.md`), matches are NOT a failure — collect them into a non-blocking warning list instead: these paths came from the user's own docs and may be legitimate. The warning suggests two remedies per match: make the path repo-relative if it points inside the project, or add a `(local-env)` tag if it is genuinely environment-bound.

Then report:

```text
agent-coord-bootstrap: upgraded {{project_name}}

Migrated:
  <source> → <destination>     (one line per executed plan row)

Dropped as template duplicates (per approved plan):
  <one line per bucket-1 drop>

Preserved verbatim:
  <files left untouched>

Parked (needs your review):
  .agent_works/upgrade_parking.md — <n> blocks

Settings: <written dev-local / appended 3 safety entries / kept existing untouched>

Portability warnings (from your original content — consider making relative):
  <file>:<line>: <pattern>     (omit section if none)

Not searched (point me at anything there worth migrating):
  <locations outside the B2 list — e.g. untracked or deeply nested dirs,
   build configs, Makefiles, CI beyond .github/>

Conflicts resolved:
  <rule> — kept your existing version / replaced per your choice

Next steps:
  1. Review .agent_works/upgrade_parking.md and re-home or delete each block.
  2. Read the merged AGENTS.md once end-to-end — confirm the folded-in rules read correctly.
  3. Commit the upgrade as a single revertable commit.
```

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.
