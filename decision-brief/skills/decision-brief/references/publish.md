# Publishing on an Artifact or as a static file

The local page (`brief.py serve <q>`) is the default. Use this file when the user asks for a claude.ai Artifact, or when the local server cannot run.

## A claude.ai Artifact

Use it when the user asks for one and the Artifact tools are available (Claude Code signed in to claude.ai). It opens on any device, and its comment box has Send to Claude, which brings this session into the thread.

1. Load the Artifact design and capabilities guidance first (the Artifact tool's quickstart gives it).
2. Run `brief.py build <q> --mode artifact`. Fix every error it prints and act on each warning.
3. Publish `page.html` with capabilities `{db:{}, user:{}, comments:{}}` and every image as a supporting file, using the paths the build prints (`shots/...`).
4. After the first publish, list the `answers` collection once with ArtifactData to confirm the page's store answers. It is empty until the user picks something.

Answers go to the `answers` collection, one document per question id: `choice` (an option id, `"other"`, or `null` after Clear), `other`, `note`, `at` and `by`.

Comments sent with Send to Claude reach this session as notifications; answer each in its thread with ArtifactComments.

To read back, in one turn: call ArtifactData `list` on the `answers` collection with `out_dir` set to the task folder, and ArtifactComments `read` for the threads. The listing lands as one file per answer in `<task folder>/answers/`; `brief.py read <q> --answers <task folder>/answers` reads them, and `brief.py mark` takes the same `--answers`.

To republish, update the existing Artifact rather than creating a new one, so the stored answers and comments stay with it.

## A static file

Use it when the server cannot start or does not outlive your command: some sandboxes forbid opening a port or end background processes.

- Build with `brief.py build <q> --mode static` and give the user the path of `page.html`.
- The page keeps answers in the browser and has no comments. It offers Download answers.json (ask the user to save it next to `page.html`) and Copy answers (to paste into the chat).
- Read back with `brief.py read <q> --answers <the downloaded file>`, or read what the user pasted.
- To republish, rebuild.
