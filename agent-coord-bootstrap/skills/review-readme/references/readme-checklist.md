# README checklist by project type

Bracketed keys name the source behind an item (list at the bottom). An item marked `[no source]` is this plugin's own judgment. No source defines one README layout for every type: Make a README says "Every project is different, so consider which of these sections apply to yours." This checklist assembles the per-domain sources into one list per type.

## How to use it

- Apply the **Baseline** plus every type that fits. A project can be several types at once. Full stack means front end + back end + the full-stack items.
- Skip an item the project has nothing for. For example, a library with no configuration needs no config section.
- **Placement.** The README holds what someone needs to get started using and contributing, including a short Development section. Longer setup, debugging and contribution detail goes in `CONTRIBUTING.md` (repo root, `docs/`, or `.github/`) and is linked from the README. [GH-R, OSG, MOZ, WTD, GH-C]

## Baseline (every type)

- Name, plus one sentence on what it does and who it is for. [SR, GH-R, OSG]
- Why it is useful. Its status: active, experimental, or deprecated. [GH-R, MAR, GDG]
- Get started, as copyable code blocks:
  - prerequisites, with the runtime version from the manifest
  - install
  - the one run command and what success looks like [SR, MAR, GH-R]
  - where a step differs by OS or shell (activating a virtualenv, setting an env var for one command), each form the project supports, or one form that works everywhere [PYVENV, no source for the general case]
- Verify: the test command. [MAR, OSG]
- Behavior a newcomer will trip over, as the code shows it: defaults, limits, error cases, and what is not supported. [CLIG, no source for the general case]
- A short map of the main folders and entry points, when the layout isn't obvious from the root listing. [no source]
- Development: the config or env vars to set, how to run the tests (all, and one), and how to start the project with a debugger attached. Link `CONTRIBUTING.md` if it exists. [MAR, MOZ, MS-DX, STRTMA]
- Where to get help, how to contribute, and a license that matches the `LICENSE` file or the manifest's license field. [GH-R, SR, MAR]

## Library or algorithm

- Install block, including the local or editable install when the package isn't published. [SR]
- An import-and-use example, with its output. [SR, MAR]
- API: exported functions and classes, their signatures, and their caveats, or a link to an API document. [SR]
- Algorithm notes: complexity, assumptions, and edge cases, as the code and its docstrings state them. [no source]
- Development: run all tests, run one test, and debug a failing test, e.g. `pytest --pdb` or a committed launch profile. [MAR, STRTMA, VSC]

## CLI

- Install, then usage led by examples. [SR, CLIG]
- Every flag and argument the code parses, and `--help`. [SR, CLIG]
- Exit codes, when the program defines them. [CLIG]
- Config files and env vars it reads. [CLIG, 12F]
- A terminal recording or sample output. [MAR]
- Development: run it from source, and run it under a debugger (e.g. `node --inspect-brk`, `python -m pdb`). [NODE, no source for the README requirement]

## Front end

- Screenshot or demo. [MAR]
- The runtime version, and the dev-server command with its URL. Vite's default port is 5173 and shifts if that port is busy. [MAR, VITE]
- Env vars, and which ones reach the browser. `VITE_*` values are client-visible and must not hold secrets. [VITE]
- Build and preview commands, and the test command. [MAR]
- Development: the browser or IDE debug profile, if one is committed (e.g. a `launch.json` Chrome configuration). [VSC]

## Back end or API

- Install and run, with the exact server command, and the development command that restarts on change when the project has one. [SR, MAR]
- Configuration as env vars: each variable, whether it is required, and its default. Point to `.env.example` if one exists, and say how its values get loaded: the app reads the file, a flag loads it (e.g. `node --env-file=.env`), or the reader exports them. Copying `.env.example` does nothing when nothing reads it. [12F, NODE-CLI]
- Backing services (database, queue): how to start them, e.g. `docker compose up`, and any setup step such as migrations. [DC, 12F]
- Endpoints, or a link to the API docs the framework serves (e.g. FastAPI's `/docs`). For each endpoint: method, path, auth, an example request and its response, and the error statuses a client will see. How clients authenticate, and how to get a credential for local testing. [SR, DIA, FAPI]
- Run in a container, when the repo has a Dockerfile or compose file: the exact build and run commands with the port mapping, how the env vars or env file are passed, and a volume for data that must outlive the container. A container reaches another compose service by its service name, and a service on the host through `host.docker.internal` (on Linux, add `--add-host=host.docker.internal:host-gateway`). [MS-PR, DKR, DC]
- Development: start with a debugger (`node --inspect`, default 127.0.0.1:9229; `debugpy`; an attach profile whose port matches) and the health or ready URL. [NODE, VSC]
- Troubleshooting, last: the startup errors and status codes a newcomer will hit, as the code raises them. [GL]

## Full stack

The front-end and back-end items apply, plus:

- **One command, or a documented order, that starts both**, e.g. a root `dev` script, `script/server`, or `docker compose up`. [STRTMA, DC, MS-DX]
- **How the front end reaches the back end in development**:
  - the dev-server proxy (e.g. `/api` → the back-end port), the CORS setting, or an API-URL env var;
  - the ports of both parts. [VITE, CRA, NEXT, 12F]
- **Joint debugging**: the compound launch profile that starts or attaches to client and server together, e.g. VS Code `compounds` with `stopAll`. This is the "press F5 and both run with the debugger attached" contract. [VSC, MS-DX]
- Troubleshooting, last, for wiring problems such as a port in use or a proxy miss. [GL]

## ML or data

- Intended use and limitations, including biases and what the data does not cover. [HF-M]
- Data: source, schema, what is in the repo versus elsewhere, and any sample data. [HF-D]
- Exact train and evaluate commands with their required arguments, the config and seed, where outputs (the model and metrics) land, and a results table with the commands that reproduce it. [PWC, HF-M]
- Inference: a get-started snippet or command. [HF-M]
- Development: a small or smoke run on sample data before a full run. [no source]

## Product (business application)

- What it is, who uses it, and a visual. [GH-R, MAR]
- Status and roadmap. Points of contact. [MAR, GDG]
- Onboarding: setup, the sandbox or test environment and test accounts, and how to build, test and deploy. [MS-PR]
- Architecture overview, or a link to `ARCHITECTURE.md`. [AR]
- Development: the F5 contract (clone, configure `.env`, launch with the debugger attached) and troubleshooting. [MS-DX, GL]

## Sources (fetched 2026-10-15)

- **SR**: Standard Readme spec. <https://github.com/RichardLitt/standard-readme/blob/main/spec.md>. Written for libraries. Order: Title, Short Description, Install, Usage, …, Contributing, License last.
- **MAR**: Make a README. <https://www.makeareadme.com/>
- **GH-R**: GitHub Docs, About READMEs. <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes>
- **GH-C**: GitHub Docs, contributor guidelines. <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors>
- **OSG**: Open Source Guides, Starting a project. <https://opensource.guide/starting-a-project/>
- **MOZ**: Mozilla Science, How to build a CONTRIBUTING.md. <https://mozillascience.github.io/working-open-workshop/contributing/>
- **WTD**: Write the Docs, beginner's guide. <https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/>
- **GDG**: Google documentation guide, READMEs. <https://google.github.io/styleguide/docguide/READMEs.html>
- **AR**: awesome-readme, the curated examples (no per-type rules). <https://github.com/matiassingers/awesome-readme>
- **CLIG**: Command Line Interface Guidelines. <https://clig.dev/>
- **VITE**: Vite server options and env. <https://vite.dev/config/server-options>, <https://vite.dev/guide/env-and-mode>
- **CRA**: Create React App, proxying (CRA is deprecated for new apps). <https://create-react-app.dev/docs/proxying-api-requests-in-development/>
- **NEXT**: Next.js rewrites. <https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites>
- **NODE**: Node.js debugging. <https://nodejs.org/en/learn/getting-started/debugging>
- **VSC**: VS Code debug configuration, compounds. <https://code.visualstudio.com/docs/debugtest/debugging-configuration>
- **MS-DX** and **MS-PR**: Microsoft Code-With Engineering Playbook, developer experience and project docs. <https://microsoft.github.io/code-with-engineering-playbook/developer-experience/>, <https://microsoft.github.io/code-with-engineering-playbook/documentation/guidance/project-and-repositories/>
- **STRTMA**: GitHub, Scripts To Rule Them All. <https://github.com/github/scripts-to-rule-them-all>
- **DC**: Docker Compose, Why use Compose. <https://docs.docker.com/compose/intro/features-uses/>
- **12F**: The Twelve-Factor App, config and dev/prod parity. <https://12factor.net/config>
- **DIA**: Diátaxis, reference. <https://diataxis.fr/reference/>
- **GL**: GitLab docs, topic types (troubleshooting last). <https://docs.gitlab.com/development/documentation/topic_types/>
- **HF-M** and **HF-D**: Hugging Face model and dataset cards. <https://huggingface.co/docs/hub/model-cards>, <https://huggingface.co/docs/hub/datasets-cards>
- **PWC**: Papers with Code, ML code completeness checklist. <https://github.com/paperswithcode/releasing-research-code>
- **PYVENV**: Python docs, venv: the activation command per platform and shell. <https://docs.python.org/3/library/venv.html>
- **NODE-CLI**: Node.js CLI, `--env-file` (v20.6.0+). <https://nodejs.org/api/cli.html#--env-filefile>
- **FAPI**: FastAPI, First Steps: interactive docs at `/docs` and `/redoc`, schema at `/openapi.json`. <https://fastapi.tiangolo.com/tutorial/first-steps/>
- **DKR**: Docker, `docker container run`: `--publish`, `--env-file`, `--volume`, and `host-gateway` for reaching the host. <https://docs.docker.com/reference/cli/docker/container/run/>

Not a source for project READMEs: `elangosundar/awesome-README-templates`, a collection of GitHub *profile* READMEs (last content commit 2020).
