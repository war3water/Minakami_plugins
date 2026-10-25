---
name: code-cleanup
description: Cleans up a codebase so a maintainer can read, debug, and change it, without changing what it does. Scales from one targeted change, to removing dead code and junk, to flattening call paths that jump through needless layers and splitting god functions, to a full overhaul or an ongoing campaign; when the request is empty or vague it surveys the project and asks which level to do. Use when someone asks to clean up, tidy, refactor, reorganize, untangle, simplify, remove dead code, or pay down technical debt.
allowed-tools: Read(${CLAUDE_SKILL_DIR}/**)
---

# Code Cleanup

Make the project easier to read, debug, and change while keeping its behavior exactly as it is: the same CLI
output and exit codes, error messages, stored file formats and keys, order of side effects, and everything
that runs through config, cron, or a lookup by name. A cleanup that changes behavior has failed, even when the
change fixes a bug, because the user can no longer trust the diff as a pure refactor: report bugs instead.

Change only what has a nameable problem (dead, duplicated, hard to trace, misleading, untested and risky);
taste alone isn't one. Deliver the level chosen, and report adjacent problems instead of acting on them.

## Pick the level

| Level | When | What it changes |
|---|---|---|
| **Targeted** | the request names one change | that change and what it requires, nothing else |
| **Tidy** | a broad ask on a project whose structure works | dead code, junk files (backups, old copies, scratch scripts), duplicated logic, unclear internal names, and docs or examples that don't match the code (a doc correction, not a behavior change); no moves |
| **Reorganize** | the request is about tracing or structure, or the survey finds a command that passes through forwarding layers, a god function, an import cycle, or modules with several unrelated jobs or vague names | every command traceable from its entry point to the work in as few steps as its real work needs (see "Reorganize and Overhaul") |
| **Overhaul** | the survey finds both dead weight and structural problems, or helpers that conflict | Tidy and Reorganize together, plus conflicting helpers (same name or purpose, different behavior) resolved into one with the difference explicit |
| **Report only** | the user asks for a review, a map, or a plan | findings and a proposed plan, no edits |

Pick the level the worst problem you found needs, then fix every problem within it, not a sample. A healthy
project may need only a few fixes, and that is a complete result even when the user said "refactor"; don't
invent structural work it doesn't need. Run an ongoing **campaign** only when the user asks for one
(exhaustive, whole-repo, "keep going"): read `references/campaign-mode.md`.

## When the request is unclear

A request is clear when it names the change, the pain, or the level ("remove dead code", "the send path has
too many layers", "inline `_run_impl`"). Then start; don't run a question round.

When the request is empty (a bare `/code-cleanup`) or too vague to choose a level, ask before changing
anything, even when the level looks obvious, because the user may want less, more, or only a report:

1. Survey for a few minutes (below). Note the biggest problems, one line of evidence each.
2. Ask one question, with the AskUserQuestion tool when it is available, otherwise as your reply, and stop
   there until the user answers. Say in two or three lines what you found, then offer the levels that fit,
   each with what it would touch in this project, first the one the worst problem needs, as your
   recommendation. In the same question, ask what the repository can't show you: whether other code imports
   this project, whether something runs it on a schedule or reads its files, and whether bug fixes are wanted
   as a separate step.
3. Proceed with the answer, without asking again about what it settled.

When nobody can answer (the user or your instructions say they are away or not to ask), pick the level the
survey supports, carry it out in full, and state the level and why in the first line of the report.

## Survey

Before changing anything: read the README and docs against the code, and try the commands and examples they
show; find the entry points; read the config, data, deploy, and CI files; run the tests. Fix what the
repository's own evidence settles. Ask only about what depends on facts outside it (see "When to ask first").

## Reorganize and Overhaul

Code that makes a simple feature jump through many files is hard for people and for agents to debug: every
extra hop is another file to open and another place a behavior can hide. The goal is that each command reads
from its entry point to the work in as few steps as the work needs.

1. **Map.** For each main command, trace the path from its entry point to where the work happens and write it
   down (`file:function → …`). For each step, name what it does besides passing the call on: validation,
   transformation, I/O at a boundary, error translation, a seam the tests patch, an extension point outside
   code registers into, a boundary a checker enforces, or reuse by callers with different needs. A step that
   does none of these is a pass-through. Also note import cycles, wiring mixed into logic, god functions,
   modules with several jobs or vague names, and conflicting helpers.
2. **Capture.** Run the documented commands (the deterministic ones, against copies of any data they write)
   and keep the outputs to compare after each step. The tests only cover what they exercise; when there are
   none, this capture is the safety net.
3. **Plan.** Follow the project's sensible conventions, or else its framework's layout: wiring (argument
   parsing, configuration, dependency setup, error-to-exit-code translation) at the entry point, logic in
   modules named for their job, I/O at the edges, as few directory levels as the module count needs. List the
   moves, the deletions, and anything that needs a yes. In an interactive session, show the plan before moving
   many files; when nobody can answer, put it in the report and carry it out.
4. **Move in small verified steps.** A useful order: delete dead code, collapse pass-throughs into their
   caller or callee, split and move, then rename. Update every caller in the same step and compare the
   captured outputs after each one. Break a cycle by moving what both sides need into a module both import, so
   nothing imports back. Split a god function where its body changes job, into steps you can name in a few
   words. When the structure itself is wrong (competing implementations), building the new path next to the
   old one and cutting over once the outputs match can beat migrating the old one piece by piece.
5. **Show it.** In the report, give each main command's path before and after.

## Rules for every change

### Deleting

Delete only what you can show nothing reaches. Search every file type, not only source: docs, configs, data
files, scripts, crontabs, CI and deploy files, and packaging entry points. Check the lookups that never spell
the full name: `getattr` or `importlib` with a built string, prefix scans over a module (`vars(module)`,
`name.startswith("render_")`), decorators and registries, names read from config, aliased imports, and
re-exports. On Python, `scripts/dead_candidates.py` lists candidates and tags the ones named in non-code files
or sitting in a module that is looked up by name; it narrows the search, it doesn't replace it. A user's "this
is dead" is a lead to check, not proof: delete what the check confirms and report what it refutes.

A search can only prove what happens inside the repository, so uses from outside decide the rest:

- If every config that can select a name is in the repository at a fixed path, the repository is the whole
  truth, and an implementation it doesn't name is dead. If a config can come from outside (a path from an
  environment variable or a flag, a deploy-time or user file), every name it could select is part of the
  interface.
- A published library's public API, a documented feature or extension point, a CLI command, and anything the
  docs, cron, or CI tell people to run are used from outside too.

Keep those and ask, or flag them with the evidence when nobody can answer. Junk files that nothing imports or
runs are dead like any other code. A file your own move emptied goes with that move. Git history is the backup
for committed files; a file with uncommitted changes has none, so it needs a yes before deletion.

### Look-alikes, layers, names, imports

- **Merging look-alikes:** diff them and run both on the inputs where they could differ: rounding halves,
  empty values, case and whitespace, separators, filters, error types, return shape. Merge only what agrees;
  where they differ, keep the difference explicit (two functions, or one with a parameter) and say why.
- **Collapsing a layer:** list what it does besides forwarding (input normalization, defaults, environment
  reads, type conversion, error translation and exit codes, retries, logging, ordering) and carry
  each into the new path.
- **Renaming:** a name stored or read outside the code (JSON, CSV, or database keys, including dataclass
  fields written with `asdict`; CLI flags; environment variables; config keys; public import paths) is a
  format. Keep it; map it to a new internal name only when the gain is worth the extra step.
- **Removing an import with no visible use:** first check that importing it doesn't register or patch
  something.
- **Adding structure:** add a function, module, or wrapper only when you can name its job. Don't replace one
  pass-through with another, and don't leave a "temporary" compatibility wrapper when every caller is in the
  repository; update the callers instead.

### When a step breaks something

Before editing a file that already had uncommitted changes, keep a copy of it. When a step breaks a behavioral
test or changes a captured output, undo only your own edits from that step (`git restore -- <path>` for a file
that was clean when you started, your copy for one that wasn't; never `git restore .`, which also discards the
user's work), then take a smaller step. A test that only pins removed structure (a mock of a deleted wrapper, a
private import path) may be updated once the captured outputs still match; say so in the report. Never edit a
test to make a behavior change pass.

## When to ask first

Work freely on anything inside the repository that you verify keeps behavior, including moving core files and
collapsing internal registries the request covers. Ask first, or when nobody can answer, leave it and flag it
with the question you would ask:

- anything someone outside the repository can observe: public API, CLI, file formats and stored names, names
  an outside config can select;
- anything whose right answer depends on facts outside the repository, such as what a deploy or another
  system reads;
- any behavior change, bug fixes included;
- deleting what you couldn't prove dead;
- adding tools, CI, or dependencies;
- in an interactive session, a reorganization that moves many files: show the plan first. A plan the user
  approves covers the items it lists.

The request approves what it names: "untangle the send path" covers the layers on that path even when the
README describes them (update the README).

## What the run leaves behind

Only the requested changes. No new git tags, branches, commits, or stashes unless the user asks (pop or drop
any stash you create), and no notes or capture files. Working files for a restructure go in
`.agent_works/code-cleanup/`, with that folder added to `.git/info/exclude`; delete the folder and remove the
line when you finish (a campaign keeps them until it ends). Keep a new test only when it covers behavior the
suite was missing. Before you finish, check that every module still imports (nothing imports a file you
removed) and that every command and example the docs show still works.

## Report

Write it for the user, as short as the change allows, in plain words:

1. The level, and why, when you chose it. Then any behavior change: what, why, and how to undo it.
2. What changed: one line each, and one line of evidence per deletion. For Reorganize and Overhaul, each main
   command's path before and after.
3. What you left alone and why, including any part of the request you didn't do.
4. Questions for the user, each with your recommendation.
5. How you verified it: the commands and their results, the starting commit (`git rev-parse --short HEAD`),
   and whether the tree was clean.

For **Report only**, the report is the deliverable. Give the findings, each with its evidence, and each main
command's path (see "Reorganize and Overhaul", step 1). Then give the plan in the order you would carry it out,
each step with what it touches and what to verify before it, including any behavior the tests don't cover yet
and how to capture or test it first. End with the questions only the user can answer, each with your
recommendation.
