# First build

The goal: a newcomer can set the project up, run it, debug it, say what each part of it does, and follow each core flow step by step to the method and the function behind it, from the README and the wiki alone, reading each fact once; and every claim can be checked against the code. Steps 1 to 3 write nothing in the repository; step 4 writes only what the user approved.

## 1. Discover

Use `../../references/extraction.md` §1, §2, §4, §8 and §9 for the languages, the entry points with what they need before they can start, and the primary pipeline (the path from the main entry point's input to its output). Use its `other-process` rule (§6) for code that runs outside the process the debugger attaches to. Then collect, citing the file each fact comes from:

| What | Where to look |
|---|---|
| Setup | manifests and lockfiles, runtime-version files (`.python-version`, `.nvmrc`, `.tool-versions`), setup scripts, `Makefile` or `justfile` targets, `Dockerfile` and compose files, and the CI workflow steps, which are the best record of commands that work from a clean checkout |
| Run | the entry points, the command-line parser, sample inputs and fixtures already in the repository, and the wrapper scripts that start the entry point with the interpreter or services it needs |
| Tests | the test command, how to run one test, what the tests need |
| Debug | committed debug configurations (`.vscode/launch.json`, `.idea/runConfigurations/`), logging, verbosity and trace switches (environment variables the code reads, `--verbose` or `--debug` flags, log-level settings), where output goes when a host hides it, and code that runs in another process with the switch that keeps it in one |
| Errors | the messages and exceptions the code raises at each stage, what happens when the entry point is started without what it needs, and the failure modes the tests cover, for the symptom table |
| Output | the structured result the program writes, if any (a file, a report, an API response), and the function that sets each field |
| Core flows | what the project exists to do, and for each such flow: its steps from input to output (`extraction.md` §4), the method each step applies as the code or its documents name it (a docstring, a comment, a reference, a design note), its call map (`python <skill folder>/tools/wiki.py callgraph <path>#<function>` for Python), and one real input whose run shows values at each step |
| Code to know first | the entry point, the dispatcher, the core function of each flow, and the most-called functions (`extraction.md` §6, `high-fan-in`) |
| Docs | the README, `docs/`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, design notes and decision records, any existing wiki or documentation site, `AGENTS.md` and `CLAUDE.md`, `.gitignore` |
| Evidence | captured outputs already in the repository: fixtures, golden files, snapshots, benchmark results |

Run `python <skill folder>/tools/wiki.py questions` as well. The questions people have already asked in sessions here show which pages a newcomer needs first. Recurring ones can seed `questions.md` (`update.md`, "Questions"), proposed with the rest in step 3.

In a temporary copy of the repository, run the commands you will document that need nothing beyond what is installed: `--help`, the test command, a sample run, with the trace switch on if the code has one. Keep their output for the pages, labelled with the command and the date. Install nothing in this step; a command that needs an install is checked later by `lint --run`, after approval.

## 2. Plan

**Where.** The wiki goes in `docs/wiki/` unless the repository already has a documentation home (for example `doc/`, an MkDocs `docs_dir`, a docs site folder); then follow it. The tools go in the folder where the repository keeps its developer scripts (`scripts/`, `tools/`, `bin/`, `dev/`), as `<that folder>/wiki/`, else in `tools/wiki/`. The `--wiki` and `--tools` arguments override both.

**What to write now.** Write what a newcomer needs first:

- the README as the front page, following `readme.md`;
- `concepts/overview.md`, following `pages.md` §The overview page: every part of the system, not only the primary path;
- a how-it-works page for each core flow, starting with the primary path, following `pages.md` §How-it-works pages: the picture, the pipeline map, the call map and the rules that decide the result;
- `howto/run-and-debug.md`, following `pages.md` §Run and debug, pointing into the call maps instead of drawing them again;
- reference pages for what readers will look up while working: each subsystem the primary path passes through, the public API, the command-line flags, the configuration, the data formats, as far as the code has them;
- how-to pages for the changes the code invites: an extension point, a registry or a plugin interface suggests "Add a …";
- a tutorial only when one guided walk through the code would help a newcomer more than the pages above.

Before writing, decide where each fact lives (`pages.md`, "One home per fact"). The README already holds the project's own tables and steps. Where a page would repeat one in full, either link to the README or propose moving the full table to the page and leaving the README the part a newcomer needs to start. Do the same for README sections a page will cover in full, such as a long debugging, configuration or architecture section: propose the short replacement (what a newcomer needs, and a link), so the reader is not given the same fact twice in different words.

Everything else the code would support is listed at the end of `index.md`, under "Not written yet", as one line per topic, so the plan is visible and nothing is dropped silently. The test for "enough": could a newcomer set up, run and debug the project, say what each part does, and explain each core flow down to its methods and functions, using only what is written? If not, write what is missing now. When the repository is larger than one wiki can cover well in one pass, cover the overview and the primary path now, list the other subsystems as not written yet, and say in the report how to extend it.

## 3. Propose (approval gate)

Present, in this order:

1. One line: the stack and the files that show it.
2. A table of what will be written: `# | File | New or changed | Purpose`. It covers the wiki pages, `SCHEMA.md`, `index.md`, `log.md`, the copied tools, and the README.
3. The exact README text to add or replace (see `readme.md`), the README content you will keep unchanged, and each proposed trim with the section's words before and after, so the user sees what a reader is spared.
4. The rules block from `templates/rules-block.md.tmpl`, with the file it goes in. Put it in `AGENTS.md`, which Codex reads and Claude Code reads when the repository has no `CLAUDE.md`. When a `CLAUDE.md` exists and does not import `AGENTS.md`, also propose a one-line `@AGENTS.md` import in `CLAUDE.md`. When neither file exists, propose creating `AGENTS.md` with only this block.
5. The command blocks that will carry `<!-- check:run -->`, with exactly what each runs and what it installs and where. They run in a temporary clean checkout, so the user's working tree is not touched.
6. Optional extras, each numbered so it can be approved alone:
   - debug configurations for the editor the repository uses (`.vscode/launch.json` entries);
   - a CodeTour (`.tours/*.tour`, anchored with `pattern` rather than `line`);
   - a CI step that runs `wiki.py lint`, plus `lint --run` where the CI has the toolchain, so drift fails the build. Show the exact change to the CI file;
   - a `.gitignore` line for the built viewer, which holds absolute paths when editor links are on, so it is not meant to be committed.
7. Recommendations that would change code or configuration. Examples: a trace switch; a small sample input; a switch that keeps out-of-process code in one process for debugging; a one-line message when the entry point is started the wrong way (the wrong interpreter, a required service not running) that names the fix and the wiki page. These are listed for the user to request separately; this skill does not apply them.
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
2. `python <skill folder>/tools/wiki.py lint`. Fix every problem, and read every warning: fix it, or say in the report why it stays. A repeated table or diagram is fixed by keeping one full copy (`pages.md`, "One home per fact"); a subset that a task page really needs may stay.
3. `python <skill folder>/tools/wiki.py lint --run --strict --clean-env --capture <a temporary folder outside the repository>`. This is the proof that a reader can follow the pages without changing anything:
   - The approved command blocks run, README first, in one temporary clean checkout, with only system environment variables. A step that relies on something the page does not state, such as a variable set on your machine, an installed tool, or a file outside git, fails here.
   - Each block's output is saved. Put the real output under the command, shortened where it is long and labelled with the command and the date. Mark it `check:output` wherever the reader will compare their own output with it, so the next lint fails if the program's output changes.
   - A server, `docker compose up` or watcher is started with `check:run background ready=<url or /log regex/>`, probed by the next blocks (a health URL, a request, a CLI call against it), and stopped with its page. A deployment step is verified the same way, as far as the machine allows: build the image, start it, request its health URL.
   - **Shared resources.** A clean checkout isolates files, not names. Before a block starts containers, creates volumes or databases, binds ports or writes to a service, check whether those names are fixed (a Compose `container_name`, a volume with `name:`, a fixed port, a database URL from the user's config). Check whether they could reach the user's own containers or data. If they could, do not run the block as written. Run it isolated (another project name, port and volume, given as a verification-only variant on the page), or ask the user, or skip it with that reason. A check must never touch the user's real data.
   - `--strict` fails on any command block that is neither run nor marked `check:skip reason="…"`. A skip says exactly what the step needs that a check cannot have, for example an API key, a phone, production credentials or a paid service. Wherever a skipped step has a safe stand-in (offline tests with a mocked client, a local server, a dry-run flag), document the stand-in as a run block next to it.
   - A failing block means the documentation is wrong or the step needs something it does not state. Fix the text, for example a missing prerequisite, an environment variable to set, or a per-OS form; never weaken, skip or unmark a block to make it pass.
   - A block whose tool is not installed on this machine (for example no Go toolchain) is reported as not verified here. Make sure the page names that prerequisite, and report the block as unverified.
4. `python <skill folder>/tools/wiki.py viewer`, then `python <skill folder>/tools/wiki_browser.py check-viewer <viewer file>`. The check needs Python Playwright; without it, say that the viewer was not opened.
5. **Read it as a newcomer.** Open the overview, then each page from the sidebar, and check:
   - Do the headings alone say what the page tells you?
   - Does each diagram show something its page's text and tables do not?
   - Can you finish each task without opening another page?
   - From each how-it-works page alone, can you name every step, its method, its function and file, and what it takes and gives? Does the picture fit, and does its table say where it stops fitting?
   - Is any fact told on two pages, in any wording? Keep it in its home and replace the other copy with a link and the one line the task needs. Is any sentence there only to restate its heading, its table, or the page's purpose? Cut it. Compare the word count lint reports before and after this pass.
   - Someone who starts the entry point the obvious way (the default interpreter, nothing else running) gets some message. Is that message in the symptom table, with its fix?
   - Does any function the break table names run in another process? If so, does its row say how to reach it?

   Fix what fails.
6. **Audit the claims.** List every concrete claim a reader will act on: commands, versions, defaults, limits, flags, ports, environment variables, exit codes, error messages, file locations, the methods and formulas named on how-it-works pages, and the behaviour of requests and responses. Verify each one, either by a `check:run` block (with `check:output` where the page shows output) or by the line of code it comes from. A claim you can verify neither way is removed, or labelled as unverified with what would verify it. Report the counts: verified by running, verified in the code, unverified.

## 6. Report

Reply briefly; the files carry the detail:

- the files written, and the topics left as not written yet;
- the lint result: problems (should be none), and the warnings left with their reasons;
- the command blocks run (in the clean checkout and clean environment), those with their output checked, those skipped on this OS or as not installed here, and every `check:skip` with its reason;
- the claim audit: how many claims were verified by running, how many in the code, and which are unverified;
- the diagrams rendered, or why not;
- the words a reader has to read (from lint), and what the read-through cut;
- the viewer path;
- what you could not verify, the recommendations you did not apply, and open questions;
- how the wiki stays current: the rules block, `/code-map:wiki update` (or `$wiki update` in Codex), and `wiki.py lint` in CI if the user wants it.
