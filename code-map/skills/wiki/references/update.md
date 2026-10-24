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
6. **Verify.** Render the diagrams you edited (`wiki_browser.py render`), run `wiki.py lint`, and run `wiki.py lint --run` when setup, commands or command blocks changed. Rebuild the viewer if the repository keeps one. Fix what fails, as in `build.md` §5.
7. **Report.** List the pages updated and why, the pages confirmed unchanged, new pages, uncovered code left out and why, the lint result, and the command blocks run.

## Lint

The mechanical part is `python <skill folder>/tools/wiki.py lint`, plus `--run` when the user asked for it or when setup or commands changed since the wiki's last commit. It checks links and anchors, `path#symbol` sources, index coverage, diagrams rendered from their current source, the log's format, sources changed since a page was last updated, and, with `--run`, every `check:run` block in a clean checkout.

Then review what a script cannot check, as Karpathy's lint does:

- claims the code no longer supports: check the concrete ones (defaults, limits, flags, file and folder names, error messages, command output) against the code and the captured runs;
- contradictions between pages, and between a page and the design documents `SCHEMA.md` names;
- pages no other page links to, apart from the index, and links a reader would need but that are missing;
- planned pages in the index that the code now needs, and written pages whose subject is gone.

Report the findings as a table, `# | Page | Problem | Evidence | Fix`, with evidence as a `path#symbol`, a file and line, or a command and its output. Then ask: apply all, some (by number), or none. Apply only what is approved; when you cannot get an answer, the report is the deliverable. Fixes stay inside the wiki.

## View

1. `python <skill folder>/tools/wiki.py viewer [--editor <name>] [--out <file>]` writes one HTML file: README first, a sidebar by page kind, search, links between pages, source chips that open the editor at the symbol, diagrams that open in a zoom and pan view, and the lint result. It needs no network.
2. `python <skill folder>/tools/wiki_browser.py check-viewer <file>` opens every page, follows a link, zooms a diagram with the mouse wheel, and reports console errors. It needs Python Playwright; without it, say that the viewer was not opened.
3. Give the path. Publish a hosted copy (for example an Artifact) only when the user asks. Build that copy with `--editor none`, because editor links do not work there and the file would otherwise carry the local absolute path.
