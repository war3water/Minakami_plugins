# Talking with the user on the page

Use this file when the user is answering now, or wants comments answered while you are away.

## Reading along

1. `brief.py wait <q> --name <your name>` blocks until the user posts a comment or presses I'm done. It prints what is new with the thread so far, and exits. While it runs, the page tells the user you are reading along.
2. Answer each new comment with `brief.py reply <q> <comment id> "<answer>"` (or `-` and the answer on stdin, for long text).
   - Answer in plain words, in the user's language, and explain any short name you use.
   - When a comment shows a card is wrong or missing an option, fix questions.json, say in the reply that you changed it, and tell the user to reload.
3. Wait again.
   - Where your runtime tells you when a background command ends (Claude Code), run `wait --timeout 0` in the background and keep the chat free.
   - Elsewhere, run it in the foreground. It returns after five minutes without news (`--timeout` changes that), and you wait again.
4. Stop when the user presses I'm done (wait says so; read back), says they are done in the chat, or has clearly moved on. Then tell them their comments are kept and read when they come back.

## Ask now, while you are away

`brief.py serve <q> --ask <runtime>` adds an "Ask … now" button to comments. The runtime is `claude`, `codex`, `grok` or `pi`, normally the one you run in.

- The button runs that agent headless and read-only, with the question, the card, the glossary and `context.md`, and posts its answer in the thread.
- Each press is one model call on the user's account. Turn it on when the user wants it or will answer while you are away, and say so when you give the link.
