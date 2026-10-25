# code-cleanup

Cleans up a codebase so a maintainer can read, debug, and change it, without changing what it does: from one
targeted change, to removing dead code and junk, to flattening call paths that jump through needless layers,
to a full overhaul, or only a map and a plan. One `SKILL.md` serves every runtime.

## Install

From this marketplace (see the [repository README](../README.md) for the one-command installer):

```bash
claude plugin install code-cleanup@minakami-plugins   # Claude Code
codex plugin add code-cleanup@minakami-plugins        # Codex CLI
```

Grok Build loads the plugins installed in Claude Code (its Claude compatibility is on by default), so the
Claude Code install covers it. Without Claude Code, install it in Grok directly:
`grok plugin install war3water/Minakami_plugins#code-cleanup`.

Another agent that loads Agent Skills folders (a folder with a `SKILL.md` that has `name` and `description`)
can use `skills/code-cleanup/` as it is: copy the folder into that agent's skills folder.

## How to ask

Start the request with the skill's name in your runtime's form:

| Runtime | Start the request with |
|---|---|
| Claude Code | `/code-cleanup:code-cleanup` |
| Codex CLI | `$code-cleanup` (interactive sessions only: `codex exec` doesn't load plugin skills) |
| Grok Build | `/code-cleanup:code-cleanup`, or `/code-cleanup` when no other skill has that name |

You don't need to investigate anything first. The prompts below use the Claude Code form.

| You want | Type | Tested |
|---|---|---|
| A whole-repo cleanup, nothing to fill in | `/code-cleanup:code-cleanup Clean up this repository so it's easy to read, debug, and change, without changing what it does.` | better than without the skill on both models |
| The same, when you can say what hurts | `/code-cleanup:code-cleanup <what hurts, in your words>. Clean it up without changing what it does.` | both models, with the larger gain |
| One command or feature only | `/code-cleanup:code-cleanup <the command or feature> goes through layer after layer before it reaches <where the work happens>. Flatten that path so it's easy to read and debug. Don't change anything else.` | both models |
| A map and a plan, no edits | `/code-cleanup:code-cleanup Review this repository: map its structure and its problems, and propose a cleanup plan. Don't change any files.` | both models |
| Only remove cruft, keep the structure | `/code-cleanup:code-cleanup Tidy this repository: remove dead code, junk files, duplicated logic, and docs that don't match the code. Keep its structure and what it does.` | a clear gain on Opus only; on Sonnet, about the same as without the skill |

- **You don't have to pick a level.** On whole-repository cleanups, the first line did as well as naming the
  right level (Tidy, Reorganize, or Overhaul).
- **Say what hurts, not how to fix it.** For one path, name where it starts and where the work happens.
  "Make one targeted change: flatten the path of X" tended to flatten only part of it.
- **Add facts only you know**, if you have them. Append a line such as `Facts the repository can't show:
  nothing outside this repo imports the internal modules; the TSV export is retired, and removing it is
  wanted.` Without such facts the skill leaves those items alone and asks about them in its report.
- **At the keyboard, a vague request may get one question first.** Answer its questions and name the level:
  replying only "go ahead" gave the most timid cleanup tested. To have it just go, end the request with "I'm
  away until you finish, so decide yourself and flag anything that needs me." Every prompt above was tested
  that way.
- **The name alone, with no request,** surveys the project, changes nothing, and asks which level to do and
  what the repository can't show.
- **It never commits, tags, or stashes.** Read the diff and its report: what changed, what it left alone and
  why, each command's path before and after, and its questions for you.

### The template, for the most control

```text
/code-cleanup:code-cleanup
Goal: <what hurts and what you want, in your own words>
Level: <Targeted: <the one change> | Tidy | Reorganize | Overhaul | Report only>
Scope: <the whole repository | only <path or feature>; leave everything else as it is>
What the repository can't tell you:
- <a fact about the outside world, e.g. "nothing outside this repo imports the internal modules">
- <another, e.g. "the TSV export is retired; removing it is wanted">
Preferences: bug fixes reported, not fixed; don't commit; I'm away until you finish, so decide yourself and flag anything that needs me.
```

It costs about 1.5 times as much as a one-line request, because it also carries out the decisions your facts
settle.

| Line | What to write | Leave it out when |
|---|---|---|
| Goal | the pain, not the solution: "a simple command jumps through six files" | never; it is the request |
| Level | from the table below | you don't know; the skill picks one and says why |
| Scope | what may change; for one path, add "leave everything else as it is" | the whole repository is fair game |
| What the repository can't tell you | who outside uses what (other apps, deploys, cron, partners), and what is retired or still wanted | you know nothing of the kind |
| Preferences | as written | you're at the keyboard and want questions first: drop "I'm away…" |

| Your situation | Level |
|---|---|
| Really messy, no clear logic, conflicting functions, hard to maintain | `Overhaul` |
| The structure is fine; remove dead code, junk files, duplicates, and stale docs | `Tidy` |
| Hard to follow or debug: needless layers, multi-hop calls, god functions, import cycles | `Reorganize` |
| One path or one feature only | `Targeted: <that change>` |
| A map and a plan first, no edits | `Report only` |

## Safety

In testing, no run in any form failed a hidden behavior test or left a module that fails to import, every
one-path run kept to its scope, and every plan-only run left the project as it was. Reviewers still found an
occasional behavior change the report didn't flag, such as two merged validators that then accepted input the
original rejected. Review the diff.

## How it was tested

Each prompt above ran headless in Claude Code on Claude Opus 5.5 and Sonnet 5.5, on 11 messy Python projects
built for each level, and was compared with the exact same text without the skill. Two blind reviewers
(GPT-6-Astra and a fresh Opus 5.5) scored every run, and hidden behavior tests and scripted checks graded it.
"Both models" means the skill scored at least 0.2 higher, on a 1 to 5 scale, on each model. The skill cost
about 1.1 to 1.7 times as much as the same prompt without it.

The projects were Python CLI tools and libraries of about 20 to 50 files; other languages and much larger
codebases weren't tested. The same `SKILL.md` runs in Codex CLI and Grok Build but wasn't scored there. The
test projects and results are kept outside this repository.

## Notes for maintainers

The agent loads `SKILL.md` on every invocation, and the campaign reference only when the user asks for an
ongoing cleanup.

### Files

| File | Loaded when |
|---|---|
| `skills/code-cleanup/SKILL.md` | every invocation: goal, levels, unclear-request handling, survey, the Reorganize and Overhaul procedure, the rules for each kind of change, when to ask, leftovers, report |
| `skills/code-cleanup/references/campaign-mode.md` | the user asks for an ongoing or exhaustive cleanup |
| `skills/code-cleanup/assets/cleanup_ledger.md` | a campaign keeps its state in a copy of this template |
| `skills/code-cleanup/scripts/dead_candidates.py`, `skills/code-cleanup/scripts/hotspots.py` | deterministic helpers (see `scripts/README.md`) |

`SKILL.md` declares `allowed-tools: Read(${CLAUDE_SKILL_DIR}/**)` so that Claude Code reads the bundled files
without a permission prompt; other runtimes ignore the field.

### Design

- **Self-sufficient `SKILL.md`.** In testing, agents almost never opened reference files the skill told them
  to read before a restructure, so everything a normal run needs is in `SKILL.md`. Only the campaign
  procedure, which the user asks for explicitly, stays in a reference.
- **Close to a good general prompt.** Each rule is stated once, in plain words, with its reason. There are no
  tier tables or private vocabulary: when blanket rules were tested, models followed them literally, and they
  failed in both directions (holding back requested changes, or deleting code an outside config could
  select).
- **Rules tied to observed failures.** The rules for each kind of change exist because their absence broke
  behavior in testing: look-alike merges that change rounding or formatting, collapsed layers that drop error
  translation, renamed stored keys, removed side-effect imports, deletions of code reached by name, by cron, or
  by an outside config, bug fixes slipped into a cleanup, orphaned modules, and docs or examples left stale.
- **Asks when it should.** An empty or vague request gets a short survey and one question offering the levels;
  decisions that depend on facts outside the repository (outside consumers, deploy tooling) are asked or
  flagged, not guessed.
- **Flattening as a first-class goal.** Reorganize maps each command's call path, folds pass-through steps into
  their caller or callee, keeps steps that do real work, and reports the paths before and after.
- **A report-only request gets a full plan.** Findings with evidence, each command's path, the steps in order
  with what to verify before each, and the questions only the user can answer.

Keep it generic: a rule belongs here only if it applies to most projects. Don't add rules shaped around one
test case or one codebase. Before changing the advice in "How to ask", re-test the changed `SKILL.md` with the
same prompts, with and without the skill, on both models, and keep the results outside this repository.

### Background reading

- Fowler, *Refactoring* (2nd ed.), <https://refactoring.com/catalog/>; *Strangler Fig* and *Branch by
  Abstraction* on martinfowler.com.
- Feathers, *Working Effectively with Legacy Code*: seams and characterization tests.
- Ousterhout, *A Philosophy of Software Design*: deep modules and shallow wrappers.
- Ellnestam and Brolund, *The Mikado Method*.
- Tornhill, *Software Design X-Rays*: hotspots (churn × size).
- Lemaire, *Refactoring at Scale*.
- Romano et al., "A Multi-Study Investigation into Dead Code", IEEE TSE 2018.
- "Agentic Refactoring: An Empirical Study", arXiv 2511.04824: agentic refactors often tangle with feature
  changes.
- "LLMs in Automated Software Refactoring" (RefactoringMirror), arXiv 2411.04444: deterministic re-application
  of LLM refactors.
