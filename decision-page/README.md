# decision-page

Agents raise questions in their own shorthand: ticket numbers, codenames they coined an hour ago, and options
with no example of what each one would change. This plugin turns a task's open questions into one page that a
newcomer can answer in one pass. You talk with the agent in the page's comment threads while you answer, and
when you are done it reads everything at once. One `SKILL.md` serves every runtime.

The page has four tabs, so finished rounds never pile up above the new questions:

- **Waiting for you** (with the number still unanswered): one short card per open question. It gives two or
  three sentences of background in plain words (anything longer folds under **More**), the options each with
  what it changes, and a **Recommended** tag on one. Where those would leave you unsure, it adds an example from
  your project that says where it comes from; where they already make the choice plain, it adds nothing.
  Below them are an **Other** answer with its own text box, **Add a note**, and **Clear** to take a choice back.
  Where a picture makes a question easier to understand than words, the card shows one made for that question: a
  chart over the range that matters, the mechanism drawn with its real parts, a timeline, the numbers worked through,
  screenshots, or a live demo you can try. Each one reads without explanation: axes and marks say what they are, and
  the card gives the facts behind its numbers. Choosing an option highlights its part of the picture. Questions that
  a sentence makes clear stay words only. When
  options look different, a switch shows each option's picture before you choose. When each option has a live
  demo, the card stays text: **Try it** on an option opens a floating window that switches between the demos and has
  **Choose this**. The **Other** box, notes and comments grow as you type, up to about 8 lines for Other and 12
  for the others, then scroll. New questions that came up during the work sit under a heading that says where they
  came from.
- **Work status**: what your earlier answers turned into, with before and after screenshots to check, and a
  count of the ones that need something from you.
- **Decided**: the latest round, under its name, with what the agent did; you can still change an answer there.
  Rounds before it shrink to one line per decision and open their cards, read-only, when you click them. To
  change an old answer, tell the agent.
- **Glossary**: every short name, ticket number and codename on the page, with its plain meaning and a checked
  link to where it comes from. On the cards, a term is underlined where it first appears, and pointing at it
  (or tapping it) shows its meaning in place. A link to a term or a card opens the tab that holds it.

Everywhere, **comments**: select any text, or press **Comment** on a card, to ask about it. The agent answers in
the thread while it reads along, or a read-only helper agent answers when you press **Ask now**. One line at the
top shows how many questions you have answered, whether answers save, and whether the agent is reading along;
**I'm done** tells it to read your answers. The instructions fold under **How this works**.

The agent keeps each card to about one laptop screen: a few sentences of background and a line per option, plus an
example, a table or a picture only where the choice is not yet plain, with worked numbers folded under **More**.
Beside the tabs, **Compact** shows each card as the question, its background and its options on one screen, with
the example, pictures and tables one click away; **Detailed**, the default, shows the whole card. The page
remembers your pick.

Answers save as you choose. Every picture has its own **Comment** and opens full size, where the wheel or a pinch
zooms and dragging pans; a live demo runs sealed off from the network and from your answers. The page follows your
system's light or dark theme, comes in four looks (notebook by default, set in IBM Plex, then ledger, rose and
slate), works with the keyboard alone (arrow keys move between tabs), fits a phone screen, and comes in English or
Chinese (other languages through translated labels). It loads nothing from the internet, except that an Artifact
loads its typeface from Google Fonts.

## Install

The [repository README](../README.md) has a one-command installer that sets this plugin up in every runtime
below. By hand:

```bash
claude plugin install decision-page@minakami-plugins   # Claude Code
codex plugin add decision-page@minakami-plugins        # Codex CLI
```

Grok Build loads the plugins installed in Claude Code (its Claude compatibility is on by default), so the
Claude Code install covers it. Without Claude Code, install it in Grok directly:
`grok plugin install war3water/Minakami_plugins#decision-page --trust`. In pi, install the marketplace
repository as a package, which brings every plugin in it: `pi install git:github.com/war3water/Minakami_plugins`.

The page's helper needs Python 3.8 or later on the computer that runs the agent. It uses only the standard
library.

**Renamed from decision-brief in 0.7.0.** Running the installer again installs decision-page and removes
decision-brief. By hand, remove the old copy with `claude plugin uninstall decision-brief@minakami-plugins` or
`codex plugin remove decision-brief@minakami-plugins`. Pages you already made keep working: a project that has a
`.decision-brief/` folder keeps its pages there, and a page you saved as a file keeps your answers.

## Start it

The skill never loads by itself: it runs only when you name it. Claude Code, Grok Build and pi honor
`disable-model-invocation: true` in its `SKILL.md`; Codex CLI honors `allow_implicit_invocation: false` in
`agents/openai.yaml`.

| Runtime | Start the request with |
|---|---|
| Claude Code | `/decision-page:decision-page` |
| Codex CLI | `$decision-page` (interactive sessions only: `codex exec` doesn't load plugin skills) |
| Grok Build | `/decision-page:decision-page`, or `/decision-page` when no other skill has that name |
| pi | `/skill:decision-page` |

The examples below use the Claude Code form.

| You want | Type |
|---|---|
| All open questions of the task you are working on, on one page | `/decision-page:decision-page` |
| Particular questions | `/decision-page:decision-page Ask me about <topic one>, <topic two> and <topic three>.` |
| Answers to your comments even while the agent is busy | add `Turn on Ask now.` to the request |
| A claude.ai link instead of the local page (Claude Code) | add `artifact` to the request |
| The agent to read your answers | press **I'm done** on the page, or say `I answered` in the chat |
| To see what a page looks like | `/decision-page:decision-page example` |

## Try it

In any project folder, start the skill with `example` in the runtime's form (for instance
`/skill:decision-page example` in pi). The agent copies a worked example into `.decision-page/example/`,
serves it on `http://127.0.0.1:8377/` (or another port when that one is busy), and reads along. The example is
a made-up shopping-list app with three questions and one progress report. Answer a card, try **Other** and
**Clear**, point at an underlined term, select a sentence and comment on it, then press **I'm done**.

Without an agent, from a checkout of this repository:

```bash
python decision-page/skills/decision-page/scripts/page.py example ../brief-try
python decision-page/skills/decision-page/scripts/page.py serve ../brief-try/questions.json --open
python decision-page/skills/decision-page/scripts/page.py reply ../brief-try/questions.json q-storage "A note from the agent"
python decision-page/skills/decision-page/scripts/page.py read ../brief-try/questions.json
python decision-page/skills/decision-page/scripts/page.py stop ../brief-try/questions.json
```

## Where the page runs

| Backend | Used when | Answers and comments are kept | The agent reads them with |
|---|---|---|---|
| Local page | the default, in every runtime | `answers.json` in the task folder | `page.py read`, and `page.py wait` while it reads along |
| claude.ai Artifact | you ask for it in Claude Code with the claude.ai Artifact tools | the Artifact's own storage and comment threads | the ArtifactData and ArtifactComments tools, in one turn |
| Static file | the local server cannot run (a sandbox that forbids opening a port) | your browser; you press **Download answers.json** or **Copy answers** | `page.py read --answers <file>`, or your pasted text |

Each answer holds your choice (an option, `other`, or nothing after Clear), your Other text, your note, and the
time. When you answer under **Other**, the agent tells you in one line how it read your words before it acts on
them. The Artifact opens on any device you are signed in on; its comment box has **Send to Claude**,
which brings the session that published it into the thread, and **I'm done** uses the same route. The static
file has no comments.

### Talking with the agent on the local page

- **The agent reads along.** After it gives you the link, the agent runs `page.py wait`, which returns as soon
  as you comment or press **I'm done**. It answers in the thread with `page.py reply`, and the answer appears
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

The agent keeps each task's page in `.decision-page/<task>/` in your project:

```text
.decision-page/
├── .gitignore          one line, "*": these working files stay out of commits
└── <task>/
    ├── questions.json  the page's content; the agent edits this, never the HTML
    ├── context.md      the agent's notes on the task, for the Ask now helper
    ├── shots/          screenshots the cards show
    ├── answers.json    your answers, comment threads and I'm done (local page)
    ├── agent.json      whether the agent is reading along, and what it has seen
    ├── page.html       the built page (Artifact and static backends)
    ├── server.json     the running local server's address and process id
    ├── server.log      the local server's log
    └── archive/        earlier rounds: index.json, one line per decision, and one file per round
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
  `page.py stop`.

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
each pair, with screenshots, the page text, the agents' replies and the read-back round. Version 0.3.0 ran twice
per pair. Two Codex pairs were left out because the run without the skill made its page on chatgpt.com, which the
test cannot open.

| | 0.3.0 | without the skill |
|---|---|---|
| Panel preference | 18 of 18 verdicts, all at confidence 5 | 0 |
| Right questions, settled ones left out (1 to 5) | 4.9 | 4.8 |
| Short names and codenames explained | 4.2 | 2.2 |
| Concrete examples | 4.2 | 1.7 |
| Options, consequences, reasoned recommendation | 4.4 | 2.4 |
| Answering: one pass, own answer, clear, notes, discussion | 4.9 | 2.1 |
| Read-back of a simulated user's partial answers | 8 of 8 runs exact | 2 of 4 runs exact (both on Claude) |
| Look, phone, dark mode | 4.4 | 1.6 |
| Straightforward: the question and its options up front | 3.7 | 3.2 |
| Cost per run on Claude Sonnet 5.5 | about $0.22 to $0.33 | about $0.10 to $0.12 |
| Time per run, Claude Code | 74 to 111 seconds | 25 to 52 seconds |
| Time per run, Codex CLI | 155 to 430 seconds | 155 to 384 seconds |

**The cleaner card against the card before it.** The same requests, with the skill both times: 0.3.0 against
0.2.0, one pair per project and agent. The panel preferred 0.3.0 in 11 of 12 verdicts, with one tie.

| | 0.3.0 | 0.2.0 |
|---|---|---|
| Straightforward | 4.2 | 2.7 |
| Look, phone, dark mode | 4.8 | 3.8 |
| Read-back | 4.8 | 4.2 |
| Short names and codenames explained | 4.1 | 4.6 |

The graders read text and screenshots, where a term's meaning shown in place does not appear. Two Codex pages
also left the project's decision numbers off their cards, which the skill now asks for.

**Cards of one screen (0.4.0).** For the Chinese project, a person rating blind kept preferring the page made
without the skill: all three questions fit on one screen. 0.4.0 keeps each card to about one laptop screen and
folds the working under **More**; the Chinese page went from about 2,400 to 1,600 pixels tall, against 1,100
without the skill. In a second blind rating, the same person chose the 0.4.0 page over both pages made without
the skill, and the detailed view over the compact one on both projects, so detailed is the default.

The panel split evenly between 0.4.0 and 0.3.0 pages: 5 verdicts each and 2 ties, all at low confidence.
0.4.0 scored higher on straightforward (4.6 against 3.7) and lower on examples (4.0 against 4.4), because one
card had dropped its example to save space. The skill now forbids that, and the build flags a card without one.
In the four runs after that change, every card had an example with its source.

**Fewer rounds of fixes, and history kept out of the way (0.5.0).** Most of a run's extra turns went to fixing
the build's warnings one edit at a time. 0.5.0 removes the commonest cause: a glossary term from the project's
own files no longer needs a hand-written source, because the page names the file it appears in. On a first round,
cost stays where it was: about $0.26 a run on Claude Sonnet 5.5, with time within run-to-run noise. An earlier
attempt cut cost by a fifth by letting everyday abbreviations such as EUR or CSV go unexplained. The panel
preferred the older pages 9 to 3 for that, so the rule that every abbreviation is explained stayed.

The savings come from the second round on. Marking a round now moves the older rounds into `archive/`, so the file
the agent reads and edits each round holds only the open cards and the latest round. In the worked example, it
shrank from 7.6 KB to 3.9 KB after two rounds. In a third-round test on both agents, the earlier round moved to
the archive and neither agent read an archive file or the built page whole.

A first comparison with the version before it, both shown in the same view, split 11 to 10. The graders found
two weak spots in 0.5.0:

- examples that restated the problem, or got a figure wrong;
- read-backs that picked one reading of a written answer, or reopened a clear choice because of its note.

The skill now has the agent work each example through with figures computed by a command. In the read-back it
asks one direct question that names the readings, and a chosen option stands even when its note seems to pull
another way. In a second comparison, the panel preferred 0.5.0 in 22 of 24 verdicts, with 1 tie:

| | 0.5.0 | before |
|---|---|---|
| Examples | 4.4 | 4.0 |
| Short names and codenames explained | 4.4 | 3.7 |
| Options, consequences, reasoned recommendation | 4.0 | 3.7 |
| Read-back | 4.6 | 4.5 |

The same holds for the local page and the static file, not only on claude.ai. The agent never reads the built
page, and `read` prints only this round's comment threads, leaving settled ones to `history --threads`. A static
page keeps the reader's saved answers from round to round, and its Copy and Download carry only the current cards.

**Pictures where they help, and nothing added to a clear card (0.6.0).** A card can now carry a picture made for
its question: a chart, the mechanism drawn with its real parts, a timeline or a live demo. Two harder projects were
written to test this: an order pipeline where duplicate parcels enter at two places (English), and a tea shop whose
price rules make some members pay more than non-members (Chinese). They ran beside the tile estimator on Claude
Sonnet 5.5, Claude Opus 5.5 and gpt-6.1-sol in Codex.

A first draft with pictures won a blind panel against 0.5.0 in 10 of 15 verdicts, with 1 tie, and scored 3.3
against 2.6 on pictures. It scored lower on straightforward, 3.3 against 3.9. Measured on a laptop screen (1366 by
768), a later draft showed why: a card with a picture ran 1.3 to 1.8 screens, and its options began 800 to 1,090
pixels down, below the first screen. The picture came on top of an example, a table and sentences that said the
same thing, and every card carried an example because 0.4.0 required one. The person the pages were made for found
them long-winded.

0.6.0 asks for less. A card is the question, its background, the options and a recommendation. An example, a table
or a picture is added only where those leave the choice unclear, once, in the form that shows it fastest, and the
build no longer warns about a card without an example. Each option is one line: what it gains and what it costs
compared with today, with how many and how much.

| | Draft with an example on every card | 0.6.0 |
|---|---|---|
| Words to read on a page's cards, Sonnet 5.5 | 820 to 1,060 | 540 to 800 |
| The same, Opus 5.5, the two harder projects | 870 to 890 | 640 to 770 |
| The same, gpt-6.1-sol in Codex, the two harder projects | 550 to 600 | 510 to 640 |
| Cards with an example | 28 of 28 | 10 of 33 |
| Where the options begin on the hard cards, Sonnet 5.5 | 800 to 1,090 pixels down | 275 to 570 |
| Cost per page, Sonnet 5.5 | about $0.49 | about $0.36 |

Three slips came back in draft after draft. The last wording removed each of them in every run of the final round
(7 pages on Claude, 3 in Codex):

- **A cost left unsaid.** One tea-shop option makes 1,164 member orders 3 yuan dearer than today. Some drafts
  recommended it, or offered it, without saying so. The final pages state it with its count and amount.
- **A claim nobody tried.** The tile estimator's cards said a larger allowance "answers the pilot complaint" in 5
  of 6 runs of one draft, though the complaint's own order comes out at the same number of boxes either way. The
  skill now has the agent try an option on the case that was reported and say what it found. Every final run there did,
  and one found a likelier cause in the project's own files.
- **How an option is built, where its effect should be.** Options for the pipeline described the fix instead of
  what it stops. They now say what stops, what continues and how long the work takes.

Every figure on the tea-shop pages was recomputed from the order data, and all of them matched. On these projects
Sonnet now mostly chooses a small table where the draft drew a picture; Opus and Codex draw more often.

After that, the cards were changed to state a problem's cause as who does what and when, with a picture where the
words would be slow to follow, and the runbook was cleaned up after a review of its instructions. A blind panel
(Claude Opus 5.5 twice and gpt-6.1-sol) compared the final wording with the first, on five pairs: Sonnet 5.5 on the
tile estimator, a newsletter tool, the order pipeline and the tea shop, and Codex on the tile estimator.

| | Final wording | First wording |
|---|---|---|
| Panel preference | 9 of 15 verdicts, 4 of 5 pairs | 6 of 15 |
| Pictures | 3.4 | 2.9 |
| Examples | 4.7 | 4.5 |
| Clear to a newcomer | 4.5 | 4.3 |
| Options, consequences, reasoned recommendation | 4.4 | 4.2 |
| Read-back | 4.3 | 4.8 |
| Straightforward | 3.6 | 3.9 |

The final cards are about a third longer, which costs some straightforwardness. The read-back lost because, asked
what "never less than one spare box per room" would mean, one run wrote 7 boxes for a two-room order that needs 8.
In four runs of that read-back, two gave a wrong figure, and none ran a command to work it out. The read-back step
now has the agent compute any figure in a reading with a command before writing it. In three runs after that
change, every read-back did, and every total was right.

- **Where the gap comes from.** Without the skill, the pages were a Markdown checklist, a static form that
  overflowed a phone screen by 590 pixels, or nothing. Twice Codex could not write its file in the Windows
  sandbox and asked in the chat instead; twice it made the page on chatgpt.com through the ChatGPT connector.
- **What the skill costs.** Two to three times the money and the time of a run without it on Claude. The
  shorter runbook (11 KB instead of 14 KB) did not lower that: runs now spend it on checking every number and
  naming each example's source.
- **Edge cases.** With nothing left to decide, 4 of 4 runs said so and made no page. On a second round, Claude
  and Codex both passed all nine checks. Each applied the clear answers in the code and followed the Other answer.
  Each moved the cards to **Decided** under a named round with what it did, answered the open comment, and
  named the Other answer in the chat. In 0.2.0, Codex could not move the cards.
- **What the panel found, and what changed.** The graders flagged slips the skill now prevents:
  - an English "made up to illustrate" on a Chinese page;
  - a chat message naming a button differently from the page;
  - cards without the project's decision numbers;
  - a filler progress report;
  - long intros.

  `serve` and `build` now print the page's own words for the chat. In the four runs after the change, every card
  carried its number and every example its source in the page's language, and no chat message misnamed a button
  or mentioned the helper. The graders still catch overstatements in some cards, such as "no stale prices" when
  the supplier feed refreshes nightly.

The panel saw two runs per arm, so treat the exact numbers as indicative. The fixtures, the harness and every run
are kept outside this repository.

**The page and its helper.** A browser test (Chromium on Windows 11, Python 3.14: 87 checks, 101 more for pictures on
cards and option demos, 21 for the picture viewer and 25 for the archive of earlier rounds) covers the following:

- the compact and detailed views, the switch, and the remembered pick; in the compact view, the example, pictures
  and tables behind one handle; sans-serif headings on Chinese pages;
- drawings placed into the page in both themes, the part marked for an option standing out when it is chosen,
  live demos sealed in their frame, and a Comment on each picture;
- answers, Other, Clear, Add a note, keyboard selection and reload; the text boxes growing with long answers;
- option demos in the floating window: Try it, the switch, Choose this answering the card, Esc and the keyboard;
- the glossary terms explained in place: by pointing, by keyboard focus and by tapping, without choosing the
  option a term sits in;
- background folded under **More**, the example's source line, and the top bar's count;
- the tabs: counts, rounds on Decided, the answer recorded on a decided card, option pictures, links that open
  the right tab, and the remembered tab;
- `mark` and "changed since I read it", and `read` listing the answers given under Other;
- select-to-comment, threads, `wait` and `reply`, **Ask now**, and **I'm done**;
- the Chinese labels, the static page, phone width in the dark theme, and the server's refusals.
- **Ask now with real agents**: `--ask claude` answered a comment end to end, reading the project's README in
  read-only mode. The `codex` settings answered a test prompt. Grok accepted its settings but was not signed in
  on the test machine; pi was not installed there.
- **The claude.ai Artifact**: the example was published with its images, its answer store accepted an answer
  in the page's exact shape, and `page.py read` read it back from both saved forms. The page's calls to the
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
| `skills/decision-page/SKILL.md` | the runbook: collect, write cards for a newcomer, publish, read along, read back in one pass, act, mark and republish |
| `skills/decision-page/references/questions-format.md` | the questions.json format, the markup, the labels |
| `skills/decision-page/references/answers-format.md` | how answers and comment threads are stored, for debugging; `page.py read` reads them |
| `skills/decision-page/references/publish.md` | the Artifact and static backends, read only when one is used |
| `skills/decision-page/references/live.md` | reading along with `wait` and `reply`, and Ask now, read only when the user answers now |
| `skills/decision-page/assets/page.html` | the one page template: the three looks, tabs, rendering, threads, and the three answer stores |
| `skills/decision-page/scripts/page.py` | `new`, `build`, `serve`, `wait`, `reply`, `read`, `mark`, `history`, `stop`, `links`, `example`; standard library only |
| `skills/decision-page/assets/example/` | the worked example `example` copies |
| `skills/decision-page/agents/openai.yaml` | Codex: explicit invocation only |

`SKILL.md` declares `allowed-tools: Read(${CLAUDE_SKILL_DIR}/**)` so that Claude Code reads the bundled files
without a permission prompt; other runtimes ignore the field.

### Design

- **Data, not HTML.** The agent writes `questions.json`; one template renders every page. The markup is a
  small subset (paragraphs, lists, bold, code, links) rendered without HTML, so project text cannot break the
  page.
- **One template, three stores.** The page uses the claude.ai storage when it runs inside an Artifact, the
  local server when `page.py serve` served it, and the browser otherwise. A store that fails falls back to the
  browser, with Copy (and Download outside claude.ai) shown.
- **Live without a framework.** The page's update request waits on the server until an answer or comment
  changes or the agent starts or stops reading along; `wait`, `reply` and the server share `answers.json`
  through a lock file, and every change raises its revision number.
- **Pictures chosen per question, carried safely.** The agent reads each card as a newcomer and uses a picture
  where the reader would otherwise get stuck, or leaves the card as words; `references/pictures.md` gives direction
  on where pictures help, how to make each form so it reads cold, and how to check it. A drawing
  (`.svg`) is placed into the page, so it takes the page's colours in both themes and the part marked for an option
  stands out when that option is chosen; its ids and styles are kept to itself. A live demo (`.html`) runs in a
  sandboxed frame with no network, storage or access to the page. A static file carries both inside it.
- **Checks the agent would otherwise skip.** `build` refuses duplicate ids, missing `alt` text, images outside
  the task folder, web images, links that are not http(s), and drawings that hold code or load outside files. It
  warns when a drawing's labels look likely to overlap, spill out of their box or run off its edge, or when it
  leaves a band of empty space above or below what it draws, estimated from their positions, since
  an agent cannot always look at the page. It also warns about all-capital short names missing
  from the glossary, cards without a recommendation, examples that do not say where they come
  from, and terms found neither in a source nor in the project's files. A term without a source shows the
  project file it first appears in. `links` lists every link to check before publishing, and `read` lists the
  answers given under Other for the agent to confirm. Codenames in ordinary words are left to the runbook's
  read-through.
- **A short runbook.** `SKILL.md` holds what every run needs; the Artifact, static and read-along details sit in
  `references/` and are read only when they apply.
- **Answers keyed by stable ids**, so editing a card keeps its answer, and `mark` records what the agent read
  so a later change shows.
- **History out of the way.** A long-running page would otherwise grow with every round. Marking a new round
  moves the older ones out of `questions.json` into `archive/`, so each round the agent reads and edits only the
  open cards and the latest round. The page fetches an earlier round only when you open it. The agent reaches
  history through `page.py history`, one line per decision or one card at a time. On claude.ai it never reads the
  published page back, and asks the answer store only for answers given since the last round.
- **No review rules.** The skill asks for no reviewer and no second model; a review happens when you ask.

The notebook look is set in IBM Plex, which ships with the plugin under the SIL Open Font License
(`skills/decision-page/assets/fonts/OFL.txt`).
