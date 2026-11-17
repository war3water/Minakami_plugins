# Publishing on an Artifact or as a static file

The local page (`page.py serve <q>`) is the default. Use this file when the user asks for a claude.ai Artifact, or when the local server cannot run.

## A claude.ai Artifact

Use it when the user asks for one and the Artifact tools are available (Claude Code signed in to claude.ai). It opens on any device, and its comment box has Send to Claude, which brings this session into the thread.

1. Load the Artifact design and capabilities guidance first (the Artifact tool's quickstart gives it).
2. Run `page.py build <q> --mode artifact`. Fix every error it prints and act on each warning.
3. Publish `page.html` with capabilities `{db:{}, user:{}, comments:{}}` and every picture (images, drawings and demos) as a supporting file, using the paths the build prints. The build also lists the archive's round files (`archive/...json`) once earlier rounds exist; publish those too.
4. After the first publish, list the `answers` collection once with ArtifactData to confirm the page's store answers. It is empty until the user picks something.

The published page is the `page.html` you built in the task folder; the answers are in the `answers` collection, and earlier rounds in `archive/` (see `page.py history`).

Answers go to the `answers` collection, one document per question id: `choice` (an option id, `"other"`, or `null` after Clear), `other`, `note`, `at` and `by`.

Comments sent with Send to Claude reach this session as notifications; answer each in its thread with ArtifactComments.

To read back, in one turn: get this round's answers with ArtifactData, with `out_dir` set to the task folder, and call ArtifactComments `read` for the threads. On the first round, `list` the `answers` collection. After a `page.py mark`, `query` it for answers with `at` at or after the time `build` prints (`marked_at` in questions.json), so earlier rounds' answers stay out; never list the whole collection again. The result lands as one file per answer in `<task folder>/answers/`; `page.py read <q> --answers <task folder>/answers` reads them, and `page.py mark` takes the same `--answers`.

To republish, update the existing Artifact rather than creating a new one, so the stored answers and comments stay with it. Pass only the files that are new or changed; files left out stay published.

## A static file

Use it when the server cannot start or does not outlive your command: some sandboxes forbid opening a port or end background processes.

- Build with `page.py build <q> --mode static` and give the user the path of `page.html`.
- The page carries its drawings and demos inside it; keep its images next to it. It keeps answers in the browser and has no comments. It offers Download answers.json (ask the user to save it next to `page.html`) and Copy answers (to paste into the chat).
- Read back with `page.py read <q> --answers <the downloaded file>`, or read what the user pasted.
- To republish, rebuild.
