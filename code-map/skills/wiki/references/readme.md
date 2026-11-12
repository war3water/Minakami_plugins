# The README as the front page

The root `README.md` is the wiki's front page: what the project is, and how to set it up, run, test and debug it, with a map to the wiki. It is held to the wiki's rules. Setup, commands and layout change together with the code; its command blocks are executed by `wiki.py lint --run`; and the lint checks its links.

These practices come from the README checklist of the `agent-coord-bootstrap` plugin's `review-readme` skill (sources fetched 2026-10-15, keys below). That skill reviews a README in depth for its kind of project (library, CLI, front end, back end, full stack, ML, product). When that plugin is installed, suggest `/agent-coord-bootstrap:review-readme` (`$review-readme` in Codex) for a full review; this skill does not depend on it.

## Rules

- **The README is the user's.** Keep what is correct in it, including its content and voice, and its section order unless that order hides the way in (§Order). Propose additions, replacements and moves as exact text in the approval step; write nothing before approval.
- **Every fact comes from the project.** A command, path, port, environment variable, flag or version goes in only if you found it in the project's files, and the proposal cites where. What only the user knows (the pitch, a license that is not in the repository, a screenshot) is asked, never invented. [SR, GH-R]
- **Run what you document.** Commands you can run safely are run in a temporary copy in step 1 of the build, and the rest are checked by `lint --run` after approval. Where a step differs by OS or shell (activating a virtual environment, setting an environment variable for one command), give each form the project supports, or one form that works everywhere. [PYVENV]

## What the front page needs

Apply the items the project has something for; skip the rest rather than adding empty sections.

| Section | Contents | Sources |
|---|---|---|
| Name and purpose | one sentence on what it does and who it is for; why it is useful; its status (active, experimental, deprecated) | SR, GH-R, OSG, MAR |
| Setup | prerequisites with the runtime version from the manifest, and anything the entry point needs that a default install lacks, such as a particular interpreter or a service that must be running, with how to provide it and what the program prints without it (`../../references/extraction.md` §2); install as copyable blocks marked `check:run` | SR, MAR, GH-R |
| Run | the one command to run it, and what success looks like (captured output) | SR, MAR |
| Tests | the test command; how to run one test | MAR, OSG |
| Debug | the short version: the trace switch, the committed debug configurations by name, and a link to the wiki's run-and-debug page | MAR, MOZ, MS-DX |
| Sources | where the README names a standard, handbook or paper the code follows, the name links to the wiki's `reference/sources.md` or to the repository's own chapter on it (proposed as an edit, like any README change) | — |
| Behaviour a newcomer trips over | defaults, limits, error cases and what is not supported, as the code shows them | CLIG |
| Layout | a short map of the main folders and entry points, when the root listing does not make it obvious | — |
| Documentation | links to the wiki's `index.md` and run-and-debug page, and one line saying the README is part of the wiki and changes with the code | — |
| Help, contributing, license | where to get help, how to contribute (or a link to `CONTRIBUTING.md`), and a license that matches the `LICENSE` file or the manifest | GH-R, SR, MAR, GH-C |

Longer setup, debugging and contribution detail belongs in the wiki or in `CONTRIBUTING.md`, linked from the README. [GH-R, OSG, MOZ, WTD, GH-C]

## Order

The sections follow what a new user does, in this order where the project has them: about (what it is, who it is for, and a screenshot for anything with a screen), getting started (prerequisites, install, run, check that it works), usage, configuration, development (tests and debugging), deployment, troubleshooting, documentation, then status and license. A README longer than a couple of screens opens with a table of contents. [SR, MAR, GH-R]

- **Setup before long feature lists.** A newcomer reaches the install step without scrolling past a feature narrative. When the README buries it, propose moving the long part to a wiki page (the overview, or a reference page) and leaving a short summary with a link. The user decides.
- **Only what a newcomer needs, then a link.** Configuration lists the settings someone must set to get started; the full table lives on the wiki's configuration page (`pages.md`, "One home per fact, said once"). The same goes for every flag, every script and every symptom.

The test: a newcomer who reads from the top reaches a running program before anything they could skip.

Project types add their own items. A CLI documents every flag the code parses and its exit codes. A back end documents its environment variables with their defaults and its backing services. A full-stack project gives the one command that starts both parts. An ML project gives its exact train and evaluate commands. The full list goes in one place: the README when it is short, otherwise the wiki's reference page, with the README keeping what a newcomer needs first and a link (§Order). The `review-readme` checklist has these lists in full, with their sources.

## Sources

- **SR**: Standard Readme spec. <https://github.com/RichardLitt/standard-readme/blob/main/spec.md>
- **MAR**: Make a README. <https://www.makeareadme.com/>
- **GH-R**: GitHub Docs, About READMEs. <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes>
- **GH-C**: GitHub Docs, contributor guidelines. <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors>
- **OSG**: Open Source Guides, Starting a project. <https://opensource.guide/starting-a-project/>
- **MOZ**: Mozilla Science, How to build a CONTRIBUTING.md. <https://mozillascience.github.io/working-open-workshop/contributing/>
- **WTD**: Write the Docs, beginner's guide. <https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/>
- **CLIG**: Command Line Interface Guidelines. <https://clig.dev/>
- **MS-DX**: Microsoft Code-With Engineering Playbook, developer experience. <https://microsoft.github.io/code-with-engineering-playbook/developer-experience/>
- **PYVENV**: Python docs, venv, the activation command per platform and shell. <https://docs.python.org/3/library/venv.html>
