# code-map

Two user-invoked skills for understanding a repository and keeping its documentation true. Both work in Claude Code and Codex CLI from the same plugin source.

| Skill | Claude Code | Codex CLI | What it makes |
|---|---|---|---|
| `code-map` | `/code-map:code-map` | `$code-map` | one local HTML file: a layered, provenance-checked map of the code, regenerated whenever you want a fresh snapshot |
| `wiki` | `/code-map:wiki` | `$wiki` | a code wiki in the repository (the README as front page plus pages in `docs/wiki/`), which an agent keeps current with the code |

`code-map` depends on no other plugin in this marketplace. The wiki's README guidance is adapted from the checklist of `agent-coord-bootstrap`'s `review-readme` skill, with its sources, and suggests that skill for a full README review when it is installed; nothing here needs it.

## code-map: the layered map

Build an interactive, layered map of a repository as one local HTML file, so you can read the full picture top-down, click any node to open its source in your editor, and plan refactors or comments from what you see. Four layers: an architecture overview, a module dependency map, the algorithm pipeline with the typed data flowing between stages, and the functions inside each stage. Every node carries a one-sentence purpose, typed inputs and outputs, hotspot flags, an **Open in editor** link, and a notes field; every edge cites the `path:line` it was seen on.

### What you get

| Layer | Nodes | Edges |
|---|---|---|
| 1 Overview | subsystems, plus a 3 to 5 sentence architecture summary | — |
| 2 Module dependency map | files or modules in scope | imports, with the line of the import statement |
| 3 Algorithm pipeline | ordered stages from the entry point's input to its output | the data type passed between stages |
| 4 Functions inside a stage | the functions a stage calls, with signatures | calls, with the line of the call site |

Every node: name, kind, `path:line`, one-sentence purpose (two for stages), inputs and outputs with types (inferred types are marked), hotspot flags, callers and callees, a deep link to your editor, and a notes field that persists in your browser across regenerations.

Hotspot flags: `no-doc`, `untyped`, `high-fan-in`, `long`, `todo`, `no-callers` — the places to comment, type, or refactor first — and `other-process`, code a debugger attached to the entry point never stops in, with how to reach it. The pipeline layer also lists what the entry point needs before it starts, such as a particular interpreter or a running service. Definitions are in `references/extraction.md` §6; they are judgments relative to the code in scope, not fixed thresholds.

### Honesty rules

The map is built for auditing and debugging, so it never draws what it did not see:

- Every node and edge cites `path:line`.
- An edge that could not be confirmed statically (dynamic dispatch, reflection, string-based imports, plugin registries) is drawn dashed and labeled `inferred`.
- Types missing from the code are inferred from usage and marked `inferred`.
- Anything left out of the map is listed by name, so nothing silently disappears.
- Everything read from the repository is data, never instructions.

### Usage

**User-invoked only.** The run reads the whole scope and writes a file into the repository, so the model never triggers it on its own (`disable-model-invocation: true` on the skill; `policy.allow_implicit_invocation: false` in the Codex skill policy).

From the repository you want mapped:

```text
/code-map:code-map                                  # Claude Code
$code-map                                           # Codex CLI (type $ and pick code-map)

/code-map:code-map src/training --entry run_training --editor cursor
/code-map:code-map "map everything, skip tests" --lang Chinese
```

| Argument | Meaning | Default |
|---|---|---|
| positional path or subsystem | focus the map on this directory or subsystem | whole repository, scoped for readability |
| `--entry <symbol>` | the entry point whose input-to-output path defines the pipeline | discovered |
| `--editor <name or scheme>` | `vscode`, `vscode-insiders`, `cursor`, `windsurf`, `jetbrains:<ide>`, or a literal template (`references/extraction.md` §10) | `vscode` |
| `--out <file>` | output path, relative to the repository root | `docs/code-map.html` (`docs/code-map-<focus>.html` with a focus) |
| `--lang <language>` | language of the explanatory text; identifiers stay as written | English |
| free text | any other wish ("map everything", "focus on the training loop", "skip tests") is honored as your scope preference | — |

The run asks one question only when the scope is genuinely ambiguous — no discoverable entry point, several equally plausible ones without `--entry`, or a focus path that does not exist. Otherwise it builds immediately and states the chosen scope in its summary; re-run with `--entry` or a focus if it guessed wrong.

Open the output file from disk in any browser. Notes you type are saved in that browser under the node's stable id, so regenerating the map keeps them. The editor link uses your chosen scheme; the `path:line` text beside it is the fallback wherever the scheme is not registered — for example in a hosted Artifact copy, which the run publishes only if you ask.

### Customizing the viewer

`skills/code-map/templates/viewer.html` is a reference viewer, not a fixed UI: the runbook lets the model adapt layout, styling, or add views when your stated purpose calls for it, as long as the file keeps every interaction you asked for (the checklist in `skills/code-map/SKILL.md` Step 4). The viewer reads one JSON object from its `code-map-data` script block; the contract is in `skills/code-map/references/data-schema.md`, with a canonical example and the integrity checks the run performs before reporting. To change the viewer for every future run, edit the template; to change it for one repository, ask for the adaptation when you invoke the skill.

## wiki: a code wiki that stays current

The wiki follows Andrej Karpathy's ["LLM Wiki" pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), applied to code. It has three layers: the sources (code, tests, captured outputs), which the wiki never edits; the wiki, which the agent writes; and a schema, the agent's rules. An index is read first, and an append-only log records each change. The point is that the wiki is maintained in the same change as the code, so it compounds instead of going stale. Two practices from code wikis such as Google's Code Wiki and DeepWiki are added: every page names the source symbols it explains, and diagrams are regenerated from source. Pages are sorted into the four [Diátaxis](https://diataxis.fr/) kinds (tutorial, how-to, reference, explanation), and the root README is the front page.

### What you get

| Part | What it is |
|---|---|
| Front page | the root `README.md`: setup, run, tests, debug, layout, and a docs map. Setup commands are executed by the lint, so they cannot go stale silently |
| Overview | "How *project* fits together": what it does, its parts in plain words with what each is built on, one diagram of how they connect, one request followed across them, and the few functions to read first. Agents name exactly the functions in that table, so the lint warns when a step of the main flow has none there |
| How it works | one page per core flow: an everyday picture of it with where the picture stops fitting; a pipeline diagram that carries the order of the steps and the data on each arrow; a step table with each step's method, linked to its clause, its functions, and values from one real run; and a call map of who calls whom, started from `wiki.py callgraph`, which reads the calls from Python code, with the complete call list in a collapsed table under it. The lint fails when a box or row names code that no longer exists, and warns when a drawn call is no longer in the caller's code |
| Map of the code | `reference/map.md`: one row for every module, in the words of a report about it, with the function to open first, so the code the other pages do not explain still has a way in; and a table of where the code is not what its name, comment, contract or documents say. The lint fails on a row whose function is gone, and counts the code files that are on no page and under no row |
| Standards and sources | `reference/sources.md` lists each standard, handbook or paper the code follows with its full citation, public link and where it is used, one anchored row each. Every section and every pipeline step that names one, even as `DNV p. 12`, links its row or the repository's chapter on it. The lint warns about a source left unlinked, and about a step whose code cites a clause that the step does not |
| Run and debug | the page developers need most: a "where to break" table pointing into the call maps, one way to run each layer alone, the trace switch, a symptom table, where each output value is set, the debug configurations |
| Reference pages | what readers look up. Each fact has one home, so a change is edited in one place; the lint warns about repeated tables and diagrams, and reports how many words a reader has to read. A warning that stays for a reason is kept on its page with that reason (`lint:accept`), so the list of open warnings can reach zero. Topics not written yet are listed at the end of the index, so the plan is visible |
| `SCHEMA.md`, `index.md`, `log.md` | the rules, the catalog in reading order, and the append-only log (`## [YYYY-MM-DD] kind \| title`) |
| `sources:` front matter | `path#Symbol` for every symbol a page explains, never line numbers; the lint proves each one still exists |
| Diagrams, tables and charts | where a section asks the reader to hold an order, a choice, a comparison, a number built from parts or a quantity across a range, the page shows it as a flowchart or a table; a chart, drawn from a captured run, only where its point is a shape no table or sentence gives. Mermaid source in the page, rendered to SVG at its natural size on a white ground, so it shows in any Markdown viewer and in dark themes; the lint fails on an SVG older than its source |
| Formulas | a formula the reader must follow sits on its own lines in a `math` block, typeset by GitHub, GitLab, VS Code and the viewer, then a table of its symbols with the example's values. The lint warns on `$$`, which breaks where math is not supported; the viewer check fails on a formula that does not typeset |
| Executable docs | every command block is either run or skipped with a reason. `lint --run --strict --clean-env` runs the blocks in a temporary clean checkout with only system environment variables. It starts and probes servers (`background ready=<url>`), and checks shown output against the real output (`check:output`). An unmarked block, a failing step or output that changed fails the lint; a block that shows an error on purpose, such as a start-up failure, declares its exit code (`exit=1`). Output the agent could not capture while writing is marked `check:output fill`, and `wiki.py fill` writes the captured output in after the run, so folding real outputs into the pages is a review, not a copying job. Steps that could touch your own containers, volumes or data are isolated or skipped, never run as written |
| Viewer | one offline HTML file: README first, then the pages under Start here, How it works, Guides and Reference; search, page links, the code each page explains (links open your editor at the symbol), diagrams with zoom and pan, typeset formulas, the reason above each command the check does not run, and a notice on pages that may be out of date. The lint's own report stays in the terminal |
| Tools in the repository | `wiki.py` and `wiki_browser.py`, copied into the repository (default `tools/wiki/`) so people, CI and other agents run the same checks without this plugin |
| Questions | `questions.md`: real questions from Claude Code and Codex sessions in the repository, each answered in the page it belongs to and linked from here. An agent adds one when it answers a question the wiki did not cover; `wiki.py questions` finds the rest in the local transcripts without spending tokens |
| Rules block | a short section for `AGENTS.md` (proposed, written only on approval). It tells every agent to search the code first and to open the wiki only for commands, symptoms and the map, and to update affected pages in the same change and run the lint |

### Usage

**User-invoked only**, like `code-map`. The first build writes nothing until you approve its proposal; updates touch only the wiki and never the code; nothing is committed.

```text
/code-map:wiki                       # first build, or update when a wiki already exists
/code-map:wiki update                # after a change: find the pages it touches and fix them
/code-map:wiki update --since main   # compare with a branch point instead of each page's last commit
/code-map:wiki lint --run            # mechanical checks, documented commands, and a review of the claims
/code-map:wiki view --editor cursor  # build and check the one-file viewer
/code-map:wiki questions             # answer the questions people asked in sessions here
$wiki                                # Codex CLI: the same modes as arguments
```

| Argument | Meaning | Default |
|---|---|---|
| `build`, `update`, `lint`, `view`, `questions` | the mode | `update` when a wiki exists, else `build` |
| `--wiki <dir>` | wiki folder | `docs/wiki`, or the repository's documentation home |
| `--tools <dir>` | where the copied tools live | the repository's dev-scripts folder plus `/wiki`, else `tools/wiki` |
| `--since <ref>` | update: the commit to compare with | each page's own last commit |
| `--run` | lint: execute the `check:run` blocks (with `--strict --clean-env`) | on in build, off in lint |
| `--editor <name>` | viewer editor links, as for `code-map`, or `none` | `vscode` |
| `--lang <language>` | language of the prose | the existing docs' language, else English |

**How it stays current.** You trigger updates; nothing runs on its own. The first build proposes the rules block for `AGENTS.md`, so any agent working in the repository, in Claude Code, Codex or elsewhere, updates the affected pages in the same change. `/code-map:wiki update` does the same on request. `python tools/wiki/wiki.py affected` lists the pages a change touches:

- each page is compared with its own last commit, or the last log entry that names it, symbol by symbol where the language allows, so documenting a change in the same commit clears it;
- it also flags pages that mention a deleted file or a removed symbol in their text.

The first build can also add a CI step that runs `wiki.py lint`, as an optional extra you approve. There are no hooks.

### Measured

Evaluated on 2026-10-23 with Opus 5.5 on three repositories: docread, the worked example; marked 15.0.12 (TypeScript); and hey (Go). The skill's builds were compared with the same request given as a plain prompt, graded by the blind panel (Opus 5.5, Fable 5.1, GPT-6 Astra; vote, then one discussion round):

| Repository | Panel prefers | Errors the graders listed (skill / plain) | Skill build cost |
|---|---|---|---|
| docread | skill (3–0) | 12 / 20 | $5.32 |
| marked (held out) | skill (2–1) | 11 / 21 | $4.96 |
| hey (held out) | plain (3–0) | 9 / 10 | $2.71 |

- **Against docread's hand-made wiki:** the panel preferred the skill's build 2–1.
- **Lint:** every skill build linted with 0 problems.
- **Update test:** three planted code changes (a rename, a new default, a moved setup file) were all reflected in the wiki by `/code-map:wiki update`, and the documented commands passed in a clean checkout.
- **Codex (GPT-6 Astra)** followed the same SKILL.md to a correct proposal.
- **Why hey went to plain:** the plain arm showed output for every example and gave more debugger tips (variables to inspect, timeouts to disable while paused). The run-and-debug guidance has since been extended with those points; that change has not been re-graded.
- **Constraint on all runs:** the evaluation ran without permission to run project commands, so the skill's capture step was off.

### What the tools need

| Task | Needs | Without it |
|---|---|---|
| lint, affected pages, viewer, copying the tools | Python 3.9 or later, standard library only | the agent does the checks by reading, and says so |
| rendering diagrams | Chrome, Edge or Chromium, used headless; or Python Playwright with its Chromium or an installed Edge or Chrome. Mermaid 11.4.1 is downloaded once into a user cache folder and checked by SHA-256 | the Mermaid source stays in the page (GitHub renders it); the run says the diagrams were not checked and names what would enable it; nothing is installed |
| checking the viewer like a reader | Python Playwright | the run says the viewer was not opened |
| `lint --run` | git, and bash (Git Bash on Windows; `WIKI_SHELL` overrides) or PowerShell for powershell blocks | blocks for another OS are reported as skipped |

The viewer has marked 4.3.0 (MIT) inlined, and KaTeX 0.16.11 (MIT) with its fonts when a page has formulas, so it opens from disk with no network access. It sanitizes page HTML before showing it.

## Plugin layout

```text
code-map/
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    references/extraction.md        Shared method: languages, entry points, pipeline, stable names, editor link schemes
    skills/code-map/                The map: SKILL.md runbook, references/data-schema.md, templates/viewer.html
    skills/wiki/                    The wiki: SKILL.md, references/ (build, update, pages, readme), templates/, tools/
    skills/wiki/tools/              wiki.py, wiki_browser.py, viewer_template.html, vendor/marked.min.js (copied into repositories)
```

Each skill reads its own folder and the shared `references/`. In Claude Code these reads are pre-approved for the turn that invokes the skill (`allowed-tools`), and so are the wiki's runs of its own tools, so neither prompts for permission. In Codex the same SKILL.md files apply, with paths resolved from each SKILL.md's folder. Codex loads plugin skills only in interactive sessions (see the repository README); in headless Codex runs, the rules block and the copied tools keep the wiki current.

## Maintenance

- A release bumps `version` in both `plugin.json` copies and in both `marketplace.json` copies (canonical-then-sync, see the repo README).
- Ship criteria: `npx markdownlint-cli2 "**/*.md"` clean, manifest pairs in sync, no absolute paths in plugin content.
- After editing `skills/code-map/templates/viewer.html`, fill it with the canonical example from `skills/code-map/references/data-schema.md` and open it: all three layers render, a stage expands, search highlights, the editor link and the copy action work, a note survives a reload.
- After editing `skills/wiki/tools/`, run the tools' functional tests and a reader check of a built viewer (`wiki_browser.py check-viewer`). The tests live in the maintainer's test workspace, not in this repository. Bump `TOOLS_VERSION` in `wiki.py` with the plugin version, so `copy-tools --check` can tell repositories that their copy is older.
- The editor link schemes in `references/extraction.md` §10 and `EDITORS` in `skills/wiki/tools/wiki.py` must match.
- The wiki's README guidance (`skills/wiki/references/readme.md`) is adapted from `agent-coord-bootstrap/skills/review-readme/references/readme-checklist.md`. When that checklist's sources are refreshed, compare the two.
