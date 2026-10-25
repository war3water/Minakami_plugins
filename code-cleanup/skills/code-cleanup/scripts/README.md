# Scripts

Two deterministic, stdlib-only helpers. Both report candidates or rankings; neither changes anything.

## `dead_candidates.py`: dead-code candidates (Python only)

```bash
python scripts/dead_candidates.py [--root .] [--prod DIR ...] [--tests DIR ...] [--json out.json]
```

Lists top-level functions and classes that are never referenced (`ZERO_REF`) or referenced only by tests
(`TEST_ONLY`, which coverage reports miss), and modules no production code imports (`ORPHAN_MODULE`,
`TEST_ONLY_MODULE`). Pass the project's real source and test directories; without them it auto-detects a
`src`/`app`/`lib`/`source` layout or the top-level packages (plus `scripts`/`tools`) and prints what it
scanned.

It also tags the candidates that are probably live anyway: named in a non-Python file (`NAMED_IN`: config,
docs, crontab, CI), defined in a module that is looked up by name (`LOOKED_UP`: `getattr` with a built string,
`vars(module)`), run as a script (`SCRIPT`), loaded by computed imports (`DYNAMIC_IMPORT`), `DECORATED`, or
`PUBLIC`. Every candidate still needs the check in SKILL.md ("Deleting"). For other languages, do that check
by hand (LSP "Find References", production vs test references).

## `hotspots.py`: churn × size

```bash
python scripts/hotspots.py [--root .] [--days 365] [--top 30]
```

Ranks tracked files by commit churn times current line count, to order problems already found by likely
pain. It only ranks files changed in the window, so it never decides what to inspect: problems in code nobody
touches are found by reading, not by this script.
