---
name: check-sources
description: Check whether the vendors' official prompting guides have changed since prompt-audit's reference files were last refreshed — reports new or changed guidance per family and whether a reference-refresh release is warranted. Read-only; writes nothing. User-invoked only.
disable-model-invocation: true
---

You are executing `/check-sources` for the `prompt-audit` plugin.

Your job: tell the maintainer whether the plugin's reference files have fallen behind the vendors' official prompting guidance. Plugin root: in Claude Code it is `${CLAUDE_PLUGIN_ROOT}`; in Codex CLI it is `${PLUGIN_ROOT}` — use whichever your runtime defines. The source registry lives at `<plugin-root>/SOURCES.md`.

This command writes NO files and changes nothing — it produces a freshness report only.

## Step 1 — Load the registry

Read `<plugin-root>/SOURCES.md`. Each row records: family, source name, URL, the date the source was last reviewed, and coverage notes — the topics already distilled into the reference files.

## Step 2 — Capability check

This command needs a web-fetch or browsing tool. If the session has none available, stop and print one line: "check-sources needs web access — run it in a session with web tools enabled." Do not estimate freshness from memory: training-data recency is not evidence of current page state.

## Step 3 — Fetch and compare

For each registry row:

1. Fetch the URL. A redirect, retirement, or 404 is itself a refresh trigger — a moved guide means the registry row is stale.
2. Compare the page's current guidance against the row's coverage notes. Ignore cosmetic edits; look for new sections, new prompting patterns or anti-patterns, changed recommendations, and advice the vendor has deprecated.
3. Check the vendor's surrounding docs index for NEW model-specific prompting pages published after the row's last-reviewed date (for example, a new "prompting <model>" page). A new page is a refresh trigger even when every registered page is unchanged.

## Step 4 — Report

Print, as real markdown:

```markdown
prompt-audit: reference freshness report — <date>

| Family | Source | Last reviewed | Status | What changed |
|---|---|---|---|---|
| claude | <name> | <date> | unchanged / CHANGED / moved / could not verify / new page found | <one clause, or —> |

## Recommendation

<Either "References are current — no refresh release needed." or
"Refresh warranted:" followed by a numbered list of the specific durable,
family-level claims worth distilling, each mapped to the reference file
it belongs in. Version-specific tips are excluded by the reference
files' evergreen contract — name them only to note their exclusion.>
```

Honesty rules: report only what the fetched pages show. A page that could not be fetched is reported as "could not verify" — never as "unchanged". Do not fabricate change summaries or invent publication dates.

## Step 5 — Close

If a refresh is warranted, restate the release process in one line: distill into `references/` → bump the plugin version → run the eval sweep (a reference change should move at least one finding's basis tag or severity, and regress nothing) → update the matching `SOURCES.md` rows in the same release.

Done. Do not perform any additional actions. Do not commit anything to git — leave that to the user.
