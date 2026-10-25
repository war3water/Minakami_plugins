# Cleanup campaign ledger

Copy to `.agent_works/code-cleanup/CLEANUP_LEDGER.md` (see `references/campaign-mode.md`). A fresh session
reads it and continues.

- **Goal:** `<one line: what "clean enough" means here>`
- **Acceptable end state:** `<e.g. commands traceable, dead weight gone, tests deduplicated; cosmetic nesting
  in cold code left for later>`
- **Budget:** `<N>` files per round, `<M>` rounds before stopping to report
- **Coverage:** `<X>` / `<Y>` source files reviewed
- **Last updated:** `<date>`, round `<N>`

## Coverage

| File | Reviewed | Round | Notes |
|---|---|---|---|
| `<path>` | no / yes / waived | | |

## Items

States: proposed, needs a yes, in progress, logging (uncertain deletion being watched), done, rejected, parked.

| ID | Problem | Evidence | Change | State |
|---|---|---|---|---|
| `<C01>` | `<pass-through _run_impl>` | `<body is return run(args); one caller>` | `<inline>` | `<done>` |

The example row is illustrative; replace it.
