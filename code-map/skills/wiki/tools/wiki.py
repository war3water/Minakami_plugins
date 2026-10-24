#!/usr/bin/env python3
"""Mechanical upkeep of a code wiki: lint, affected pages, viewer, tool copy.

Shipped by the code-map plugin's `wiki` skill and copied into the repository it documents, so anyone (a person, CI,
any coding agent) can run it without the plugin. Standard library only, Python 3.9 or later. The wiki's rules live in
<wiki>/SCHEMA.md; this script checks the parts of them a machine can check.

  python wiki.py lint       [--repo R] [--wiki W] [--run [--in-place] [--timeout S] [--capture DIR]] [--list-run] [--json]
  python wiki.py affected   [--repo R] [--wiki W] [--since REF] [--json]
  python wiki.py viewer     [--repo R] [--wiki W] [--out FILE] [--editor NAME|TEMPLATE|none] [--title T]
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

TOOLS_VERSION = "0.2.0"
HERE = Path(__file__).resolve().parent
TOOL_FILES = ["wiki.py", "wiki_browser.py", "viewer_template.html", "vendor/marked.min.js", "vendor/marked-LICENSE.txt"]
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
            out.update(ok=True, line=d[1], end=d[2], how=how)
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
    running for the page's later blocks). `<!-- check:output -->` above the next fenced block holds the output the
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
            oses = [o.strip().lower() for o in str(attrs.get("os", "any")).split(",")]
            last_run = {"page": page.label, "line": j + 1, "shell": SHELLS[lang], "os": oses, "body": body,
                        "background": bool(attrs.get("background")), "ready": attrs.get("ready") if attrs.get("ready") is not True else None,
                        "wait": int(attrs["wait"]) if str(attrs.get("wait", "")).isdigit() else None, "expect": None}
            blocks.append(last_run)
        elif kind == "output":
            if not last_run or last_run["background"]:
                errors.append((i + 1, "check:output has no check:run block above it on this page"))
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
        rx = re.compile("^" + ".*".join(re.escape(part) for part in re.split(r"…|\.\.\.", e)) + "$")
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
            cmd = ([bash, "-e", "-o", "pipefail", "-c", b["body"]] if b["shell"] == "bash" else
                   [pwsh, "-NoProfile", "-NonInteractive", "-Command", "$ErrorActionPreference = 'Stop'\n" + b["body"]])
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
                    elif r.returncode != 0:
                        res.update(status="failed", detail=f"exit {r.returncode}: {(r.stderr or r.stdout).strip()[-400:]}")
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
              "coverage": {"run": 0, "skip": 0, "unmarked": 0}}

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
            if not page.sources and page.kind in ("reference", "explanation", "how-to"):
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
            stamp = SVG_STAMP.search(read(svg)[:400])
            if not stamp or stamp.group(2) != block["hash"]:
                bad(page, block["line"], f"diagrams/{block['id']}.svg is older than its source (run wiki_browser.py render)")
            if f"diagrams/{block['id']}.svg" not in page.text:
                warn(page, block["line"], f"the page does not show diagrams/{block['id']}.svg")
        # placeholders left from a template
        for i, line in enumerate(prose_lines(page.text), 1):
            for ph in re.findall(r"\{\{[^}]+\}\}", line):
                warn(page, i, f"template placeholder left: {ph}")
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
    return ", ".join(parts) + f": {len(report['problems'])} problems, {len(report['warnings'])} warnings"


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


def viewer(repo: Path, wiki: Path, out: Path, editor: str, title: str | None) -> str:
    report = lint(repo, wiki)
    pages = collect_pages(repo, wiki)
    data_pages = []
    for p in pages:
        data_pages.append({"id": p.rel, "title": p.title, "kind": p.kind, "updated": str(p.meta.get("updated", "") or ""),
                           "body": p.body,
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
        "lint": {"summary": summary(report), "problems": report["problems"], "warnings": report["warnings"]},
        "pages": data_pages, "svgs": svgs, "images": images,
        "symbols": {k: v["line"] for k, v in report["sources"].items() if v.get("ok")},
    }
    shell = read(HERE / "viewer_template.html")
    marked = read(HERE / "vendor" / "marked.min.js").replace("</script", "<\\/script")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    index = next((p for p in pages if p.wiki_rel == "index.md"), None)
    name = title or (index.title if index and index.meta.get("title") else f"{repo.name} wiki")
    page = (shell.replace("__WIKI_TITLE__", html.escape(name))
                 .replace("/*MARKED*/", marked)
                 .replace("/*WIKI_DATA*/null", blob))
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
    repo = (a.repo or default_repo()).resolve()
    wiki = (repo / a.wiki).resolve() if a.wiki and not a.wiki.is_absolute() else (a.wiki or default_wiki(repo)).resolve()
    if a.cmd == "lint":
        if a.list_run:
            blocks = [b for p in collect_pages(repo, wiki) for b in run_blocks(p)[0]]
            for b in blocks:
                print(f"--- {b['page']}:{b['line']} ({b['shell']}, os={','.join(b['os'])})\n{b['body']}")
            print(f"{len(blocks)} command blocks")
            return 0
        report = lint(repo, wiki, run=a.run, in_place=a.in_place, timeout=a.timeout,
                      capture=a.capture.resolve() if a.capture else None, strict=a.strict, clean_env=a.clean_env)
        if report.get("env_left_out") and not a.json:
            print("clean environment left out: " + ", ".join(report["env_left_out"]))  # names only, never values
        print(json.dumps(report, indent=2, ensure_ascii=False)) if a.json else print_lint(report)
        return 1 if report["problems"] else 0
    if a.cmd == "affected":
        res = affected(repo, wiki, a.since)
        print(json.dumps(res, indent=2, ensure_ascii=False)) if a.json else print_affected(res)
        return 0
    if a.cmd == "viewer":
        print(viewer(repo, wiki, (a.out if a.out and a.out.is_absolute() else repo / (a.out or Path(posix(wiki, repo)) / "viewer.html")),
                     a.editor, a.title))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
