# First build

The goal: a newcomer can set the project up, run it, debug it and understand its main path from the README and the wiki alone, and every claim can be checked against the code. Steps 1 to 3 write nothing in the repository; step 4 writes only what the user approved.

## 1. Discover

Use `../../references/extraction.md` §1, §2, §4, §8 and §9 for the languages, the entry points and the primary pipeline (the path from the main entry point's input to its output). Then collect, citing the file each fact comes from:

| What | Where to look |
|---|---|
| Setup | manifests and lockfiles, runtime-version files (`.python-version`, `.nvmrc`, `.tool-versions`), setup scripts, `Makefile` or `justfile` targets, `Dockerfile` and compose files, and the CI workflow steps, which are the best record of commands that work from a clean checkout |
| Run | the entry points, the command-line parser, sample inputs and fixtures already in the repository |
| Tests | the test command, how to run one test, what the tests need |
| Debug | committed debug configurations (`.vscode/launch.json`, `.idea/runConfigurations/`), logging, verbosity and trace switches (environment variables the code reads, `--verbose` or `--debug` flags, log-level settings), and where output goes when a host hides it |
| Errors | the messages and exceptions the code raises at each stage, and the failure modes the tests cover, for the symptom table |
| Docs | the README, `docs/`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, design notes and decision records, any existing wiki or documentation site, `AGENTS.md` and `CLAUDE.md`, `.gitignore` |
| Evidence | captured outputs already in the repository: fixtures, golden files, snapshots, benchmark results |

In a temporary copy of the repository, run the commands you will document that need nothing beyond what is installed: `--help`, the test command, a sample run, with the trace switch on if the code has one. Keep their output for the pages, labelled with the command and the date. Install nothing in this step; a command that needs an install is checked later by `lint --run`, after approval.

## 2. Plan

**Where.** The wiki goes in `docs/wiki/` unless the repository already has a documentation home (for example `doc/`, an MkDocs `docs_dir`, a docs site folder); then follow it. The tools go in the folder where the repository keeps its developer scripts (`scripts/`, `tools/`, `bin/`, `dev/`), as `<that folder>/wiki/`, else in `tools/wiki/`. The `--wiki` and `--tools` arguments override both.

**What to write now.** Write what a newcomer needs first:

- the README as the front page, following `readme.md`;
- `howto/run-and-debug.md`, following `pages.md` §Run and debug;
- one explanation of the primary path, for example `concepts/how-a-request-works.md`;
- reference pages for what readers will look up while working: each subsystem the primary path passes through, the public API, the command-line flags, the configuration, the data formats, as far as the code has them;
- how-to pages for the changes the code invites: an extension point, a registry or a plugin interface suggests "Add a …";
- a tutorial only when one guided walk through the code would help a newcomer more than the pages above.

Everything else the code would support goes into `index.md` as a planned page, without ●, with one line on what it will cover, so the plan is visible and nothing is dropped silently. The test for "enough": could a newcomer set up, run, debug and explain the main path using only what is written? If not, write what is missing now. When the repository is larger than one wiki can cover well in one pass, cover the primary path now, list the other subsystems as planned pages, and say in the report how to extend it.

## 3. Propose (approval gate)

Present, in this order:

1. One line: the stack and the files that show it.
2. A table of what will be written: `# | File | New or changed | Purpose`. It covers the wiki pages, `SCHEMA.md`, `index.md`, `log.md`, the copied tools, and the README.
3. The exact README text to add or replace (see `readme.md`), and the README content you will keep unchanged.
4. The rules block from `templates/rules-block.md.tmpl`, with the file it goes in. Put it in `AGENTS.md`, which Codex reads and Claude Code reads when the repository has no `CLAUDE.md`. When a `CLAUDE.md` exists and does not import `AGENTS.md`, also propose a one-line `@AGENTS.md` import in `CLAUDE.md`. When neither file exists, propose creating `AGENTS.md` with only this block.
5. The command blocks that will carry `<!-- check:run -->`, with exactly what each runs and what it installs and where. They run in a temporary clean checkout, so the user's working tree is not touched.
6. Optional extras, each numbered so it can be approved alone:
   - debug configurations for the editor the repository uses (`.vscode/launch.json` entries);
   - a CodeTour (`.tours/*.tour`, anchored with `pattern` rather than `line`);
   - a CI step that runs `wiki.py lint`, plus `lint --run` where the CI has the toolchain, so drift fails the build. Show the exact change to the CI file;
   - a `.gitignore` line for the built viewer, which holds absolute paths when editor links are on, so it is not meant to be committed.
7. Recommendations that would change code or configuration, such as a trace switch or a small sample input. These are listed for the user to request separately; this skill does not apply them.
8. The questions only the user can answer, each with what the page will say if it stays unanswered.

Then ask: apply all, apply some (by number), or stop. Write nothing until the user answers. When you cannot get an answer (a non-interactive run), stop here; the proposal is the deliverable.

## 4. Write

Write only what was approved:

1. Copy the tools: `python <skill folder>/tools/wiki.py copy-tools <tools folder>`. It writes `tools.json`, which records the version and a hash of each file, so later copies can tell an older version from a local edit.
2. `SCHEMA.md` from `templates/SCHEMA.md.tmpl`. Fill in this repository's source layers, where captured evidence lives, the design documents pages must agree with, and the chosen folders in the commands.
3. `index.md` and `log.md` from their templates. The log's first entry is `build`.
4. The pages, following `pages.md`. Set `updated:` to today's date.
5. The README edits, the rules block, and the approved extras.

Replace every `{{…}}` placeholder; lint warns about any that are left.

## 5. Verify, fix, repeat until clean

Run each check from the repository root and fix what it finds before the next one:

1. `python <skill folder>/tools/wiki_browser.py render`. A diagram that does not parse is fixed in the page (`pages.md` §Diagrams), never dropped. Exit code 3 means there is no browser or no Mermaid file: keep the Mermaid source in the page, and say so in the report.
2. `python <skill folder>/tools/wiki.py lint`. Fix every problem, and read every warning: fix it, or say in the report why it stays.
3. `python <skill folder>/tools/wiki.py lint --run --capture <a temporary folder outside the repository>`. This executes the approved command blocks, README first, in one temporary clean checkout, and saves each block's output. Replace every illustrative output whose command ran with the captured one, shortened where it is long and labelled with the command and the date. A failing block means the documentation is wrong or the step needs something it does not state. Fix the text, for example a missing prerequisite or a per-OS form; never weaken or unmark the block to make it pass. A block whose tool is not installed on this machine (for example no Go toolchain) is reported as not verified here. Make sure the page names that prerequisite, and report the block as unverified.
4. `python <skill folder>/tools/wiki.py viewer`, then `python <skill folder>/tools/wiki_browser.py check-viewer <viewer file>`. The check needs Python Playwright; without it, say that the viewer was not opened.
5. Read each page once more as a newcomer would. Every claim should trace to a source symbol, a captured output, or the user.

## 6. Report

Reply briefly; the files carry the detail:

- the files written, and the planned pages left for later;
- the lint result: problems (should be none), and the warnings left with their reasons;
- the command blocks run, and those skipped on this OS;
- the diagrams rendered, or why not;
- the viewer path;
- what you could not verify, the recommendations you did not apply, and open questions;
- how the wiki stays current: the rules block, `/code-map:wiki update` (or `$wiki update` in Codex), and `wiki.py lint` in CI if the user wants it.
