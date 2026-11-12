#!/usr/bin/env python3
"""Mechanical upkeep of a code wiki: lint, affected pages, viewer, tool copy.

Shipped by the code-map plugin's `wiki` skill and copied into the repository it documents, so anyone (a person, CI,
any coding agent) can run it without the plugin. Standard library only, Python 3.9 or later. The wiki's rules live in
<wiki>/SCHEMA.md; this script checks the parts of them a machine can check.

  python wiki.py lint       [--repo R] [--wiki W] [--run [--in-place] [--timeout S] [--capture DIR]] [--list-run] [--json]
  python wiki.py affected   [--repo R] [--wiki W] [--since REF] [--json]
  python wiki.py questions  [--repo R] [--wiki W] [--since YYYY-MM-DD] [--json]
  python wiki.py viewer     [--repo R] [--wiki W] [--out FILE] [--editor NAME|TEMPLATE|none] [--title T]
  python wiki.py callgraph  PATH#FUNCTION [--depth N] [--max-nodes N] [--id ID] [--table]
  python wiki.py fill       --capture DIR [--repo R] [--wiki W] [--max-lines N]
  python wiki.py copy-tools DEST [--force] [--check]
  python wiki.py version

Defaults: --repo is the git top level of the current directory; --wiki is docs/wiki, or the folder holding a
SCHEMA.md whose front matter says `kind: schema`. Exit codes: 0 no problems (warnings allowed), 1 problems, 2 usage.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import date
from pathlib import Path

TOOLS_VERSION = "0.3.0"
HERE = Path(__file__).resolve().parent
TOOL_FILES = ["wiki.py", "wiki_browser.py", "viewer_template.html", "vendor/marked.min.js", "vendor/marked-LICENSE.txt",
              "vendor/katex.min.js", "vendor/katex.min.css", "vendor/katex-LICENSE.txt"]
SPECIAL_PAGES = {"index.md": "index", "log.md": "log", "SCHEMA.md": "schema"}
PAGE_KINDS = {"tutorial", "how-to", "reference", "explanation"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "diagrams", "vendor"}


# ---------------------------------------------------------------- small helpers

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def git(repo: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r.stdout if r.returncode == 0 else ""


def is_git(repo: Path) -> bool:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--git-dir"], capture_output=True).returncode == 0


def posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    """Hash of a file's content with CRLF read as LF, so a checkout that converts line endings (core.autocrlf)
    does not make an untouched copy look edited."""
    return sha256(path.read_bytes().replace(b"\r\n", b"\n"))


# ---------------------------------------------------------------- markdown scanning

FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def fences(lines: list[str]) -> list[tuple[int, int, str]]:
    """Fenced code blocks as (opening line, closing line, info string), 0-based. An unclosed fence runs to the end."""
    out, i = [], 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m or (m.group(2)[0] == "`" and "`" in m.group(3)):
            i += 1
            continue
        mark, j = m.group(2), i + 1
        while j < len(lines):
            c = re.match(r"^\s*(`{3,}|~{3,})\s*$", lines[j])
            if c and c.group(1)[0] == mark[0] and len(c.group(1)) >= len(mark):
                break
            j += 1
        out.append((i, j, m.group(3).strip()))
        i = j + 1
    return out


def prose_lines(text: str) -> list[str]:
    """The page's lines with code blocks, inline code and HTML comments blanked, so links inside examples are not
    checked. Line numbers stay the same."""
    lines = text.split("\n")
    for start, end, _ in fences(lines):
        for k in range(start, min(end, len(lines) - 1) + 1):
            lines[k] = ""
    joined = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), "\n".join(lines), flags=re.S)
    return [re.sub(r"(`+)(?!`).+?(?<!`)\1(?!`)", " ", line) for line in joined.split("\n")]


def front_matter(text: str) -> tuple[dict, str, int]:
    """(metadata, body, number of front-matter lines). Supports `key: value`, `key: [a, b]` and block lists."""
    m = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", text, re.S)
    if not m:
        return {}, text, 0
    meta: dict = {}
    key = None
    for line in m.group(1).split("\n"):
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and key and isinstance(meta.get(key), list):
            meta[key].append(item.group(1).strip().strip("'\""))
            continue
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        key, v = k.strip(), re.sub(r"\s+#.*$", "", v).strip()
        if v.startswith("[") and v.endswith("]"):
            meta[key] = [s.strip().strip("'\"") for s in v[1:-1].split(",") if s.strip()]
        elif v == "":
            meta[key] = []
        else:
            meta[key] = v.strip("'\"")
    return meta, text[m.end():], m.group(0).count("\n")


def slugify(heading: str) -> str:
    """GitHub's heading anchor: lower case, punctuation removed, spaces to hyphens."""
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)  # links keep their text
    s = re.sub(r"<[^>]+>", "", s).replace("`", "").strip().lower()
    return re.sub(r"[^\w\- ]", "", s).replace(" ", "-")


def anchors(text: str) -> set[str]:
    """Every anchor a link can target in this Markdown text: heading slugs (with GitHub's -1, -2 suffixes for
    repeats) and explicit id/name attributes."""
    found: set[str] = set()
    counts: dict[str, int] = {}
    lines = text.split("\n")
    in_code = set()
    for start, end, _ in fences(lines):
        in_code.update(range(start, end + 1))
    for i, line in enumerate(lines):
        if i in in_code:
            continue
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            base = slugify(m.group(1))
            n = counts.get(base, 0)
            found.add(base if n == 0 else f"{base}-{n}")
            counts[base] = n + 1
        for a in re.findall(r"""\b(?:id|name)\s*=\s*["']([^"']+)["']""", line):
            found.add(a.lower())
    return found


LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
HTML_LINK = re.compile(r"""<(?:a|img|source)\b[^>]*?\b(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
REF_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)")


def links(text: str) -> list[tuple[int, str]]:
    """(1-based line, target) for every Markdown, reference-style and HTML link or image outside code."""
    out = []
    for i, line in enumerate(prose_lines(text), 1):
        for rx in (LINK, HTML_LINK):
            out.extend((i, t) for t in rx.findall(line))
        m = REF_DEF.match(line)
        if m:
            out.append((i, m.group(1)))
    return out


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]+:", target)) or target.startswith("//")


# ---------------------------------------------------------------- pages

class Page:
    def __init__(self, path: Path, repo: Path, wiki: Path):
        self.path, self.repo, self.wiki = path, repo, wiki
        self.text = read(path)
        self.meta, self.body, self.fm_lines = front_matter(self.text)
        self.rel = posix(path, repo)                       # repository-relative id
        self.is_readme = path.resolve() == (repo / "README.md").resolve()
        wiki_rel = None if self.is_readme else posix(path, wiki)
        self.wiki_rel = wiki_rel
        self.kind = "readme" if self.is_readme else (SPECIAL_PAGES.get(wiki_rel or "") or str(self.meta.get("kind", "")))
        self.title = str(self.meta.get("title") or ("README" if self.is_readme else Path(self.rel).stem))
        src = self.meta.get("sources", [])
        self.sources = [src] if isinstance(src, str) else list(src)

    @property
    def label(self) -> str:
        return "README.md" if self.is_readme else (self.wiki_rel or self.rel)

    @property
    def is_content(self) -> bool:
        return not self.is_readme and self.kind not in ("index", "log", "schema")


def log_mentions(repo: Path, wiki: Path) -> tuple[dict[str, tuple[str, int]], set[str]]:
    """Pages named in log entries: ({wiki-relative page path: (newest commit whose log addition names it, its time)},
    {pages named in uncommitted log additions}). A page the agent checked and found still true has nothing to edit;
    naming it in the change's log entry records the check, so the page stops being reported as out of date."""
    rel = posix(wiki / "log.md", repo)
    named: dict[str, tuple[str, int]] = {}
    commit = None
    for line in git(repo, "log", "--format=@@commit %h %ct", "-p", "--unified=0", "--", rel, check=False).splitlines():
        if line.startswith("@@commit "):
            _, sha, ct = line.split()
            commit = (sha, int(ct))
        elif commit and line.startswith("+") and not line.startswith("+++"):
            for m in re.findall(r"[\w./-]+\.md\b", line):
                named.setdefault(m, commit)  # git log lists the newest commit first
    pending = set()
    for line in git(repo, "diff", "HEAD", "--unified=0", "--", rel, check=False).splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            pending.update(re.findall(r"[\w./-]+\.md\b", line))
    return named, pending


def baseline(repo: Path, page: Page, mentions=None) -> tuple[str | None, bool]:
    """(the commit this page was last checked against the code in, whether it is being updated in this change).
    That is the newer of the page's own last commit and the last commit whose log entry names the page: a page is
    updated, or confirmed unchanged and named in the log, in the same change as the code it describes."""
    rel = page.rel
    out = git(repo, "log", "-1", "--format=%h %ct", "--", rel, check=False).split()
    last = (out[0], int(out[1])) if len(out) == 2 else None
    edited = bool(git(repo, "status", "--porcelain", "--", rel, check=False).strip())
    if mentions is not None and page.wiki_rel:
        named, pending = mentions
        hit = named.get(page.wiki_rel)
        if hit and (not last or hit[1] > last[1]):
            last = hit
        edited = edited or page.wiki_rel in pending
    return (last[0] if last else None), edited


def default_repo() -> Path:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def default_wiki(repo: Path) -> Path:
    if os.environ.get("WIKI_DIR"):
        return (repo / os.environ["WIKI_DIR"]).resolve()
    if (repo / "docs" / "wiki" / "SCHEMA.md").exists():
        return repo / "docs" / "wiki"
    for schema in sorted(repo.rglob("SCHEMA.md")):
        if any(part in SKIP_DIRS for part in schema.relative_to(repo).parts):
            continue
        if front_matter(read(schema))[0].get("kind") == "schema":
            return schema.parent
    return repo / "docs" / "wiki"


def collect_pages(repo: Path, wiki: Path) -> list[Page]:
    """The repository's root README (the wiki's front page) first, then every Markdown file under the wiki folder,
    except tool folders (the one this script sits in, vendor/, diagrams/)."""
    pages = []
    if (repo / "README.md").exists():
        pages.append(Page(repo / "README.md", repo, wiki))
    if wiki.exists():
        for md in sorted(wiki.rglob("*.md")):
            parts = md.relative_to(wiki).parts[:-1]
            if any(p in SKIP_DIRS or p.startswith(".") for p in parts) or (md.parent / "wiki.py").exists():
                continue
            pages.append(Page(md, repo, wiki))
    return pages


# ---------------------------------------------------------------- symbols

N = r"[A-Za-z_$][\w$]*"
BRACES = "braces"
LANGS: dict[str, tuple[tuple[str, ...], str, list[str]]] = {
    # name: (extensions, how a body ends, definition patterns with {n} for the name)
    "js": ((".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte"), BRACES, [
        r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*({n})\b",
        r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+({n})\b",
        r"^\s*(?:export\s+)?(?:declare\s+)?(?:interface|type|enum|namespace|module)\s+({n})\b",
        r"^\s*(?:export\s+)?(?:declare\s+)?(?:const|let|var)\s+({n})\b",
        r"^\s*(?:(?:public|private|protected|static|readonly|async|override|abstract|get|set)\s+)*\*?({n})\s*(?:<[^>]*>)?\s*\([^;]*$",
        r"^\s*({n})\s*:\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|{n}\s*=>)",
        r"^\s*[\"']?({n})[\"']?\s*:",
    ]),
    "go": ((".go",), BRACES, [
        r"^func\s+(?:\([^)]*\)\s*)?({n})\s*[\[(]",
        r"^\s*type\s+({n})\b",
        r"^\s*(?:var|const)\s+({n})\b",
    ]),
    "rust": ((".rs",), BRACES, [
        r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:(?:async|const|unsafe|extern\s+\"[^\"]*\")\s+)*fn\s+({n})\b",
        r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait|union|type|mod|const|static)\s+({n})\b",
        r"^\s*macro_rules!\s*({n})\b",
        r"^\s*impl(?:<[^>]*>)?\s+(?:[\w:<>]+\s+for\s+)?({n})\b",
    ]),
    "jvm": ((".java", ".kt", ".kts", ".scala", ".cs", ".swift", ".dart", ".groovy"), BRACES, [
        r"\b(?:class|interface|enum|record|struct|object|trait|protocol|extension)\s+({n})\b",
        r"\b(?:fun|func|def)\s+(?:<[^>]*>\s*)?(?:[\w.]+\.)?({n})\b",
        r"^\s*(?!(?:return|new|throw|else|case|await|yield|if|for|while|switch|catch)\b)(?:[\w<>\[\],.?@]+\s+)+({n})\s*\([^;]*$",
    ]),
    "c": ((".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx", ".cu", ".cuh", ".mm", ".ino"), BRACES, [
        r"^(?!\s*(?:return|else|if|for|while|switch|case|do)\b)[\w\*\s&:<>,~\[\]]*?\b(?:\w+::)*({n})\s*\([^;]*$",
        r"\b(?:struct|class|enum|union|namespace)\s+({n})\b",
        r"^\s*#\s*define\s+({n})\b",
        r"\btypedef\b.*?\b({n})\s*;",
    ]),
    "php": ((".php",), BRACES, [r"function\s+&?\s*({n})\s*\(", r"\b(?:class|interface|trait|enum)\s+({n})\b"]),
    "ruby": ((".rb", ".rake"), "indent", [r"^\s*def\s+(?:self\.)?({n}[?!=]?)", r"^\s*(?:class|module)\s+(?:[\w:]+::)?({n})\b"]),
    "shell": ((".sh", ".bash", ".zsh", ".ksh"), BRACES, [r"^\s*(?:function\s+)?({n})\s*\(\)", r"^\s*function\s+({n})\b"]),
    "lua": ((".lua",), "indent", [r"function\s+(?:[\w.]+[.:])?({n})\s*\(", r"\blocal\s+function\s+({n})\b", r"\b({n})\s*=\s*function\b"]),
    "r": ((".r",), BRACES, [r"^\s*({n})\s*(?:<-|=)\s*function\b"]),
    "julia": ((".jl",), "indent", [r"^\s*(?:function|macro)\s+(?:[\w.]+\.)?({n})\b", r"^\s*({n})\s*\([^)]*\)\s*=[^=]",
                                    r"^\s*(?:mutable\s+)?(?:struct|abstract\s+type|module)\s+({n})\b"]),
    "matlab": ((".m",), "indent", [r"^\s*function\s+(?:\[?[\w,\s]*\]?\s*=\s*)?({n})\b", r"^\s*classdef\s+(?:\([^)]*\)\s*)?({n})\b",
                                   r"^\s*[-+]\s*\([^)]*\)\s*({n})\b", r"@(?:interface|implementation)\s+({n})\b"]),
    "elixir": ((".ex", ".exs"), "indent", [r"^\s*def(?:p|macro|macrop)?\s+({n}[?!]?)", r"^\s*defmodule\s+(?:[\w.]+\.)?({n})\b"]),
    "haskell": ((".hs",), "indent", [r"^({n})\s*::", r"^(?:data|newtype|type|class)\s+({n})\b"]),
    "sql": ((".sql",), "indent", [r"(?i)\bcreate\s+(?:or\s+replace\s+)?(?:table|view|function|procedure|index|trigger|type)\s+(?:if\s+not\s+exists\s+)?(?:[\w\"]+\.)?\"?({n})\b"]),
    "json": ((".json", ".jsonc"), "indent", [r"\"({n})\"\s*:"]),
    "yaml": ((".yml", ".yaml"), "indent", [r"^\s*[\"']?({n})[\"']?\s*:"]),
    "toml": ((".toml", ".ini", ".cfg", ".conf"), "indent", [r"^\s*\[+\s*(?:[\w.-]+\.)?({n})\s*\]+", r"^\s*({n})\s*="]),
    "make": ((".mk", ".just"), "indent", [r"^({n})\s*:(?!=)"]),
}
BY_EXT = {ext: name for name, (exts, _, _) in LANGS.items() for ext in exts}
BY_NAME = {"makefile": "make", "gnumakefile": "make", "justfile": "make"}
GENERIC = ("generic", "indent", [
    r"\b(?:def|function|func|fn|fun|sub|proc|procedure|class|struct|interface|enum|type|module|let|const|var)\s+({n})\b",
    r"^\s*({n})\s*[:=(]",
])


def language(path: Path) -> tuple[str, str, list[str]]:
    name = BY_NAME.get(path.name.lower()) or BY_EXT.get(path.suffix.lower())
    if name:
        return (name, LANGS[name][1], LANGS[name][2])
    return GENERIC


class Symbols:
    """Finds where a `path#symbol` source is defined. Python is parsed with `ast`; other languages use definition
    patterns, so their answer is a good guess, not proof; Markdown sources name a heading."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.cache: dict[Path, tuple[str, list]] = {}

    def defs(self, path: Path) -> tuple[str, list[tuple[str, int, int]]]:
        """('ast' | 'pattern', [(qualified name, first line, last line)])."""
        if path in self.cache:
            return self.cache[path]
        text = read(path)
        result = None
        if path.suffix.lower() in (".py", ".pyi"):
            try:
                result = ("ast", py_defs(text))
            except (SyntaxError, ValueError):
                result = None
        if result is None and path.suffix.lower() in (".md", ".markdown"):
            result = ("heading", md_defs(text))
        if result is None:
            result = ("pattern", pattern_defs(path, text))
        self.cache[path] = result
        return result

    def find(self, ref: str) -> dict:
        """{'ref', 'path', 'symbol', 'ok', 'line', 'end', 'how', 'note'} for one `path` or `path#symbol` source."""
        path_part, _, symbol = ref.partition("#")
        out = {"ref": ref, "path": path_part, "symbol": symbol, "ok": False, "line": None, "end": None, "how": "", "note": ""}
        target = (self.repo / urllib.parse.unquote(path_part)).resolve()
        try:
            target.relative_to(self.repo.resolve())
        except ValueError:
            out["note"] = "source path leaves the repository"
            return out
        if not target.exists():
            out["note"] = "source file missing"
            return out
        if not symbol:
            out.update(ok=True, line=1, how="file")
            return out
        if re.fullmatch(r"L\d+(-L?\d+)?", symbol):
            out["note"] = "line numbers drift: name the symbol instead"
            return out
        how, defs = self.defs(target)
        want = symbol.replace("::", ".")
        exact = [d for d in defs if d[0] == want or (how == "heading" and d[0] == slugify(symbol))]
        tail = [d for d in defs if d[0].split(".")[-1] == want.split(".")[-1]]
        if exact:
            d = exact[0]
        elif "." in want and how != "ast":
            d = qualified_guess(defs, want)
        elif "." not in want and len(tail) == 1:
            d = tail[0]
            out["note"] = f"found as {d[0]}; write the qualified name"
        else:
            d = None
        if d:
            out.update(ok=True, line=d[1], end=d[2], how=how, qual=d[0])
        else:
            out["note"] = "symbol not found" + (" (ambiguous: " + ", ".join(x[0] for x in tail[:4]) + ")" if len(tail) > 1 else "")
        return out


def py_defs(text: str) -> list[tuple[str, int, int]]:
    tree = ast.parse(text)
    out: list[tuple[str, int, int]] = []

    def walk(node, prefix: str):
        for n in ast.iter_child_nodes(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.append((prefix + n.name, n.lineno, getattr(n, "end_lineno", n.lineno)))
                walk(n, prefix + n.name + ".")
            elif isinstance(n, (ast.Assign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    for name in ast.walk(t):
                        if isinstance(name, ast.Name):
                            out.append((prefix + name.id, n.lineno, getattr(n, "end_lineno", n.lineno)))
            elif isinstance(n, ast.If) and prefix == "" and "__name__" in ast.dump(n.test) and "__main__" in ast.dump(n.test):
                out.append(("__main__", n.lineno, getattr(n, "end_lineno", n.lineno)))  # the `if __name__ == "__main__":` block
                walk(n, prefix)
            elif isinstance(n, (ast.If, ast.Try, ast.With)) or type(n).__name__ == "TryStar":
                walk(n, prefix)  # definitions under `if TYPE_CHECKING:`, `try: import ...`

    walk(tree, "")
    return out


def md_defs(text: str) -> list[tuple[str, int, int]]:
    """Headings as symbols: Markdown `#` headings and HTML `<h1>`…`<h6>` (by slug, and by id when they carry one)."""
    lines = text.split("\n")
    heads = []
    for i, line in enumerate(lines):
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            heads.append((i + 1, slugify(m.group(1))))
            continue
        for h in re.finditer(r"<h[1-6]\b([^>]*)>(.*?)</h[1-6]>", line, re.I):
            heads.append((i + 1, slugify(re.sub(r"<[^>]+>", "", h.group(2)))))
            hid = re.search(r"""\bid\s*=\s*["']([^"']+)["']""", h.group(1))
            if hid:
                heads.append((i + 1, hid.group(1).lower()))
    return [(s, ln, (heads[k + 1][0] - 1 if k + 1 < len(heads) else len(lines))) for k, (ln, s) in enumerate(heads)]


def pattern_defs(path: Path, text: str) -> list[tuple[str, int, int]]:
    lang, body, patterns = language(path)
    lines = text.split("\n")
    rx = [re.compile(p.replace("{n}", N)) for p in patterns]
    found: list[tuple[str, int, int]] = []
    containers: list[tuple[str, int, int]] = []
    for i, line in enumerate(lines):
        for k, r in enumerate(rx):
            m = r.search(line)
            if m:
                found.append((m.group(1), i + 1, k))
                break
    spans = []
    for name, ln, k in found:
        end = brace_end(lines, ln - 1) if body == BRACES else indent_end(lines, ln - 1, [f[1] for f in found])
        spans.append((name, ln, end))
        if re.search(r"\b(class|struct|impl|interface|trait|object|namespace|module|enum|protocol|extension|record|defmodule|classdef|type)\b",
                     lines[ln - 1]):
            containers.append((name, ln, end))
    if lang == "go":  # methods: func (r *Type) Name( -> also known as Type.Name
        for i, line in enumerate(lines):
            m = re.match(rf"^func\s+\(\s*\w*\s*\*?({N})(?:\[[^\]]*\])?\s*\)\s*({N})\s*[\[(]", line)
            if m:
                spans.append((f"{m.group(1)}.{m.group(2)}", i + 1, brace_end(lines, i)))
    for cname, cl, ce in containers:  # Container.member for members defined inside a container's span
        for name, ln, end in list(spans):
            if cl < ln <= ce and "." not in name:
                spans.append((f"{cname}.{name}", ln, end))
    return spans


def qualified_guess(defs, want: str):
    for d in defs:
        if d[0] == want:
            return d
    parts = want.split(".")
    for d in defs:
        if d[0] == parts[-1] and any(q[0] == parts[0] and q[1] < d[1] for q in defs):
            return d
    return None


def brace_end(lines: list[str], start: int) -> int:
    """1-based last line of the body opened at or after `start` by '{'; the statement's own line when none opens."""
    depth, opened = 0, False
    for i in range(start, len(lines)):
        line = re.sub(r"(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`[^`]*`|//.*$)", "", lines[i])  # strings, line comments
        for ch in line:
            if ch == "{":
                depth, opened = depth + 1, True
            elif ch == "}":
                depth -= 1
                if opened and depth <= 0:
                    return i + 1
        if not opened and (line.rstrip().endswith(";") or i - start > 3):
            return i + 1
    return len(lines)


def indent_end(lines: list[str], start: int, def_lines: list[int]) -> int:
    width = len(lines[start]) - len(lines[start].lstrip())
    for ln in sorted(def_lines):
        if ln - 1 > start:
            other = lines[ln - 1]
            if len(other) - len(other.lstrip()) <= width:
                return ln - 1
    return len(lines)


# ---------------------------------------------------------------- diagrams

def mermaid_blocks(page: Page) -> list[dict]:
    lines = page.text.split("\n")
    out = []
    for start, end, info in fences(lines):
        if info.split()[:1] != ["mermaid"]:
            continue
        body = "\n".join(lines[start + 1:end])
        m = re.match(r"\s*%%\s*id:\s*([a-z0-9][a-z0-9-]*)\s*$", body.split("\n", 1)[0] if body else "")
        out.append({"id": m.group(1) if m else None, "line": start + 1, "source": body, "hash": diagram_hash(body)})
    return out


def diagram_hash(source: str) -> str:
    norm = "\n".join(line.rstrip() for line in source.strip().split("\n"))
    return sha256(norm.encode("utf-8"))


SVG_STAMP = re.compile(r"<!--\s*code-map-wiki diagram=\"([^\"]+)\" source-sha256=\"([0-9a-f]{64})\"\s*-->")


# ---------------------------------------------------------------- command blocks

MARK = re.compile(r"^\s*<!--\s*check:(run|output|skip)\b(.*?)-->\s*$")
SHELLS = {"bash": "bash", "sh": "bash", "shell": "bash", "zsh": "bash", "console": "bash",
          "powershell": "pwsh", "pwsh": "pwsh", "ps1": "pwsh", "ps": "pwsh"}
COMMAND_LANGS = set(SHELLS) | {"cmd", "bat", "batch", "fish"}  # blocks a reader would paste into a terminal


def this_os() -> str:
    return "windows" if os.name == "nt" else ("macos" if sys.platform == "darwin" else "linux")


def mark_attrs(text: str) -> dict:
    """`os=windows background ready="http://x" wait=60 reason="needs a key"` -> dict (flags map to True)."""
    return {k.lower(): (v[1:-1] if v.startswith('"') else v) if v else True
            for k, v in re.findall(r'(\w+)(?:=("[^"]*"|\S+))?', text)}


def run_blocks(page: Page) -> tuple[list[dict], list[tuple[int, str]], dict]:
    """The page's command blocks and how each is marked.

    `<!-- check:run -->` above a bash or powershell block runs it (`os=windows`, `os=posix`, `os=linux,macos` limit it
    to an OS; `background ready=<url or /regex/> wait=<s>` starts it as a server, waits until it answers, and keeps it
    running for the page's later blocks; `exit=<code>` means the block shows a failure on purpose and must end with that
    exit code). `<!-- check:output -->` above the next fenced block holds the output the
    preceding run block must print: its lines must appear in order, `…` matching any text. `<!-- check:skip
    reason="…" -->` marks a block that cannot run here, with the reason. Returns (run blocks, errors, coverage)."""
    lines = page.text.split("\n")
    opens = {start: (end, info) for start, end, info in fences(lines)}
    blocks, errors = [], []
    marked: dict[int, str] = {}
    last_run = None
    for i, line in enumerate(lines):
        m = MARK.match(line)
        if not m:
            continue
        kind, attrs = m.group(1), mark_attrs(m.group(2))
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j not in opens:
            errors.append((i + 1, f"check:{kind} is not followed by a code block"))
            continue
        end, info = opens[j]
        lang = info.split()[0].lower() if info else ""
        body = "\n".join(lines[j + 1:end]).strip("\n")
        marked[j] = kind
        if kind == "run":
            if lang not in SHELLS:
                errors.append((i + 1, "check:run is not followed by a bash or powershell code block"))
                continue
            if "exit" in attrs and not str(attrs["exit"]).isdigit():
                errors.append((i + 1, "check:run exit= needs the exit code the block is expected to end with, such as exit=1"))
                continue
            oses = [o.strip().lower() for o in str(attrs.get("os", "any")).split(",")]
            last_run = {"page": page.label, "line": j + 1, "shell": SHELLS[lang], "os": oses, "body": body,
                        "background": bool(attrs.get("background")), "ready": attrs.get("ready") if attrs.get("ready") is not True else None,
                        "wait": int(attrs["wait"]) if str(attrs.get("wait", "")).isdigit() else None, "expect": None,
                        "exit": int(attrs.get("exit", 0))}
            blocks.append(last_run)
        elif kind == "output":
            if not last_run or last_run["background"]:
                errors.append((i + 1, "check:output has no check:run block above it on this page"))
            elif attrs.get("fill"):
                last_run["fill"] = j + 1  # a placeholder `wiki.py fill` replaces with the captured output
            else:
                last_run["expect"] = body
        elif kind == "skip" and (not isinstance(attrs.get("reason"), str) or not attrs["reason"].strip()):
            errors.append((i + 1, 'check:skip needs reason="…": say what the block needs that a check cannot have'))
    coverage = {"run": 0, "skip": 0, "unmarked": []}
    for start, end, info in fences(lines):
        lang = info.split()[0].lower() if info else ""
        if lang not in COMMAND_LANGS:
            continue
        kind = marked.get(start)
        if kind == "run":
            coverage["run"] += 1
        elif kind == "skip":
            coverage["skip"] += 1
        else:
            coverage["unmarked"].append(start + 1)
    return blocks, errors, coverage


def output_mismatch(expected: str, actual: str) -> str | None:
    """None when every expected line appears in the actual output, in order; `…` (or `...`) inside a line matches any
    text, and runs of spaces compare as one. Otherwise the first expected line that was not found."""
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip())

    act = [norm(line) for line in actual.replace("\r\n", "\n").split("\n")]
    pos = 0
    for raw in expected.replace("\r\n", "\n").split("\n"):
        e = norm(raw)
        if not e or e in ("…", "..."):
            continue
        parts = re.split(r"…|\.\.\.", e)
        pattern = re.escape(parts[0])
        for part in parts[1:]:  # `a … b` also matches `a b`: the ellipsis may stand for nothing
            if pattern.endswith(" ") and part.startswith(" "):
                pattern += r"(?:.* )?" + re.escape(part[1:])
            else:
                pattern += ".*" + re.escape(part)
        rx = re.compile("^" + pattern + "$")
        while pos < len(act) and not rx.match(act[pos]):
            pos += 1
        if pos == len(act):
            return f"expected output line not found (in order): {raw.strip()[:120]}"
        pos += 1
    return None


def os_matches(oses: list[str]) -> bool:
    here = this_os()
    return "any" in oses or here in oses or ("posix" in oses and here != "windows")


def find_bash() -> str | None:
    """WIKI_SHELL, else bash from PATH as an absolute path. On Windows a bare "bash" is never used: process creation
    searches System32 before PATH and would start WSL, a separate Linux system without this checkout's tools."""
    if os.environ.get("WIKI_SHELL"):
        return os.environ["WIKI_SHELL"]
    found = shutil.which("bash")
    if os.name == "nt" and (not found or re.search(r"(?i)\\(system32|windowsapps)\\", found)):
        candidates = []
        git_exe = shutil.which("git")
        if git_exe:
            candidates.append(Path(git_exe).resolve().parent.parent / "bin" / "bash.exe")
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
            if base:
                candidates.append(Path(base) / "Git" / "bin" / "bash.exe")
        found = next((str(c) for c in candidates if c.exists()), None)
    return found


def find_pwsh() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def make_checkout(repo: Path) -> tuple[Path, Path]:
    """A temporary worktree of HEAD plus the working tree's own changes: what a newcomer gets from a fresh clone of
    the change you are about to commit. Ignored files (virtualenvs, caches, build output) are not copied."""
    tmp = Path(tempfile.mkdtemp(prefix="wiki-run-"))
    dest = tmp / repo.name
    git(repo, "worktree", "add", "--detach", "--quiet", str(dest), "HEAD")
    changed = [p for p in git(repo, "diff", "--name-only", "-z", "HEAD").split("\0") if p]
    changed += [p for p in git(repo, "ls-files", "-z", "-o", "--exclude-standard").split("\0") if p]
    for rel in changed:
        src, dst = repo / rel, dest / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif dst.exists() and not src.exists():
            dst.unlink()
    return tmp, dest


def remove_checkout(repo: Path, tmp: Path, dest: Path) -> None:
    git(repo, "worktree", "remove", "--force", str(dest), check=False)

    def unlock(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(tmp, onerror=unlock) if sys.version_info < (3, 12) else shutil.rmtree(tmp, onexc=unlock)
    git(repo, "worktree", "prune", check=False)


KEEP_ENV = {"PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME",
            "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "PROGRAMFILES",
            "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)", "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE", "OS", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "USER", "USERNAME", "LOGNAME", "SHELL",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy", "DOCKER_HOST", "SSL_CERT_FILE"}


def run_env(clean: bool) -> tuple[dict, list[str]]:
    """The environment command blocks run in, and the names of variables a clean run left out. A clean run keeps only
    what the system and the network need, so a step that silently relies on the author's own variables fails."""
    env = dict(os.environ)
    if env.get("UV_INTERNAL__PYTHONHOME") and env.get("PYTHONHOME") == env["UV_INTERNAL__PYTHONHOME"]:
        # uv's launcher set PYTHONHOME for the interpreter running this script; the project's own python must not inherit it
        env.pop("PYTHONHOME")
        env.pop("UV_INTERNAL__PYTHONHOME")
    dropped = []
    if clean:
        dropped = sorted(k for k in env if k.upper() not in {v.upper() for v in KEEP_ENV} and not k.upper().startswith("XDG_"))
        env = {k: v for k, v in env.items() if k not in dropped}
    env["WIKI_CHECK_RUN"] = "1"
    return env, dropped


def stop_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def wait_ready(proc: subprocess.Popen, log: Path, ready, seconds: int) -> str | None:
    """None once the service answers: `ready` is a URL that returns any status below 500, or /regex/ found in its
    output, or, without `ready`, the process is still running after `seconds`. Otherwise why it did not."""
    import time
    import urllib.error
    import urllib.request
    deadline = time.time() + seconds
    while time.time() < deadline:
        if proc.poll() is not None:
            return f"exited with {proc.returncode} before it was ready: {read(log)[-300:].strip()}"
        if isinstance(ready, str) and ready.startswith(("http://", "https://")):
            try:
                with urllib.request.urlopen(ready, timeout=2):
                    return None
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    return None
            except (OSError, ValueError):
                pass
        elif isinstance(ready, str) and len(ready) > 2 and ready.startswith("/") and ready.endswith("/"):
            if re.search(ready[1:-1], read(log)):
                return None
        time.sleep(0.5)
    return None if not ready else f"not ready after {seconds} s ({ready}): {read(log)[-300:].strip()}"


def execute(blocks: list[dict], cwd: Path, timeout: int, capture: Path | None = None, clean_env: bool = False) -> tuple[list[dict], list[str]]:
    """Run each block as one script, in order. With `capture`, each block's output is saved there (one file per block,
    named after its page and line), so pages can show real, dated output instead of illustrative examples. Background
    blocks keep running until the last block of their page has run. Returns (results, names of variables left out)."""
    results = []
    if capture:
        capture.mkdir(parents=True, exist_ok=True)
    bash, pwsh = find_bash(), find_pwsh()
    env, dropped = run_env(clean_env)
    services: list[subprocess.Popen] = []
    handles = []
    logs = Path(tempfile.mkdtemp(prefix="wiki-logs-"))

    def save(b, code, out, err):
        if capture:
            name = re.sub(r"[^\w.-]+", "_", f"{b['page']}-{b['line']}") + ".txt"
            (capture / name).write_text(f"# {date.today().isoformat()} {b['page']}:{b['line']} ({b['shell']}), exit {code}\n"
                                        f"# {cwd.name} is a clean checkout of the change\n$ {b['body']}\n\n--- stdout\n{out}"
                                        f"\n--- stderr\n{err}", encoding="utf-8")
            return str(capture / name)
        return None

    for k, b in enumerate(blocks):
        res = dict(b, status="ok", detail="")
        if not os_matches(b["os"]):
            res.update(status="skipped", detail=f"os={','.join(b['os'])}, this is {this_os()}")
        elif b["shell"] == "bash" and not bash:
            res.update(status="failed", detail="no bash found (set WIKI_SHELL to its path)")
        elif b["shell"] == "pwsh" and not pwsh:
            res.update(status="failed", detail="no pwsh or powershell found")
        else:
            want = b.get("exit", 0)
            if b["shell"] == "bash":
                cmd = [bash, "-e", "-o", "pipefail", "-c", b["body"]]
            else:
                # Stop at the first failing program, as bash -e does (PowerShell 7.3+; older shells ignore the variable).
                # A block that fails on purpose keeps going and ends with the program's own exit code instead.
                cmd = [pwsh, "-NoProfile", "-NonInteractive", "-Command",
                       "$ErrorActionPreference = 'Stop'\n"
                       f"$PSNativeCommandUseErrorActionPreference = {'$false' if want else '$true'}\n"
                       "if ($PSStyle) { $PSStyle.OutputRendering = 'PlainText' }\n"
                       + b["body"] + ("\nexit $LASTEXITCODE" if want else "")]
            if b.get("background"):
                log = logs / f"{k}.log"
                fh = open(log, "w", encoding="utf-8", errors="replace")
                handles.append(fh)
                kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, env=env, **kw)
                services.append(proc)
                why = wait_ready(proc, log, b.get("ready"), b.get("wait") or (120 if b.get("ready") else 3))
                if why:
                    res.update(status="failed", detail=f"service {why}")
                else:
                    res.update(detail=f"running in the background{' (ready: ' + b['ready'] + ')' if b.get('ready') else ''}")
                res["captured"] = save(b, "running", read(log), "")
            else:
                try:
                    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                       timeout=timeout, env=env)
                    missing = re.search(r"(?m)([\w.+-]+): command not found\s*$", r.stderr or "")  # bash's message, any prefix
                    if r.returncode == 127 and missing:
                        # the block needs a tool this machine lacks: not evidence that the docs are wrong, but not verified either
                        res.update(status="unavailable", detail=f"{missing.group(1)} is not installed here")
                    elif r.returncode != want:
                        res.update(status="failed", detail=f"exit {r.returncode}{f', expected {want}' if want else ''}: "
                                                           f"{(r.stderr or r.stdout).strip()[-400:]}")
                    elif b.get("expect") is not None:
                        diff = output_mismatch(b["expect"], (r.stdout or "") + "\n" + (r.stderr or ""))
                        if diff:
                            res.update(status="failed", detail=diff)
                        else:
                            res.update(detail="output checked")
                    res["captured"] = save(b, r.returncode, r.stdout, r.stderr)
                except subprocess.TimeoutExpired:
                    res.update(status="failed", detail=f"timeout after {timeout} s")
        results.append(res)
        if services and (k + 1 == len(blocks) or blocks[k + 1]["page"] != b["page"]):
            for proc in services:  # a page's services end with its last block
                stop_tree(proc)
            services = []
    for proc in services:
        stop_tree(proc)
    for fh in handles:
        fh.close()
    shutil.rmtree(logs, ignore_errors=True)
    return results, dropped


# ---------------------------------------------------------------- lint

def lint(repo: Path, wiki: Path, run: bool = False, in_place: bool = False, timeout: int = 600, capture: Path | None = None,
         strict: bool = False, clean_env: bool = False) -> dict:
    pages = collect_pages(repo, wiki)
    problems: list[dict] = []
    warnings: list[dict] = []
    syms = Symbols(repo)
    report = {"repo": repo.name, "wiki": posix(wiki, repo) if wiki.exists() else str(wiki), "pages": len(pages),
              "problems": problems, "warnings": warnings, "sources": {}, "diagrams": 0, "commands": [],
              "coverage": {"run": 0, "skip": 0, "unmarked": 0}, "words": {}, "map": {}, "accepted": []}
    files = None
    vocab = None  # the sources page's short names, read on first use

    def bad(page, line, msg):
        problems.append({"page": page.label, "line": line, "msg": msg})

    def warn(page, line, msg):
        warnings.append({"page": page.label, "line": line, "msg": msg})

    if not wiki.exists():
        problems.append({"page": "-", "line": 0, "msg": f"wiki folder not found: {wiki}"})
        return report
    for name in ("index.md", "SCHEMA.md", "log.md"):
        if not (wiki / name).exists():
            problems.append({"page": "-", "line": 0, "msg": f"{name} missing from the wiki folder"})

    index = next((p for p in pages if p.wiki_rel == "index.md"), None)
    indexed = set()
    if index:
        for _, t in links(index.text):
            if not is_external(t) and not t.startswith("#"):
                target = (index.path.parent / urllib.parse.unquote(t.partition("#")[0])).resolve()
                indexed.add(target)

    anchor_cache: dict[Path, set[str]] = {}
    seen_ids: dict[str, str] = {}
    all_blocks: list[dict] = []
    for page in pages:
        # front matter
        if page.is_content:
            if page.kind not in PAGE_KINDS:
                bad(page, 1, f"kind is '{page.kind or '(none)'}'; use one of {', '.join(sorted(PAGE_KINDS))}")
            if not page.meta.get("title"):
                warn(page, 1, "no title in front matter")
            if not page.sources and page.kind in ("reference", "explanation", "how-to") and not any(
                    "open first" in header for _, header, _ in table_rows(page)):  # the map's rows are checked one by one
                warn(page, 1, "no sources: the page cannot be checked against the code")
            if page.path.resolve() not in indexed:
                bad(page, 1, "not listed in index.md")
        # links (a diagram that is not rendered yet is reported once, by the diagram check below)
        own_svgs = {(wiki / "diagrams" / f"{b['id']}.svg").resolve() for b in mermaid_blocks(page) if b["id"]}
        for line, target in links(page.text):
            if is_external(target):
                continue
            if (page.path.parent / urllib.parse.unquote(target.partition("#")[0])).resolve() in own_svgs:
                continue
            if re.match(r"^[A-Za-z]:[\\/]", target) or target.startswith("\\\\"):
                bad(page, line, f"absolute machine path in a link: {target}")
                continue
            path_part, _, frag = target.partition("#")
            base = repo if path_part.startswith("/") else page.path.parent
            dest = (base / urllib.parse.unquote(path_part.lstrip("/"))).resolve() if path_part else page.path.resolve()
            try:
                dest.relative_to(repo.resolve())
            except ValueError:
                bad(page, line, f"link leaves the repository: {target}")
                continue
            if not dest.exists():
                bad(page, line, f"broken link: {target}")
            elif frag and dest.is_file() and dest.suffix.lower() in (".md", ".markdown"):
                if dest not in anchor_cache:
                    anchor_cache[dest] = anchors(read(dest))
                if urllib.parse.unquote(frag).lower() not in anchor_cache[dest]:
                    bad(page, line, f"missing anchor: {target}")
            elif frag and re.fullmatch(r"L\d+(-L?\d+)?", frag):
                warn(page, line, f"line-number link drifts: {target}; cite the symbol in sources instead")
        # sources
        for ref in page.sources:
            res = syms.find(ref)
            report["sources"][ref] = res
            if not res["ok"]:
                bad(page, 1, f"source {ref}: {res['note']}")
            elif res["note"]:
                warn(page, 1, f"source {ref}: {res['note']}")
        # output-field tables: the symbol in each `Set in` cell exists and still mentions the field it sets
        for line, field, symbol, target in set_in_rows(page):
            dest = (page.path.parent / urllib.parse.unquote(target.partition("#")[0])).resolve()
            try:
                ref = f"{posix(dest, repo)}#{symbol}"
            except ValueError:
                continue  # a link that leaves the repository is reported by the link check
            res = syms.find(ref)
            if not res["ok"]:
                bad(page, line, f"Set in {ref}: {res['note']}")
                continue
            names = [t for t in re.split(r"[.\[\]/\s'\"]+", field) if t]
            code = "\n".join(read(dest).split("\n")[res["line"] - 1:res["end"]])
            if names and not re.search(rf"(?<![\w-]){re.escape(names[-1])}(?![\w-])", code):
                warn(page, line, f"field '{field}' does not appear in {ref}: the code that sets it moved, or the field was renamed")
            if ref not in page.sources:
                warn(page, line, f"Set in {ref} is not in sources:, so a change to it does not flag this page")
        # tables that send the reader to code (`Open first`, `Code`): each linked name is defined in the file it links
        for line, col, name, target in code_cells(page):
            dest = (page.path.parent / urllib.parse.unquote(target.partition("#")[0])).resolve()
            if is_external(target) or not dest.is_file() or dest.suffix.lower() not in CODE_EXT:
                continue  # a missing file is the link check's to report
            if name == dest.name or not re.fullmatch(rf"{N}(?:\.{N})*", name):
                continue  # the link names the file, or is not a symbol
            try:
                path = posix(dest, repo)
            except ValueError:
                continue
            parts = name.split(".")  # `app.Engine.run` may carry its module: try `Engine.run` and `run` as well
            found = [syms.find(f"{path}#{'.'.join(parts[k:])}") for k in range(len(parts))]
            if not any(r["ok"] for r in found):
                bad(page, line, f"{col.capitalize()} {found[0]['ref']}: {found[0]['note']}")
        # step tables: the pipeline diagram's arrows carry what passes between steps
        for start, header, _ in table_rows(page):
            if header and header[0] == "#" and "step" in header and ("takes" in header or "gives" in header):
                warn(page, start, "this step table has Takes and Gives columns, which repeat the arrows of the pipeline diagram "
                                  "above it: drop the columns, and put a type the arrows lack on its arrow")
        # diagrams
        for block in mermaid_blocks(page):
            report["diagrams"] += 1
            if not block["id"]:
                bad(page, block["line"], "mermaid block without a first line '%% id: <name>'")
                continue
            if block["id"] in seen_ids:
                bad(page, block["line"], f"diagram id '{block['id']}' also used in {seen_ids[block['id']]}")
            seen_ids[block["id"]] = page.label
            svg = wiki / "diagrams" / f"{block['id']}.svg"
            if not svg.exists():
                bad(page, block["line"], f"diagrams/{block['id']}.svg not rendered (run wiki_browser.py render)")
                continue
            head = read(svg)[:1200]
            stamp = SVG_STAMP.search(head)
            if not stamp or stamp.group(2) != block["hash"]:
                bad(page, block["line"], f"diagrams/{block['id']}.svg is older than its source (run wiki_browser.py render)")
            elif re.search(r'<svg\b[^>]*\swidth="100%"', head):
                warn(page, block["line"], f"diagrams/{block['id']}.svg has no natural size, so a Markdown preview stretches "
                                          "or squeezes it (run wiki_browser.py render again)")
            if f"diagrams/{block['id']}.svg" not in page.text:
                warn(page, block["line"], f"the page does not show diagrams/{block['id']}.svg")
        # boxes that name code, and the calls a call map draws
        if "```mermaid" in page.text:
            if files is None:
                files = code_files(repo)
            map_checks(repo, page, syms, files, bad, warn)
        # how much a reader has to read (reported, never limited)
        if page.is_readme or page.is_content:
            report["words"][page.label] = len(re.findall(r"[^\W_]+", re.sub(r"\]\([^)]*\)", "]", "\n".join(prose_lines(page.text)))))
        # placeholders left from a template
        for i, line in enumerate(prose_lines(page.text), 1):
            for ph in re.findall(r"\{\{[^}]+\}\}", line):
                warn(page, i, f"template placeholder left: {ph}")
            if line.lstrip().startswith("$$"):
                warn(page, i, "a $$ formula: write it as a ```math block, which GitHub, GitLab, VS Code and the viewer "
                              "typeset and every other viewer shows as its TeX source; $$ text is mangled where math "
                              "is not supported")
        # command blocks: every block a reader would paste into a terminal is either run or skipped with a reason
        blocks, errs, cov = run_blocks(page)
        for line, msg in errs:
            bad(page, line, msg)
        all_blocks.extend(blocks)
        report["coverage"]["run"] += cov["run"]
        report["coverage"]["skip"] += cov["skip"]
        for line in cov["unmarked"]:
            report["coverage"]["unmarked"] += 1
            (bad if strict else warn)(page, line, 'command block neither checked (check:run) nor skipped with a reason (check:skip reason="…")')
        for b in blocks:
            if b.get("fill"):
                warn(page, b["fill"], "output waiting to be filled: run lint --run --capture <folder>, then wiki.py fill --capture <folder>")
        # sources the code follows: a source named in a section is linked in that section, and in each step of a step table
        if vocab is None:
            vocab = source_vocab(pages)
        for line, cite in unlinked_citations(page, vocab):
            warn(page, line, f"names {cite} without linking its source in this section: link it to the document in the "
                             "repository that covers it, or to its entry on the wiki's sources page")
        step_citation_checks(repo, page, syms, vocab, warn)
        bare = [line for line, t in links(page.text) if not is_external(t) and re.search(r"(^|/)sources\.md$", t)
                and not (page.wiki_rel and Path(page.wiki_rel).name == "sources.md")]
        if bare and page.kind != "index":  # the index lists the page itself
            warn(page, bare[0], f"{len(bare)} link(s) to the sources page name no entry: end each with the source's anchor "
                                "(sources.md#dnv-cn-41-2), so the reader lands on that source's row, with its clauses and "
                                "public link, instead of the top of the table")
        # complete call lists (`Caller | Calls` tables): each row is a call in the caller's code
        if "| caller" in page.text.lower():
            if files is None:
                files = code_files(repo)
            call_table_checks(repo, page, syms, files, bad, warn)

    # diagrams nobody uses any more
    if (wiki / "diagrams").exists():
        for svg in sorted((wiki / "diagrams").glob("*.svg")):
            if svg.stem not in seen_ids:
                warnings.append({"page": f"diagrams/{svg.name}", "line": 0, "msg": "no mermaid block has this id; delete it or restore the block"})

    readme = next((p for p in pages if p.is_readme), None)
    if readme and index and not any(not is_external(t) and (readme.path.parent / t.partition("#")[0]).resolve() == index.path.resolve()
                                    for _, t in links(readme.text)):
        warnings.append({"page": "README.md", "line": 0, "msg": "the README does not link to the wiki's index.md"})

    log_checks(repo, wiki, warnings)
    stale_checks(repo, wiki, pages, warnings)
    tour_checks(repo, warnings)
    repeat_checks(pages, warnings)
    first_read_checks(pages, warnings)
    report["map"] = coverage_checks(repo, wiki, pages, warnings)

    report["commands"] = [dict(b, status="not run") for b in all_blocks]
    if run and all_blocks:
        if in_place:
            report["commands"], report["env_left_out"] = execute(all_blocks, repo, timeout, capture, clean_env)
            report["ran_in"] = "working tree"
        elif not is_git(repo):
            problems.append({"page": "-", "line": 0, "msg": "--run needs a git repository for its clean checkout; add --in-place to run in the working tree"})
        else:
            tmp, dest = make_checkout(repo)
            try:
                report["commands"], report["env_left_out"] = execute(all_blocks, dest, timeout, capture, clean_env)
                report["ran_in"] = "clean checkout" + (", clean environment" if clean_env else "")
            finally:
                remove_checkout(repo, tmp, dest)
        for r in report["commands"]:
            if r["status"] == "failed":
                problems.append({"page": r["page"], "line": r["line"], "msg": f"command block failed: {r['detail']}"})
            elif r["status"] == "unavailable":
                warnings.append({"page": r["page"], "line": r["line"], "msg": f"command block not verified here: {r['detail']}"})
    report["accepted"] = apply_accepts(pages, problems, warnings)
    return report



LOG_ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([\w-]+) \| (.+)$")


def log_entries(text: str) -> list[str]:
    body = front_matter(text)[1]
    return re.findall(r"^## .*?(?=^## |\Z)", body, re.S | re.M)


def log_checks(repo: Path, wiki: Path, warnings: list[dict]) -> None:
    log = wiki / "log.md"
    if not log.exists():
        return
    text = read(log)
    entries = log_entries(text)
    last, out_of_order = "", 0
    for e in entries:
        head = e.split("\n", 1)[0].strip()
        m = LOG_ENTRY.match(head)
        if not m:
            warnings.append({"page": "log.md", "line": 0, "msg": f"log heading not in the form '## [YYYY-MM-DD] kind | title': {head[:80]}"})
            continue
        out_of_order += m.group(1) < last
        last = max(last, m.group(1))
    if out_of_order:
        warnings.append({"page": "log.md", "line": 0, "msg": f"{out_of_order} entries are older than the one before them: "
                                                             "append new entries at the end, so `tail` shows the latest"})
    if is_git(repo):
        rel = posix(log, repo)
        old = git(repo, "show", f"HEAD:{rel}", check=False)
        if old:
            before = log_entries(old)
            if [e.strip() for e in entries[:len(before)]] != [e.strip() for e in before]:
                warnings.append({"page": "log.md", "line": 0, "msg": "an entry committed earlier was changed or removed; the log is append-only"})


def stale_checks(repo: Path, wiki: Path, pages: list[Page], warnings: list[dict]) -> None:
    """A page whose source files changed after it was last updated or checked, and which is not being updated in this
    change, may be out of date."""
    if not is_git(repo):
        return
    mentions = log_mentions(repo, wiki)
    for page in pages:
        if not page.is_content or not page.sources:
            continue
        base, edited = baseline(repo, page, mentions)
        if edited or not base:
            continue  # being updated in this change, or not committed yet
        files = sorted({s.partition("#")[0] for s in page.sources})
        changed = [p for p in git(repo, "diff", "--name-only", "-z", base, "--", *files, check=False).split("\0") if p]
        if changed:
            warnings.append({"page": page.label, "line": 1,
                             "msg": f"sources changed after this page was last updated or checked ({base}): {', '.join(changed)}; "
                                    "update it, or name it in the log entry if it is still true"})


TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
DIAGRAM_SYNTAX = {"flowchart", "graph", "subgraph", "sequencediagram", "participant", "classdef", "class", "style", "note", "json"}


def tables(page: Page) -> list[tuple[int, set[str]]]:
    """(1-based line of the header, the items its rows are about) for each Markdown table outside code: a row's
    first cell, without code marks, link syntax or bold. Numbers and very short cells name no item."""
    lines = page.text.split("\n")
    in_code = {k for start, end, _ in fences(lines) for k in range(start, end + 1)}
    found, rows, start = [], None, 0
    for i, line in enumerate(lines + [""]):
        m = None if i in in_code else TABLE_ROW.match(line)
        if m:
            if rows is None:
                rows, start = [], i + 1
            rows.append(m.group(1))
        elif rows is not None:
            found.append((start, rows))
            rows = None
    out = []
    for start, rows in found:
        if len(rows) < 3 or not re.fullmatch(r"[\s|:-]+", rows[1]):
            continue
        keys = set()
        for row in rows[2:]:
            key = re.sub(r"[`*]", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", row.split("|")[0])).strip().lower()
            if len(key) >= 3 and not re.fullmatch(r"[\d.\s#]+", key):
                keys.add(key)
        if keys:
            out.append((start, keys))
    return out


CELL_SPLIT = re.compile(r"(?<!\\)\|")
CODE_LINK = re.compile(r"\[`?([^\]`]+?)`?\]\(\s*<?([^)\s>]+)>?\s*\)")


def set_in_rows(page: Page) -> list[tuple[int, str, str, str]]:
    """(1-based line, field, symbol, link target) for each row of a table, outside code, that has a `Set in` column:
    the output-field tables of pages.md, whose cell links the symbol that sets the field to its file."""
    lines = page.text.split("\n")
    in_code = {k for start, end, _ in fences(lines) for k in range(start, end + 1)}
    out, header, col = [], None, None
    for i, line in enumerate(lines):
        m = None if i in in_code else TABLE_ROW.match(line)
        if not m:
            header = col = None
            continue
        cells = [c.strip() for c in CELL_SPLIT.split(m.group(1))]
        if header is None:
            header = [c.strip("*").lower() for c in cells]
            col = header.index("set in") if "set in" in header else None
        elif col is not None and col < len(cells) and not re.fullmatch(r"[\s:-]*", cells[0]):
            link = CODE_LINK.search(cells[col])
            field = re.sub(r"[`*]", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cells[0])).strip()
            if link and field:
                out.append((i + 1, field, link.group(1).strip(), link.group(2)))
    return out


def diagram_names(source: str) -> set[str]:
    """The identifiers a diagram's labels name, such as the functions of a call chain."""
    labels = " ".join(re.findall(r'"([^"]+)"', "\n".join(l for l in source.split("\n") if not l.strip().startswith("%%"))))
    return {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", labels)} - DIAGRAM_SYNTAX


# ---------------------------------------------------------------- function maps

LABEL_BREAK = re.compile(r"<br\s*/?>|\\n|\n", re.I)
CODE_REF = re.compile(r"^`?(?P<path>[\w.\-/]+\.[A-Za-z0-9]+)`?\s*:\s*`?(?P<names>[\w.]+(?:\s*(?:,|\band\b)\s*`?[\w.]+`?)*)`?$")
NODE_DEF = re.compile(r'(?<![\w-])([A-Za-z_][\w-]*)\s*(?:\[\[|\[\(|\(\(|\(\[|\[/|\[\\|\{\{|\[|\(|\{|>)\s*"([^"]*)"\s*'
                      r'(?:\]\]|\)\]|\)\)|\]\)|/\]|\\\]|\}\}|\]|\)|\})')
ARROW = re.compile(r'(--\s*"[^"]*"\s*-->|==\s*"[^"]*"\s*==>|-\.\s*"[^"]*"\s*\.->|(?:-->|==>|-\.->|---|-\.-|===)(?:\|[^|]*\|)?)')
FLOW_KEYWORDS = ("flowchart", "graph", "subgraph", "end", "classdef", "class ", "style", "linkstyle", "click", "direction")


def code_files(repo: Path) -> list[str]:
    """Repository-relative paths of the source files a diagram may name."""
    out = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if Path(f).suffix.lower() in CODE_EXT:
                out.append(posix(Path(root) / f, repo))
    return out


def resolve_code_path(path: str, files: list[str]) -> tuple[str | None, str]:
    """A label's path may be shortened to any unique tail (`rating/life.py`). Returns (repository path, note)."""
    path = path.lstrip("./")
    hits = [f for f in files if f == path or f.endswith("/" + path)]
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return None, "file not found"
    return None, "path matches several files (" + ", ".join(hits[:3]) + "): write more of it"


def flow_graph(source: str) -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """({node id: label}, [(from, to, 'solid' | 'dotted' | 'line')]) of a Mermaid flowchart."""
    labels: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    for raw in source.split("\n"):
        line = raw.split("%%", 1)[0].strip()
        if not line or line.lower().startswith(FLOW_KEYWORDS):
            continue
        for m in NODE_DEF.finditer(line):
            labels.setdefault(m.group(1), m.group(2))
        bare = NODE_DEF.sub(lambda m: m.group(1) + " ", line)
        parts = ARROW.split(bare)
        for i in range(1, len(parts) - 1, 2):
            op = parts[i]
            kind = "dotted" if "-." in op or ".-" in op else ("solid" if ">" in op else "line")
            left = [t.strip() for t in parts[i - 1].split("&") if t.strip()]
            right = [t.strip() for t in parts[i + 1].split("&") if t.strip()]
            for a in left:
                for b in right:
                    if re.fullmatch(r"[A-Za-z_][\w-]*", a) and re.fullmatch(r"[A-Za-z_][\w-]*", b):
                        edges.append((a, b, kind))
    return labels, edges


def label_code(label: str) -> tuple[str, list[str]] | None:
    """(`path`, [names]) when a node's last label line is `path: function`, as boxes on function maps are written."""
    lines = [re.sub(r"[*_]{2}", "", s).strip() for s in LABEL_BREAK.split(label) if s.strip()]
    m = CODE_REF.match(lines[-1]) if lines else None
    if not m or Path(m.group("path")).suffix.lower() not in CODE_EXT:
        return None
    names = [n.strip("` ") for n in re.split(r"\s*(?:,|\band\b)\s*", m.group("names")) if n.strip("` ")]
    return m.group("path"), names


def map_checks(repo: Path, page: Page, syms: Symbols, files: list[str], bad, warn) -> None:
    """Boxes written `path: function` must name code that exists, on any diagram. On a call map (a diagram with a
    `%% calls` line), each solid arrow between two such boxes says the first calls the second, so the callee's name
    must appear in the caller's code; an indirect call (a registry, a callback, another process) is drawn dotted."""
    for block in mermaid_blocks(page):
        labels, edges = flow_graph(block["source"])
        is_call_map = any(l.strip().lower() == "%% calls" for l in block["source"].split("\n"))
        where = f"diagram '{block['id'] or '?'}'"
        found: dict[str, list[tuple[str, dict]]] = {}
        unlisted = []
        for node, label in labels.items():
            ref = label_code(label)
            if not ref:
                continue
            rel, note = resolve_code_path(ref[0], files)
            if not rel:
                bad(page, block["line"], f"{where}: box '{ref[0]}: {', '.join(ref[1])}': {note}")
                continue
            for name in ref[1]:
                res = syms.find(f"{rel}#{name}")
                if not res["ok"]:
                    bad(page, block["line"], f"{where}: box '{ref[0]}: {name}': {res['note']}")
                    continue
                found.setdefault(node, []).append((name, res))
                if not any(s == rel or s.startswith(rel + "#") for s in page.sources):
                    unlisted.append(rel)
        if unlisted:
            warn(page, block["line"], f"{where} draws code in {', '.join(sorted(set(unlisted))[:4])} that is not in sources:, "
                                      "so a change there does not flag this page")
        if not is_call_map:
            continue
        for a, b, kind in edges:
            if kind != "solid" or a not in found or b not in found:
                continue
            for caller, res in found[a]:
                body = read(repo / res["path"]).split("\n")[res["line"]:res["end"]]  # the definition line itself left out
                code = "\n".join(l for l in body if not l.lstrip().startswith(("#", "//")))
                resolved = py_callees(repo, res)  # Python: also calls through an import alias
                if not any(re.search(rf"(?<![\w$]){re.escape(callee.split('.')[-1])}(?![\w$])", code)
                           or (r["path"], r.get("qual")) in resolved for callee, r in found[b]):
                    warn(page, block["line"], f"{where}: the arrow {caller} -> {', '.join(c for c, _ in found[b])} is a call that "
                                              f"is not in {caller}'s code: the call moved, or it is indirect (draw it dotted, "
                                              "-.->, with how it is reached)")


_PYCALLS: dict[Path, "PyCalls"] = {}


def py_callees(repo: Path, res: dict) -> set[tuple[str, str]]:
    """{(path, qualified name)} a Python function calls, as PyCalls resolves them; empty for other languages."""
    if not res["path"].endswith(".py") or not res.get("qual"):
        return set()
    pc = _PYCALLS.setdefault(repo, PyCalls(repo))
    mod = pc.by_path.get((repo / res["path"]).resolve())
    try:
        callees, _ = pc.calls(mod, res["qual"]) if mod else ([], [])
    except (KeyError, SyntaxError, ValueError):
        return set()
    return {(posix(pc.mods[m], repo), q) for m, q in callees}


CITATION = re.compile(r"\b(?:ISO|IEC|DIN|AGMA|DNV(?: ?GL)?(?: ?CN)?|VDI|ASTM|ANSI|ASME|JIS|GB/T|RFC|IEEE|BS|EN)[  ]?"
                      r"\d[\d.]*(?:-\d+)*(?::\d{4})?")
LINK_TEXT = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\([^)]*\)")


def source_vocab(pages: list[Page]) -> list[tuple[re.Pattern, str]]:
    """(pattern, short name) for each source on the wiki's sources page, read from the first column of its table: the
    short name itself, and its first word alone when no other source starts with that word and the rest of the name
    is a document number (`DNV` of DNV CN 41.2, `Zhang` of Zhang et al. 2020; not `API` of API contract). So `DNV p. 12` and `DNV cl. 1.9.3.2` count as citations of DNV CN 41.2, which the bare standard
    pattern misses."""
    page = next((p for p in pages if p.wiki_rel and Path(p.wiki_rel).name == "sources.md"), None)
    if not page:
        return []
    names: list[str] = []
    for _, header, rows in table_rows(page):
        if not header or header[0] not in ("source", "sources", "short name", "name"):
            continue
        for _, cells in rows:
            name = re.sub(r"<[^>]+>", "", cells[0])
            name = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", name)
            name = re.sub(r"\([^)]*\)", "", name).replace("`", "").replace("*", "").strip()
            if len(name) >= 3 and name not in names:
                names.append(name)
    out = [(re.compile(r"(?<![\w/-])" + r"[\s ]+".join(map(re.escape, n.split())) + r"(?!\w)"), n) for n in names]
    firsts: dict[str, int] = {}
    for n in names:
        firsts[n.split()[0]] = firsts.get(n.split()[0], 0) + 1
    for n in names:
        w = n.split()[0]
        if firsts[w] == 1 and w != n and len(w) >= 3 and w[0].isupper() and re.search(r"\d", n[len(w):]):
            out.append((re.compile(r"(?<![\w/-])" + re.escape(w) + r"(?![\w/-])"), n))
    return out


def cite_mentions(text: str, vocab: list[tuple[re.Pattern, str]]) -> list[tuple[int, int, str, str]]:
    """(start, end, source key, text as written) for each citation in the text: a standard by number (ISO 6336-1,
    RFC 9457), or a source the sources page lists, by its short name or its own first word."""
    found = []
    for m in CITATION.finditer(text):
        s = re.sub(r"[\s ]+", " ", m.group(0))
        key = next((n for _, n in vocab if s.upper().startswith(n.upper())), s.upper())
        found.append((m.start(), m.end(), key, m.group(0)))
    for rx, name in vocab:
        for m in rx.finditer(text):
            if not any(a <= m.start() < b for a, b, _, _ in found):
                found.append((m.start(), m.end(), name, m.group(0)))
    return sorted(found)


def unlinked_citations(page: Page, vocab: list[tuple[re.Pattern, str]] = ()) -> list[tuple[int, str]]:
    """(line, citation) for each source a section names (ISO 6336-1, DNV CN 41.2, RFC 9457, or `DNV` in `DNV p. 12`
    when the sources page lists DNV CN 41.2) that no mention in that section links: a reader checking a number in that
    section cannot reach the source. The rule is the first mention in each section; one linked mention anywhere in the
    section passes. The sources page itself is exempt; it is where the links point."""
    if page.wiki_rel and Path(page.wiki_rel).name == "sources.md":
        return []
    out: list[tuple[int, str]] = []
    first: dict[str, tuple[int, str]] = {}
    linked: set[str] = set()
    for i, line in enumerate(prose_lines(page.text), 1):
        if i <= page.fm_lines:
            continue
        if re.match(r"\s{0,3}#{1,6}\s", line):
            out += [first[k] for k in first if k not in linked]
            first, linked = {}, set()
        spans = [m.span(1) for m in LINK_TEXT.finditer(line)]
        for a, _, key, text in cite_mentions(line, vocab):
            first.setdefault(key, (i, text))
            if any(x <= a < y for x, y in spans):
                linked.add(key)
    return out + [first[k] for k in first if k not in linked]


DOC_TARGET = re.compile(r"\.(?:md|markdown|rst|txt|pdf|html?)(?:#|$)", re.I)
INLINE_CODE = re.compile(r"(`+)(?!`).+?(?<!`)\1(?!`)")


def step_citation_checks(repo: Path, page: Page, syms: "Symbols", vocab: list[tuple[re.Pattern, str]], warn) -> None:
    """In a step table (header `# | Step | Method | Code …`), the Method cell is where a reader checking a number goes
    to the clause it comes from. Each source the cell names is linked in that cell; and a step whose code cites a
    source (a docstring or comment such as "DNV p.12"), in its own functions or in a function of the same file they
    call, links its source in the Method cell. Review of 2026-11-08: steps 5-7 of a spur rating cited `DNV p. 12` and
    `DNV cl. 1.9.3.2`, or nothing, without a link, and the page-level check passed because DNV CN 41.2 was linked
    once higher up."""
    for _, header, rows in table_rows(page):
        if not (header and header[0] == "#" and "step" in header and "method" in header):
            continue
        mcol, scol = header.index("method"), header.index("step")
        ccol = header.index("code") if "code" in header else None
        for line, cells in rows:
            if mcol >= len(cells):
                continue
            cell = INLINE_CODE.sub(lambda m: " " * len(m.group(0)), cells[mcol])
            label = re.sub(r"[*`]", "", re.sub(r"\s+", " ", cells[scol]))[:60] if scol < len(cells) else ""
            step = f"step {cells[0]} ({label})"
            spans = [m.span(1) for m in LINK_TEXT.finditer(cell)]
            mentions = cite_mentions(cell, vocab)
            done = {k for a, _, k, _ in mentions if any(x <= a < y for x, y in spans)}
            for a, _, key, text in mentions:
                if key not in done:
                    done.add(key)
                    warn(page, line, f"{step} names {text} in its Method cell without a link: link it there, to the section "
                                     "of the repository's document that covers the clause, or to the source's entry on the "
                                     "sources page")
            targets = re.findall(r"\]\(\s*<?([^)\s>]+)", cells[mcol])
            if mentions or ccol is None or ccol >= len(cells) or any(DOC_TARGET.search(t) or is_external(t) for t in targets):
                continue
            cited: list[str] = []
            for text, target in CODE_LINK.findall(cells[ccol]):
                if is_external(target):
                    continue
                path = (page.path.parent / urllib.parse.unquote(target.partition("#")[0])).resolve()
                try:
                    rel = path.relative_to(repo.resolve()).as_posix()
                except ValueError:
                    continue
                name = re.sub(r"\(\)$", "", text.strip())
                res = syms.find(f"{rel}#{name}")
                if not res["ok"] or not res.get("end"):
                    continue
                lines = read(path).split("\n")
                code = "\n".join(lines[res["line"] - 1:res["end"]])
                bodies = [(name, code)]
                for qual, start, end in syms.defs(path)[1]:
                    short = qual.split(".")[-1]
                    if short != name.split(".")[-1] and re.search(rf"(?<![\w.]){re.escape(short)}\s*\(", code):
                        bodies.append((f"{short}, called by {name}", "\n".join(lines[start - 1:end])))
                for who, body in bodies:
                    for _, _, _, t in cite_mentions(body, vocab):
                        item = re.sub(r"[\s ]+", " ", t) + f" ({who})"
                        if item not in cited:
                            cited.append(item)
            if cited:
                more = " …" if len(cited) > 3 else ""
                warn(page, line, f"{step}: its code cites {', '.join(cited[:3])}{more}, and its Method cell links no source: "
                                 "name the method as the code does and link the clause, or link the repository's chapter "
                                 "that describes the step")



def call_table_checks(repo: Path, page: Page, syms: Symbols, files: list[str], bad, warn) -> None:
    """A complete call list is a table whose header starts `Caller | Calls` (or `Callee`), one row per call, each cell
    `file: function`. Like a call map's solid arrows: both functions must exist, and the callee must be called in the
    caller's code."""
    lines = page.text.split("\n")
    in_code = {k for start, end, _ in fences(lines) for k in range(start, end + 1)}
    header = None
    for i, line in enumerate(lines):
        m = None if i in in_code else TABLE_ROW.match(line)
        if not m:
            header = None
            continue
        cells = [re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", c).strip().strip("`* ") for c in CELL_SPLIT.split(m.group(1))]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if not (len(header) >= 2 and header[0] == "caller" and header[1] in ("calls", "callee")) or re.fullmatch(r"[\s:-]*", cells[0]):
            continue
        ends = []
        for cell in cells[:2]:
            ref = label_code(cell)
            if not ref:
                bad(page, i + 1, f"call list: '{cell}' is not `file: function`")
                break
            rel, note = resolve_code_path(ref[0], files)
            res = syms.find(f"{rel}#{ref[1][0]}") if rel else {"ok": False, "note": note}
            if not res["ok"]:
                bad(page, i + 1, f"call list: '{cell}': {res['note']}")
                break
            ends.append((ref[1][0], res))
        if len(ends) < 2:
            continue
        (caller, a), (callee, b) = ends
        body = "\n".join(l for l in read(repo / a["path"]).split("\n")[a["line"]:a["end"]] if not l.lstrip().startswith(("#", "//")))
        if not (re.search(rf"(?<![\w$]){re.escape(callee.split('.')[-1])}(?![\w$])", body)
                or (b["path"], b.get("qual")) in py_callees(repo, a)):
            warn(page, i + 1, f"call list: {callee} is not called in {caller}'s code: the call moved, or it is indirect")


def table_rows(page: Page) -> list[tuple[int, list[str], list[tuple[int, list[str]]]]]:
    """(1-based header line, lower-case header cells, [(1-based line, raw cells)]) for each table outside code."""
    lines = page.text.split("\n")
    in_code = {k for start, end, _ in fences(lines) for k in range(start, end + 1)}
    out, cur = [], None
    for i, line in enumerate(lines):
        m = None if i in in_code else TABLE_ROW.match(line)
        if not m:
            cur = None
            continue
        cells = [c.strip() for c in CELL_SPLIT.split(m.group(1))]
        if cur is None:
            cur = (i + 1, [re.sub(r"[`*]", "", c).strip().lower() for c in cells], [])
            out.append(cur)
        elif not re.fullmatch(r"[\s:-]*", "".join(cells)):
            cur[2].append((i + 1, cells))
    return out


def code_names(cell: str) -> dict[tuple[str, str], str]:
    """The functions a cell links, such as [`Resolver.search`](…/resolver.py): {(file name, last part of the name):
    the name as written}, so `LLMClient.chat` and `chat` linked to the same file are one function, and `search` in
    api/search.py is not `Resolver.search` in resolver.py."""
    out = {}
    for text, target in CODE_LINK.findall(cell):
        name = re.sub(r"\(\)$", "", text.strip())
        out[(Path(target.partition("#")[0]).name.lower(), name.split(".")[-1].lower())] = name
    return out


def first_read_checks(pages: list[Page], warnings: list[dict]) -> None:
    """The overview's "code to know first" table (header `Code | What it decides …`) covers each step of the main
    flow: every step of the pipeline table on a how-it-works page linked from that section has at least one of its
    functions in the table. Reading agents name exactly the functions in this table, so a step it skips, they skip;
    they also stop near its end, so the fix is a swap or a stated reason, not a longer table (trial of 2026-11-08)."""
    by_path = {p.path.resolve(): p for p in pages}
    for page in pages:
        lines = page.text.split("\n")
        for start, header, rows in table_rows(page):
            if not (header and header[0] == "code" and any(h.startswith("what it decides") for h in header)):
                continue
            listed = {k for _, cells in rows for k in code_names(cells[0])}
            top = next((k for k in range(start - 1, -1, -1) if re.match(r"#{1,6} ", lines[k])), 0)
            end = next((k for k in range(start, len(lines)) if re.match(r"#{1,6} ", lines[k])), len(lines))
            flows = []
            for _, target in links("\n".join(lines[top:end])):
                path = target.partition("#")[0]
                if is_external(target) or not re.search(r"how-[\w-]+-works\.md$", path):
                    continue
                other = by_path.get((page.path.parent / path).resolve())
                if other and other not in flows:
                    flows.append(other)
            if not flows:
                warnings.append({"page": page.label, "line": start, "msg": "the code-to-know-first section links no how-it-works "
                                 "page: link the main flow's page in its lead, so a reader can go on to the steps"})
            for flow in flows:
                for _, fheader, frows in table_rows(flow):
                    if not (fheader and fheader[0] == "#" and "step" in fheader and "code" in fheader):
                        continue
                    col, scol = fheader.index("code"), fheader.index("step")
                    for _, cells in frows:
                        names = code_names(cells[col]) if col < len(cells) else {}
                        if names and not names.keys() & listed:
                            step = re.sub(r"\s+", " ", cells[scol])[:70] if scol < len(cells) else ""
                            warnings.append({"page": page.label, "line": start, "msg": f"step {cells[0]} of {flow.label} ({step}) "
                                             f"has none of its functions in this table ({', '.join(sorted(names.values()))}): readers "
                                             "who start here skip that step. Put its deciding function in place of a row that "
                                             f"decides less, or keep the gap with its reason (lint:accept \"step {cells[0]} of "
                                             f"{flow.label}\" reason=\"…\"); a longer table pushes its last rows out of what "
                                             "readers take"})


CHECKED_COLUMNS = ("open first", "code")


def code_cells(page: Page) -> list[tuple[int, str, str, str]]:
    """(1-based line, column, name, link target) for each code link in a table column named `Open first` or `Code`:
    the map's rows, the overview's code to know first, a step table's code."""
    out = []
    for _, header, rows in table_rows(page):
        cols = [i for i, h in enumerate(header) if h in CHECKED_COLUMNS]
        for line, cells in rows:
            for c in cols:
                for text, target in CODE_LINK.findall(cells[c]) if c < len(cells) else []:
                    out.append((line, header[c], re.sub(r"\(\)$", "", text.strip()), target))
    return out


CONFIG_EXT = {".json", ".jsonc", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".mk", ".just"}


def tracked_code(repo: Path, wiki: Path) -> list[str]:
    """The code files a reader may be sent to: tracked by git, so installs and build output are out; without git,
    every code file found. Configuration formats, the wiki and its tools are left out."""
    names = [f for f in git(repo, "ls-files", check=False).split("\n") if f] if is_git(repo) else []
    names = names or code_files(repo)
    skip = [posix(wiki, repo) + "/"]
    try:
        skip.append(posix(HERE, repo) + "/")
    except ValueError:
        pass
    return [f for f in names if Path(f).suffix.lower() in CODE_EXT - CONFIG_EXT and not f.endswith(".d.ts")
            and not any(part in SKIP_DIRS for part in Path(f).parts) and not any(f.startswith(s) for s in skip)]


def coverage_checks(repo: Path, wiki: Path, pages: list[Page], warnings: list[dict]) -> dict:
    """How much of the code the wiki leads to. A code file counts when a page links it or names it in `sources:`, or
    when a row of the map (a table with an `Open first` column) names it, or a folder above it, in its first cell.
    The files left over are where a reader with a user's report finds no way in, so they are reported, by folder."""
    code = tracked_code(repo, wiki)
    if not code:
        return {}
    root = repo.resolve()

    def rel(base: Path, target: str) -> str | None:
        try:
            return (base / urllib.parse.unquote(target)).resolve().relative_to(root).as_posix()
        except (ValueError, OSError):
            return None

    linked, rows, map_page, unlinked = set(), {}, None, {}
    for page in pages:
        for ref in page.sources:
            linked.add(ref.partition("#")[0])
        for _, target in links(page.text):
            if not is_external(target) and not target.startswith("#"):
                linked.add(rel(page.path.parent, target.partition("#")[0]))
        for _, header, trows in table_rows(page):
            if "open first" not in header:
                continue
            map_page = map_page or page
            col = header.index("open first")
            for line, cells in trows:
                linked_row = col < len(cells) and bool(CODE_LINK.search(cells[col]))
                names = [rel(page.path.parent, t.partition("#")[0]) for _, t in CODE_LINK.findall(cells[0]) if not is_external(t)]
                names += [rel(repo, t.split("*")[0]) for t in re.findall(r"`([^`]+)`", re.sub(r"\[[^\]]*\]\([^)]*\)", "", cells[0]))]
                for name in names:
                    if name and (repo / name).exists():
                        rows.setdefault(name.rstrip("/"), 0)
                        if not linked_row:
                            unlinked.setdefault(name.rstrip("/"), (page, line))
    on_pages = [f for f in code if f in linked]
    under, none = [], []
    for f in code:
        if f in linked:
            continue
        row = next((r for r in sorted(rows, key=len, reverse=True) if f == r or f.startswith(r + "/")), None)
        if row is None:
            none.append(f)
        else:
            under.append(f)
            rows[row] += 1
    for name, (page, line) in unlinked.items():
        if rows[name] > 1:  # a row for one file, a package marker or a config file needs no function
            warnings.append({"page": page.label, "line": line, "msg": f"this map row stands for {rows[name]} code files under "
                             f"{name}/ and links none of them in Open first: link the one where the behaviour starts, and give "
                             "each file with logic of its own a row"})
    out = {"code_files": len(code), "on_pages": len(on_pages), "under_map_rows": len(under), "on_none": none,
           "largest_rows": sorted(((r, n) for r, n in rows.items() if n > 1), key=lambda kv: -kv[1])[:3]}
    if none:
        folders: dict[str, int] = {}
        for f in none:
            folders[f.rpartition("/")[0] or "."] = folders.get(f.rpartition("/")[0] or ".", 0) + 1
        top = ", ".join(f"{d}/ ({n})" for d, n in sorted(folders.items(), key=lambda kv: (-kv[1], kv[0]))[:8])
        more = "" if len(folders) <= 8 else f", and {len(folders) - 8} more folders"
        if map_page:
            warnings.append({"page": map_page.label, "line": 0, "msg": f"{len(none)} of {len(code)} code files are on no page and "
                             f"under no row of this map: {top}{more}. Add a row for each part, with the function to open first"})
        else:
            warnings.append({"page": "index.md", "line": 0, "msg": f"{len(none)} of {len(code)} code files are on no page: {top}"
                             f"{more}. A reader with a report about that code finds no way in: add the map of the code "
                             "(reference/map.md: one row per module, with what it does and the function to open first)"})
    return out


ACCEPT = re.compile(r"<!--\s*lint:accept\s+\"([^\"]+)\"(?:\s+reason=\"([^\"]*)\")?\s*-->")


def apply_accepts(pages: list[Page], problems: list[dict], warnings: list[dict]) -> list[dict]:
    """A warning that stays for a reason is kept on its page, in a line the next maintainer reads:
    <!-- lint:accept "part of the warning's message" reason="why it stays" -->. Such warnings leave the warning list
    and are reported with their reasons. Problems cannot be kept this way, and a line that matches no warning is
    itself reported, so the lines do not outlive what they excuse."""
    accepted = []
    for page in pages:
        lines = page.text.split("\n")
        in_code = {k for start, end, _ in fences(lines) for k in range(start, end + 1)}
        for i, line in enumerate(lines):
            for text, reason in ACCEPT.findall(line) if i not in in_code else []:
                if not reason.strip():
                    problems.append({"page": page.label, "line": i + 1, "msg": f'lint:accept "{text}" gives no reason="…"'})
                    continue
                hits = [w for w in warnings if w["page"] == page.label and text.lower() in w["msg"].lower()]
                if not hits:
                    warnings.append({"page": page.label, "line": i + 1,
                                     "msg": f'lint:accept "{text}" matches no warning on this page now: remove the line'})
                for w in hits:
                    warnings.remove(w)
                    accepted.append(dict(w, reason=reason.strip()))
    return accepted


VOLATILE = [  # values that differ on every run; `wiki.py fill` writes … in their place, which check:output matches
    (re.compile(r"[A-Za-z]:[\\/][^\s\"'<>|]*?wiki-run-\w+[\\/]repo"), "…"),
    (re.compile(r"/[^\s\"'<>|]*?wiki-run-\w+/repo"), "…"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"), "…"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "…"),
    (re.compile(r"\bin \d+(?:\.\d+)?s\b"), "in …s"),
    (re.compile(r"\b\d+(?:\.\d+)? ?ms\b"), "… ms"),
]
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def captured_output(path: Path) -> str:
    """The stdout, then the stderr, of one capture file written by lint --run --capture."""
    text = read(path)
    out = text.split("\n--- stdout\n", 1)[1] if "\n--- stdout\n" in text else ""
    out, _, err = out.partition("\n--- stderr\n")
    return "\n".join(x.rstrip("\n") for x in (out, err) if x.strip())


def fill(repo: Path, wiki: Path, capture: Path, max_lines: int = 40) -> dict:
    """Put the captured output of each run block under it, where the page marks the place with
    `<!-- check:output fill -->`: run-specific values become …, long output keeps its first and last lines, and the
    marker becomes `<!-- check:output -->` so the next run compares against it. The agent then reviews each block and
    its label; this does the copying."""
    filled, missing = [], []
    for page in collect_pages(repo, wiki):
        todo = [b for b in run_blocks(page)[0] if b.get("fill")]
        if not todo:
            continue
        lines = page.text.split("\n")
        ends = {start: end for start, end, _ in fences(lines)}
        for b in sorted(todo, key=lambda x: -x["fill"]):
            name = re.sub(r"[^\w.-]+", "_", f"{b['page']}-{b['line']}") + ".txt"
            if not (capture / name).exists():
                missing.append(f"{page.label}:{b['line']}")
                continue
            out = ANSI.sub("", captured_output(capture / name)).replace("\r\n", "\n")
            for rx, rep in VOLATILE:
                out = rx.sub(rep, out)
            body = [l.rstrip() for l in out.split("\n")]
            total = len(body)
            if total > max_lines:
                body = body[:max_lines // 2] + ["…"] + body[-(max_lines // 2 - 5):]
            start = b["fill"] - 1
            marker = start - 1
            while marker > 0 and not lines[marker].strip():
                marker -= 1
            lines[marker] = re.sub(r"check:output\s+fill", "check:output", lines[marker])
            lines[start + 1:ends[start]] = body
            filled.append({"page": page.label, "line": b["line"], "lines": total, "kept": len(body)})
        newline = "\r\n" if b"\r\n" in page.path.read_bytes() else "\n"  # keep the page's own line endings
        page.path.write_text("\n".join(lines), encoding="utf-8", newline=newline)
    return {"filled": filled, "missing": missing}


def py_module_index(repo: Path) -> dict[str, Path]:
    """{dotted module name: file} for every Python file, named from the nearest folder without an __init__.py."""
    out = {}
    for rel in code_files(repo):
        if not rel.endswith(".py"):
            continue
        path = repo / rel
        parts = [] if path.stem == "__init__" else [path.stem]
        d = path.parent
        while (d / "__init__.py").exists() and d != repo:
            parts.insert(0, d.name)
            d = d.parent
        if parts:
            out.setdefault(".".join(parts), path)
    return out


class PyCalls:
    """Static call edges between Python functions of one repository: direct calls by name, through an imported module,
    or on self/cls. Calls on other objects and dynamic dispatch are listed as not followed, for the agent to draw."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.mods = py_module_index(repo)
        self.by_path = {p.resolve(): m for m, p in self.mods.items()}
        self.parsed: dict[str, tuple[dict, dict]] = {}

    def module(self, mod: str) -> tuple[dict, dict]:
        """({qualified name: def node}, {local alias: ('module', name) | ('symbol', module, name)})."""
        if mod in self.parsed:
            return self.parsed[mod]
        tree = ast.parse(read(self.mods[mod]))
        defs, imports = {}, {}
        pkg = mod if self.mods[mod].stem == "__init__" else mod.rpartition(".")[0]
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs[n.name] = n
            elif isinstance(n, ast.ClassDef):
                defs[n.name] = n
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        defs[f"{n.name}.{m.name}"] = m
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.asname:
                        imports[a.asname] = ("module", a.name)
                    else:
                        imports[a.name.split(".")[0]] = ("module", a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom):
                base = n.module or ""
                if n.level:
                    up = pkg.split(".") if pkg else []
                    up = up[:len(up) - (n.level - 1)] if n.level > 1 else up
                    base = ".".join(up + ([base] if base else []))
                for a in n.names:
                    full = f"{base}.{a.name}" if base else a.name
                    imports[a.asname or a.name] = ("module", full) if full in self.mods else ("symbol", base, a.name)
        self.parsed[mod] = (defs, imports)
        return defs, imports

    def symbol(self, mod: str, name: str, hops: int = 0) -> tuple[str, str] | None:
        """Follow re-exports to the module that defines `name`."""
        if mod not in self.mods or hops > 6:
            return None
        defs, imports = self.module(mod)
        if name in defs and isinstance(defs[name], (ast.FunctionDef, ast.AsyncFunctionDef)):
            return mod, name
        if name in defs:
            return None  # a class: instantiation is not followed
        imp = imports.get(name)
        if imp and imp[0] == "symbol":
            return self.symbol(imp[1], imp[2], hops + 1)
        return None

    def calls(self, mod: str, qual: str) -> tuple[list[tuple[str, str]], list[str]]:
        """([(module, function) called, in call order], [calls not followed])."""
        defs, imports = self.module(mod)
        fn = defs[qual]
        cls = qual.rpartition(".")[0]
        out, skipped = [], []
        nodes = sorted((n for stmt in fn.body for n in ast.walk(stmt) if isinstance(n, ast.Call)),  # decorators left out
                       key=lambda n: (n.lineno, n.col_offset))
        for call in nodes:
            target, chain = None, []
            f = call.func
            while isinstance(f, ast.Attribute):
                chain.insert(0, f.attr)
                f = f.value
            if not isinstance(f, ast.Name):
                continue
            head = f.id
            if not chain:
                if head in defs:
                    target = self.symbol(mod, head)
                elif head in imports:
                    imp = imports[head]
                    target = self.symbol(imp[1], imp[2]) if imp[0] == "symbol" else None
            elif head in ("self", "cls") and cls and len(chain) == 1:
                if f"{cls}.{chain[0]}" in defs:
                    target = (mod, f"{cls}.{chain[0]}")
            elif head in imports and imports[head][0] == "module":
                base = imports[head][1]
                while len(chain) > 1 and f"{base}.{chain[0]}" in self.mods:
                    base = f"{base}.{chain.pop(0)}"
                if len(chain) == 1:
                    target = self.symbol(base, chain[0])
            elif head in imports and imports[head][0] == "symbol" and f"{imports[head][1]}.{imports[head][2]}" in self.mods:
                target = self.symbol(f"{imports[head][1]}.{imports[head][2]}", chain[0]) if len(chain) == 1 else None
            if target:
                if target not in out and target != (mod, qual):
                    out.append(target)
            elif chain and chain[-1] in self.repo_names() and not (head in imports and imports[head][0] == "module"
                                                                  and imports[head][1] not in self.mods):
                desc = f"{head}.{'.'.join(chain)}"  # a method on an object, or an inherited one: the type decides
                if desc not in skipped:
                    skipped.append(desc)
        return out, skipped

    def repo_names(self) -> set[str]:
        """Names of every function and method defined in the repository, to tell a possible call into it from a
        library call such as `items.append`."""
        if not hasattr(self, "_names"):
            names = set()
            for m in self.mods:
                try:
                    names |= {q.split(".")[-1] for q, n in self.module(m)[0].items()
                              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                except (SyntaxError, ValueError):
                    continue
            self._names = names
        return self._names


def callgraph(repo: Path, start: str, depth: int, max_nodes: int, diagram_id: str | None,
              table: bool = False) -> tuple[str, list[str]]:
    """A Mermaid call map from `path#function` (Python), breadth first, for a page to start from; with `table`, the
    same calls as a `Caller | Calls` table, the complete list a page keeps beside a pruned map."""
    path_part, _, qual = start.partition("#")
    pc = PyCalls(repo)
    mod = pc.by_path.get((repo / path_part).resolve())
    if not mod or not qual:
        raise SystemExit(f"callgraph: {start} is not path#function in a Python file of this repository")
    defs, _ = pc.module(mod)
    if qual not in defs or not isinstance(defs[qual], (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise SystemExit(f"callgraph: no function {qual} in {path_part}")
    files = code_files(repo)

    def short(m: str) -> str:
        rel = posix(pc.mods[m], repo)
        parts = rel.split("/")
        for k in range(1, len(parts) + 1):
            tail = "/".join(parts[-k:])
            if sum(1 for f in files if f == tail or f.endswith("/" + tail)) == 1:
                return tail
        return rel

    ids: dict[tuple[str, str], str] = {}
    order: list[tuple[str, str]] = []
    edges: list[tuple[str, str]] = []
    notes: list[str] = []
    queue = [((mod, qual), 0)]
    ids[(mod, qual)] = "n1"
    order.append((mod, qual))
    while queue:
        (m, q), d = queue.pop(0)
        if d >= depth:
            continue
        callees, skipped = pc.calls(m, q)
        if skipped:
            notes.append(f"{short(m)}: {q} also calls, not followed: {', '.join(skipped[:8])}{' …' if len(skipped) > 8 else ''}")
        for t in callees:
            if t not in ids:
                if len(ids) >= max_nodes:
                    notes.append(f"stopped at {max_nodes} boxes; raise --max-nodes or start deeper")
                    queue = []
                    break
                ids[t] = f"n{len(ids) + 1}"
                order.append(t)
                queue.append((t, d + 1))
            edges.append((ids[(m, q)], ids[t]))
    if table:
        names = {v: k for k, v in ids.items()}
        rows = ["| Caller | Calls |", "|---|---|"]
        rows += [f"| `{short(names[a][0])}: {names[a][1]}` | `{short(names[b][0])}: {names[b][1]}` |" for a, b in dict.fromkeys(edges)]
        return "\n".join(rows), notes
    did = diagram_id or "calls-" + re.sub(r"[^a-z0-9]+", "-", qual.lower()).strip("-")
    out = [f"%% id: {did}", "%% calls", "flowchart TB"]
    out += [f'    {ids[t]}["{short(t[0])}: {t[1]}"]' for t in order]
    out += [f"    {a} --> {b}" for a, b in dict.fromkeys(edges)]
    return "\n".join(out), notes


def repeat_checks(pages: list[Page], warnings: list[dict]) -> None:
    """A fact kept in full in two places drifts: one copy gets the change and the other does not, and the reader cannot
    tell which is current. Flag a table that repeats most rows of a table on another page, and a diagram that repeats
    most of another diagram. Whether the repeat is the subset a task needs, or a second full copy, is the agent's call."""
    content = [p for p in pages if p.is_readme or p.is_content]
    seen: list[tuple[Page, int, set[str]]] = []
    for page in content:
        for line, keys in tables(page):
            for other, oline, okeys in seen:
                shared = keys & okeys
                if other is not page and len(shared) >= 4 and len(shared) >= 0.5 * min(len(keys), len(okeys)):
                    warnings.append({"page": page.label, "line": line,
                                     "msg": f"this table repeats {len(shared)} rows of the table at {other.label}:{oline} "
                                            f"({', '.join(sorted(shared)[:3])}, …): keep the full table in one place, and here "
                                            "only the rows this page's task needs, with a link to the rest"})
                    break
            seen.append((page, line, keys))
    drawn: list[tuple[Page, str, set[str]]] = []
    for page in content:
        for block in mermaid_blocks(page):
            names = diagram_names(block["source"])
            for other, oid, onames in drawn:
                shared = names & onames
                if other is not page and len(shared) >= 6 and len(shared) >= 0.5 * min(len(names), len(onames)):
                    warnings.append({"page": page.label, "line": block["line"],
                                     "msg": f"diagram '{block['id']}' names mostly the same code as diagram '{oid}' in "
                                            f"{other.label}: draw it once, and link to it from the other page"})
                    break
            drawn.append((page, block["id"] or "?", names))


def tour_checks(repo: Path, warnings: list[dict]) -> None:
    """CodeTour files (.tours/*.tour) the wiki keeps: each step's file exists, and its `pattern` still matches a line.
    A step anchored by `line` drifts with every edit above it, so it is reported."""
    for tour in sorted((repo / ".tours").glob("*.tour")) if (repo / ".tours").is_dir() else []:
        label = posix(tour, repo)
        try:
            steps = json.loads(read(tour)).get("steps", [])
        except ValueError as e:
            warnings.append({"page": label, "line": 0, "msg": f"not valid JSON: {e}"})
            continue
        for i, step in enumerate(steps, 1):
            f = step.get("file")
            if not f:
                continue
            target = repo / f
            if not target.exists():
                warnings.append({"page": label, "line": 0, "msg": f"step {i}: file missing: {f}"})
            elif step.get("pattern"):
                try:
                    ok = re.search(step["pattern"], read(target), re.M)
                except re.error as e:
                    ok, step["pattern"] = None, f"{step['pattern']} (invalid: {e})"
                if not ok:
                    warnings.append({"page": label, "line": 0, "msg": f"step {i}: pattern no longer matches {f}: {step['pattern']}"})
            elif step.get("line"):
                warnings.append({"page": label, "line": 0, "msg": f"step {i}: anchored by line {step['line']}, which drifts; use pattern"})


def print_lint(report: dict) -> None:
    for p in report["problems"]:
        print(f"FAIL {p['page']}{':' + str(p['line']) if p['line'] else ''}: {p['msg']}")
    for w in report["warnings"]:
        print(f"warn {w['page']}{':' + str(w['line']) if w['line'] else ''}: {w['msg']}")
    for w in report.get("accepted", []):
        print(f"kept {w['page']}{':' + str(w['line']) if w['line'] else ''}: {w['msg'][:110]}… Reason: {w['reason']}")
    if report["warnings"]:
        print('A warning that stays for a reason: put <!-- lint:accept "part of its message" reason="why it stays" --> on its page.')
    label = {"ok": "run ", "skipped": "skip", "unavailable": "n/a ", "failed": "FAIL"}
    for c in report["commands"]:
        if c["status"] != "not run":
            print(f"{label[c['status']]} {c['page']}:{c['line']} "
                  f"{c['body'].splitlines()[0][:80] if c['body'] else ''}{' -> ' + c['detail'] if c['detail'] else ''}")
    print(summary(report))


def summary(report: dict) -> str:
    ran = [c for c in report["commands"] if c["status"] in ("ok", "failed", "unavailable")]
    parts = [f"{report['pages']} pages", f"{len(report['sources'])} sources", f"{report['diagrams']} diagrams"]
    if ran:
        na = sum(c["status"] == "unavailable" for c in ran)
        checked = sum(c.get("detail") == "output checked" for c in ran)
        parts.append(f"{len(ran)} command blocks run in the {report.get('ran_in', '')}" + (f", {checked} with their output checked" if checked else "") +
                     (f" ({na} need a tool not installed here)" if na else ""))
    elif report["commands"]:
        parts.append(f"{len(report['commands'])} command blocks (not run)")
    cov = report.get("coverage", {})
    if cov.get("skip") or cov.get("unmarked"):
        parts.append(f"{cov.get('skip', 0)} skipped with a reason, {cov.get('unmarked', 0)} unmarked")
    words = report.get("words") or {}
    if words:
        longest = sorted(words.items(), key=lambda kv: -kv[1])[:3]
        parts.append(f"{sum(words.values())} words to read (longest: " + ", ".join(f"{k} {v}" for k, v in longest) + ")")
    cmap = report.get("map") or {}
    if cmap:
        parts.append(f"{cmap['code_files']} code files: {cmap['on_pages']} on pages, {cmap['under_map_rows']} under map rows, "
                     f"{len(cmap['on_none'])} on none" + "".join(f" (widest map row: {r}/, {n} files)" for r, n in cmap["largest_rows"][:1]))
    kept = len(report.get("accepted") or [])
    return (", ".join(parts) + f": {len(report['problems'])} problems, {len(report['warnings'])} warnings"
            + (f", {kept} kept with a reason" if kept else ""))


# ---------------------------------------------------------------- affected

MANIFEST = re.compile(r"(?i)(^|/)(package\.json|pyproject\.toml|setup\.(py|cfg)|requirements[^/]*\.txt|Pipfile|poetry\.lock|uv\.lock|"
                      r"Cargo\.toml|go\.mod|Gemfile|composer\.json|pom\.xml|build\.gradle(\.kts)?|[^/]+\.csproj|CMakeLists\.txt|Makefile|"
                      r"justfile|Dockerfile|docker-compose[^/]*\.ya?ml|compose\.ya?ml|\.env\.example|\.tool-versions|\.nvmrc|\.python-version|"
                      r"\.vscode/launch\.json|\.github/workflows/[^/]+)$")
CODE_EXT = set(BY_EXT) | {".py", ".pyi"}


def diff_ranges(repo: Path, base: str, path: str) -> list[tuple[int, int]]:
    """Changed line ranges on the current side of `git diff base -- path` (the working tree, uncommitted edits included)."""
    out = []
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git(repo, "diff", "-U0", base, "--", path, check=False), re.M):
        start, count = int(m.group(1)), int(m.group(2) or "1")
        out.append((start, start + max(count, 1) - 1))
    return out


def affected(repo: Path, wiki: Path, since: str | None) -> dict:
    """Which pages a change touches. Each page is compared with its own last commit (or with --since): a source file
    or symbol it names changed, a file it links to changed, or, for the README, setup, run or debug files changed.
    Changed code that no page names is listed against the wiki's last commit, so new code is not missed."""
    if not is_git(repo):
        raise SystemExit("affected needs a git repository")
    pages = collect_pages(repo, wiki)
    syms = Symbols(repo)
    head = git(repo, "rev-parse", "--short", "HEAD", check=False).strip() or "(no commits)"
    cache: dict[str, dict[str, str]] = {}

    def changes(base: str) -> dict[str, str]:
        """{path: A, M or D} between base and the working tree, untracked files included as A."""
        if base not in cache:
            res: dict[str, str] = {}
            for line in git(repo, "diff", "--name-status", "-M", base, check=False).splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    res[parts[-1]] = "A" if parts[0][0] == "R" else parts[0][0]
                    if parts[0][0] == "R":
                        res[parts[1]] = "D"
            for p in git(repo, "ls-files", "-o", "--exclude-standard").splitlines():
                res.setdefault(p, "A")
            cache[base] = res
        return cache[base]

    wiki_rel = posix(wiki, repo)
    wiki_base = since or git(repo, "log", "-1", "--format=%h", "--", wiki_rel, check=False).strip() or None
    out = {"head": head, "since": since, "wiki_base": wiki_base, "check": [], "edited": [], "front_page": [], "uncovered": [], "new_pages": []}
    covered: set[str] = set()
    mentions = log_mentions(repo, wiki)
    gone = sorted({ref.partition("#")[2].split(".")[-1] for p in pages for ref in p.sources
                   if ref.partition("#")[2] and not syms.find(ref)["ok"]})  # symbols some page names that no longer exist
    for page in pages:
        if page.kind in ("index", "log", "schema"):
            continue
        named = {s.partition("#")[0] for s in page.sources}
        covered |= named
        last, edited = baseline(repo, page, mentions)
        base = since or last
        if not base:
            out["new_pages"].append(page.label)
            continue
        ch = changes(base)
        reasons = []
        for ref in page.sources:
            path, _, symbol = ref.partition("#")
            if path not in ch:
                continue
            if ch[path] == "D":
                reasons.append(f"{path}: deleted or renamed")
            elif not symbol:
                reasons.append(f"{path}: changed")
            else:
                res = syms.find(ref)
                if not res["ok"]:
                    reasons.append(f"{ref}: symbol not found any more")
                elif any(a <= (res["end"] or res["line"]) and b >= res["line"] for a, b in diff_ranges(repo, base, path)):
                    reasons.append(f"{ref}: changed")
        for _, t in links(page.text):
            if is_external(t) or t.startswith("#"):
                continue
            try:
                rel = posix((page.path.parent / urllib.parse.unquote(t.partition("#")[0])).resolve(), repo)
            except ValueError:
                continue
            if rel in ch and rel not in named and not rel.endswith(".md"):
                reasons.append(f"{rel}: linked from the page, changed")
        if page.is_readme:
            reasons += [f"{p}: setup, run or debug file changed" for p in sorted(ch) if MANIFEST.search(p)]
        # the text can name a file or a symbol without listing it in sources or linking it
        reasons += [f"{p}: named in the text, deleted or renamed" for p, st in sorted(ch.items())
                    if st == "D" and p in page.text and f"{p}: deleted or renamed" not in reasons]
        reasons += [f"{name}: named in the text, no longer defined" for name in gone if re.search(rf"\b{re.escape(name)}\b", page.text)]
        if reasons:
            (out["edited"] if edited else out["check"]).append({"page": page.label, "base": base, "reasons": sorted(set(reasons))})
    if wiki_base:
        for path, status in sorted(changes(wiki_base).items()):
            if path.startswith(wiki_rel + "/"):
                continue
            if MANIFEST.search(path):
                out["front_page"].append(path)
            if Path(path).suffix.lower() in CODE_EXT and status != "D" and path not in covered:
                out["uncovered"].append(f"{path} ({'new' if status == 'A' else 'changed'})")
    return out


def print_affected(res: dict) -> None:
    print(f"HEAD {res['head']}; " + (f"compared with {res['since']}" if res["since"] else
          f"each page compared with its own last commit; the wiki was last committed in {res['wiki_base'] or '(never)'}"))
    groups = [("check", "Pages to update (code they describe changed after their last commit):"),
              ("edited", "Pages already edited in this change (confirm they cover these changes):")]
    for key, head in groups:
        if res[key]:
            print("\n" + head)
            for p in res[key]:
                print(f"  {p['page']}  (compared with {p['base']})")
                for r in p["reasons"]:
                    print(f"    - {r}")
    if not res["check"] and not res["edited"]:
        print("\nNo page names a changed file or symbol.")
    if res["front_page"]:
        print("\nSetup, run or debug files changed (check the README and the run-and-debug page): " + ", ".join(res["front_page"]))
    if res["uncovered"]:
        print("\nChanged code that no page names in its sources (it may need a page, a source entry, or an index line):")
        for u in res["uncovered"]:
            print(f"  - {u}")
    if res["new_pages"]:
        print("\nPages not committed yet: " + ", ".join(res["new_pages"]))


# ---------------------------------------------------------------- questions

ASK_EN = re.compile(r"(?i)^(how|why|what|where|which|when|who|whose|is|are|does|do|did|can|could|should|would|will|was|were|has|have|isn't|doesn't|don't)\b")
REQUEST = re.compile(r"(?i)^(can|could|would|will) (you|u)\b|^please\b|^(let's|lets)\b")  # asks to do something, not about the code
ASK_ZH = re.compile(r"(为什么|怎么|如何|哪里|哪个|哪些|什么|是否|能否|能不能|可不可以|多少|吗|呢)")
SECRET = re.compile(r"(?i)\b(?:sk|pk|rk|ghp|gho|github_pat|xox[abprs])[-_][A-Za-z0-9_\-]{12,}|\b[A-Za-z0-9+/_\-]{32,}\b")
CODE_LIKE = re.compile(r"[{};]|=>|[=!]==?|\?\?|^\s*[(.]|^\s*(export|import|const|let|var|def|return|function|class|if \(|for \(|<\w)|\w\(.*\)\s*\?$")


def within(path: str | None, repo: Path) -> bool:
    if not path:
        return False
    try:
        Path(path).resolve().relative_to(repo.resolve())
        return True
    except (ValueError, OSError):
        return False


def typed_messages(repo: Path, since: str | None):
    """(runtime, session id, ISO time, text) for every message a person typed in a Claude Code or Codex session whose
    working folder is inside this repository. Reads the local transcripts only; nothing leaves the machine."""
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    encoded = re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))
    if claude.is_dir():
        for d in sorted(claude.iterdir()):
            if not (d.name == encoded or d.name.startswith(encoded + "-")):
                continue
            for f in sorted(d.glob("*.jsonl")):
                for line in read(f).splitlines():
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    if e.get("type") != "user" or e.get("isMeta") or e.get("promptSource", "typed") != "typed" or not within(e.get("cwd"), repo):
                        continue
                    content = (e.get("message") or {}).get("content")
                    text = content if isinstance(content, str) else " ".join(
                        c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text")
                    ts = str(e.get("timestamp", ""))
                    if text and (not since or ts[:10] >= since):
                        yield "claude", str(e.get("sessionId", f.stem)), ts, text
    codex = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    if codex.is_dir():
        for f in sorted(codex.rglob("rollout-*.jsonl")):
            lines = read(f).splitlines()
            try:
                meta = json.loads(lines[0]).get("payload", {}) if lines else {}
            except ValueError:
                continue
            if not within(meta.get("cwd"), repo):
                continue
            for line in lines[1:]:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                p = e.get("payload") or {}
                if e.get("type") != "response_item" or p.get("type") != "message" or p.get("role") != "user":
                    continue
                text = " ".join(c.get("text", "") for c in p.get("content") or [] if isinstance(c, dict) and c.get("type") == "input_text")
                ts = str(e.get("timestamp", meta.get("timestamp", "")))
                if text and not text.lstrip().startswith(("<", "# AGENTS.md")) and (not since or ts[:10] >= since):
                    yield "codex", str(meta.get("id", f.stem)), ts, text


def question_sentences(text: str) -> list[str]:
    """The sentences of a message that ask something, as far as plain rules can tell. Commands, skill invocations and
    requests to do something are left out; secrets that look like keys or tokens are masked."""
    if text.lstrip().startswith(("/", "$", "<", "!")):
        return []
    out = []
    for part in re.split(r"(?<=[?？])\s+|\n+", text):
        s = re.sub(r"\s+", " ", part).strip(" -*>\t")
        if not s or len(s) > 300 or REQUEST.match(s) or s.count("`") > 6 or CODE_LIKE.search(s):
            continue  # pasted code (a ternary, `??`) ends in a question mark too
        ends = s.endswith(("?", "？"))
        if (ends and (ASK_EN.match(s) or ASK_ZH.search(s) or len(s.split()) >= 3)) or (ASK_ZH.search(s) and s.endswith(("吗", "呢"))):
            out.append(SECRET.sub("[masked]", s))
    return out


def qnorm(s: str) -> set[str]:
    words = re.findall(r"[a-z0-9_]+|[一-鿿]", s.lower())
    return {w for w in words if w not in {"the", "a", "an", "is", "are", "do", "does", "to", "of", "in", "it", "this", "that", "and", "or"}}


def similar(a: set[str], b: set[str]) -> bool:
    return bool(a and b) and len(a & b) / len(a | b) >= 0.6


def questions(repo: Path, wiki: Path, since: str | None) -> dict:
    """Questions people asked in sessions in this repository, grouped when they ask the same thing, most asked first;
    questions the wiki's questions.md already holds are left out."""
    answered = []
    qpage = wiki / "questions.md"
    if qpage.exists():
        answered = [qnorm(m) for m in re.findall(r"^#{2,3}\s+(.+?)\s*$", read(qpage), re.M)]
    groups: list[dict] = []
    seen_sessions, runtimes, skipped = set(), {"claude": set(), "codex": set()}, 0
    for runtime, session, ts, text in typed_messages(repo, since):
        seen_sessions.add((runtime, session))
        runtimes[runtime].add(session)
        for q in question_sentences(text):
            key = qnorm(q)
            if any(similar(key, a) for a in answered):
                skipped += 1
                continue
            g = next((g for g in groups if similar(key, g["key"])), None)
            if g is None:
                g = {"question": q, "key": key, "count": 0, "sessions": set(), "last": ""}
                groups.append(g)
            g["count"] += 1
            g["sessions"].add(f"{runtime}:{session}")
            g["last"] = max(g["last"], ts[:10])
    groups.sort(key=lambda g: (len(g["sessions"]), g["count"], g["last"]), reverse=True)  # asked most widely, then most often, then latest
    return {"sessions": len(seen_sessions), "claude_sessions": len(runtimes["claude"]), "codex_sessions": len(runtimes["codex"]),
            "since": since, "already_answered": skipped,
            "questions": [{"question": g["question"], "count": g["count"], "sessions": len(g["sessions"]), "last": g["last"],
                           "from": sorted(g["sessions"])} for g in groups]}


def print_questions(res: dict) -> None:
    print(f"{len(res['questions'])} question candidates from {res['sessions']} sessions in this repository "
          f"(Claude Code {res['claude_sessions']}, Codex {res['codex_sessions']})" + (f" since {res['since']}" if res["since"] else "") +
          (f"; {res['already_answered']} already in questions.md were left out" if res["already_answered"] else ""))
    for q in res["questions"]:
        print(f"  {q['count']}x in {q['sessions']} session(s), last {q['last'] or '?'}: {q['question']}")


# ---------------------------------------------------------------- viewer

EDITORS = {  # the same schemes as code-map's references/extraction.md section 10
    "vscode": "vscode://file/{abs_path}:{line}:{col}",
    "vscode-insiders": "vscode-insiders://file/{abs_path}:{line}:{col}",
    "cursor": "cursor://file/{abs_path}:{line}:{col}",
    "windsurf": "windsurf://file/{abs_path}:{line}:{col}",
}


def editor_template(name: str) -> str:
    if name in ("", "none"):
        return ""
    if name in EDITORS:
        return EDITORS[name]
    if name.startswith("jetbrains:"):
        return f"jetbrains://{name.split(':', 1)[1]}/navigate/reference?project={{project}}&path={{rel_path}}:{{line}}"
    return name


IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
EMBED_LIMIT = 2_000_000  # bytes: an image up to this size travels inside the one-file viewer; larger ones are linked


def page_images(repo: Path, pages: list[Page], link_large: bool) -> dict[str, str]:
    """{repository-relative path: data URI or file URI} for every raster image the pages show (img, picture source).
    The viewer is opened from wherever it was written, so relative image paths would not resolve there."""
    import base64
    out: dict[str, str] = {}
    for p in pages:
        targets = [t for _, t in links(p.text)] + re.findall(r"""\bsrcset\s*=\s*["']([^"'\s,]+)""", p.text)
        for t in targets:
            if is_external(t):
                continue
            f = (p.path.parent / urllib.parse.unquote(t.partition("#")[0])).resolve()
            kind = IMAGE_TYPES.get(f.suffix.lower())
            if not kind or not f.is_file():
                continue
            try:
                rel = posix(f, repo)
            except ValueError:
                continue
            if rel in out:
                continue
            if f.stat().st_size <= EMBED_LIMIT:
                out[rel] = f"data:{kind};base64," + base64.b64encode(f.read_bytes()).decode("ascii")
            elif link_large:
                out[rel] = f.as_uri()
    return out


def reader_notices(pages: list[Page], report: dict) -> dict[str, list[str]]:
    """{page id: the lint findings a reader of that page should know, in a reader's words}: code the page names that
    is gone, code that changed after the page was last checked, links that lead nowhere. The rest of the report
    (placeholders, diagrams to re-render, index and log format) is the maintainer's, and stays out of the viewer."""
    ids = {p.label: p.rel for p in pages}
    out: dict[str, list[str]] = {}
    for kind in ("problems", "warnings"):
        for f in report[kind]:
            msg, text = f["msg"], None
            if kind == "problems" and msg.startswith("source "):
                text = f"it names code that is no longer there: {msg[len('source '):].split(': ')[0]}"
            elif msg.startswith("broken link: "):
                text = f"a link leads nowhere: {msg[len('broken link: '):]}"
            elif msg.startswith("missing anchor: "):
                text = f"a link points to a section that is gone: {msg[len('missing anchor: '):]}"
            elif msg.startswith("sources changed after this page"):
                m = re.search(r"\): (.*?); update it", msg)
                text = "the code it describes changed after the page was last checked" + (f": {m.group(1)}" if m else "")
            if text and f["page"] in ids:
                out.setdefault(ids[f["page"]], []).append(text)
    return out


def viewer(repo: Path, wiki: Path, out: Path, editor: str, title: str | None, artifact: bool = False) -> str:
    """Write the one-file viewer. With `artifact`, write the copy meant for publishing as a claude.ai Artifact: no
    document wrapper (the platform adds its own), no editor links and no local paths, and the page's review comments
    on (select text, press Comment)."""
    if artifact:
        editor = "none"
    report = lint(repo, wiki)
    pages = collect_pages(repo, wiki)
    index = next((p for p in pages if p.wiki_rel == "index.md"), None)
    order: dict[str, int] = {}  # the sidebar follows the order the index lists its pages in
    for _, target in links(index.text) if index else []:
        path = target.partition("#")[0]
        if path and not is_external(path):
            try:
                order.setdefault(posix(index.path.parent / path, repo), len(order))
            except ValueError:  # a link out of the repository; the lint reports it
                pass
    data_pages = []
    for p in pages:
        data_pages.append({"id": p.rel, "title": p.title, "kind": p.kind, "updated": str(p.meta.get("updated", "") or ""),
                           "order": order.get(p.rel), "body": p.body,
                           "sources": [{"ref": s, "ok": report["sources"].get(s, {}).get("ok", False),
                                        "path": s.partition("#")[0], "line": report["sources"].get(s, {}).get("line")}
                                       for s in p.sources]})
    svgs = {}
    if (wiki / "diagrams").exists():
        svgs = {posix(svg, repo): SVG_STAMP.sub("", read(svg)).strip() for svg in sorted((wiki / "diagrams").glob("*.svg"))}
    template = editor_template(editor)
    images = page_images(repo, pages, link_large=bool(template))
    data = {
        "repo": repo.name, "wiki": posix(wiki, repo), "generated": date.today().isoformat(), "toolsVersion": TOOLS_VERSION,
        "editor": template, "repoRoot": repo.resolve().as_posix() if template else "",
        "notices": reader_notices(pages, report),
        "pages": data_pages, "svgs": svgs, "images": images,
        "symbols": {k: v["line"] for k, v in report["sources"].items() if v.get("ok")},
    }
    shell = read(HERE / "viewer_template.html")
    marked = read(HERE / "vendor" / "marked.min.js").replace("</script", "<\\/script")
    # KaTeX (about 640 kB with its fonts) only when a page has a ```math block to typeset
    has_math = any(info.split()[:1] == ["math"] for p in pages for _, _, info in fences(p.body.split("\n")))
    katex_js = read(HERE / "vendor" / "katex.min.js").replace("</script", "<\\/script") if has_math else ""
    katex_css = read(HERE / "vendor" / "katex.min.css").replace("</style", "<\\/style") if has_math else ""
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    name = title or (index.title if index and index.meta.get("title") else f"{repo.name} wiki")
    page = (shell.replace("__WIKI_TITLE__", html.escape(name))
                 .replace("/*MARKED*/", marked)
                 .replace("/*KATEX_CSS*/", katex_css)
                 .replace("/*KATEX*/", katex_js)
                 .replace("/*WIKI_DATA*/null", blob))
    if artifact:
        page = re.sub(r"(?is)\A\s*<!doctype html>\s*<html[^>]*>\s*<head>\s*", "", page)
        page = re.sub(r'(?i)<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", page)
        page = re.sub(r"(?i)</head>\s*<body>\s*", "", page, count=1)
        page = re.sub(r"(?i)\s*</body>\s*</html>\s*\Z", "\n", page)
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    shown = posix(out, repo) if out.is_relative_to(repo.resolve()) else str(out)
    return f"{shown}: {len(data_pages)} pages, {len(svgs)} diagrams; lint: {summary(report)}"



# ---------------------------------------------------------------- copy-tools

def copy_tools(dest: Path, force: bool, check_only: bool) -> int:
    """Copy these tools into a repository. A file someone edited after an earlier copy is kept unless --force, and
    tools.json records what was copied so the next copy can tell an edit from an old version."""
    manifest_path = dest / "tools.json"
    old = json.loads(read(manifest_path)) if manifest_path.exists() else {"files": {}}
    status, kept = [], 0
    if not check_only:
        dest.mkdir(parents=True, exist_ok=True)
    new_files = {}
    for name in TOOL_FILES:
        src, dst = HERE / name, dest / name
        new_hash = file_hash(src)
        new_files[name] = new_hash
        if not dst.exists():
            state = "new"
        else:
            cur = file_hash(dst)
            if cur == new_hash:
                state = "current"
            elif cur == old["files"].get(name):
                state = "older version"
            else:
                state = "edited here"
        status.append((name, state))
        if check_only or state == "current":
            continue
        if state == "edited here" and not force:
            kept += 1
            new_files[name] = old["files"].get(name, "")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for name, state in status:
        action = "" if check_only or state == "current" else (" -> kept (use --force to replace)" if state == "edited here" and not force else " -> copied")
        print(f"{state:14} {name}{action}")
    if not check_only:
        manifest_path.write_text(json.dumps({"tools_version": TOOLS_VERSION, "copied_by": "code-map wiki skill",
                                             "files": new_files}, indent=2) + "\n", encoding="utf-8")
        print(f"tools {TOOLS_VERSION} in {dest}" + (f"; {kept} edited file(s) kept" if kept else ""))
    else:
        print(f"installed: {old.get('tools_version', 'none')}, this copy: {TOOLS_VERSION}")
    return 0


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="wiki.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lint", "affected", "viewer"):
        s = sub.add_parser(name)
        s.add_argument("--repo", type=Path)
        s.add_argument("--wiki", type=Path)
        s.add_argument("--json", action="store_true")
        if name == "lint":
            s.add_argument("--run", action="store_true", help="execute the check:run blocks (README first)")
            s.add_argument("--in-place", action="store_true", help="run them in the working tree, not a clean checkout")
            s.add_argument("--timeout", type=int, default=600, help="seconds per command block")
            s.add_argument("--list-run", action="store_true", help="print the check:run blocks without running them")
            s.add_argument("--capture", type=Path, help="with --run: save each block's output in this folder (outside the repository)")
            s.add_argument("--strict", action="store_true", help="a command block neither checked nor skipped with a reason is a problem")
            s.add_argument("--clean-env", action="store_true", help="with --run: run with only system variables, as a newcomer would")
        if name == "affected":
            s.add_argument("--since", help="compare every page with this commit instead of its own last commit")
        if name == "viewer":
            s.add_argument("--out", type=Path)
            s.add_argument("--editor", default="vscode", help="vscode, vscode-insiders, cursor, windsurf, jetbrains:<ide>, a template, or none")
            s.add_argument("--title")
            s.add_argument("--artifact", action="store_true", help="write the copy to publish as a claude.ai Artifact, with review comments")
    q = sub.add_parser("questions", help="questions asked in Claude Code and Codex sessions in this repository")
    q.add_argument("--repo", type=Path)
    q.add_argument("--wiki", type=Path)
    q.add_argument("--since", help="YYYY-MM-DD: only messages from this day on")
    q.add_argument("--json", action="store_true")
    g = sub.add_parser("callgraph", help="a Mermaid call map from a Python function, for a page to start from")
    g.add_argument("start", help="path#function, for example src/app/run.py#main or src/app/engine.py#Engine.run")
    g.add_argument("--repo", type=Path)
    g.add_argument("--depth", type=int, default=3, help="call levels to follow from the start")
    g.add_argument("--max-nodes", type=int, default=30, help="stop adding boxes after this many")
    g.add_argument("--id", help="diagram id for the first line")
    g.add_argument("--table", action="store_true", help="print the calls as a `Caller | Calls` table instead of a diagram")
    f = sub.add_parser("fill", help="put captured outputs where a page marks <!-- check:output fill -->")
    f.add_argument("--capture", type=Path, required=True, help="the folder lint --run --capture wrote")
    f.add_argument("--repo", type=Path)
    f.add_argument("--wiki", type=Path)
    f.add_argument("--max-lines", type=int, default=40, help="keep the first and last lines of longer output")
    c = sub.add_parser("copy-tools")
    c.add_argument("dest", type=Path)
    c.add_argument("--force", action="store_true")
    c.add_argument("--check", action="store_true", help="report what would change, copy nothing")
    sub.add_parser("version")
    a = ap.parse_args(argv)

    if a.cmd == "version":
        print(TOOLS_VERSION)
        return 0
    if a.cmd == "copy-tools":
        return copy_tools(a.dest.resolve(), a.force, a.check)
    if a.cmd == "callgraph":
        repo = (a.repo or default_repo()).resolve()
        diagram, notes = callgraph(repo, a.start.replace("\\", "/"), a.depth, a.max_nodes, a.id, a.table)
        print(diagram)
        if notes:
            print("\nNot followed (method calls on objects, inherited methods, dynamic dispatch). Draw the ones that "
                  "matter by hand: solid when the caller calls it directly, dotted (-.->) with how it is reached otherwise.")
            print("\n".join("  " + n for n in notes))
        return 0
    repo = (a.repo or default_repo()).resolve()
    wiki = (repo / a.wiki).resolve() if a.wiki and not a.wiki.is_absolute() else (a.wiki or default_wiki(repo)).resolve()
    if a.cmd == "lint":
        if a.list_run:
            blocks = [b for p in collect_pages(repo, wiki) for b in run_blocks(p)[0]]
            for b in blocks:
                print(f"--- {b['page']}:{b['line']} ({b['shell']}, os={','.join(b['os'])}"
                      f"{', expected to exit ' + str(b['exit']) if b['exit'] else ''})\n{b['body']}")
            print(f"{len(blocks)} command blocks")
            return 0
        report = lint(repo, wiki, run=a.run, in_place=a.in_place, timeout=a.timeout,
                      capture=a.capture.resolve() if a.capture else None, strict=a.strict, clean_env=a.clean_env)
        if report.get("env_left_out") and not a.json:
            print("clean environment left out: " + ", ".join(report["env_left_out"]))  # names only, never values
        print(json.dumps(report, indent=2, ensure_ascii=False)) if a.json else print_lint(report)
        return 1 if report["problems"] else 0
    if a.cmd == "fill":
        res = fill(repo, wiki, a.capture.resolve(), a.max_lines)
        for r in res["filled"]:
            short = f", kept {r['kept']} of {r['lines']} lines" if r["kept"] < r["lines"] else ""
            print(f"filled {r['page']}:{r['line']}{short}")
        for m in res["missing"]:
            print(f"no capture for {m}: the block did not run (another OS, or a failed run before it)")
        print(f"{len(res['filled'])} filled, {len(res['missing'])} without a capture. Review each one: shorten it, keep "
              "what the reader compares, and change its label to say it was captured, with the date.")
        return 1 if res["missing"] else 0
    if a.cmd == "questions":
        res = questions(repo, wiki, a.since)
        print(json.dumps(res, indent=2, ensure_ascii=False)) if a.json else print_questions(res)
        return 0
    if a.cmd == "affected":
        res = affected(repo, wiki, a.since)
        print(json.dumps(res, indent=2, ensure_ascii=False)) if a.json else print_affected(res)
        return 0
    if a.cmd == "viewer":
        print(viewer(repo, wiki, (a.out if a.out and a.out.is_absolute() else repo / (a.out or Path(posix(wiki, repo)) / "viewer.html")),
                     a.editor, a.title, a.artifact))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
