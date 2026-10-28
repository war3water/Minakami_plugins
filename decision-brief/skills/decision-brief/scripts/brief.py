#!/usr/bin/env python
"""decision-brief helper: build the decision page from questions.json, serve it on this computer with live
comment threads, connect the agent's session to it, and read every answer back.

Standard library only, Python 3.8 or later. Network use: the local server, bound to 127.0.0.1, and, only when
started with --ask, a read-only headless agent (claude -p, codex exec, grok -p, pi -p) that answers a comment
when the user presses "Ask now".

Usage:
    python scripts/brief.py new   SLUG [--images FILE ...] [--root DIR]
    python scripts/brief.py build QUESTIONS [--mode artifact|static] [--out PAGE] [--inline-images]
    python scripts/brief.py serve QUESTIONS [--ask claude|codex|grok|pi|COMMAND] [--port N] [--open] [--foreground]
    python scripts/brief.py wait  QUESTIONS [--timeout SECONDS] [--answers-too] [--name AGENT]
    python scripts/brief.py reply QUESTIONS TARGET [TEXT | - | --file FILE] [--name AGENT]
    python scripts/brief.py read  QUESTIONS [--answers FILE] [--json]
    python scripts/brief.py mark  QUESTIONS [--answers FILE] [--ids ID,ID] [--reports ID,ID] [--round TEXT] [--reopen]
    python scripts/brief.py stop  QUESTIONS
    python scripts/brief.py links QUESTIONS
    python scripts/brief.py example DIR

QUESTIONS is the task's questions.json (format: references/questions-format.md). Next to it live:
    page.html      the built page (build)
    answers.json   answers, comment threads and the "I'm done" signal (the server, wait, reply)
    context.md     optional: what a headless agent should know about the task (written by the agent)
    agent.json     whether the agent's session is listening, and what it has already seen (wait, reply, read)
    server.json    the running local server's address and process id (serve writes it, stop removes it)
    server.log     the local server's log

new      creates .decision-brief/SLUG/ with shots/ (copying the images named) and the .gitignore, in one step.
build    checks questions.json and writes the page. Errors stop the build; warnings (short names missing from
         the glossary, a card without a recommendation, a term without an origin link) are for the agent to act on.
serve    starts the local server in the background and prints its address. The page is rebuilt from
         questions.json on every load, and answers and comments reach every open page within a second.
wait     blocks until the user comments, replies, or presses "I'm done", prints what is new, and exits; while it
         waits, the page tells the user the agent is reading along. --answers-too also wakes on changed answers.
reply    posts the agent's answer: TARGET is a comment id (c7) to answer in its thread, or a card anchor (q-<id>,
         p-<id>, g-<term>, page) to start a thread there.
read     prints every answer and comment thread in one pass, and marks them seen.
mark     moves the cards you acted on to the Decided tab (state "answered", the answer you read kept so a later
         change shows) and, with --reports, archives finished progress reports there; --round names the heading.
links    lists every link in questions.json with where it appears, to check each one before publishing.
example  copies the worked example (assets/example/) into a new folder.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import hmac
import html
import http.client
import json
import mimetypes
import os
import re
import secrets
import shutil
import signal
import socketserver
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "page.html"
APP = "decision-brief"
FORMAT = 2
DEFAULT_PORT = 8377           # tried first; a busy port falls back to one the system picks
MAX_BODY = 1_000_000          # a request larger than this is not an answer
MAX_TEXT = 20_000             # characters kept from one comment or note
POLL_HOLD = 20                # seconds the page's update request waits for news before it asks again
LISTENING_FRESH = 20          # a waiting agent renews its heartbeat every few seconds; older means it stopped
WORKING_FRESH = 900           # seconds after the agent last read or replied that the page says it is working
ASK_TIMEOUT = 600             # seconds a headless answer may take
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^()\s]*(?:\([^()\s]*\)[^()\s]*)*)\)")
ABBR_RE = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]*[A-Z0-9](?:[-/][A-Z0-9]+)*(?![\w-])"
                     r"|(?<![\w-])[A-Z][A-Z0-9]+(?:-[A-Za-z0-9]+)+(?![\w-])")  # also codes such as WF-flat, SW-cache
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".webp": "image/webp", ".svg": "image/svg+xml", ".avif": "image/avif"}

# Headless agents for "Ask now", each limited to reading the project. The prompt goes in on stdin, or through
# the file named by {prompt_file}; codex writes its last message to {reply_file}.
ASK_PRESETS = {
    "claude": ("Claude", ["claude", "-p", "--tools", "Read,Grep,Glob", "--strict-mcp-config",
                          "--no-session-persistence", "--permission-mode", "dontAsk"]),
    "codex": ("Codex", ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral",
                        "-o", "{reply_file}", "-"]),
    "grok": ("Grok", ["grok", "--prompt-file", "{prompt_file}", "--tools", "read_file,grep,list_dir",
                      "--disallowed-tools", "Agent", "--output-format", "plain"]),
    "pi": ("pi", ["pi", "-p", "--no-session", "--tools", "read,grep,find,ls",
                  "Answer the request in the attached file.", "@{prompt_file}"]),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, obj) -> None:
    """Write through a temporary file, so a reader never sees half a file."""
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for _ in range(40):  # Windows refuses the swap while another process has the file open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05)
    os.replace(tmp, path)


@contextmanager
def file_lock(path: Path):
    """One writer at a time across processes (the server, wait, reply): a lock file created exclusively."""
    lock = path.with_name(path.name + ".lock")
    deadline = time.time() + 15
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 30:  # left behind by a process that died mid-write
                    lock.unlink()
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                raise TimeoutError(f"{lock} is held by another process")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def task_files(questions: Path, answers: str | None = None) -> dict:
    base = questions.parent
    return {"base": base, "answers": Path(answers).resolve() if answers else base / "answers.json",
            "agent": base / "agent.json", "server": base / "server.json", "log": base / "server.log",
            "page": base / "page.html", "context": base / "context.md"}


def project_root(questions: Path) -> Path:
    """The project the task belongs to: the folder holding .decision-brief/, else the task folder itself."""
    for parent in questions.parents:
        if parent.name == ".decision-brief":
            return parent.parent
    return questions.parent


# ---------------------------------------------------------------- questions.json: walk, check, prepare

def all_questions(data: dict) -> list:
    """Every question card, in page order: the main list, then each progress report's follow-ups."""
    out = list(data.get("questions") or [])
    for p in data.get("progress") or []:
        out.extend(p.get("questions") or [])
    return out


def glossary_anchors(data: dict) -> list:
    """(entry, anchor) for each glossary entry; the page links a term as #g-<anchor>."""
    taken: set = set()
    return [(g, slug(str(g.get("term", "")), taken)) for g in data.get("glossary") or [] if isinstance(g, dict)]


def comment_targets(data: dict) -> dict:
    """Every place a comment thread can sit, with a name for it."""
    out = {"page": "the page as a whole"}
    for q in all_questions(data):
        out["q-" + str(q.get("id"))] = str(q.get("title", ""))
    for p in data.get("progress") or []:
        out["p-" + str(p.get("id"))] = str(p.get("title", ""))
    for g, anchor in glossary_anchors(data):
        out["g-" + anchor] = f'glossary: {g.get("term")}'
    return out


def texts(data: dict):
    """(where, text) for every piece of reader-facing text outside the glossary."""
    yield "intro", data.get("intro")
    for q in all_questions(data):
        w = f"question {q.get('id')}"
        yield w, q.get("title")
        yield w, q.get("group")
        yield w, q.get("round")
        yield w, q.get("plain")
        yield w, q.get("outcome")
        ex = q.get("example")
        if isinstance(ex, dict):
            yield w, ex.get("text")
            yield from table_texts(w, ex.get("table"))
            yield from figure_texts(w, ex.get("figures"))
        else:
            yield w, ex
        yield from table_texts(w, q.get("table"))
        yield from figure_texts(w, q.get("figures"))
        for o in q.get("options") or []:
            yield w, o.get("label")
            yield w, o.get("effect")
            if isinstance(o.get("recommended"), str):
                yield w, o["recommended"]
            if isinstance(o.get("figure"), dict):
                yield w, o["figure"].get("caption")
    for p in data.get("progress") or []:
        w = f"report {p.get('id')}"
        yield w, p.get("title")
        yield w, p.get("status")
        yield w, p.get("round")
        yield w, p.get("text")
        yield w, p.get("action")
        yield from table_texts(w, p.get("table"))
        yield from figure_texts(w, p.get("figures"))


def table_texts(where: str, t):
    if isinstance(t, dict):
        for cell in (t.get("head") or []):
            yield where, cell
        for row in (t.get("rows") or []):
            for cell in row:
                yield where, cell


def figure_texts(where: str, figs):
    for f in figs or []:
        if isinstance(f, dict):
            yield where, f.get("caption")


def flat(text) -> str:
    if text is None:
        return ""
    return "\n\n".join(map(str, text)) if isinstance(text, list) else str(text)


def slug(term: str, taken: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") or "term"
    s, n = base, 2
    while s in taken:
        s, n = f"{base}-{n}", n + 1
    taken.add(s)
    return s


def check(data, base: Path) -> tuple[list, list]:
    """Return (errors, warnings) for a questions.json document."""
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["the file must hold one JSON object"], []
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        errors.append('"title" is missing')
    if data.get("style") not in (None, "rose", "ledger", "slate"):
        errors.append('"style" is "rose", "ledger" or "slate"')
    for key in ("glossary", "questions", "progress"):
        items = data.get(key)
        if items is not None and (not isinstance(items, list) or not all(isinstance(x, dict) for x in items)):
            errors.append(f'"{key}" must be a list of objects')
    for p in data.get("progress") or []:
        if isinstance(p, dict) and p.get("questions") is not None and (
                not isinstance(p["questions"], list) or not all(isinstance(x, dict) for x in p["questions"])):
            errors.append(f'progress report {p.get("id")!r}: "questions" must be a list of objects')
    if errors:
        return errors, warnings

    covered, anchors = set(), {"page"}
    unlinked: list = []
    for g, anchor in glossary_anchors(data):
        if not g.get("term") or not g.get("meaning"):
            errors.append(f"glossary entry {g.get('term')!r}: needs a term and a meaning")
            continue
        anchors.add("g-" + anchor)
        for name in [g["term"], *(g.get("aka") or [])]:
            covered.update(ABBR_RE.findall(str(name)))
            covered.update(re.findall(r"[A-Z][A-Z0-9]+", str(name)))  # "NFR-nnn" covers NFR-001, NFR-002, ...
            covered.add(str(name).strip())
        sources = g.get("sources") or []
        if not sources:
            unlinked.append(str(g["term"]))
        for s in sources:
            if not isinstance(s, dict) or not re.match(r"^https?://", str(s.get("url", ""))):
                errors.append(f'glossary "{g["term"]}": every source needs an http(s) "url"')
    if unlinked:
        warnings.append("glossary terms without an origin link: " + ", ".join(unlinked) + ". Add one where a term "
                        "comes from a page a reader can open (a spec, a doc in the repository, a standard).")

    seen_q, seen_p = set(), set()
    for p in data.get("progress") or []:
        pid = p.get("id")
        if not isinstance(pid, str) or not ID_RE.match(pid):
            errors.append(f"progress report {pid!r}: id must be lowercase letters, digits and dashes")
            continue
        if pid in seen_p:
            errors.append(f"progress report {pid}: the id is used twice")
        seen_p.add(pid)
        anchors.add("p-" + pid)
        if not p.get("title"):
            errors.append(f"progress report {pid}: needs a title")
        if not isinstance(p.get("archived", False), bool):
            errors.append(f'progress report {pid}: "archived" is true or false')
        for key in ("status", "round"):
            if p.get(key) is not None and not isinstance(p[key], str):
                errors.append(f'progress report {pid}: "{key}" must be text')
        figure_check(p.get("figures"), base, f"report {pid}", errors)

    for q in all_questions(data):
        qid = q.get("id")
        if not isinstance(qid, str) or not ID_RE.match(qid):
            errors.append(f"question {qid!r}: id must be lowercase letters, digits and dashes")
            continue
        if qid in seen_q:
            errors.append(f"question {qid}: the id is used twice; answers are stored by id")
        seen_q.add(qid)
        anchors.add("q-" + qid)
        for key in ("title", "plain"):
            if not q.get(key):
                errors.append(f'question {qid}: needs "{key}"')
        if q.get("state", "open") not in ("open", "answered"):
            errors.append(f'question {qid}: "state" is "open" or "answered"')
        for key in ("group", "round", "ref"):
            if q.get(key) is not None and not isinstance(q[key], str):
                errors.append(f'question {qid}: "{key}" must be text')
        opts = q.get("options") or []
        if not opts:
            errors.append(f"question {qid}: needs at least one option (Other is added by the page)")
        oids = set()
        for o in opts:
            oid = o.get("id") if isinstance(o, dict) else None
            if not isinstance(oid, str) or not ID_RE.match(oid):
                errors.append(f"question {qid}: option {oid!r} needs an id of lowercase letters, digits and dashes")
            elif oid == "other":
                errors.append(f'question {qid}: the option id "other" is reserved for the page\'s Other answer')
            elif oid in oids:
                errors.append(f"question {qid}: option id {oid} is used twice")
            oids.add(oid)
            if isinstance(o, dict) and not o.get("label"):
                errors.append(f"question {qid}: option {oid} needs a label")
            if isinstance(o, dict) and o.get("figure") is not None:
                figure_check([o["figure"]], base, f"question {qid}, option {oid}", errors)
        recs = [o for o in opts if isinstance(o, dict) and o.get("recommended")]
        if len(recs) > 1:
            errors.append(f"question {qid}: more than one option is recommended; recommend one and say when "
                          "another fits in its recommendation text")
        elif not recs and q.get("state", "open") == "open":
            warnings.append(f"question {qid}: no recommended option. Recommend one, or say in the text why you "
                            "have no preference.")
        ex = q.get("example")
        if isinstance(ex, dict):
            figure_check(ex.get("figures"), base, f"question {qid}", errors)
        figure_check(q.get("figures"), base, f"question {qid}", errors)

    glossary_texts = [(f'glossary "{g.get("term")}"', g.get("meaning")) for g in data.get("glossary") or []]
    for where, text in [*glossary_texts, *texts(data)]:
        for label, url in LINK_RE.findall(flat(text)):
            if url.startswith("#"):
                if url[1:] not in anchors:
                    warnings.append(f"{where}: link [{label}]({url}) points to no card or glossary entry here")
            elif not re.match(r"^https?://", url):
                errors.append(f"{where}: link [{label}]({url}) must start with http:// or https://")

    missing: dict = {}
    for where, text in texts(data):
        plain_text = LINK_RE.sub(lambda m: m.group(1), flat(text))
        for tok in ABBR_RE.findall(plain_text):
            if tok not in covered and tok.split("-")[0] not in covered and tok.split("/")[0] not in covered:
                missing.setdefault(tok, where)
    if missing:
        warnings.append("short names not in the glossary (explain each there or in plain words where it appears): "
                        + ", ".join(f"{tok} ({where})" for tok, where in sorted(missing.items())))
    return errors, warnings


def figure_check(figs, base: Path, where: str, errors: list) -> None:
    for f in figs or []:
        if not isinstance(f, dict) or not f.get("src"):
            errors.append(f'{where}: every figure needs "src"')
            continue
        if not f.get("alt"):
            errors.append(f'{where}: figure {f["src"]} needs "alt", a description for readers who cannot see it')
        src = str(f["src"])
        if src.startswith("data:"):
            continue
        if re.match(r"^[a-z]+:", src, re.I):
            errors.append(f"{where}: figure {src} must be a file in the task folder, not a web address")
            continue
        path = (base / src).resolve()
        if not path.is_file():
            errors.append(f"{where}: figure {src} not found (paths are relative to questions.json)")
        elif path.suffix.lower() not in IMAGE_TYPES:
            errors.append(f"{where}: figure {src} is not an image type the page can show")
        elif base.resolve() not in path.parents:
            errors.append(f"{where}: figure {src} must sit inside the folder that holds questions.json")


def figure_list(data: dict) -> list:
    out = []
    for q in all_questions(data):
        out.extend(q.get("figures") or [])
        if isinstance(q.get("example"), dict):
            out.extend(q["example"].get("figures") or [])
        out.extend(o["figure"] for o in q.get("options") or [] if isinstance(o, dict) and isinstance(o.get("figure"), dict))
    for p in data.get("progress") or []:
        out.extend(p.get("figures") or [])
    return out


def prepare(data: dict, base: Path, inline_images: bool) -> tuple[dict, int]:
    """The data the page embeds: glossary anchors, a page id, the build time, image sources. Returns (data, image bytes)."""
    out = copy.deepcopy(data)
    ids = [q.get("id", "") for q in all_questions(out)]
    out["page_id"] = hashlib.sha1((out.get("title", "") + "|" + ",".join(ids)).encode("utf-8")).hexdigest()[:12]
    out["generated"] = now()
    for g, anchor in glossary_anchors(out):
        g["anchor"] = anchor
    size = 0
    for f in figure_list(out):
        src = str(f.get("src", ""))
        if src.startswith("data:"):
            size += len(src)
            continue
        path = (base / src).resolve()
        size += path.stat().st_size if path.is_file() else 0
        if inline_images and path.is_file():
            mime = IMAGE_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            f["src"] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        else:
            f["src"] = Path(src).as_posix()
    return out, size


def render(data: dict, config: dict, mode: str) -> str:
    """Fill the page template. Artifact mode keeps the fragment form claude.ai Artifacts take (the publisher adds
    the document skeleton); the others get a full document."""
    template = TEMPLATE.read_text(encoding="utf-8")
    head, body = template.split("<!-- brief:body -->", 1)

    def blob(obj) -> str:  # JSON inside <script>: escape the characters that could end the element
        return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    head = head.replace("__BRIEF_TITLE__", html.escape(str(data.get("title", "Decisions")), quote=False))
    body = body.replace("__BRIEF_DATA__", blob(data)).replace("__BRIEF_CONFIG__", blob(config))
    if mode == "artifact":
        return head + body
    lang = html.escape(str(data.get("lang") or "en"))
    return (f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n{head}</head>\n<body>\n{body}</body>\n</html>\n')


def load_checked(questions: Path) -> tuple[dict, list]:
    try:
        data = read_json(questions)
    except FileNotFoundError:
        sys.exit(f"error: {questions} not found")
    except json.JSONDecodeError as e:
        sys.exit(f"error: {questions} is not valid JSON: {e}")
    errors, warnings = check(data, questions.parent)
    if errors:
        print(f"{questions}: {len(errors)} problem(s), nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    return data, warnings


def describe(data: dict) -> str:
    def n(count, word):
        return f"{count} {word}" + ("" if count == 1 else "s")
    qs = all_questions(data)
    open_n = sum(1 for q in qs if q.get("state", "open") == "open")
    parts = [n(len(qs), "question") + f" ({open_n} open, {len(qs) - open_n} decided)",
             n(len(data.get("glossary") or []), "glossary term")]
    if data.get("progress"):
        archived = sum(1 for p in data["progress"] if p.get("archived"))
        parts.append(n(len(data["progress"]), "progress report") + (f" ({archived} archived)" if archived else ""))
    return ", ".join(parts)


def cmd_build(a) -> int:
    questions = Path(a.questions).resolve()
    data, warnings = load_checked(questions)
    page, size = prepare(data, questions.parent, a.inline_images)
    out = Path(a.out).resolve() if a.out else task_files(questions)["page"]
    if not a.inline_images and out.parent != questions.parent and size:
        print("warning: the page is written outside the task folder, so its relative image paths will not resolve; "
              "add --inline-images or write it next to questions.json", file=sys.stderr)
    out.write_text(render(page, {"mode": a.mode}, a.mode), encoding="utf-8")
    print(f"wrote {out} ({a.mode} mode): {describe(data)}")
    figs = sorted({str(f.get("src")) for f in figure_list(data) if not str(f.get("src", "")).startswith("data:")})
    if size:
        print(f"images: {size // 1024} KB" + (" inlined into the page" if a.inline_images else
                                              ", linked by relative path; keep them next to the page"))
        if a.mode == "artifact" and not a.inline_images:
            print("publish them with the page as files: " + ", ".join(f'"{s}": "{s}"' for s in figs))
    for w in warnings:
        print(f"warning: {w}")
    return 0


# ---------------------------------------------------------------- answers.json: answers, threads, the done signal

def empty_answers(title: str = "") -> dict:
    return {"app": APP, "format": FORMAT, "title": title, "rev": 0, "answers": {}, "comments": [], "done": None}


def parse_answers(raw) -> tuple[dict, list]:
    """Answers and comments from answers.json, from a page download, or from a saved Artifact collection listing
    (a list of documents, each with an id and the answer fields or a "data" object)."""
    if isinstance(raw, dict) and isinstance(raw.get("answers"), dict):
        return raw["answers"], list(raw.get("comments") or [])
    docs = None
    if isinstance(raw, list):
        docs = raw
    elif isinstance(raw, dict):
        for key in ("documents", "docs", "items", "results"):
            if isinstance(raw.get(key), list):
                docs = raw[key]
                break
        if docs is None and all(isinstance(v, dict) for v in raw.values()):
            return dict(raw), []
    answers = {}
    for d in docs or []:
        if not isinstance(d, dict):
            continue
        did = d.get("id") or d.get("docId") or d.get("key") or str(d.get("path", "")).rsplit("/", 1)[-1]
        body = d.get("data") if isinstance(d.get("data"), dict) else {k: v for k, v in d.items()
                                                                      if k not in ("id", "docId", "key", "path")}
        if did:
            answers[str(did)] = body
    return answers, []


def load_store(path: Path) -> dict:
    """answers.json as the server writes it; a missing file is an empty store. Also reads what an agent saved from
    an Artifact: the folder ArtifactData `list` with `out_dir` writes (one <question id>.json per answer), or the
    listing's text pasted into a file (one {"id": ..., "data": {...}} object per line)."""
    if path.is_dir():
        store = empty_answers()
        for f in sorted(path.glob("*.json")):
            store["answers"][f.stem] = read_json(f)
        return store
    if not path.is_file():
        return empty_answers()
    text = path.read_text(encoding="utf-8-sig")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        raw = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]
        if not raw:
            raise
    store = empty_answers(raw.get("title", "") if isinstance(raw, dict) else "")
    if isinstance(raw, dict) and isinstance(raw.get("answers"), dict):
        store.update({k: v for k, v in raw.items() if k in ("title", "rev", "answers", "comments", "done")})
    else:  # a download or listing saved by hand
        store["answers"], store["comments"] = parse_answers(raw)
    store["comments"] = [c for c in store.get("comments") or [] if isinstance(c, dict)]
    store["rev"] = int(store.get("rev") or 0)
    return store


def update_store(path: Path, change):
    """Apply change(store) under the cross-process lock, bump the revision the pages wait on, save."""
    with file_lock(path):
        store = load_store(path)
        result = change(store)
        store["rev"] += 1
        write_json(path, store)
    return result


def new_comment(store: dict, **fields) -> dict:
    numbers = [int(c["id"][1:]) for c in store["comments"] if re.match(r"^c\d+$", str(c.get("id", "")))]
    comment = {"id": f"c{max(numbers, default=0) + 1}", "at": now(), **fields}
    store["comments"].append(comment)
    return comment


def thread_root(comments: list, cid: str) -> dict | None:
    by_id = {c.get("id"): c for c in comments}
    c = by_id.get(cid)
    while c is not None and c.get("parent") in by_id:
        c = by_id[c["parent"]]
    return c


def threads(comments: list) -> list:
    """[(root, [root, replies...])] in the order the threads were started."""
    roots, out = {}, []
    for c in comments:
        root = thread_root(comments, c.get("id"))
        if root is None:
            continue
        if root["id"] not in roots:
            roots[root["id"]] = [root]
            out.append((root, roots[root["id"]]))
        if c is not root:
            roots[root["id"]].append(c)
    return out


def who(c: dict) -> str:
    return "user" if c.get("by") == "user" else (c.get("name") or "agent")


# ---------------------------------------------------------------- the agent's presence and what it has seen

def load_agent(files: dict) -> dict:
    try:
        return read_json(files["agent"]) if files["agent"].is_file() else {}
    except (OSError, ValueError):
        return {}


def update_agent(files: dict, change) -> dict:
    with file_lock(files["agent"]):
        agent = load_agent(files)
        change(agent)
        write_json(files["agent"], agent)
    return agent


def beat(agent: dict, state: str, name: str | None = None) -> None:
    agent["state"], agent["beat"], agent["heartbeat"] = state, time.time(), now()
    if name:
        agent["name"] = name


def agent_status(files: dict) -> dict:
    """What the page shows: listening (a wait is running), working (it read or replied a moment ago), or away."""
    agent = load_agent(files)
    age = time.time() - float(agent.get("beat") or 0)
    state = "away"
    if agent.get("state") == "listening" and age < LISTENING_FRESH:
        state = "listening"
    elif agent.get("state") in ("listening", "working") and age < WORKING_FRESH:
        state = "working"
    return {"state": state, "name": agent.get("name") or "the agent"}


def mark_seen(files: dict, store: dict, state: str = "working", name: str | None = None) -> None:
    def change(agent):
        agent["seen_comments"] = sorted({c.get("id") for c in store["comments"]} | set(agent.get("seen_comments") or []))
        agent["seen_done"] = (store.get("done") or {}).get("at")
        agent["seen_answers"] = {k: (v or {}).get("at") for k, v in store["answers"].items()}
        beat(agent, state, name)
    update_agent(files, change)


def news(store: dict, agent: dict, answers_too: bool) -> dict:
    seen = set(agent.get("seen_comments") or [])
    fresh = [c for c in store["comments"] if c.get("by") == "user" and c.get("id") not in seen]
    done = store.get("done") or {}
    out = {"comments": fresh, "done": done if done.get("at") and done.get("at") != agent.get("seen_done") else None,
           "answers": []}
    if answers_too:
        was = agent.get("seen_answers") or {}
        out["answers"] = [k for k, v in store["answers"].items() if (v or {}).get("at") != was.get(k)]
    return out


# ---------------------------------------------------------------- reading back

def option_label(q: dict, choice) -> str:
    for o in q.get("options") or []:
        if o.get("id") == choice:
            return re.sub(r"[*`]", "", str(o.get("label", choice)))
    return str(choice)


def is_recommended(q: dict, choice) -> bool:
    return any(o.get("id") == choice and o.get("recommended") for o in q.get("options") or [])


def summarize(data: dict, answers: dict, comments: list, done=None) -> dict:
    result = {"title": data.get("title"), "answered": [], "open": [], "changed": [], "threads": [], "unknown": [],
              "done": done}
    known = set()
    for q in all_questions(data):
        qid = q["id"]
        known.add(qid)
        a = answers.get(qid) or {}
        choice = a.get("choice")
        entry = {"id": qid, "title": q.get("title"), "state": q.get("state", "open"), "choice": choice,
                 "note": (a.get("note") or "").strip(), "at": a.get("at")}
        if choice == "other":
            entry["answer"] = "Other: " + (a.get("other") or "").strip()
        elif choice is not None:
            entry["answer"] = option_label(q, choice)
            entry["recommended"] = is_recommended(q, choice)
        read = q.get("read")
        if q.get("state") == "answered" and read is not None and any(
                (read.get(k) or None) != (a.get(k) or None) for k in ("choice", "other", "note")):
            entry["was"] = read
            result["changed"].append(entry)
        if choice is None:
            if q.get("state", "open") == "open":
                result["open"].append(entry)
        elif q.get("state", "open") == "open":
            result["answered"].append(entry)
    result["unknown"] = sorted(k for k in answers if k not in known)
    names = comment_targets(data)
    for root, msgs in threads(comments):
        result["threads"].append({"id": root["id"], "target": root.get("target"),
                                  "on": names.get(root.get("target"), root.get("target")), "quote": root.get("quote"),
                                  "messages": [{"id": m.get("id"), "by": who(m), "text": m.get("text", ""),
                                                "at": m.get("at")} for m in msgs],
                                  "waiting": msgs[-1].get("by") == "user"})
    return result


def print_summary(s: dict) -> None:
    waiting = [t for t in s["threads"] if t["waiting"]]
    n_threads = len(s["threads"])
    print(f"{s['title']}: {len(s['answered'])} answered, {len(s['open'])} still open"
          + (f", {len(s['changed'])} changed after you marked them" if s["changed"] else "")
          + (f", {n_threads} comment thread{'' if n_threads == 1 else 's'} ({len(waiting)} waiting for an answer)"
             if s["threads"] else "")
          + ("; the user pressed I'm done" if s.get("done") else "") + ".")

    def line(e):
        rec = ""
        if "recommended" in e:
            rec = " [recommended]" if e["recommended"] else " [not the recommended option]"
        out = f"  {e['id']}: {e['title']}"
        if e.get("answer"):
            out += f"\n      -> {e['answer']}{rec}"
        if e.get("note"):
            out += f"\n      note: {e['note']}"
        return out

    for head, key in (("Answered", "answered"), ("Still open", "open"), ("Changed after you marked them", "changed")):
        if s[key]:
            print(f"\n{head}")
            for e in s[key]:
                print(line(e))
                if key == "changed":
                    was = e["was"]
                    print(f"      was: {was.get('choice')}" + (f" / {was.get('other')}" if was.get("other") else "")
                          + (f" / note: {was.get('note')}" if was.get("note") else ""))
    if s["threads"]:
        print("\nComment threads")
        for t in s["threads"]:
            print_thread(t)
    if s.get("done"):
        note = (s["done"] or {}).get("note")
        print(f"\nThe user pressed I'm done at {s['done'].get('at')}" + (f": {note}" if note else "."))
    if s["unknown"]:
        print("\nAnswers for ids no longer in questions.json: " + ", ".join(s["unknown"]))


def print_thread(t: dict, new_ids: set | None = None) -> None:
    print(f"  [{t['id']}] on {t['target']} ({t['on']})" + ("  <- waiting for your answer" if t.get("waiting") else ""))
    if t.get("quote"):
        print(f"      about: \"{t['quote']}\"")
    for m in t["messages"]:
        mark = "NEW " if new_ids and m["id"] in new_ids else ""
        text = m["text"].strip().replace("\n", "\n        ")
        print(f"      {mark}{m['by']} ({m['id']}): {text}")


def cmd_read(a) -> int:
    questions = Path(a.questions).resolve()
    data, _ = load_checked(questions)
    files = task_files(questions, a.answers)
    path = files["answers"]
    try:
        store = load_store(path)
    except ValueError as e:
        sys.exit(f"error: {path} is not valid JSON: {e}")
    s = summarize(data, store["answers"], store["comments"], store.get("done"))
    s["answers_file"] = str(path) if path.exists() else None
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        if not path.exists():
            print(f"(no answers file at {path} yet)")
        print_summary(s)
    if path.is_file() and not a.answers:
        mark_seen(files, store)
    return 0


def cmd_mark(a) -> int:
    questions = Path(a.questions).resolve()
    data, _ = load_checked(questions)
    try:
        answers = load_store(task_files(questions, a.answers)["answers"])["answers"]
    except ValueError as e:
        sys.exit(f"error: the answers file is not valid JSON: {e}")
    def names(values):  # "a,b", "a b" and "a, b" all work
        return {i.strip() for v in values or [] for i in re.split(r"[,\s]+", v) if i.strip()}
    wanted, reports = names(a.ids), names(a.reports)
    changed, missing_outcome, archived = [], [], []
    for q in all_questions(data) if wanted or not reports else []:
        qid = q["id"]
        ans = answers.get(qid) or {}
        if wanted:
            if qid not in wanted:
                continue
        elif a.reopen or ans.get("choice") is None or q.get("state") == "answered":
            continue
        if a.reopen:
            q["state"] = "open"
            q.pop("read", None)
            q.pop("round", None)
        else:
            q["state"] = "answered"
            if a.round:
                q["round"] = a.round
            if qid in answers:
                q["read"] = {k: ans.get(k) for k in ("choice", "other", "note", "at")}
            if not q.get("outcome"):
                missing_outcome.append(qid)
        changed.append(qid)
    for p in data.get("progress") or []:
        if p.get("id") not in reports:
            continue
        p["archived"] = not a.reopen
        if a.reopen:
            p.pop("round", None)
        elif a.round:
            p["round"] = a.round
        archived.append(p["id"])
    unknown = sorted(wanted - {q["id"] for q in all_questions(data)})
    unknown += sorted(reports - {p.get("id") for p in data.get("progress") or []})
    if unknown:
        print("warning: no question or report with id " + ", ".join(unknown), file=sys.stderr)
    if not changed and not archived:
        print("nothing to mark")
        return 0
    write_json(questions, data)
    if changed:
        print(("reopened: " if a.reopen else "marked answered, now on the Decided tab: ") + ", ".join(changed))
    if archived:
        print(("back on Work status: " if a.reopen else "reports moved to the Decided tab: ") + ", ".join(archived))
    if missing_outcome:
        print('add an "outcome" to each of these, saying what you did: ' + ", ".join(missing_outcome))
    return 0


def cmd_links(a) -> int:
    questions = Path(a.questions).resolve()
    data = read_json(questions)
    rows = []
    for g in data.get("glossary") or []:
        for s in g.get("sources") or []:
            rows.append((s.get("url", ""), f'glossary "{g.get("term")}"'))
        for _, url in LINK_RE.findall(flat(g.get("meaning"))):
            rows.append((url, f'glossary "{g.get("term")}"'))
    for where, text in texts(data):
        for _, url in LINK_RE.findall(flat(text)):
            if not url.startswith("#"):
                rows.append((url, where))
    for url, where in rows:
        print(f"{url}\t{where}")
    if not rows:
        print("(no links)")
    return 0


# ---------------------------------------------------------------- the live session: wait and reply

def cmd_wait(a) -> int:
    questions = Path(a.questions).resolve()
    data, _ = load_checked(questions)
    files = task_files(questions)
    deadline = time.time() + a.timeout if a.timeout > 0 else None
    update_agent(files, lambda agent: beat(agent, "listening", a.name))
    last_beat = time.time()
    try:
        while True:
            store = load_store(files["answers"])
            found = news(store, load_agent(files), a.answers_too)
            if found["comments"] or found["done"] or found["answers"]:
                print_news(questions, data, store, found)
                mark_seen(files, store, "working", a.name)
                return 0
            if deadline and time.time() > deadline:
                update_agent(files, lambda agent: beat(agent, "working", a.name))
                print(f"NO NEW ACTIVITY in {a.timeout} s. Run wait again to keep listening, or stop when the user "
                      "has moved on.")
                return 0
            if time.time() - last_beat > 5:
                update_agent(files, lambda agent: beat(agent, "listening", a.name))
                last_beat = time.time()
            time.sleep(0.5)
    except KeyboardInterrupt:
        update_agent(files, lambda agent: beat(agent, "working", a.name))
        return 130


def print_news(questions: Path, data: dict, store: dict, found: dict) -> None:
    s = summarize(data, store["answers"], store["comments"], store.get("done"))
    new_ids = {c["id"] for c in found["comments"]}
    touched = [t for t in s["threads"] if any(m["id"] in new_ids for m in t["messages"])]
    parts = []
    if touched:
        parts.append(f"{len(new_ids)} new comment(s) in {len(touched)} thread(s)")
    if found["answers"]:
        parts.append(f"{len(found['answers'])} changed answer(s)")
    if found["done"]:
        parts.append("the user pressed I'm done")
    print(f"NEW ACTIVITY on {s['title']}: " + ", ".join(parts) + ".")
    for t in touched:
        print()
        print_thread(t, new_ids)
        print(f"      answer with: brief.py reply {questions} {t['messages'][-1]['id']} \"<your answer>\"")
    if found["answers"]:
        print()
        for e in s["answered"] + s["open"] + s["changed"]:
            if e["id"] in found["answers"]:
                print(f"  {e['id']}: {e['title']} -> {e.get('answer') or 'no choice'}"
                      + (f" (note: {e['note']})" if e.get("note") else ""))
    if found["done"]:
        note = found["done"].get("note")
        print("\nThe user pressed I'm done" + (f": {note}" if note else "") + f". Read everything now: brief.py read {questions}")


def cmd_reply(a) -> int:
    questions = Path(a.questions).resolve()
    data, _ = load_checked(questions)
    files = task_files(questions)
    if a.file:
        text = Path(a.file).read_text(encoding="utf-8-sig")
    elif a.text in (None, "-"):
        text = sys.stdin.read()
    else:
        text = a.text
    text = text.strip()
    if not text:
        sys.exit("error: the reply is empty")
    targets = comment_targets(data)
    name = a.name or load_agent(files).get("name") or "agent"

    def change(store):
        if re.match(r"^c\d+$", a.target):
            root = thread_root(store["comments"], a.target)
            if root is None:
                raise SystemExit(f"error: no comment {a.target}")
            return new_comment(store, target=root.get("target"), parent=root["id"], by="agent", name=name,
                               text=text[:MAX_TEXT])
        if a.target not in targets:
            raise SystemExit(f"error: {a.target} is neither a comment id nor a place on the page "
                             f"({', '.join(sorted(targets))})")
        return new_comment(store, target=a.target, by="agent", name=name, text=text[:MAX_TEXT])

    comment = update_store(files["answers"], change)

    def seen_own(agent):
        agent.setdefault("seen_comments", []).append(comment["id"])
        beat(agent, "working", name)
    update_agent(files, seen_own)
    where = f"thread {comment.get('parent')}" if comment.get("parent") else f"a new thread {comment['id']}"
    print(f"posted {comment['id']} in {where} on {comment['target']}; open pages show it within a second")
    return 0


# ---------------------------------------------------------------- "Ask now": one read-only headless answer

def ask_spec(choice: str | None, name: str | None):
    """(display name, command list or shell string) for --ask, or None. Presets are checked on PATH."""
    if not choice:
        return None
    if choice in ASK_PRESETS:
        label, cmd = ASK_PRESETS[choice]
        exe = shutil.which(cmd[0])
        if not exe:
            sys.exit(f"error: --ask {choice}: {cmd[0]} is not on PATH")
        if exe.lower().endswith(".ps1"):
            shell = shutil.which("pwsh") or shutil.which("powershell")
            return name or label, [shell, "-NoProfile", "-File", exe, *cmd[1:]]
        return name or label, [exe, *cmd[1:]]
    return name or choice.split()[0], choice


def card_text(data: dict, target: str, answers: dict) -> str:
    """The commented place as plain text for a headless agent."""
    def opts(q):
        lines = []
        for o in q.get("options") or []:
            rec = ""
            if o.get("recommended"):
                rec = " (recommended" + (f": {o['recommended']}" if isinstance(o["recommended"], str) else "") + ")"
            lines.append(f"- {o.get('label')}{rec}: {o.get('effect', '')}")
        a = answers.get(q.get("id")) or {}
        choice = a.get("choice")
        if choice is None:
            current = "no choice yet"
        elif choice == "other":
            current = "Other: " + str(a.get("other", ""))
        else:
            current = option_label(q, choice)
        lines.append(f"The user's current answer: {current}" + (f"; note: {a.get('note')}" if a.get("note") else ""))
        return "\n".join(lines)

    for q in all_questions(data):
        if target == "q-" + q["id"]:
            ex = q.get("example")
            ex_text = flat(ex.get("text") if isinstance(ex, dict) else ex)
            return (f"Question: {q.get('title')}\n\nIn plain words: {flat(q.get('plain'))}\n\n"
                    + (f"Example: {ex_text}\n\n" if ex_text else "") + "Options:\n" + opts(q)
                    + (f"\n\nWhat the agent did: {flat(q.get('outcome'))}" if q.get("outcome") else ""))
    for p in data.get("progress") or []:
        if target == "p-" + p["id"]:
            return (f"Progress report: {p.get('title')} ({p.get('status', 'built')})\n\n{flat(p.get('text'))}"
                    + (f"\n\nAction asked of the user: {p['action']}" if p.get("action") else ""))
    for g, anchor in glossary_anchors(data):
        if target == "g-" + anchor:
            return f"Glossary entry: {g.get('term')}: {flat(g.get('meaning'))}"
    return f"The page as a whole: {data.get('title')}. {flat(data.get('intro'))}"


def ask_prompt(data: dict, store: dict, cid: str, context: str) -> str:
    root = thread_root(store["comments"], cid) or {"target": "page"}
    msgs = next((ms for t_root, ms in threads(store["comments"]) if t_root is root), [])
    convo = "\n".join(f"{'User' if m.get('by') == 'user' else m.get('name', 'Agent')}: {m.get('text', '')}"
                      for m in msgs)
    glossary = "\n".join(f"- {g.get('term')}: {flat(g.get('meaning'))}" for g in data.get("glossary") or [])
    quote = f'Quoted from the page: "{root["quote"]}"\n' if root.get("quote") else ""
    return f"""You are answering one comment on a decision page that a coding agent made for the user. You cannot see
that agent's conversation: the material below and the project files in the current folder are all you have.

Answer the user's last message in the thread directly, in plain words, in the language they wrote in, in a few
sentences. Explain every short name you use. Read project files when the answer depends on them, and say which
file you looked at. If the answer needs something you cannot see, say what, and suggest asking the main session.
Do not change any file. Reply with the answer text only.

# What the agent wrote about the task
{context.strip() or "(nothing)"}

# The page: {data.get('title')}
Glossary:
{glossary or "(none)"}

# Where the comment sits
{card_text(data, root.get('target', 'page'), store['answers'])}

# The thread
{quote}{convo}
"""


class Asker:
    """Runs one headless answer at a time, so a burst of questions never starts several agents at once."""

    def __init__(self, name: str, cmd, files: dict, questions: Path):
        self.name, self.cmd, self.files, self.questions = name, cmd, files, questions
        self.lock = threading.Lock()

    def start(self, cid: str) -> None:
        threading.Thread(target=self.run, args=(cid,), daemon=True).start()

    def run(self, cid: str) -> None:
        with self.lock:
            prompt_file = self.files["base"] / f".ask-{cid}.prompt.txt"
            reply_file = self.files["base"] / f".ask-{cid}.reply.txt"
            text, ok = "", False
            try:
                data = read_json(self.questions)
                store = load_store(self.files["answers"])
                context = self.files["context"].read_text(encoding="utf-8") if self.files["context"].is_file() else ""
                prompt = ask_prompt(data, store, cid, context)
                prompt_file.write_text(prompt, encoding="utf-8")

                def fill(s: str) -> str:
                    return s.replace("{prompt_file}", str(prompt_file)).replace("{reply_file}", str(reply_file))
                uses_file = "{prompt_file}" in (self.cmd if isinstance(self.cmd, str) else " ".join(self.cmd))
                kw = {"input": None if uses_file else prompt, "capture_output": True, "text": True, "encoding": "utf-8",
                      "errors": "replace", "timeout": ASK_TIMEOUT, "cwd": str(project_root(self.questions))}
                if isinstance(self.cmd, str):
                    p = subprocess.run(fill(self.cmd), shell=True, **kw)
                else:
                    p = subprocess.run([fill(x) for x in self.cmd], **kw)
                text = reply_file.read_text(encoding="utf-8", errors="replace") if reply_file.is_file() else p.stdout
                text = (text or "").strip()
                ok = p.returncode == 0 and bool(text)
                if not ok:
                    sys.stderr.write(f"{now()} ask {cid}: exit {p.returncode}\n{(p.stderr or '')[-2000:]}\n")
                    last = ((p.stderr or "").strip().splitlines() or [""])[-1][:300]
                    text = f"{self.name} could not answer (exit code {p.returncode}). {last}".strip()
            except subprocess.TimeoutExpired:
                text = f"{self.name} did not answer within {ASK_TIMEOUT // 60} minutes."
            except Exception as e:  # report every failure in the thread rather than leave it pending
                text = f"{self.name} could not be asked: {e}"
            finally:
                for f in (prompt_file, reply_file):
                    try:
                        f.unlink()
                    except OSError:
                        pass

            def change(store):
                asked = next((c for c in store["comments"] if c.get("id") == cid), None)
                if asked is not None:
                    asked["ask"] = "answered" if ok else "failed"
                root = thread_root(store["comments"], cid) or {"id": cid, "target": "page"}
                new_comment(store, target=root.get("target"), parent=root["id"], by="agent",
                            name=f"{self.name} (asked from the page)", text=text[:MAX_TEXT], headless=True)
            update_store(self.files["answers"], change)


# ---------------------------------------------------------------- local server

class BriefServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"  # on Windows, reuse would let two servers share a port

    def server_bind(self):  # skip HTTPServer's reverse DNS lookup of the address
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


class Handler(BaseHTTPRequestHandler):
    server_version = APP
    ctx: dict = {}  # set by serve_foreground(): questions, files, token, asker

    def log_message(self, fmt, *args):
        if "/api/state" not in str(args[0] if args else ""):  # the page's waiting requests would flood the log
            sys.stderr.write(f"{now()} {fmt % args}\n")

    def send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # the page went away while it waited

    def json(self, code: int, obj):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def allowed(self) -> bool:
        """Only this computer's own browser: the Host header must name the loopback address, which keeps out web
        pages that rebind their domain to 127.0.0.1; reads and writes also need the page's token and JSON."""
        port = self.server.server_address[1]
        if self.headers.get("Host", "") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            self.json(403, {"error": "host not allowed"})
            return False
        return True

    def authed(self) -> bool:
        ok = hmac.compare_digest(self.headers.get("X-Brief-Token", ""), self.ctx["token"])
        if not ok:
            self.json(403, {"error": "missing or wrong token; reload the page"})
        return ok

    def body(self):
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self.json(415, {"error": "send JSON"})
            return None
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            self.json(413, {"error": "too large"})
            return None
        try:
            doc = json.loads(self.rfile.read(n).decode("utf-8") or "null")
        except (ValueError, UnicodeDecodeError):
            self.json(400, {"error": "not JSON"})
            return None
        if not isinstance(doc, dict):
            self.json(400, {"error": "send an object"})
            return None
        return doc

    def questions(self):
        """The current questions.json, re-read on every request so edits show on reload."""
        try:
            data = read_json(self.ctx["questions"])
            errors, _ = check(data, self.ctx["questions"].parent)
            if not errors:
                self.ctx["last_good"] = data
            return data, errors
        except (OSError, ValueError) as e:
            return self.ctx.get("last_good"), [f"questions.json could not be read: {e}"]

    def state(self) -> dict:
        store = load_store(self.ctx["files"]["answers"])
        asker = self.ctx.get("asker")
        return {"rev": store["rev"], "answers": store["answers"], "comments": store["comments"],
                "done": store.get("done"), "agent": agent_status(self.ctx["files"]),
                "ask": {"name": asker.name} if asker else None}

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.allowed():
            return
        url = urlsplit(self.path)
        if url.path == "/":
            data, errors = self.questions()
            if errors:
                items = "".join(f"<li>{html.escape(e)}</li>" for e in errors)
                page = ("<!doctype html><meta charset=utf-8><title>questions.json has problems</title>"
                        f"<h1>questions.json has problems</h1><ul>{items}</ul>")
                return self.send(500, page.encode("utf-8"), "text/html; charset=utf-8")
            page, _ = prepare(data, self.ctx["questions"].parent, inline_images=False)
            out = render(page, {"mode": "local", "api": "/api/", "token": self.ctx["token"]}, "local")
            csp = ("default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                   "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
            return self.send(200, out.encode("utf-8"), "text/html; charset=utf-8", {"Content-Security-Policy": csp})
        if url.path == "/api/ping":
            return self.json(200, {"app": APP, "pid": os.getpid(), "questions": str(self.ctx["questions"])})
        if url.path == "/api/state":
            if not self.authed():
                return
            query = parse_qs(url.query)
            try:
                since = int((query.get("since") or ["-1"])[0])
            except ValueError:
                since = -1
            known = (query.get("agent") or [""])[0]  # the agent state the page shows now
            deadline = time.time() + POLL_HOLD
            state = self.state()
            # hold the request until an answer or comment changes, or the agent starts or stops reading along
            while state["rev"] == since and state["agent"]["state"] == known and time.time() < deadline:
                time.sleep(0.4)
                state = self.state()
            return self.json(200, state)
        # images next to questions.json, and nothing else
        base = self.ctx["questions"].parent.resolve()
        target = (base / unquote(url.path).lstrip("/")).resolve()
        if base in target.parents and target.is_file() and target.suffix.lower() in IMAGE_TYPES:
            return self.send(200, target.read_bytes(), IMAGE_TYPES[target.suffix.lower()])
        self.json(404, {"error": "not found"})

    def do_PUT(self):
        if not self.allowed() or not self.authed():
            return
        path = urlsplit(self.path).path
        if not path.startswith("/api/answers/"):
            return self.json(404, {"error": "not found"})
        qid = unquote(path[len("/api/answers/"):])
        doc = self.body()
        if doc is None:
            return
        data, _ = self.questions()
        q = next((q for q in all_questions(data or {}) if q.get("id") == qid), None)
        if q is None:
            return self.json(404, {"error": f"no question {qid}"})
        choice = doc.get("choice")
        if choice is not None and choice not in {o.get("id") for o in q.get("options") or []} | {"other"}:
            return self.json(400, {"error": f"unknown choice {choice!r}"})
        answer = {"choice": choice, "other": str(doc.get("other") or "")[:MAX_TEXT],
                  "note": str(doc.get("note") or "")[:MAX_TEXT], "at": now()}

        def change(store):
            store["answers"][qid] = answer
            store["title"] = (data or {}).get("title", store.get("title", ""))
        update_store(self.ctx["files"]["answers"], change)
        self.json(200, answer)

    def do_POST(self):
        if not self.allowed() or not self.authed():
            return
        path = urlsplit(self.path).path
        doc = self.body()
        if doc is None:
            return
        if path == "/api/done":
            done = {"at": now(), "note": str(doc.get("note") or "")[:MAX_TEXT]}

            def mark_done(store):
                store["done"] = done
            update_store(self.ctx["files"]["answers"], mark_done)
            return self.json(200, done)
        if path != "/api/comments":
            return self.json(404, {"error": "not found"})
        data, _ = self.questions()
        text = str(doc.get("text") or "").strip()
        asker = self.ctx.get("asker")
        if not text:
            return self.json(400, {"error": "a comment needs some text"})
        if doc.get("ask") and not asker:
            return self.json(400, {"error": "this server was started without --ask"})

        def change(store):
            if doc.get("parent"):
                root = thread_root(store["comments"], str(doc["parent"]))
                if root is None:
                    return None
                fields = {"target": root.get("target"), "parent": root["id"]}
            else:
                if doc.get("target") not in comment_targets(data or {}):
                    return None
                fields = {"target": doc["target"]}
                if doc.get("quote"):
                    fields["quote"] = str(doc["quote"]).strip()[:2000]
            if doc.get("ask"):
                fields["ask"] = "pending"
            return new_comment(store, by="user", text=text[:MAX_TEXT], **fields)
        comment = update_store(self.ctx["files"]["answers"], change)
        if comment is None:
            return self.json(400, {"error": "a comment needs a known place on the page or an existing thread"})
        if doc.get("ask"):
            asker.start(comment["id"])
        self.json(200, comment)


def ping(port: int) -> dict | None:
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("GET", "/api/ping", headers={"Host": f"127.0.0.1:{port}"})
        r = conn.getresponse()
        body = json.loads(r.read().decode("utf-8")) if r.status == 200 else None
        conn.close()
        return body if body and body.get("app") == APP else None
    except (OSError, ValueError):
        return None


def running(files: dict) -> dict | None:
    """The recorded server, if it is still the one answering on its port."""
    if not files["server"].is_file():
        return None
    try:
        info = read_json(files["server"])
    except (OSError, ValueError):
        return None
    live = ping(int(info.get("port", 0)))
    return info if live and live.get("pid") == info.get("pid") else None


def serve_foreground(questions: Path, files: dict, port: int, ask) -> int:
    if files["answers"].is_file():
        try:
            load_store(files["answers"])
        except ValueError as e:
            sys.exit(f"error: {files['answers']} is not valid JSON ({e}); fix it or move it away first, so no "
                     "answer is lost")
    asker = Asker(ask[0], ask[1], files, questions) if ask else None
    Handler.ctx = {"questions": questions, "files": files, "token": secrets.token_urlsafe(24), "asker": asker}
    try:
        httpd = BriefServer(("127.0.0.1", port), Handler)
    except OSError:
        httpd = BriefServer(("127.0.0.1", 0), Handler)  # the port is taken: let the system pick a free one
    actual = httpd.server_address[1]
    url = f"http://127.0.0.1:{actual}/"
    info = {"url": url, "port": actual, "pid": os.getpid(), "questions": str(questions),
            "answers": str(files["answers"]), "ask": asker.name if asker else None, "started": now()}
    write_json(files["server"], info)
    print(f"serving {url}  (answers: {files['answers']}" + (f"; Ask now: {asker.name}" if asker else "") + ")",
          flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        try:
            if read_json(files["server"]).get("pid") == os.getpid():
                files["server"].unlink()
        except (OSError, ValueError):
            pass
    return 0


def cmd_serve(a) -> int:
    questions = Path(a.questions).resolve()
    data, warnings = load_checked(questions)
    files = task_files(questions)
    ask = ask_spec(a.ask, a.ask_name)
    for w in warnings:
        print(f"warning: {w}")
    if a.foreground:
        return serve_foreground(questions, files, a.port, ask)
    info = running(files)
    if info:
        print(f"already running: {info['url']}  (pid {info['pid']}"
              + (f"; Ask now: {info['ask']}" if info.get("ask") else "") + "; reloading shows the current questions.json)")
        if (info.get("ask") or None) != (ask[0] if ask else None):
            print("note: it runs with a different --ask setting; stop it and serve again to change that")
        if a.open:
            import webbrowser
            webbrowser.open(info["url"])
        return 0
    if files["server"].is_file():
        files["server"].unlink()
    cmd = [sys.executable, str(Path(__file__).resolve()), "serve", str(questions), "--foreground", "--port", str(a.port)]
    if a.ask:
        cmd += ["--ask", a.ask] + (["--ask-name", a.ask_name] if a.ask_name else [])
    log = open(files["log"], "ab")
    kw = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log, "cwd": str(files["base"]), "close_fds": True}
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        try:  # leave the agent's job object, if it allows that, so the server outlives the command
            child = subprocess.Popen(cmd, creationflags=flags | 0x01000000, **kw)  # CREATE_BREAKAWAY_FROM_JOB
        except OSError:
            child = subprocess.Popen(cmd, creationflags=flags, **kw)
    else:
        child = subprocess.Popen(cmd, start_new_session=True, **kw)
    log.close()
    for _ in range(100):
        time.sleep(0.1)
        if child.poll() is not None:
            break
        info = running(files)
        if info:
            print(f"serving {info['url']}  (pid {info['pid']}; answers: {files['answers']}"
                  + (f"; Ask now: {info['ask']}" if info.get("ask") else "") + ")")
            print(f"{describe(data)}. Reloading the page shows edits to questions.json. Stop it with: "
                  f"brief.py stop {questions}")
            if a.open:
                import webbrowser
                webbrowser.open(info["url"])
            return 0
    tail = files["log"].read_text(encoding="utf-8", errors="replace")[-2000:] if files["log"].is_file() else ""
    print("error: the local server did not start. If this runs in a sandbox that forbids opening a port, build a "
          "static page instead (brief.py build --mode static).", file=sys.stderr)
    if tail:
        print(tail, file=sys.stderr)
    return 1


def cmd_stop(a) -> int:
    questions = Path(a.questions).resolve()
    files = task_files(questions)
    info = running(files)
    if not info:
        if files["server"].is_file():
            files["server"].unlink()
        print("no local server is running for this task")
        return 0
    try:
        os.kill(int(info["pid"]), signal.SIGTERM)  # on Windows this ends the process
    except OSError as e:
        print(f"error: could not stop pid {info['pid']}: {e}", file=sys.stderr)
        return 1
    for _ in range(30):
        if not ping(int(info["port"])):
            break
        time.sleep(0.1)
    if files["server"].is_file():
        files["server"].unlink()
    print(f"stopped the server at {info['url']} (pid {info['pid']})")
    return 0


def cmd_new(a) -> int:
    """Set up a task folder in one step: .decision-brief/<slug>/ with shots/, the images copied in, and the
    .gitignore that keeps .decision-brief/ out of commits."""
    if not ID_RE.match(a.slug):
        sys.exit("error: the task name must be lowercase letters, digits and dashes, such as lane-b-estimator")
    root = Path(a.root).resolve()
    base = root / ".decision-brief"
    task = base / a.slug
    (task / "shots").mkdir(parents=True, exist_ok=True)
    if not (base / ".gitignore").exists():
        (base / ".gitignore").write_text("*\n", encoding="utf-8")
    copied = []
    for img in a.images or []:
        src = (root / img) if not Path(img).is_absolute() else Path(img)
        if not src.is_file():
            print(f"warning: {img} not found; not copied", file=sys.stderr)
            continue
        if src.suffix.lower() not in IMAGE_TYPES:
            print(f"warning: {img} is not an image type the page can show; not copied", file=sys.stderr)
            continue
        shutil.copy2(src, task / "shots" / src.name)
        copied.append(f"shots/{src.name}")
    print(f"task folder: {task}")
    print(f"write: {task / 'questions.json'} and {task / 'context.md'}")
    if copied:
        print("images, as figure src values: " + ", ".join(copied))
    return 0


def cmd_example(a) -> int:
    dest = Path(a.dir).resolve()
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"error: {dest} is not empty; pick a new folder")
    shutil.copytree(HERE.parent / "assets" / "example", dest, dirs_exist_ok=True)
    print(f"copied the example to {dest}. Try: brief.py serve {dest / 'questions.json'} --open")
    return 0


def main() -> int:
    if not sys.stdout.isatty():
        try:  # agents read the output through a pipe; keep non-English titles intact
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description="Build, serve and read a decision-brief page.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="check questions.json and write the page")
    b.add_argument("questions")
    b.add_argument("--mode", choices=("artifact", "static"), default="static",
                   help="artifact: the page to publish as a claude.ai Artifact; static: a file to open in a browser")
    b.add_argument("--out", help="page path (default: page.html next to questions.json)")
    b.add_argument("--inline-images", action="store_true", help="embed images in the page instead of linking them")
    s = sub.add_parser("serve", help="serve the page on 127.0.0.1, with live answers and comment threads")
    s.add_argument("questions")
    s.add_argument("--ask", help="let the page ask a read-only headless agent: claude, codex, grok, pi, or a command "
                                 "({prompt_file} and {reply_file} are filled in; otherwise the prompt goes to stdin)")
    s.add_argument("--ask-name", help="the name the page shows for that agent")
    s.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port to try first (default {DEFAULT_PORT})")
    s.add_argument("--open", action="store_true", help="open the page in the default browser")
    s.add_argument("--foreground", action="store_true", help="run in this process until stopped")
    w = sub.add_parser("wait", help="block until the user comments or presses I'm done, then print what is new")
    w.add_argument("questions")
    w.add_argument("--timeout", type=int, default=300, help="seconds to wait; 0 waits until something happens")
    w.add_argument("--answers-too", action="store_true", help="also wake on changed answers")
    w.add_argument("--name", help="your name on the page, such as Claude or Codex")
    rp = sub.add_parser("reply", help="post your answer in a comment thread, or start one on a card")
    rp.add_argument("questions")
    rp.add_argument("target", help="a comment id (c7), or q-<id>, p-<id>, g-<term>, page")
    rp.add_argument("text", nargs="?", help="the answer; - or nothing reads it from stdin")
    rp.add_argument("--file", help="read the answer from this file")
    rp.add_argument("--name", help="your name on the page, such as Claude or Codex")
    t = sub.add_parser("stop", help="stop this task's local server")
    t.add_argument("questions")
    r = sub.add_parser("read", help="print every answer and comment thread")
    r.add_argument("questions")
    r.add_argument("--answers", help="answers file (default: answers.json next to questions.json)")
    r.add_argument("--json", action="store_true", help="machine-readable output")
    m = sub.add_parser("mark", help="move the cards you acted on, and finished reports, to the Decided tab")
    m.add_argument("questions")
    m.add_argument("--answers", help="answers file (default: answers.json next to questions.json)")
    m.add_argument("--ids", nargs="+", help="question ids, separated by commas or spaces (default: every open card "
                                             "with a choice, unless only --reports is given)")
    m.add_argument("--reports", nargs="+", help="progress report ids to archive on the Decided tab")
    m.add_argument("--round", help="the heading they go under on the Decided tab, such as \"Round 1, 27 October\"")
    m.add_argument("--reopen", action="store_true", help="move the given cards or reports back")
    k = sub.add_parser("links", help="list every link with where it appears")
    k.add_argument("questions")
    nw = sub.add_parser("new", help="create the task folder, its shots/ (with images copied in) and the .gitignore")
    nw.add_argument("slug", help="the task's folder name, such as lane-b-estimator")
    nw.add_argument("--images", nargs="*", help="screenshots or mockups to copy into shots/")
    nw.add_argument("--root", default=".", help="the project root (default: the current folder)")
    e = sub.add_parser("example", help="copy the worked example into a new folder to try the page")
    e.add_argument("dir")
    a = ap.parse_args()
    if a.cmd == "mark" and a.reopen and not (a.ids or a.reports):
        ap.error("--reopen needs --ids or --reports")
    return {"build": cmd_build, "serve": cmd_serve, "wait": cmd_wait, "reply": cmd_reply, "stop": cmd_stop,
            "read": cmd_read, "mark": cmd_mark, "links": cmd_links, "example": cmd_example, "new": cmd_new}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
