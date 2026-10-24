# Update, lint, view

## Update

The goal: every page tells the truth about the code as it is now, and the change that alters the code also carries the page updates. Edit only the wiki: pages, the README, diagrams, the index and the log.

1. **Tools.** Run `python <skill folder>/tools/wiki.py copy-tools <tools folder> --check`. If the repository's copy is older than the plugin's, refresh it with the same command without `--check`. A file someone edited in the repository is kept and reported; say so in your report.
2. **Find what the change touches.** Run `python <skill folder>/tools/wiki.py affected`, adding `--since <ref>` when the user named a starting point. Each page is compared with its own last commit:
   - "Pages to update": a source file or symbol the page names changed after the page's last commit, a file it links to changed, or, for the README, setup, run or debug files changed;
   - "Pages already edited in this change": confirm their edits cover the listed reasons;
   - "Changed code that no page names": code the wiki does not cover yet;
   - "Setup, run or debug files changed": check the README and the run-and-debug page.
3. **Update each listed page.** Read the diff of its sources (`git diff <base> -- <paths>`, base as listed) and the page. Then fix every claim, table row, diagram, command and captured example the change made wrong. Re-capture a captured output by running the command it names, and update its date. When the change leaves everything the page says true, leave the page alone and name it, by its path in the wiki, in the log entry of step 5. The log entry records the check, so `affected` and the lint stop listing the page. A symbol that was renamed or moved is updated in `sources:` and in the text. `affected` cannot see a meaning that changed elsewhere, such as a new default a page restates, so also search the wiki for the old values the diff removes.
   The extras the first build wrote are part of the wiki and are updated the same way: CodeTour steps (the lint checks that each `pattern` still matches), debug configurations, and the rules block.
4. **Uncovered code.** For each changed file no page names, decide: an existing page should cover it (add it to that page's `sources:` and text), it needs a new page (write it and add it to `index.md`), or readers do not need it (say so in the report). A planned page in the index that the change now makes necessary is written now.
5. **Log.** Append one entry at the end of `log.md`: `## [YYYY-MM-DD] change | <title>`, then one to three lines on what changed. Name, by path, the pages updated and the pages checked and still true, for example `Updated: README.md, howto/run-and-debug.md. Checked: reference/cache.md.`
6. **Verify.** Render the diagrams you edited (`wiki_browser.py render`) and run `wiki.py lint --strict`. When setup, commands, command blocks, or output shown as `check:output` may have changed, run `wiki.py lint --run --strict --clean-env --capture <folder>` and update the captured outputs. Rebuild the viewer if the repository keeps one. Fix what fails, as in `build.md` §5.
7. **Report.** List the pages updated and why, the pages confirmed unchanged, new pages, uncovered code left out and why, the lint result, and the command blocks run.

## Lint

The mechanical part is `python <skill folder>/tools/wiki.py lint`, plus `--run` when the user asked for it or when setup or commands changed since the wiki's last commit. It checks links and anchors, `path#symbol` sources, index coverage, diagrams rendered from their current source, the log's format, sources changed since a page was last updated, and, with `--run`, every `check:run` block in a clean checkout.

Then review what a script cannot check, as Karpathy's lint does:

- claims the code no longer supports: check the concrete ones (defaults, limits, flags, file and folder names, error messages, command output) against the code and the captured runs;
- contradictions between pages, and between a page and the design documents `SCHEMA.md` names;
- pages no other page links to, apart from the index, and links a reader would need but that are missing;
- planned pages in the index that the code now needs, and written pages whose subject is gone.

Report the findings as a table, `# | Page | Problem | Evidence | Fix`, with evidence as a `path#symbol`, a file and line, or a command and its output. Then ask: apply all, some (by number), or none. Apply only what is approved; when you cannot get an answer, the report is the deliverable. Fixes stay inside the wiki.

## Questions

The goal: questions people actually ask about this repository get answered once, in the wiki, instead of being worked out again in every session. This follows Karpathy's "query" operation, where good answers are filed back. Only the answering costs tokens; finding the questions does not.

1. **Harvest.** Run `python <skill folder>/tools/wiki.py questions`, adding `--since YYYY-MM-DD` when the user names a starting day. It reads the local transcripts of Claude Code and Codex sessions whose working folder is inside this repository, and keeps only what people typed. It picks out the sentences that ask something, masks anything that looks like a key, and groups questions that ask the same thing. Questions `questions.md` already holds are dropped. The output is ranked: asked in the most sessions first, then most often, then most recent. Claude Code deletes transcripts older than its `cleanupPeriodDays` setting (30 days by default), so older questions may be gone.
2. **Choose.** The list is found by plain rules, so it includes noise: fragments of pasted text, questions the agent asked and the user quoted back, and one-off task questions ("which prompt should I use?"). Keep a question only when all three hold:
   - it is about how this repository works or how to use it;
   - someone would ask it again: asked in more than one session, or it took real exploration to answer;
   - the wiki does not already answer it (check the index and the page it would belong to).
   Name what you left out in a single line, by kind, not one by one.
3. **Answer.** For each kept question, find the answer in the code and the wiki, under the same rules as any page: traceable, with captured output or `path#Symbol`. Decide where the full answer belongs. Usually that is a section of an existing page, improved or added. Otherwise it is a new page listed in the index.
4. **Propose (approval gate).** Show a table: `# | Question (as asked) | Short answer | Where the full answer goes | Asked`. Also show the exact text of each page change. Ask: apply all, some (by number), or none. Without an answer, the proposal is the deliverable.
5. **Apply.** Create `questions.md` from `templates/questions.md.tmpl` on first use and add it to the index. Add one entry per question, with its link and its sources. Make the page edits, append a `questions` entry to the log naming the pages, then run `wiki.py lint --strict`.

The rules block adds the other trigger. An agent that answers such a question during normal work adds it in the same session, so most good questions never need the harvest.

## View

1. `python <skill folder>/tools/wiki.py viewer [--editor <name>] [--out <file>]` writes one HTML file: README first, a sidebar by page kind, search, links between pages, source chips that open the editor at the symbol, diagrams that open in a zoom and pan view, and the lint result. It needs no network.
2. `python <skill folder>/tools/wiki_browser.py check-viewer <file>` opens every page, follows a link, zooms a diagram with the mouse wheel, and reports console errors. It needs Python Playwright; without it, say that the viewer was not opened.
3. Give the path. Publish a hosted copy (for example an Artifact) only when the user asks. Build that copy with `--editor none`, because editor links do not work there and the file would otherwise carry the local absolute path.
