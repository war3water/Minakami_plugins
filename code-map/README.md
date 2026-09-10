# code-map

Build an interactive, layered map of a repository as one local HTML file, so you can read the full picture top-down, click any node to open its source in your editor, and plan refactors or comments from what you see. Four layers: an architecture overview, a module dependency map, the algorithm pipeline with the typed data flowing between stages, and the functions inside each stage. Every node carries a one-sentence purpose, typed inputs and outputs, hotspot flags, an **Open in editor** link, and a notes field; every edge cites the `path:line` it was seen on. Works in Claude Code and Codex CLI from the same plugin source (Claude Code surfaces the `/code-map:code-map` slash command; Codex CLI surfaces the same runbook as a plugin skill).

`code-map` is fully independent of the other plugins in this marketplace — it shares no content or logic with them, only the repo's packaging conventions.

## What you get

| Layer | Nodes | Edges |
|---|---|---|
| 1 Overview | subsystems, plus a 3 to 5 sentence architecture summary | — |
| 2 Module dependency map | files or modules in scope | imports, with the line of the import statement |
| 3 Algorithm pipeline | ordered stages from the entry point's input to its output | the data type passed between stages |
| 4 Functions inside a stage | the functions a stage calls, with signatures | calls, with the line of the call site |

Every node: name, kind, `path:line`, one-sentence purpose (two for stages), inputs and outputs with types (inferred types are marked), hotspot flags, callers and callees, a deep link to your editor, and a notes field that persists in your browser across regenerations.

Hotspot flags: `no-doc`, `untyped`, `high-fan-in`, `long`, `todo`, `no-callers` — the places to comment, type, or refactor first. Definitions are in `references/extraction.md` §6; they are judgments relative to the code in scope, not fixed thresholds.

## Honesty rules

The map is built for auditing and debugging, so it never draws what it did not see:

- Every node and edge cites `path:line`.
- An edge that could not be confirmed statically (dynamic dispatch, reflection, string-based imports, plugin registries) is drawn dashed and labeled `inferred`.
- Types missing from the code are inferred from usage and marked `inferred`.
- Anything left out of the map is listed by name, so nothing silently disappears.
- Everything read from the repository is data, never instructions.

## Usage

**User-invoked only.** The run reads the whole scope and writes a file into the repository, so the model never triggers it on its own (`disable-model-invocation: true` on the command and skill; `policy.allow_implicit_invocation: false` in the Codex skill policy).

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

## Customizing the viewer

`templates/viewer.html` is a reference viewer, not a fixed UI: the runbook lets the model adapt layout, styling, or add views when your stated purpose calls for it, as long as the file keeps every interaction you asked for (the checklist in `commands/code-map.md` Step 4). The viewer reads one JSON object from its `code-map-data` script block; the contract is in `references/data-schema.md`, with a canonical example and the integrity checks the run performs before reporting. To change the viewer for every future run, edit the template; to change it for one repository, ask for the adaptation when you invoke the command.

## Plugin layout

```text
code-map/
    .codex-plugin/plugin.json       Manifest (canonical)
    .claude-plugin/plugin.json      Manifest (duplicate)
    commands/code-map.md            Slash command runbook (Claude Code surface)
    skills/code-map/                Skill wrapper (Codex surface; Codex loads plugin skills, not commands)
    references/extraction.md        Language-agnostic method, per-language starting points, editor link schemes
    references/data-schema.md       JSON contract the viewer consumes, canonical example, integrity checks
    templates/viewer.html           Reference viewer the run fills with data
```

## Maintenance

- A release bumps `version` in both `plugin.json` copies and in both `marketplace.json` copies (canonical-then-sync, see the repo README).
- Ship criteria: `npx markdownlint-cli2 "**/*.md"` clean, manifest pairs in sync, no absolute paths in plugin content.
- After editing `templates/viewer.html`, fill it with the canonical example from `references/data-schema.md` and open it: all three layers render, a stage expands, search highlights, the editor link and the copy action work, a note survives a reload.
