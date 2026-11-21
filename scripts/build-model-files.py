#!/usr/bin/env python3
"""Build prompt-audit's per-model guidance files from the per-provider entries sources.

Each prompt-audit/sources/<provider>-entries.md holds a Models table and model-specific entries, each written once
and starting with `- *Applies to:* <model>, <model>.`. This script writes one file per model name in the table (each
row's model and the models it also covers) to prompt-audit/references/providers/<provider>/<slug>.md. The slug is the
name in lowercase with spaces and dots turned into hyphens ("Opus 5.5" -> opus-5-5.md), so an audit can read the file
without looking it up first. Each file holds only the entries that name a model of its row, so an audit never sees
another model's advice.

Usage:
  python scripts/build-model-files.py           write the built files, delete built files no model asks for
  python scripts/build-model-files.py --check   change nothing; exit 1 if any built file is missing, stale, or extra

It also fails when an entry names a model the table doesn't list, when a row has no entries, or when a listed model
is missing from the provider file's own text (its Models table is what audits match names against).
Standard library only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "prompt-audit"
SOURCES = ROOT / "sources"
PROVIDERS = ROOT / "references" / "providers"
APPLIES = re.compile(r"^- \*Applies to:\* (.+?)\.\s+(?=\S)(.*)$")


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[ .]", "-", name.strip().lower()))


def read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def parse(provider, text):
    """Return (rows, sections, problems): rows = [(model, [also])]; sections = [(heading, [(names, body)])]."""
    problems, rows, sections = [], [], []
    current = None
    in_models = False
    for line in text.split("\n"):
        if line.startswith("## "):
            heading = line[3:].strip()
            in_models = heading == "Models"
            current = None if in_models else (heading, [])
            if current:
                sections.append(current)
            continue
        if in_models and line.startswith("|") and not line.startswith("|---") and not line.startswith("| Model |"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 2:
                problems.append(f"{provider}: bad Models row (want | Model | Also covers |): {line}")
                continue
            also = [] if cells[1] in ("", "—", "-") else [a.strip() for a in cells[1].split(",")]
            rows.append((cells[0], also))
        elif line.startswith("- *Applies to:*"):
            m = APPLIES.match(line)
            if not m or current is None:
                problems.append(f"{provider}: cannot read entry (or entry outside a section): {line[:80]}")
                continue
            current[1].append(([n.strip() for n in m.group(1).split(",")], m.group(2).strip()))
    return rows, sections, problems


def build(provider, rows, sections):
    known = {name for model, also in rows for name in [model] + also}
    problems, files = [], {}
    for heading, entries in sections:
        for names, _ in entries:
            for n in names:
                if n not in known:
                    problems.append(f"{provider}: entry under '{heading}' names '{n}', which the Models table does not list")
    for model, also in rows:
        covered = [model] + also
        body, count = [], 0
        for heading, entries in sections:
            mine = [b for names, b in entries if any(n in covered for n in names)]
            if mine:
                body += [f"## {heading}", ""] + [f"- {b}" for b in mine] + [""]
                count += len(mine)
        if count == 0:
            problems.append(f"{provider}: Models row '{model}' has no entries; remove the row")
        for name in covered:
            file = slug(name)
            if file in files:
                problems.append(f"{provider}: two models map to the file name '{file}.md'")
            head = [f"<!-- Built by scripts/build-model-files.py from prompt-audit/sources/{provider}-entries.md. "
                    f"Do not edit by hand: edit the source and rebuild. -->",
                    "",
                    f"# {name}: model guidance",
                    "",
                    f"Applies only to {name}. Read it with `providers/{provider}.md`; where an entry here disagrees with that "
                    f"file or with `general.md`, the entry here wins. Cite as `[ref: providers/{provider}/{file}.md §<section>]`.",
                    ""]
            files[file] = "\n".join(head + body).rstrip("\n") + "\n"
    return files, problems


def plan_is_clean():
    for src in sorted(SOURCES.glob("*-entries.md")):
        provider = src.name[: -len("-entries.md")]
        rows, sections, p = parse(provider, read(src))
        _, p2 = build(provider, rows, sections)
        if p or p2:
            return False
    return True


def main():
    # Any problem makes this a check run: nothing is written or deleted from an inconsistent source.
    check = "--check" in sys.argv[1:] or not plan_is_clean()
    problems, changes = [], []
    for src in sorted(SOURCES.glob("*-entries.md")):
        provider = src.name[: -len("-entries.md")]
        rows, sections, p = parse(provider, read(src))
        problems += p
        files, p = build(provider, rows, sections)
        problems += p
        provider_file = PROVIDERS / f"{provider}.md"
        if not provider_file.exists():
            problems.append(f"{provider}: {provider_file.relative_to(ROOT)} is missing")
        else:
            ptext = read(provider_file)
            for model, also in rows:
                for name in [model] + also:
                    if name not in ptext:
                        problems.append(f"{provider}: '{name}' is not in {provider_file.relative_to(ROOT)}")
                    if f"providers/{provider}/{slug(name)}.md" not in ptext:
                        problems.append(f"{provider}: the Models table does not give providers/{provider}/{slug(name)}.md for '{name}'")
        outdir = PROVIDERS / provider
        wanted = {f"{f}.md" for f in files}
        for name, content in files.items():
            path = outdir / f"{name}.md"
            if not path.exists() or read(path) != content:
                changes.append(f"{'stale or missing' if check else 'wrote'}: {path.relative_to(ROOT)}")
                if not check:
                    outdir.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8", newline="\n")
        if outdir.exists():
            for path in sorted(outdir.glob("*.md")):
                if path.name not in wanted:
                    changes.append(f"{'extra' if check else 'deleted'}: {path.relative_to(ROOT)}")
                    if not check:
                        path.unlink()
    for line in changes:
        print(line)
    for line in problems:
        print("problem:", line, file=sys.stderr)
    if problems or (check and changes):
        sys.exit(1)
    print("model files are current" if not changes else f"{len(changes)} model file change(s)")


if __name__ == "__main__":
    main()
