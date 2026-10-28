# decision-brief

Agents raise questions in their own shorthand: ticket numbers, codenames they coined an hour ago, and options
with no example of what each one would change. This plugin turns a task's open questions into one page that a
newcomer can answer in one pass. You talk with the agent in the page's comment threads while you answer, and
when you are done it reads everything at once. One `SKILL.md` serves every runtime.

The page has four tabs, so finished rounds never pile up above the new questions:

- **Waiting for you** (with the number still unanswered): one card per open question, with the background in
  plain words, a real example from your project, the options each with what it changes, a labelled
  recommendation, an **Other** answer with its own text box, **Clear choice** to take a choice back, and a note.
  When options look different, a switch shows each option's picture before you choose. New questions that came
  up during the work sit under a heading that says where they came from.
- **Work status**: what your earlier answers turned into, with before and after screenshots to check, and a
  count of the ones that need something from you.
- **Decided**: earlier rounds, archived under their round's name, with what the agent did. You can still change
  an answer there.
- **Glossary**: every short name, ticket number and codename on the page, with its plain meaning and a checked
  link to where it comes from. A link to a term or a card opens the tab that holds it.

Everywhere, **comments**: select any text, or press **Comment on this** on a card, to ask about it. The agent
answers in the thread while it reads along, or a read-only helper agent answers when you press **Ask now**. A line
says whether the agent is reading along, and **I'm done** tells it to read your answers.

Answers save as you choose. Every picture opens full size, where the wheel or a pinch zooms and dragging pans. The
page follows your system's light or dark theme, comes in three looks (ledger by default, rose and slate), works
with the keyboard alone (arrow keys move between tabs), fits a phone screen, and comes in English or Chinese (other
languages through translated labels).

## Install

The [repository README](../README.md) has a one-command installer that sets this plugin up in every runtime
below. By hand:

```bash
claude plugin install decision-brief@minakami-plugins   # Claude Code
codex plugin add decision-brief@minakami-plugins        # Codex CLI
```

Grok Build loads the plugins installed in Claude Code (its Claude compatibility is on by default), so the
Claude Code install covers it. Without Claude Code, install it in Grok directly:
`grok plugin install war3water/Minakami_plugins#decision-brief --trust`. In pi, install the marketplace
repository as a package, which brings every plugin in it: `pi install git:github.com/war3water/Minakami_plugins`.

The page's helper needs Python 3.8 or later on the computer that runs the agent. It uses only the standard
library.

## Start it

The skill never loads by itself: it runs only when you name it. Claude Code, Grok Build and pi honor
`disable-model-invocation: true` in its `SKILL.md`; Codex CLI honors `allow_implicit_invocation: false` in
`agents/openai.yaml`.

| Runtime | Start the request with |
|---|---|
| Claude Code | `/decision-brief:decision-brief` |
| Codex CLI | `$decision-brief` (interactive sessions only: `codex exec` doesn't load plugin skills) |
| Grok Build | `/decision-brief:decision-brief`, or `/decision-brief` when no other skill has that name |
| pi | `/skill:decision-brief` |

The examples below use the Claude Code form.

| You want | Type |
|---|---|
| All open questions of the task you are working on, on one page | `/decision-brief:decision-brief` |
| Particular questions | `/decision-brief:decision-brief Ask me about <topic one>, <topic two> and <topic three>.` |
| Answers to your comments even while the agent is busy | add `Turn on Ask now.` to the request |
| A claude.ai link instead of the local page (Claude Code) | add `artifact` to the request |
| The agent to read your answers | press **I'm done** on the page, or say `I answered` in the chat |
| To see what a page looks like | `/decision-brief:decision-brief example` |

## Try it

In any project folder, start the skill with `example` in the runtime's form (for instance
`/skill:decision-brief example` in pi). The agent copies a worked example into `.decision-brief/example/`,
serves it on `http://127.0.0.1:8377/` (or another port when that one is busy), and reads along. The example is
a made-up shopping-list app with three questions and one progress report. Answer a card, try **Other** and
**Clear choice**, select a sentence and comment on it, then press **I'm done**.

Without an agent, from a checkout of this repository:

```bash
python decision-brief/skills/decision-brief/scripts/brief.py example ../brief-try
python decision-brief/skills/decision-brief/scripts/brief.py serve ../brief-try/questions.json --open
python decision-brief/skills/decision-brief/scripts/brief.py reply ../brief-try/questions.json q-storage "A note from the agent"
python decision-brief/skills/decision-brief/scripts/brief.py read ../brief-try/questions.json
python decision-brief/skills/decision-brief/scripts/brief.py stop ../brief-try/questions.json
```

## Where the page runs

| Backend | Used when | Answers and comments are kept | The agent reads them with |
|---|---|---|---|
| Local page | the default, in every runtime | `answers.json` in the task folder | `brief.py read`, and `brief.py wait` while it reads along |
| claude.ai Artifact | you ask for it in Claude Code with the claude.ai Artifact tools | the Artifact's own storage and comment threads | the ArtifactData and ArtifactComments tools, in one turn |
| Static file | the local server cannot run (a sandbox that forbids opening a port) | your browser; you press **Download answers.json** or **Copy answers** | `brief.py read --answers <file>`, or your pasted text |

Each answer holds your choice (an option, `other`, or nothing after Clear choice), your Other text, your note,
and the time. The Artifact opens on any device you are signed in on; its comment box has **Send to Claude**,
which brings the session that published it into the thread, and **I'm done** uses the same route. The static
file has no comments.

### Talking with the agent on the local page

- **The agent reads along.** After it gives you the link, the agent runs `brief.py wait`, which returns as soon
  as you comment or press **I'm done**. It answers in the thread with `brief.py reply`, and the answer appears
  on your page within a second. The page says when the agent is reading along. Claude Code runs the wait in
  the background, so the chat stays free; Codex CLI, Grok Build and pi run it in the foreground and wait again
  after each answer, so their chat is busy while you work on the page.
- **Ask now.** When the agent is not reading along, the page can still answer: started with
  `serve --ask <runtime>`, each comment gets an **Ask … now** button. It runs that agent once, headless and
  read-only, with your question, the card, the glossary and the agent's notes on the task (`context.md`), and
  posts the answer in the thread. Each press is one model call on your own account. These are the read-only
  settings it uses:

| `--ask` | Command (the prompt goes in on stdin or as a file) |
|---|---|
| `claude` | `claude -p --tools Read,Grep,Glob --strict-mcp-config --no-session-persistence --permission-mode dontAsk` |
| `codex` | `codex exec --sandbox read-only --skip-git-repo-check --ephemeral -o <reply file> -` |
| `grok` | `grok --prompt-file <prompt file> --tools read_file,grep,list_dir --disallowed-tools Agent --output-format plain` |
| `pi` | `pi -p --no-session --tools read,grep,find,ls "Answer the request in the attached file." @<prompt file>` |
| any other command | runs through the shell; `{prompt_file}` and `{reply_file}` in it are filled in, and otherwise the prompt goes to stdin |

### The task folder

The agent keeps each task's page in `.decision-brief/<task>/` in your project:

```text
.decision-brief/
├── .gitignore          one line, "*": these working files stay out of commits
└── <task>/
    ├── questions.json  the page's content; the agent edits this, never the HTML
    ├── context.md      the agent's notes on the task, for the Ask now helper
    ├── shots/          screenshots the cards show
    ├── answers.json    your answers, comment threads and I'm done (local page)
    ├── agent.json      whether the agent is reading along, and what it has seen
    ├── page.html       the built page (Artifact and static backends)
    ├── server.json     the running local server's address and process id
    └── server.log      the local server's log
```

The decisions themselves end up where your project records decisions, once the agent acts on them.

### The local server

- It listens on `127.0.0.1` only, so other computers cannot reach it, and it refuses requests whose `Host`
  header names anything other than this computer, which keeps out web pages that point their domain at it.
- Reading and writing needs a token that exists only in the server's memory and the page it serves; writes
  must be JSON, so another site's form cannot post to it.
- It serves the page and the images inside the task folder, and nothing else. The page's content security
  policy forbids requests to any other address.
- It makes no outside connections of its own; only **Ask now**, when you started it with `--ask`, runs the agent
  you chose. It writes only in the task folder, and runs in the background until the agent or you stop it with
  `brief.py stop`.

## Language

The agent writes the cards in the language you use with it and sets the page's `lang`. The page's own labels
come in English and Simplified Chinese; for another language the agent supplies translated labels in the
questions file. Code identifiers, file names and standard names stay as they are and are explained in your
language, because those are the words you will meet in the project.

## What was tested

**Skill against no skill, same request.** Each agent got the same one-line request in the same small project,
with and without the skill:

- the agents: Claude Code with Claude Sonnet 5.5, and Codex CLI with GPT-6.1 Terra;
- the projects: an English web app with four open decisions, one already settled and two mockups; and a Chinese
  command-line tool with three open decisions and one already settled.

A blind panel (Claude Opus 5.5, Claude Fable 5.1, GPT-6 Astra at its highest effort) compared the two pages in
each of the four pairs, with screenshots, the page text, the agents' replies and the read-back round.

| | with the skill | without |
|---|---|---|
| Panel preference (12 verdicts) | 12, all at confidence 5 | 0 |
| Right questions, settled ones left out (1 to 5) | 4.9 | 4.8 |
| Short names and codenames explained | 4.3 | 2.3 |
| Concrete examples | 4.0 | 1.9 |
| Options, consequences, reasoned recommendation | 4.3 | 2.2 |
| Answering: one pass, own answer, clear, notes, discussion | 4.8 | 1.9 |
| Read-back of a simulated user's partial answers | 4.8 (4 of 4 runs exact) | 2.0 (0 of 2 runs got the answers) |
| Look, phone, dark mode | 4.3 | 2.3 |
| Cost per run on Claude Sonnet 5.5 | about $0.22 to $0.26 | about $0.10 to $0.14 |
| Time per run, Claude Code | 66 to 85 seconds | 31 to 42 seconds |
| Time per run, Codex CLI | 132 to 328 seconds | 165 to 172 seconds |

- **Where the gap comes from.** Without the skill, the pages were a Markdown checklist, a plain Markdown file,
  or a form that refused to save while any question was open. None explained the project's short names, and
  their examples were thin. The two forms overflowed a phone screen by about 590 pixels.
- **What the skill costs.** Its page is richer, so a run writes about twice the text and reads about three times
  the context. Setting the task folder up with one command (`brief.py new`) cut input tokens by 10 to 36 % and
  turns by about 10 % in a second round, with the same results.
- **Edge cases.** With nothing left to decide, every run with the skill said so and made no page. On a second
  round, Claude applied the clear answers, moved them to **Decided** under a named round, answered the open
  comment, and asked about the one ambiguous answer instead of guessing. Codex did the code work but could not
  move the cards: first it passed ids separated by spaces (now accepted), then Windows refused to start more
  processes in its sandbox.
- **Errors the panel found in the skill's pages.** One example's arithmetic was off in the fourth decimal place,
  and one page left out the mockups. The skill now says to check every number and copies images when it sets
  the task folder up.

Each result is one run per arm, so treat the exact numbers as indicative. The fixtures, the harness and every
run are kept outside this repository.

**The page and its helper.** A browser test (Chromium on Windows 11, Python 3.14, 54 checks) covers the
following:

- answers, Other, Clear choice, keyboard selection and reload;
- the tabs: counts, rounds on Decided, the answer recorded on a decided card, option pictures, links that open
  the right tab, and the remembered tab;
- `mark` and "changed since I read it";
- select-to-comment, threads, `wait` and `reply`, **Ask now**, and **I'm done**;
- the Chinese labels, the static page, phone width in the dark theme, and the server's refusals.
- **Ask now with real agents**: `--ask claude` answered a comment end to end, reading the project's README in
  read-only mode. The `codex` settings answered a test prompt. Grok accepted its settings but was not signed in
  on the test machine; pi was not installed there.
- **The claude.ai Artifact**: the example was published with its images, its answer store accepted an answer
  in the page's exact shape, and `brief.py read` read it back from both saved forms. The page's calls to the
  platform (saving, live updates, the comment composer, Send to Claude for **I'm done**) were checked against
  the platform's published interface and a stand-in in the browser test, not by clicking in claude.ai.
- **Explicit invocation**: in Claude Code 2.1.311 with the plugin loaded, a headless session did not list the
  skill among its skills.

Not tested yet: interactive Codex CLI, Grok Build and pi sessions (the contrast test ran Claude Code and Codex
headless), clicking through the published Artifact, the tabs inside claude.ai, macOS and Linux, and Python before
3.13.

## Notes for maintainers

### Files

| File | Role |
|---|---|
| `skills/decision-brief/SKILL.md` | the runbook: collect, write cards for a newcomer, publish, read along, read back in one pass, act, mark and republish |
| `skills/decision-brief/references/questions-format.md` | the questions.json format, the markup, the labels, the answers and comments format |
| `skills/decision-brief/assets/page.html` | the one page template: the three looks, tabs, rendering, threads, and the three answer stores |
| `skills/decision-brief/scripts/brief.py` | `new`, `build`, `serve`, `wait`, `reply`, `read`, `mark`, `stop`, `links`, `example`; standard library only |
| `skills/decision-brief/assets/example/` | the worked example `example` copies |
| `skills/decision-brief/agents/openai.yaml` | Codex: explicit invocation only |

`SKILL.md` declares `allowed-tools: Read(${CLAUDE_SKILL_DIR}/**)` so that Claude Code reads the bundled files
without a permission prompt; other runtimes ignore the field.

### Design

- **Data, not HTML.** The agent writes `questions.json`; one template renders every page. The markup is a
  small subset (paragraphs, lists, bold, code, links) rendered without HTML, so project text cannot break the
  page.
- **One template, three stores.** The page uses the claude.ai storage when it runs inside an Artifact, the
  local server when `brief.py serve` served it, and the browser otherwise. A store that fails falls back to the
  browser, with Copy (and Download outside claude.ai) shown.
- **Live without a framework.** The page's update request waits on the server until an answer or comment
  changes or the agent starts or stops reading along; `wait`, `reply` and the server share `answers.json`
  through a lock file, and every change raises its revision number.
- **Checks the agent would otherwise skip.** `build` refuses duplicate ids, missing `alt` text, images outside
  the task folder, web images and links that are not http(s); it warns about all-capital short names missing
  from the glossary, cards without a recommendation, and terms without an origin link. `links` lists every link
  to check before publishing. Codenames in ordinary words are left to the runbook's read-through.
- **Answers keyed by stable ids**, so editing a card keeps its answer, and `mark` records what the agent read
  so a later change shows.
- **No review rules.** The skill asks for no reviewer and no second model; a review happens when you ask.
