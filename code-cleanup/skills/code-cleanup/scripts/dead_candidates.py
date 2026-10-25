#!/usr/bin/env python
"""Dead-code + test-only-orphan candidate scanner (SKILL.md, "Deleting").

PYTHON ONLY. Lists, in the production source:

  ZERO_REF       top-level function / class whose NAME is never referenced outside its definition.
  TEST_ONLY      referenced ONLY by tests: the tests exercise dead production code.
                 Coverage reports these as covered, so it never flags them.
  ORPHAN_MODULE  a module no other production module imports (TEST_ONLY_MODULE: only tests import it).

CANDIDATES ONLY — deletes nothing. Name-based and biased toward LIVE (a shared name protects every same-named
def), so it UNDER-reports. It also tags the candidates most likely to be live anyway — the check in SKILL.md
("Deleting") is still yours:

  NAMED_IN(file)     the name (or the module's dotted path) appears in a non-Python file: config, docs,
                     data, scripts, crontab, CI, packaging metadata
  LOOKED_UP(file:n)  the defining module is looked up by name: getattr(module, <built string>),
                     vars(module) / dir(module) / module.__dict__, or vars() / globals() inside it
  DYNAMIC_IMPORT(file:n)  (modules) production code imports modules from computed strings
  SCRIPT             (modules) has an `if __name__ == "__main__":` block — run as `python -m ...`
  DECORATED          the definition is decorated (registration is likely)
  PUBLIC             listed in an __all__

LAYOUT-AGNOSTIC. Pass your project's real source/test dirs (the agent knows them from the project map) — that
is the reliable path. If you omit them the script AUTO-DETECTS: a src/app/lib/source layout, else top-level
packages (dirs with __init__.py), else the whole repo; it always adds scripts/tools/bin as production,
excludes tests + vendor dirs, and prints exactly what it scanned. It fails loud with guidance if it finds no
source. For non-Python repos, do the same check by hand (LSP "Find References", production vs test
references).

Usage:
    python scripts/dead_candidates.py [--root .] [--prod DIR ...] [--tests DIR ...] [--json out.json]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# `test`/`tests` as a whole word — matches test, tests, unit_tests, integration-test;
# NOT contest / latest / attestation. Auto-detect is conservative on purpose; pass
# --tests explicitly for nonstandard layouts (e.g. a dir named `testing`).
_TESTISH = re.compile(r"(?:^|[^a-z])tests?(?:[^a-z]|$)")
_VENDOR = {".git", ".venv", "venv", "env", ".env", "node_modules", "__pycache__",
           "build", "dist", ".tox", ".mypy_cache", ".pytest_cache", "site-packages"}
# non-Python files searched for names; binary formats are skipped
_TEXT_SKIP_DIRS = _VENDOR | {".agent_works", ".idea", ".vscode"}
_BINARY = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".tar", ".whl", ".so",
           ".dll", ".exe", ".db", ".sqlite", ".woff", ".woff2", ".ttf"}


def _resolve_tests(root: Path, explicit: list[str] | None) -> list[Path]:
    if explicit:
        return [root / d for d in explicit if (root / d).is_dir()]
    found = [root / d for d in ("tests", "test") if (root / d).is_dir()]
    seen = {p.resolve() for p in found}
    for p in sorted(root.iterdir()):
        if (p.is_dir() and p.name not in _VENDOR
                and _TESTISH.search(p.name.lower()) and p.resolve() not in seen):
            found.append(p)
    return found


def _resolve_prod(root: Path, explicit: list[str] | None, tests: list[Path]) -> list[Path]:
    if explicit:
        return [root / d for d in explicit if (root / d).is_dir()]
    prod: list[Path] = []
    for name in ("src", "app", "lib", "source"):  # 1) conventional source roots
        d = root / name
        if d.is_dir() and next(d.rglob("*.py"), None):
            prod.append(d)
    if not prod:  # 2) flat layout — top-level packages (have __init__.py)
        test_set = {t.resolve() for t in tests}
        prod = [p for p in sorted(root.iterdir())
                if p.is_dir() and (p / "__init__.py").is_file()
                and p.resolve() not in test_set and p.name not in _VENDOR]
    for name in ("scripts", "tools", "bin"):  # sibling tooling counts as production
        d = root / name
        if d.is_dir() and next(d.rglob("*.py"), None):
            prod.append(d)
    return prod or [root]  # 3) whole-repo fallback (tests/vendor filtered in _py_files)


def _py_files(dirs: list[Path], tests: list[Path]) -> list[Path]:
    test_roots = [str(t.resolve()) for t in tests]
    out: list[Path] = []
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if _VENDOR & set(p.parts):
                continue
            rp = str(p.resolve())
            # separator-bounded: `test` root must not swallow a sibling like `testbed`
            if any(rp == tr or rp.startswith(tr + os.sep) for tr in test_roots):  # never count tests as production
                continue
            out.append(p)
    return out


def _text_files(root: Path) -> list[tuple[Path, str]]:
    """Every readable non-Python text file under root (configs, docs, data, scripts, crontab, CI)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _TEXT_SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in _BINARY or p.suffix == ".py":
                continue
            try:
                if p.stat().st_size <= 1_000_000:
                    out.append((p, p.read_text(encoding="utf-8")))
            except (OSError, UnicodeDecodeError):
                continue
    return out


def _word_counts(files: list[Path]) -> Counter:
    counts: Counter = Counter()
    for f in files:
        try:
            counts.update(_WORD.findall(f.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):  # a non-UTF-8 file must not abort the whole scan
            continue
    return counts


def _parse(f: Path):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # don't echo lint warnings from scanned files
            return ast.parse(f.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        print(f"warning: skipping {f}: {exc}", file=sys.stderr)
        return None


def _module_name(path: Path) -> str:
    """Dotted import name, found by walking up through packages (dirs with __init__.py)."""
    parts = [] if path.stem == "__init__" else [path.stem]
    d = path.parent
    while (d / "__init__.py").is_file():
        parts.insert(0, d.name)
        d = d.parent
    return ".".join(parts)


def _collect_defs(prod_files: list[Path], trees: dict):
    """Return (defs: name -> [(file, line, decorated, kind)], public: set[name])."""
    defs: dict[str, list] = defaultdict(list)
    public: set[str] = set()
    for f in prod_files:
        tree = trees.get(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            # recognize __all__ as plain / annotated / augmented assignment
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = [node.target]
            else:
                targets = []
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                for el in getattr(node.value, "elts", []):
                    if isinstance(el, ast.Constant) and isinstance(el.value, str):
                        public.add(el.value)
        for node in ast.iter_child_nodes(tree):  # top-level definitions only
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                defs[node.name].append((f, node.lineno, bool(node.decorator_list), kind))
    return defs, public


def _scan_imports(f: Path, tree, modules: set[str]):
    """Return (modules this file imports, {module: lookup site line}, [dynamic-import lines])."""
    mod = _module_name(f)
    package = mod if f.stem == "__init__" else mod.rpartition(".")[0]
    imported: set[str] = set()
    aliases: dict[str, str] = {}  # local name -> module it is bound to
    lookups: dict[str, int] = {}
    dynamic: list[int] = []

    def lookup(name: str | None, line: int):
        target = mod if name is None else aliases.get(name)
        if target:
            lookups.setdefault(target, line)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                parts = a.name.split(".")
                imported.update(".".join(parts[:i]) for i in range(1, len(parts) + 1))
                aliases[a.asname or parts[0]] = a.name if a.asname else parts[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package.split(".") if package else []
                base_parts = base_parts[: len(base_parts) - node.level + 1]
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            if base:
                parts = base.split(".")
                imported.update(".".join(parts[:i]) for i in range(1, len(parts) + 1))
            for a in node.names:
                full = f"{base}.{a.name}" if base else a.name
                if full in modules:
                    imported.add(full)
                    aliases[a.asname or a.name] = full
        elif isinstance(node, ast.Call):
            fn, args = node.func, node.args
            if isinstance(fn, ast.Name):
                if fn.id == "getattr" and len(args) >= 2 and isinstance(args[0], ast.Name) \
                        and not isinstance(args[1], ast.Constant):
                    lookup(args[0].id, node.lineno)
                elif fn.id in ("vars", "dir") and len(args) == 1 and isinstance(args[0], ast.Name):
                    lookup(args[0].id, node.lineno)
                elif fn.id in ("vars", "globals") and not args:
                    lookup(None, node.lineno)
                elif fn.id == "__import__" and args and not isinstance(args[0], ast.Constant):
                    dynamic.append(node.lineno)
            elif isinstance(fn, ast.Attribute) and fn.attr == "import_module" and args \
                    and not isinstance(args[0], ast.Constant):
                dynamic.append(node.lineno)
        elif isinstance(node, ast.Attribute) and node.attr == "__dict__" and isinstance(node.value, ast.Name):
            lookup(node.value.id, node.lineno)
    return imported, lookups, dynamic


def _is_script(tree) -> bool:
    return any(isinstance(n, ast.If) and "__name__" in ast.dump(n.test) and "__main__" in ast.dump(n.test)
               for n in tree.body)


def main() -> None:
    ap = argparse.ArgumentParser(description="Find ZERO_REF / TEST_ONLY / ORPHAN_MODULE candidates (Python).")
    ap.add_argument("--root", default=".", help="repo root (default: current dir)")
    ap.add_argument("--prod", nargs="+",
                    help="source dirs (default: auto-detect src/app/lib/source or top-level packages)")
    ap.add_argument("--tests", nargs="+",
                    help="test dirs (default: auto-detect tests/, test/, and *test* dirs)")
    ap.add_argument("--json", help="optional path to write the candidate ledger as JSON")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    test_dirs = _resolve_tests(root, args.tests)
    prod_dirs = _resolve_prod(root, args.prod, test_dirs)
    prod_files = _py_files(prod_dirs, test_dirs)
    rel = lambda p: str(p.relative_to(root)).replace("\\", "/")
    if not prod_files:
        sys.exit(f"error: no production .py files found under {[rel(d) for d in prod_dirs]}.\n"
                 f"Pass --prod with your source dir(s), e.g.  --prod mypackage")
    test_files = _py_files(test_dirs, [])
    texts = _text_files(root)
    print(f"scanned prod: {[rel(d) for d in prod_dirs]} ({len(prod_files)} files) | "
          f"tests: {[rel(d) for d in test_dirs] or '(none)'} ({len(test_files)} files) | "
          f"other text files: {len(texts)}")

    trees = {f: _parse(f) for f in prod_files + test_files}
    modules = {_module_name(f): f for f in prod_files}
    defs, public = _collect_defs(prod_files, trees)
    prod_counts = _word_counts(prod_files)
    test_counts = _word_counts(test_files)

    prod_imports: set[str] = set()
    test_imports: set[str] = set()
    looked_up: dict[str, str] = {}  # module -> first lookup site
    dynamic_sites: list[str] = []
    for f in prod_files + test_files:
        if trees.get(f) is None:
            continue
        imported, lookups, dynamic = _scan_imports(f, trees[f], set(modules))
        is_test = f not in modules.values()
        (test_imports if is_test else prod_imports).update(imported - {_module_name(f)})
        if not is_test:
            for m, line in lookups.items():
                looked_up.setdefault(m, f"{rel(f)}:{line}")
            dynamic_sites += [f"{rel(f)}:{line}" for line in dynamic]

    def named_in(*needles: str) -> list[str]:
        pats = [re.compile(rf"(?<![\w.]){re.escape(n)}(?![\w])") for n in needles if n]
        return sorted({rel(p) for p, text in texts if any(pat.search(text) for pat in pats)})

    def tagged(tags: list[str], named: list[str]) -> list[str]:
        if named:
            tags.append(f"NAMED_IN({','.join(named[:3])}{',...' if len(named) > 3 else ''})")
        return tags

    candidates = []
    for name, sites in sorted(defs.items()):
        if name.startswith("__") and name.endswith("__"):
            continue  # dunder / protocol methods are framework-driven
        prod_refs = prod_counts.get(name, 0) - len(sites)  # references beyond the def lines
        test_refs = test_counts.get(name, 0)
        if prod_refs > 0:
            continue  # referenced in production -> LIVE (biased to live)
        verdict = "ZERO_REF" if test_refs == 0 else "TEST_ONLY"
        for f, line, decorated, kind in sites:
            tags = []
            if decorated:
                tags.append("DECORATED")
            if name in public:
                tags.append("PUBLIC")
            if _module_name(f) in looked_up:
                tags.append(f"LOOKED_UP({looked_up[_module_name(f)]})")
            candidates.append({"verdict": verdict, "name": name, "kind": kind, "file": rel(f), "line": line,
                               "test_refs": test_refs, "tags": tagged(tags, named_in(name))})

    for mod, f in sorted(modules.items()):
        if f.stem in ("__init__", "__main__") or mod in prod_imports:
            continue
        tags = []
        if trees.get(f) is not None and _is_script(trees[f]):
            tags.append("SCRIPT")
        if dynamic_sites:
            tags.append(f"DYNAMIC_IMPORT({dynamic_sites[0]})")
        candidates.append({"verdict": "TEST_ONLY_MODULE" if mod in test_imports else "ORPHAN_MODULE",
                           "name": mod, "kind": "module", "file": rel(f), "line": 1, "test_refs": 0,
                           "tags": tagged(tags, named_in(mod, rel(f)))})

    candidates.sort(key=lambda c: (c["verdict"], c["file"], c["line"]))
    print(f"defs scanned: {sum(len(v) for v in defs.values())} | modules: {len(modules)} | "
          f"candidates: {len(candidates)} ({dict(Counter(c['verdict'] for c in candidates))})")
    print("-- tagged candidates are probably live; verify every one before removal (SKILL.md Deletion rule) --")
    for c in candidates:
        tagstr = (" [" + ", ".join(c["tags"]) + "]") if c["tags"] else ""
        ref = f" test_refs={c['test_refs']}" if c["verdict"] == "TEST_ONLY" else ""
        print(f"{c['verdict']:16} {c['file']}:{c['line']}  {c['name']} ({c['kind']}){tagstr}{ref}")

    if args.json:
        Path(args.json).write_text(json.dumps(candidates, indent=2), encoding="utf-8")
        print(f"\nledger -> {args.json}")


if __name__ == "__main__":
    main()
