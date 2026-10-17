# Template source registry

Read by `check-templates`. Each **claim** is a statement in this plugin's skills or templates about an outside tool or standard. Each claim names the **sources** that back it. A release that changes a template updates the matching rows, and `Last verified` changes only when a check actually fetched the source.

Paths in the File column are relative to the plugin's `skills/` folder.

## Sources

| ID | Source | URL | Last verified |
|---|---|---|---|
| S-CC-MEMORY | Claude Code: memory (CLAUDE.md, imports, AGENTS.md) | <https://code.claude.com/docs/en/memory> | 2026-10-17 |
| S-CC-BP | Claude Code: best practices | <https://code.claude.com/docs/en/best-practices> | 2026-10-15 |
| S-CC-SKILLS | Claude Code: skills | <https://code.claude.com/docs/en/skills> | 2026-10-15 |
| S-CC-PLUGINS | Claude Code: plugins reference | <https://code.claude.com/docs/en/plugins-reference> | 2026-10-15 |
| S-CC-PERMS | Claude Code: permissions (`/permissions`, permission modes) | <https://code.claude.com/docs/en/permissions> | 2026-10-17 |
| S-CC-SETTINGS | Claude Code: settings files | <https://code.claude.com/docs/en/settings> | 2026-10-17 |
| S-CODEX-AGENTS | Codex: AGENTS.md discovery | <https://learn.chatgpt.com/docs/agent-configuration/agents-md> (moved from developers.openai.com/codex/guides/agents-md) | 2026-10-15 |
| S-CODEX-SKILLS | Codex: skills | <https://learn.chatgpt.com/docs/build-skills> (moved from developers.openai.com/codex/skills) | 2026-10-15 |
| S-GEMINI | Gemini CLI: GEMINI.md context files | <https://geminicli.com/docs/cli/gemini-md/> | 2026-10-15 |
| S-AGENTSMD | agents.md | <https://agents.md/> | 2026-10-15 |
| S-SKILLSPEC | Agent Skills specification | <https://agentskills.io/specification> | 2026-10-15 |
| S-SR | Standard Readme spec | <https://github.com/RichardLitt/standard-readme/blob/main/spec.md> | 2026-10-15 |
| S-MAR | Make a README | <https://www.makeareadme.com/> | 2026-10-15 |
| S-GH-R | GitHub Docs: About READMEs | <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes> | 2026-10-15 |
| S-GH-C | GitHub Docs: contributor guidelines | <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors> | 2026-10-15 |
| S-AR | awesome-readme | <https://github.com/matiassingers/awesome-readme> | 2026-10-15 |
| S-ART | awesome-README-templates | <https://github.com/elangosundar/awesome-README-templates> | 2026-10-15 |
| S-VITE | Vite: server options; env and mode | <https://vite.dev/config/server-options>, <https://vite.dev/guide/env-and-mode> | 2026-10-15 |
| S-CRA | React blog: sunsetting Create React App | <https://react.dev/blog/2025/02/14/sunsetting-create-react-app> | 2026-10-15 |
| S-NODE | Node.js: debugging | <https://nodejs.org/en/learn/getting-started/debugging> | 2026-10-15 |
| S-VSC | VS Code: debug configuration (compounds) | <https://code.visualstudio.com/docs/debugtest/debugging-configuration> | 2026-10-15 |
| S-HF-M | Hugging Face: model cards | <https://huggingface.co/docs/hub/model-cards> | 2026-10-15 |
| S-PWC | Papers with Code: ML code completeness checklist | <https://github.com/paperswithcode/releasing-research-code> | 2026-10-15 |
| S-PYVENV | Python docs: venv (activation per platform and shell) | <https://docs.python.org/3/library/venv.html> | 2026-10-17 |

## Claims

| ID | File | Claim (topic, as the file states it) | Sources |
|---|---|---|---|
| C1 | `init-agent-coord/SKILL.md` Step A5; `init-agent-coord/templates/AGENTS.md.tmpl` §7; `conventions.md.tmpl` Alias mechanics | Codex CLI and Cursor read `AGENTS.md` directly; no alias file needed | S-CODEX-AGENTS, S-AGENTSMD |
| C2 | `init-agent-coord/SKILL.md` Steps A3, A5; `conventions.md.tmpl` Alias mechanics | A one-line `@AGENTS.md` file is an import that Claude Code and Gemini CLI resolve (the default alias) | S-CC-MEMORY, S-GEMINI |
| C3 | `init-agent-coord/templates/AGENTS.md.tmpl` §7 | Claude Code reads `CLAUDE.md`, so it gets an alias of `AGENTS.md`. (It reads `AGENTS.md` itself from v2.1.277, but only when no `CLAUDE.md` or `CLAUDE.local.md` is in the folder or above; the alias keeps it loading either way.) | S-CC-MEMORY |
| C4 | `init-agent-coord/templates/AGENTS.md.tmpl` §7 | Gemini CLI reads `GEMINI.md` (symlink or `@AGENTS.md`) | S-GEMINI |
| C5 | `init-agent-coord/SKILL.md` Step B2 | Codex scans `.agents/skills/`, not `.agent/skills/` | S-CODEX-SKILLS |
| C6 | `init-agent-coord/SKILL.md` Step A3 | Claude Code permissions are set in the tool (`/permissions`, a permission mode); it writes `.claude/settings.local.json` itself and keeps that file out of git, so the skill writes no settings | S-CC-PERMS, S-CC-SETTINGS |
| C8 | `init-agent-coord/templates/AGENTS.md.tmpl` §8 | The keep-or-cut test: "would removing it cause a mistake?" | S-CC-BP |
| C9 | every `SKILL.md` frontmatter | `disable-model-invocation: true` keeps Claude Code from invoking a skill on its own; Codex needs `agents/openai.yaml` with `allow_implicit_invocation: false` | S-CC-SKILLS, S-CODEX-SKILLS |
| C10 | every `SKILL.md` | Skill format: `name` and `description` required; files referenced by relative path from the skill folder | S-SKILLSPEC, S-CC-SKILLS |
| C11 | `conventions.md.tmpl` Debugging; `README.md.tmpl` Debug; `readme-checklist.md` Full stack | VS Code `compounds` start several launch configurations together (client + server) | S-VSC |
| C12 | `README.md.tmpl` Debug; `readme-checklist.md` Front end | Vite dev-server default port, and that it shifts when busy | S-VITE |
| C13 | `readme-checklist.md` Front end | `VITE_*` env values are exposed to the client and must not hold secrets | S-VITE |
| C14 | `readme-checklist.md` Back end | Node's `--inspect` default host and port | S-NODE |
| C15 | `readme-checklist.md` Sources | Standard Readme section order (License last) and that it targets libraries | S-SR |
| C16 | `readme-checklist.md` intro | Make a README: "Every project is different, so consider which of these sections apply to yours." | S-MAR |
| C17 | `readme-checklist.md` How to use | README holds the get-started minimum; CONTRIBUTING may live in root, `docs/`, or `.github/` | S-GH-R, S-GH-C |
| C18 | `readme-checklist.md` Sources; `conventions.md.tmpl` README vs AGENTS.md | awesome-readme is a curated example list without per-type rules | S-AR |
| C19 | `readme-checklist.md` Sources | awesome-README-templates collects GitHub profile READMEs | S-ART |
| C20 | `readme-checklist.md` Sources | Create React App is deprecated for new apps | S-CRA |
| C21 | `readme-checklist.md` ML or data | Model-card content: intended use, limitations, training data, evaluation, get-started snippet | S-HF-M |
| C22 | `readme-checklist.md` ML or data | ML code completeness: dependencies, training and evaluation code, pre-trained models, results table with commands | S-PWC |
| C23 | `init-agent-coord/SKILL.md` Steps A5, B2; `conventions.md.tmpl` Alias mechanics | Git checks a committed symlink out as a plain text file on Windows without `core.symlinks`, so the alias is a pointer file by default | S-CC-MEMORY |
| C25 | `readme-checklist.md` Baseline; `README.md.tmpl` Install | Activating a Python virtualenv takes a different command per platform and shell | S-PYVENV |
