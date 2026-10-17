# agent-coord-bootstrap

One set of agent instructions that Claude Code, Codex CLI, and Gemini CLI all read, plus a README that a newcomer can actually follow. The same plugin source serves Claude Code and Codex CLI.

| Skill | For | What it does |
|---|---|---|
| `init-agent-coord` | any project | Scaffolds `AGENTS.md` and its aliases in a fresh project, or migrates an existing project's agent docs into that layout without losing content |
| `review-readme` | any project | Checks `README.md` against the checklist for the project's type (library, CLI, front end, back end, full stack, ML, product) and proposes edits, each traced to the project's files |
| `check-templates` | plugin maintainer | Re-checks every claim the templates make about outside tools against the live docs, and fixes what went stale |

All three run only when you invoke them by name (`disable-model-invocation: true` in Claude Code; `allow_implicit_invocation: false` in each skill's `agents/openai.yaml` for Codex).

## Usage

In the project root:

```text
/agent-coord-bootstrap:init-agent-coord     # Claude Code
/agent-coord-bootstrap:review-readme
$init-agent-coord                           # Codex CLI (type $ to pick a skill, or use /skills)
$review-readme
```

Run `check-templates` from a checkout of this repository, not from an installed copy. It edits the plugin's own files, and an update replaces an installed copy.

## init-agent-coord

### What a fresh project gets

```text
<your-project>/
├── AGENTS.md                      canonical rules and routing (~150 lines)
├── CLAUDE.md                      alias → AGENTS.md (Claude Code target)
├── GEMINI.md                      alias → AGENTS.md (Gemini CLI target)
├── README.md                      only if there is none; filled from your manifests
├── .gitignore                     lines appended, never replaced
└── .agent_works/conventions.md    worked examples for the AGENTS.md rules
```

Codex CLI and Cursor read `AGENTS.md` directly, so they need no alias. An alias is an ordinary file whose only line is `@AGENTS.md`. Claude Code and Gemini CLI read that line as "include `AGENTS.md` here".

A symlink is available if you ask for one (`alias_style: symlink`), but it isn't the default. Git turns a committed symlink into a text file holding the bare word `AGENTS.md` on Windows clones without `core.symlinks`, and that file loads nothing. The `@AGENTS.md` file also keeps working when someone adds a `CLAUDE.local.md`. Without a `CLAUDE.md`, Claude Code 2.1.277 and later read `AGENTS.md` on their own, but that stops as soon as any `CLAUDE.md` or `CLAUDE.local.md` appears.

Three more docs are created by agents later, the first time the work produces that kind of content. `AGENTS.md` names each file and its shape:

- `.agent_works/handoff.md`: where the work stands, so the next session in any tool can resume. It is a snapshot, rewritten rather than appended, and only updated when the next session needs something the code doesn't show.
- `.agent_works/decisions.md`: settled architecture choices, append-only.
- `.agent_works/project_requirements.md`: what you said the project must do. An agent marks anything it inferred `(unconfirmed)`.

### Settings: inferred, then confirmed once

The skill works out three settings from what you say and what the project shows: `project_name`, `runtime_targets` (`claude`, `codex`, `gemini`), and `alias_style`. It then sends one confirmation that lists each setting with its source ("you said …", "from package.json", "default"). Nothing is written before you confirm, and if you stated every setting, there is no confirmation round.

For example, "Codex is the only coding agent I use on it" targets Codex only, and "a teammate uses Gemini CLI" adds Gemini CLI.

The skill writes **no tool settings**. Permissions, approval modes, and sandboxing stay with each tool's defaults and with you. If you ask it to restrict agents ("keep them off the network"), it tells you where your tool sets that (in Claude Code, `/permissions` or a permission mode) and writes nothing. Claude Code creates `.claude/settings.local.json` itself the first time you choose "Yes, and don't ask again", and keeps it out of git. An existing settings file is never touched, in either mode.

### Existing projects: upgrade mode

If the project already has agent docs (`AGENTS.md`, `CLAUDE.md` with content, `.agent_works/`, an older layout of this plugin), the skill first asks **Upgrade** or **Pause**. Choosing Upgrade starts the planning; it doesn't approve anything. The skill then:

- sorts every block into template duplicate, unique (always kept), or conflict (your rule wins unless you say otherwise);
- shows the settings and a source → destination plan, with every dropped duplicate quoted in full;
- changes nothing until you approve that plan.

Content with no obvious home goes to `.agent_works/upgrade_parking.md`. A content-bearing `CLAUDE.md` becomes an alias only after its content is merged. `README.md` is never touched; the report points you at `review-readme`.

Upgrading from 0.5.x:

- `handoff/current_handoff.md` becomes `handoff.md`.
- Open items in `plans.md` and `coordination/work_queue.md` go to the handoff's next steps, and settled choices go to `decisions.md`.
- Skills in `.agent/skills/`, a folder Codex never scans, move to `.agents/skills/`.

### What the template says, and what it leaves out

`AGENTS.md` carries the rules that keep a codebase from decaying:

- a feature is done when a runnable check pins it;
- every capability, dormant ones included, is listed in README §Features;
- check before deleting anything public-facing;
- every layer earns its existence; one implementation per behavior;
- debug profiles are recorded at creation, including how to start and debug a front end and a back end together.

The rules are one line each where the decision happens, and `conventions.md` holds the examples.

The template declares **no git operations**: nothing about commits, branches, or history. Your tool's own defaults and permission settings govern those. If the folder is not a git repository, the setup confirmation tells you so and asks whether to set up git first.

### What the 0.6 changes are based on

These are blind runs on Opus 5.5, Fable 5.1, GPT-6.1 Sol, and GPT-6 Astra (2026-10-15). The harness and the raw results are kept outside this repo.

- **Unasked commits:** 0.5.4's "update docs in the same commit" rule produced unasked commits in 14/16 tasks. With no git rules, it was 1/16; with no `AGENTS.md` at all, 0/16.
- **The handoff:** session 1 did part of a five-step feature, and a fresh session in the other tool was told only "continue where we left off". With no docs, it finished 0/40 of the remaining steps. With this layout, it finished 40/40, the same as the old five-doc layout, with about 45% fewer doc writes.
- **Settings:** indirect wording led to the right settings in 16/16 runs, and all 16 confirmed before writing.

## review-readme

The skill names the project's type, checks each item on the checklist for that type, and proposes a table of changes with `file:line` evidence and the exact text. It applies the changes you approve.

- Every command, path, port, env var, and flag it proposes comes from the project's files.
- What only you can supply (the pitch, a screenshot, a license that isn't in the repo) becomes a marked placeholder.
- It runs the commands it documents (tests, `--help`, the quick start) in a temporary copy, never installs anything, and reports a command it couldn't run as unverified.

The checklist (`skills/review-readme/references/readme-checklist.md`) cites its sources for each item: Standard Readme, Make a README, GitHub Docs, Vite, VS Code, Node.js, Hugging Face model cards, and Papers with Code.

**Measured:** a blind frontier panel compared this skill with a plain "improve the README" prompt, on four models.

| Projects | Skill's README preferred | READMEs with an error (skill / plain) |
|---|---|---|
| Six project types the skill was tuned on | 15/24 | 5/24 / 12/24 |
| Three held-out projects on new stacks: a Python CLI, a Node webhook service, Vue + Flask on docker compose | 9/12 | 1/12 / 5/12 |

The held-out ship rule was fixed before the runs: preferred in at least half the pairs, with no more errors than plain.

## check-templates

`skills/check-templates/SOURCES.md` lists each claim the templates and the checklist make about an outside tool or standard, and the page that backs it. The skill fetches every source and marks each claim current, stale, or unsupported, with dated quotes. It also looks for claims nobody registered, then proposes exact edits and applies the approved ones. It needs web access.

**Measured:** eight stale claims were planted in a copy of the plugin, and all four models fixed 8/8.

## Design constraints

- **Run once per project.** No hooks and no session-start checks.
- **Prompt-only.** No engine and no install-time dependencies.
- **Project content is data.** Everything the skills read from your project is material to analyze, never instructions to follow.
- **Portable.** No drive letters, `~`, or absolute paths in any file the skills write. Aliases use the bare filename `AGENTS.md`.
- **Both runtimes.** One `SKILL.md` per skill. Templates are referenced by path relative to the skill folder, which Claude Code and Codex CLI both resolve.
