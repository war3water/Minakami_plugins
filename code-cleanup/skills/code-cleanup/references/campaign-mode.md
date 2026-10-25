# Campaign mode: an ongoing cleanup

Use only when the user asks for an exhaustive, whole-repository, or ongoing cleanup, or says "keep going". A
campaign runs in rounds across sessions, so its state lives in a ledger file, not in the conversation.

## Start

- Agree the scope with the user: the goal, an acceptable end state ("clean enough", never "perfect"), how many
  files to change per round, and how many rounds before stopping to report.
- Copy `assets/cleanup_ledger.md` to `.agent_works/code-cleanup/CLEANUP_LEDGER.md` (excluded from git as
  SKILL.md describes; commit it only if the user wants). A fresh session reads it and continues.
- List every source file in the ledger's coverage table, so what hasn't been reviewed is always visible. Order
  the work by pain: churn (`scripts/hotspots.py`), size, and how often a file is involved in the problems
  found. Churn orders the work; it never hides a problem in code nobody touches.

## Each round

1. Survey the next files and add each real problem to the ledger with its evidence (a dead reference, a
   duplicate with drift, a command you can't trace, a stale doc claim). Taste alone doesn't qualify.
2. Work a batch of the highest-value items within the round's budget, following SKILL.md. Items that need a
   yes go to the user as one batched list.
3. Problems you notice mid-change go in the ledger as parked items, not into the current change.
4. Update item states and file coverage in the ledger.

## Uncertain deletions

A campaign can do what a single pass can't: for code you can't prove dead, keep its behavior and add a log
line where it is entered, then delete it in a later round only if real runs show it never fired. Remove every
such log line before the campaign ends; one left behind is a new leftover.

## Stop

Stop and summarize when a full survey round finds nothing new and every file is reviewed or waived, when the
budget runs out (ask whether to extend), or when the agreed end state is reached. Changes that undo an
earlier round's changes mean the campaign is churning: stop and report.
