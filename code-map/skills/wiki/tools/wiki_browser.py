#!/usr/bin/env python3
"""The parts of wiki upkeep that need a browser: render Mermaid diagrams to SVG, and test the viewer like a reader.

  python wiki_browser.py render       [--repo R] [--wiki W] [--mermaid FILE] [--renderer auto|playwright|cli]
  python wiki_browser.py check-viewer FILE

Why render at all: GitHub renders Mermaid, but VS Code's built-in Markdown preview and many viewers show the raw code.
Pages therefore show the rendered SVG and keep the Mermaid source beside it in a <details> block. Each SVG is written at
its natural size on a white ground, so a Markdown preview neither stretches it to its column nor shows dark text on a
dark theme. Rendering is also the only real syntax check: a diagram that does not parse fails here, not in a reader's
browser.

Which browser, in order: Python Playwright with its own Chromium; Playwright driving an installed Edge or Chrome;
without Playwright, an installed Chrome, Edge or Chromium run headless from the command line. Nothing is installed.
Mermaid itself (pinned version, checked by SHA-256) is downloaded once into a user cache folder, or taken from
--mermaid or WIKI_MERMAID. Exit codes: 0 ok, 1 a diagram or check failed, 3 no browser or Mermaid available.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki  # noqa: E402  (the same folder: page scanning and diagram hashing are shared with the lint)

MERMAID_VERSION = "11.4.1"
MERMAID_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
MERMAID_SHA256 = "a43bc1afd446f9c4cc66ac5dd45d02e8d65e26fc5344ec0ef787f88d6ddb6f9e"
NO_BROWSER = 3
# The neutral theme draws chart bars, lines and pie slices in pale greys; charts get a palette that reads on white.
CHART_COLORS = ["#2f6db3", "#d9822b", "#3a9a5b", "#c0504d", "#7b5ea7", "#6b7a89"]
# Spacing a little tighter than Mermaid's (50 and 50) keeps more diagrams within a Markdown column (COLUMN_PX).
# Measured and drawn in the same family, so a label fits the box Mermaid sized for it.
FONT = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'
STYLE_JS = Path(__file__).resolve().parent / "diagram_style.js"
# What the theme variables of the other kinds (KIN_VARIABLES) cannot say. Mermaid sizes a note's box for words a
# little smaller than it then draws, so the words are drawn smaller; the words on a line sit on white, not on a patch.
KIN_CSS = (".noteText, .noteText > tspan { font-size: 14px !important; } "
           ".statediagram .edgeLabel rect, .classDiagram .edgeLabel rect, .labelBkg, .er.relationshipLabelBox { fill: #ffffff; opacity: .92; } "
           ".packetBlock { fill: #eef0fe; stroke: #4f46e5; stroke-width: 1.5px; }")
MERMAID_INIT = ('mermaid.initialize({startOnLoad: false, theme: "neutral", securityLevel: "strict", htmlLabels: false, '
                'flowchart: {htmlLabels: false, nodeSpacing: 30, rankSpacing: 40}, '
                'sequence: {actorFontFamily: \'' + FONT + '\', noteFontFamily: \'' + FONT + '\', messageFontFamily: \'' + FONT + '\'}, '
                'themeCSS: "' + KIN_CSS + '", themeVariables: {fontFamily: \'' + FONT + '\', xyChart: {plotColorPalette: "' + ", ".join(CHART_COLORS) + '"}, '
                + ", ".join(f'pie{i + 1}: "{c}"' for i, c in enumerate(CHART_COLORS)) + '}});')
# About the width of the Markdown column on GitHub and in VS Code's preview: a wider diagram is shrunk to fit, and its
# labels with it. Mermaid sets them at 16 px; below three quarters of that they are hard to read.
COLUMN_PX = 860
LEGIBLE_PX = round(COLUMN_PX / 0.75)
SVG_HEAD = re.compile(r"<svg\b[^>]*>")
VIEWBOX = re.compile(r'viewBox="([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)"')


def fit_svg(svg: str) -> tuple[str, float]:
    """(the SVG at its natural size on a white ground, its natural width). Mermaid writes width="100%" and no height,
    so a Markdown preview, which shows the file as an image, stretches or squeezes it to its column; and its ground is
    transparent, so a dark theme puts its dark text on a dark page. The viewer corrects both itself; other readers
    only get what the file says."""
    head = SVG_HEAD.search(svg)
    box = VIEWBOX.search(head.group(0)) if head else None
    if not box:
        return svg, 0.0
    x, y, w, h = (float(v) for v in box.groups())
    tag = re.sub(r'\s(?:width|height)="[^"]*"', "", head.group(0)[:-1]).rstrip("/ ")
    tag += f' width="{math.ceil(w)}" height="{math.ceil(h)}">'
    ground = f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="#ffffff"/>'
    return svg[:head.start()] + tag + ground + svg[head.end():], w


# Mermaid keeps the boxes of a group together, and when calls cross the groups it sets the groups out like a staircase
# with most of the picture empty. Such a picture is laid out a second time without its groups; when that is well under
# the size (0.6 of the area), it is the one kept, and diagram_style.js shows each group by colour.
RENDER_ONE = """async ([id, src, look]) => {
  try { let r = await mermaid.render("wiki-" + id, src), flat = false;
        if (look && look.flat) {
          const area = s => { const m = /viewBox="[-\\d.]+[ ,]+[-\\d.]+[ ,]+([\\d.]+)[ ,]+([\\d.]+)"/.exec(s); return m ? m[1] * m[2] : 0; };
          const f = await mermaid.render("wiki-" + id + "-flat", look.flat);
          if (area(f.svg) && area(f.svg) < 0.6 * area(r.svg)) { r = f; flat = true; }
        }
        return {ok: true, svg: look && window.wikiDress ? window.wikiDress(r.svg, Object.assign({}, look, {flat: flat})) : r.svg}; }
  catch (e) { document.querySelectorAll('[id^="dwiki-"], [id^="wiki-"]').forEach(n => n.remove());
              return {ok: false, error: String(e && e.message || e)}; } }"""


class Unavailable(Exception):
    """No browser or no Mermaid: the diagrams cannot be checked on this machine."""


def cache_dir() -> Path:
    if os.environ.get("WIKI_CACHE"):
        return Path(os.environ["WIKI_CACHE"])
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "code-map-wiki"
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "code-map-wiki"


def mermaid_file(explicit: str | None) -> Path:
    given = explicit or os.environ.get("WIKI_MERMAID")
    if given:
        path = Path(given)
        if not path.exists():
            raise Unavailable(f"Mermaid file not found: {path}")
        return path
    cached = cache_dir() / f"mermaid-{MERMAID_VERSION}.min.js"
    if cached.exists() and wiki.sha256(cached.read_bytes()) == MERMAID_SHA256:
        return cached
    try:
        with urllib.request.urlopen(MERMAID_URL, timeout=60) as r:
            data = r.read()
    except OSError as e:
        raise Unavailable(f"Mermaid {MERMAID_VERSION} is not cached and could not be downloaded ({e}). "
                          f"Allow network access once, or pass --mermaid <path to mermaid.min.js>.") from e
    if wiki.sha256(data) != MERMAID_SHA256:
        raise Unavailable(f"the downloaded Mermaid file does not match the pinned SHA-256; not used ({MERMAID_URL})")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return cached


def browser_binary() -> str | None:
    """An installed Chrome, Edge or Chromium (WIKI_BROWSER overrides)."""
    if os.environ.get("WIKI_BROWSER"):
        return os.environ["WIKI_BROWSER"]
    for name in ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    candidates = []
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidates += [Path(base) / "Google/Chrome/Application/chrome.exe", Path(base) / "Microsoft/Edge/Application/msedge.exe",
                           Path(base) / "Chromium/Application/chrome.exe"]
    candidates += [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                   Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                   Path("/Applications/Chromium.app/Contents/MacOS/Chromium")]
    return next((str(c) for c in candidates if c.exists()), None)


def launch(p):
    """Playwright's own Chromium, else an installed Edge or Chrome through Playwright. (browser, label)"""
    errors = []
    for kw, label in (({}, "Playwright Chromium"), ({"channel": "msedge"}, "Edge via Playwright"), ({"channel": "chrome"}, "Chrome via Playwright")):
        try:
            return p.chromium.launch(**kw), label
        except Exception as e:  # missing executable, wrong channel
            errors.append(f"{label}: {str(e).splitlines()[0]}")
    raise Unavailable("Playwright is installed but no browser started: " + "; ".join(errors))


def render_playwright(jobs: list[tuple[str, str, dict | None]], mermaid: Path) -> tuple[list[dict], str]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser, label = launch(p)
        try:
            page = browser.new_page()
            page.set_content("<!doctype html><html><head><meta charset='utf-8'></head><body></body></html>")
            page.add_script_tag(path=str(mermaid))
            page.add_script_tag(path=str(STYLE_JS))
            page.evaluate(MERMAID_INIT)
            return [dict(page.evaluate(RENDER_ONE, [i, s, look]), id=i) for i, s, look in jobs], label
        finally:
            browser.close()


def render_cli(jobs: list[tuple[str, str, dict | None]], mermaid: Path) -> tuple[list[dict], str]:
    """No Playwright: load a page that renders every diagram into the DOM, and read it back with --dump-dom."""
    exe = browser_binary()
    if not exe:
        raise Unavailable("no Playwright and no Chrome, Edge or Chromium found")
    with tempfile.TemporaryDirectory(prefix="wiki-render-") as tmp:
        tmpd = Path(tmp)
        shutil.copy(mermaid, tmpd / "mermaid.min.js")
        shutil.copy(STYLE_JS, tmpd / "diagram_style.js")
        jobs_js = json.dumps(jobs).replace("</", "<\\/")
        (tmpd / "render.html").write_text(f"""<!doctype html><html><head><meta charset="utf-8"></head><body>
<pre id="out"></pre><script src="mermaid.min.js"></script><script src="diagram_style.js"></script><script>
{MERMAID_INIT}
const one = {RENDER_ONE};
(async () => {{ const res = []; for (const job of {jobs_js}) res.push(Object.assign(await one(job), {{id: job[0]}}));
  document.getElementById("out").textContent = "WIKI-RESULT-BEGIN" + JSON.stringify(res) + "WIKI-RESULT-END"; }})();
</script></body></html>""", encoding="utf-8")
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files",
               f"--user-data-dir={tmpd / 'profile'}", "--virtual-time-budget=120000", "--dump-dom", (tmpd / "render.html").as_uri()]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise Unavailable(f"could not run {exe}: {e}") from e
        out = r.stdout
        if "WIKI-RESULT-BEGIN" not in out:
            raise Unavailable(f"{Path(exe).name} --dump-dom returned no result (exit {r.returncode}): {(r.stderr or out).strip()[-300:]}")
        blob = out.split("WIKI-RESULT-BEGIN", 1)[1].split("WIKI-RESULT-END", 1)[0]
        return json.loads(html.unescape(blob)), f"{Path(exe).name} headless"


# What a flowchart's source says about itself, handed to diagram_style.js, which draws it. The source stays plain text
# that any Markdown viewer renders: its groups are subgraphs, `%% key: <node id>` names the box to notice,
# `class <ids> stop` and `class <ids> ok` name the ends that refuse and the ends that succeed, and
# `%% legend: thick = ...; dashed = ...` says what the arrow kinds stand for. A source that styles itself is left alone.
LEGEND_WORDS = ("key", "thick", "solid", "dashed", "stop", "ok")
LABEL = re.compile(r'(?<![\w])([A-Za-z_][\w-]*)\s*(?:\[\[|\[\(|\(\[|\(\(|\{\{|\[|\(|\{)\s*"([^"]*)"')
BREAK = re.compile(r"<br\s*/?>")
CALL_BOX = re.compile(r'"([\w./\\-]+\.\w+):\s+([^"<]+)"')
ASK = re.compile(r'(?<![\w{])([A-Za-z_][\w-]*)\{(?!\{)\s*("[^"]*"|[^{}"]+?)\s*\}(?!\})')


def diagram_legend(source: str) -> dict[str, str]:
    line = re.search(r"^\s*%%\s*legend:\s*(.+)$", source, re.M)
    pairs = (part.split("=", 1) for part in line.group(1).split(";") if "=" in part) if line else ()
    return {k.strip().lower(): v.strip() for k, v in pairs if k.strip().lower() in LEGEND_WORDS and v.strip()}


NODE_ID = re.compile(r"\s*([A-Za-z_][\w-]*)")


def returning(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """(the lines with every dashed arrow that comes back turned round, those arrows as [from, to] as now written).
    A dashed arrow comes back when the box it points at already leads to the box it leaves: the result of a call, an
    answer to a request. Laid out as written, it pulls its source below its target and the picture's rows fall apart;
    turned round it follows the flow, and diagram_style.js puts the head back on the right end."""
    forward: dict[str, set[str]] = {}
    dashed = []
    for n, line in enumerate(lines):
        if line.lstrip().startswith("%%"):
            continue
        parts = wiki.ARROW.split(line)
        ends = [[m.group(1) for m in map(NODE_ID.match, seg.split("&")) if m] for seg in parts[0::2]]
        for i, arrow in enumerate(parts[1::2]):
            if "-." in arrow:
                if len(parts) == 3 and len(ends[0]) == 1 and len(ends[1]) == 1:
                    dashed.append((n, ends[0][0], ends[1][0]))
            else:
                for a in ends[i]:
                    forward.setdefault(a, set()).update(ends[i + 1])

    def leads(a: str, b: str) -> bool:
        seen, stack = {a}, [a]
        while stack:
            for nxt in forward.get(stack.pop(), ()):
                if nxt == b:
                    return True
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    out, turned = list(lines), []
    for n, a, b in dashed:
        if leads(b, a):
            left, arrow, right = wiki.ARROW.split(lines[n])
            pad = left[:len(left) - len(left.lstrip())]
            out[n] = f"{pad}{right.strip()} {arrow} {left.strip()}"
            turned.append([b, a])
    return out, turned


SUBGRAPH = re.compile(r'^\s*subgraph\s+(?:([A-Za-z_][\w-]*)\s*\[\s*"?([^"\]]*)"?\s*\]|"?([^"]+?)"?\s*$)')


def ungrouped(lines: list[str]) -> tuple[str, dict[str, int], list[str]] | None:
    """(the source without its subgraphs, each box's group, the groups' names), or None when the picture has no
    groups or an arrow ends on a group, which cannot be drawn without it."""
    flat, groups, names, ids, stack = [], {}, [], set(), []
    for line in lines:
        head = SUBGRAPH.match(line)
        if head:
            ids.add(head.group(1) or head.group(3).strip())
            names.append((head.group(2) or head.group(3) or head.group(1)).strip())
            stack.append(len(names) - 1)
        elif stack and re.match(r"^\s*end\s*$", line):
            stack.pop()
        elif stack and re.match(r"^\s*direction\b", line):
            continue
        else:
            flat.append(line)
            if not line.lstrip().startswith(("%%", "class ", "click ")):
                for seg in wiki.ARROW.split(re.sub(r'"[^"]*"', '""', line))[0::2]:
                    for m in filter(None, map(NODE_ID.match, seg.split("&"))):
                        if m.group(1) in ids:
                            return None
                        if stack:
                            groups.setdefault(m.group(1), stack[-1])
    return ("\n".join(flat) + "\n", groups, names) if names else None


# The kinds other than a flowchart keep Mermaid's own drawing, which suits each of them (lifelines, state boxes,
# table-like entities), in the colours and type of the flowcharts, so a wiki's pictures read as one family whatever
# their form. A note is the highlight in every kind, in the colour of a flowchart's marked box.
KIN = {"ink": "#0f172a", "muted": "#475569", "line": "#64748b", "faint": "#94a3b8", "soft": "#f1f5f9", "box": "#ffffff",
       "tint": "#eef0fe", "edge": "#4f46e5", "tint2": "#e6f3fb", "edge2": "#0369a1", "note": "#fff4e6", "key": "#ea580c",
       "noteInk": "#7c2d12"}
KIN_SCALE = [("#eef0fe", "#4f46e5"), ("#e6f3fb", "#0369a1"), ("#fdf5e4", "#b45309"), ("#e8f7ef", "#047857"),
             ("#fcecf2", "#be185d"), ("#e5f5f5", "#0f766e")]
KIN_VARIABLES = {
    "fontSize": "15px", "background": "#ffffff", "textColor": KIN["ink"], "titleColor": KIN["ink"],
    "primaryColor": KIN["tint"], "primaryBorderColor": KIN["edge"], "primaryTextColor": KIN["ink"],
    "secondaryColor": KIN["tint2"], "secondaryBorderColor": KIN["edge2"], "secondaryTextColor": KIN["ink"],
    "tertiaryColor": KIN["soft"], "tertiaryBorderColor": KIN["faint"], "tertiaryTextColor": KIN["ink"],
    "lineColor": KIN["line"], "mainBkg": KIN["tint"], "nodeBorder": KIN["edge"], "edgeLabelBackground": "#ffffff",
    "noteBkgColor": KIN["note"], "noteBorderColor": KIN["key"], "noteTextColor": KIN["noteInk"],
    # sequence
    "actorBkg": KIN["tint"], "actorBorder": KIN["edge"], "actorTextColor": KIN["ink"], "actorLineColor": KIN["faint"],
    "signalColor": KIN["muted"], "signalTextColor": KIN["ink"], "labelBoxBkgColor": KIN["soft"],
    "labelBoxBorderColor": KIN["faint"], "labelTextColor": KIN["muted"], "loopTextColor": KIN["muted"],
    "activationBkgColor": KIN["tint2"], "activationBorderColor": KIN["edge2"], "sequenceNumberColor": "#ffffff",
    # state
    "stateBkg": KIN["tint"], "stateLabelColor": KIN["ink"], "compositeBackground": "#ffffff",
    "compositeTitleBackground": KIN["soft"], "compositeBorder": KIN["faint"], "transitionColor": KIN["line"],
    "transitionLabelColor": KIN["muted"], "specialStateColor": KIN["ink"], "innerEndBackground": "#ffffff",
    "altBackground": KIN["soft"],
    # entities and classes
    "attributeBackgroundColorOdd": "#ffffff", "attributeBackgroundColorEven": "#f8fafc", "classText": KIN["ink"],
    # charts and the rest
    "xyChart": {"plotColorPalette": ", ".join(CHART_COLORS), "titleColor": KIN["ink"], "xAxisLabelColor": KIN["muted"],
                "yAxisLabelColor": KIN["muted"], "xAxisTitleColor": KIN["muted"], "yAxisTitleColor": KIN["muted"],
                "xAxisLineColor": KIN["faint"], "yAxisLineColor": KIN["faint"], "xAxisTickColor": KIN["faint"],
                "yAxisTickColor": KIN["faint"]},
    "packet": {"blockFillColor": KIN["tint"], "blockStrokeColor": KIN["edge"], "blockStrokeWidth": "1.5",
               "labelColor": KIN["ink"], "startByteColor": KIN["muted"], "endByteColor": KIN["muted"],
               "titleColor": KIN["muted"]},
    **{f"pie{i + 1}": c for i, c in enumerate(CHART_COLORS)},
    **{f"cScale{i}": tint for i, (tint, _) in enumerate(KIN_SCALE)},
    **{f"cScaleLabel{i}": KIN["ink"] for i in range(len(KIN_SCALE))},
    **{f"cScaleInv{i}": edge for i, (_, edge) in enumerate(KIN_SCALE)},
}
KIN_CONFIG = {
    "theme": "base", "themeVariables": KIN_VARIABLES,
    # one row of participants, each as wide as its words; a note wraps inside the space it has (see kin_source)
    "sequence": {"mirrorActors": False, "wrap": False, "messageMargin": 34, "noteMargin": 12, "boxMargin": 8,
                 "actorMargin": 36, "width": 170},
    "state": {"nodeSpacing": 40, "rankSpacing": 44}, "class": {"nodeSpacing": 40, "rankSpacing": 50},
    "er": {"layoutDirection": "TB", "minEntityWidth": 120, "entityPadding": 12},
    "timeline": {"disableMulticolor": False}, "packet": {"bitsPerRow": 32, "rowHeight": 34, "paddingY": 14},
}
# Where these kinds print a label's quotes as written (a flowchart needs them, so a page tends to write them everywhere).
QUOTED_TAIL = re.compile(r'^(.*?:\s*)"([^"]*)"\s*$')
QUOTED_WORD = {
    "sequence": re.compile(r'^(\s*(?:(?:participant|actor)\s+\S+\s+as|loop|alt|else|opt|par|and|critical|option|break)\s+)"([^"]*)"\s*$'),
    "timeline": re.compile(r'^(\s*(?:title|section)\s+)"([^"]*)"\s*$'),
    "gantt": re.compile(r'^(\s*(?:title|section)\s+)"([^"]*)"\s*$'),
    "journey": re.compile(r'^(\s*(?:title|section)\s+)"([^"]*)"\s*$'),
    "packet": re.compile(r'^(\s*title\s+)"([^"]*)"\s*$'),
}


SEQ_NOTE = re.compile(r"^(\s*Note\s+over\s+[^:,]+,[^:]+:\s*)(?!wrap:|nowrap:)", re.I)


def kin_source(source: str, kind: str) -> str:
    """The source of a picture that is no flowchart, as it is laid out: in the family's colours, its labels unquoted."""
    lines = []
    for line in source.split("\n"):
        if not line.lstrip().startswith("%%"):
            if kind in ("sequence", "state", "class"):
                line = QUOTED_TAIL.sub(r"\1\2", line)
            if kind in QUOTED_WORD:
                line = QUOTED_WORD[kind].sub(r"\1\2", line)
            if kind == "sequence":  # a note across participants wraps inside its box, where Mermaid would run it out
                line = SEQ_NOTE.sub(r"\1wrap: ", line)
        lines.append(line)
    return "%%{init: " + json.dumps(KIN_CONFIG) + "}%%\n" + "\n".join(lines)


def diagram_look(source: str) -> tuple[str, dict | None]:
    """(the source to lay out, what to tell diagram_style.js), or (the source, None) for a picture drawn as it is."""
    kind = wiki.diagram_kind(source)
    if kind != "flowchart":
        return (kin_source(source, kind) if kind != "other" else source), None
    if re.search(r"^\s*(style|classDef|linkStyle)\b", source, re.M):
        return source, None
    key = re.search(r"^\s*%%\s*key:\s*([A-Za-z_][\w-]*)", source, re.M)
    # a question is drawn as a flat six-sided box: Mermaid's diamond grows with its text until it fills the picture
    asks, lines = [], []
    for line in source.split("\n"):
        if not line.lstrip().startswith("%%"):
            asks += [m.group(1) for m in ASK.finditer(line)]
            line = ASK.sub(r"\1{{\2}}", line)
        lines.append(line)
    lines, turned = returning(lines)
    # a call map's boxes are `file: function` in the source, which the lint reads; drawn, the function comes first
    # and its file sits under it, and boxes of one file share a colour unless the page grouped them itself
    calls = bool(re.search(r"^\s*%%\s*calls\b", source, re.M))
    by_file: dict[str, int] = {}
    if calls:
        files: dict[str, int] = {}
        for m in LABEL.finditer(source):
            box = CALL_BOX.fullmatch('"' + m.group(2) + '"')
            if box:
                by_file[m.group(1)] = files.setdefault(box.group(1), len(files))
        lines = [ln if ln.lstrip().startswith("%%") else CALL_BOX.sub(lambda m: f'"{m.group(2).strip()}<br/>{m.group(1)}"', ln)
                 for ln in lines]
    if asks:
        lines = [ln for ln in lines if ln.strip()] + ["    class " + ",".join(dict.fromkeys(asks)) + " wikiask"]
    # a box whose text the page broke with <br/> has a title: its first part
    titles = {m.group(1): BREAK.split(m.group(2))[0].strip() for m in LABEL.finditer("\n".join(lines)) if BREAK.search(m.group(2))}
    look = {"key": key.group(1) if key else None, "legend": diagram_legend(source), "titles": titles, "turned": turned,
            "calls": calls}
    without = ungrouped(lines)
    if without:
        look.update(flat=without[0], groups=without[1], groupNames=without[2])
    elif len(set(by_file.values())) > 1:
        look.update(groups=by_file, wear=True)
    return "\n".join(lines) + "\n", look


# A figure is a drawing kept as its own SVG file in <wiki>/figures: what the symbols of a formula mean on the part
# itself, the areas of a page or a screen. Its shapes carry classes and no colours; render writes the look into the
# file, as it does for a diagram, so every figure of every wiki is drawn alike and a page never spells a colour.
FIGURE_LOOK = (
    '<style id="wiki-look">'
    'text{font-family:' + FONT + ';font-size:14px;fill:#0f172a}'
    '.part{fill:#eef0fe;stroke:#4f46e5;stroke-width:1.5}'
    '.part2{fill:#e6f3fb;stroke:#0369a1;stroke-width:1.5}'
    '.part3{fill:#e8f7ef;stroke:#047857;stroke-width:1.5}'
    '.key{fill:#fff4e6;stroke:#ea580c;stroke-width:2.5}'
    'text.key,tspan.key{fill:#c2410c;stroke:none;font-weight:700}'
    '.line{fill:none;stroke:#64748b;stroke-width:1.5}'
    '.arrow{fill:none;stroke:#475569;stroke-width:1.5;marker-end:url(#wiki-tip)}'
    '.dim{fill:none;stroke:#475569;stroke-width:1;marker-start:url(#wiki-tip);marker-end:url(#wiki-tip)}'
    '.key.line,.key.arrow,.key.dim{fill:none;stroke:#ea580c}'
    '.key.arrow{marker-end:url(#wiki-tip-key)}'
    '.key.dim{marker-start:url(#wiki-tip-key);marker-end:url(#wiki-tip-key)}'
    '.axis{fill:none;stroke:#94a3b8;stroke-width:1;stroke-dasharray:12 3 2 3}'
    '.ghost{fill:none;stroke:#94a3b8;stroke-width:1.25;stroke-dasharray:5 4}'
    'text.sym,tspan.sym{font-family:"Cambria Math","STIX Two Math","Times New Roman",serif;font-style:italic;font-size:16px}'
    'text.quiet,tspan.quiet{fill:#475569;font-size:12.5px}'
    'text.title,tspan.title{font-weight:650;font-size:15px}'
    '</style>'
    '<defs id="wiki-marks">'
    '<marker id="wiki-tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    '<path d="M0,0 L10,5 L0,10 Z" fill="#475569"/></marker>'
    '<marker id="wiki-tip-key" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    '<path d="M0,0 L10,5 L0,10 Z" fill="#ea580c"/></marker>'
    '</defs>')
FIGURE_OWN = re.compile(r'<style id="wiki-look">.*?</style>|<defs id="wiki-marks">.*?</defs>|<rect id="wiki-ground"[^>]*>', re.S)
FIGURE_UNSAFE = re.compile(r"""<script\b|<foreignObject\b|\son\w+\s*=|(?:href|src)\s*=\s*["'](?:https?:|//|data:)""", re.I)


def dress_figure(text: str) -> tuple[str, float, str]:
    """(the figure in the family's look at its natural size on a white ground, its width, what is wrong with it)."""
    import xml.etree.ElementTree as ET
    own = FIGURE_OWN.sub("", text)
    try:
        root = ET.fromstring(own)
    except ET.ParseError as e:
        return text, 0.0, f"not well-formed XML ({e})"
    if not root.tag.endswith("svg"):
        return text, 0.0, "its root element is not <svg>"
    if FIGURE_UNSAFE.search(own):
        return text, 0.0, "holds a script, a foreignObject, an event handler or a link out of the file"
    head = SVG_HEAD.search(own)
    box = VIEWBOX.search(head.group(0)) if head else None
    if not box:
        return text, 0.0, 'its <svg> has no viewBox="0 0 <width> <height>"'
    x, y, w, h = (float(v) for v in box.groups())
    tag = re.sub(r'\s(?:width|height)="[^"]*"', "", head.group(0)[:-1]).rstrip("/ ")
    tag += f' width="{math.ceil(w)}" height="{math.ceil(h)}">'
    ground = f'<rect id="wiki-ground" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="#ffffff"/>'
    return own[:head.start()] + tag + FIGURE_LOOK + ground + own[head.end():], w, ""


def render_figures(repo: Path, wiki_dir: Path) -> tuple[int, list[str], list[tuple[str, str]]]:
    """(figures that failed, the ones too wide, [(preview name, svg)]) after giving each figure the family's look."""
    failed, wide, drawn = 0, [], []
    for fig in sorted((wiki_dir / "figures").glob("*.svg")) if (wiki_dir / "figures").exists() else []:
        text = fig.read_text(encoding="utf-8")
        new, width, wrong = dress_figure(text)
        label = wiki.posix(fig, repo)
        if wrong:
            failed += 1
            print(f"FAIL {label}: {wrong}")
            continue
        if new != text:
            fig.write_text(new, encoding="utf-8")
        print(f"ok   {label}")
        drawn.append((f"figure-{fig.stem}", new))
        if width > LEGIBLE_PX:
            wide.append(f"wide {label}: {width:.0f} px")
    return failed, wide, drawn


def write_previews(items: list[tuple[str, str]], out_dir: Path) -> bool:
    """A PNG of each picture, so whoever drew it can look at it: a model reads Mermaid text, a reader sees the
    drawing, and faults such as words on top of each other or one box filling the picture show only in the drawing.
    The folder ignores itself in git. False when no browser could take the pictures."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".gitignore").write_text("*\n", encoding="utf-8")
    for old in out_dir.glob("*.png"):
        old.unlink()
    shell = '<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:8px;background:#ffffff">{}</body></html>'
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser, _ = launch(p)
            try:
                page = browser.new_page(viewport={"width": 1400, "height": 900})
                for name, svg in items:
                    page.set_content(shell.format(svg))
                    page.locator("svg").first.screenshot(path=str(out_dir / f"{name}.png"))
            finally:
                browser.close()
        return True
    except ImportError:
        pass
    except Exception:  # a browser that does not start: try the installed one
        pass
    exe = browser_binary()
    if not exe:
        return False
    with tempfile.TemporaryDirectory(prefix="wiki-preview-") as tmp:
        for name, svg in items:
            head = SVG_HEAD.search(svg)
            size = re.search(r'width="(\d+)" height="(\d+)"', head.group(0)) if head else None
            w, h = (int(size.group(1)) + 16, int(size.group(2)) + 16) if size else (1400, 900)
            src = Path(tmp) / f"{name}.html"
            src.write_text(shell.format(svg), encoding="utf-8")
            try:
                subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                                f"--user-data-dir={Path(tmp) / 'profile'}", f"--window-size={w},{h}",
                                f"--screenshot={out_dir / (name + '.png')}", src.as_uri()],
                               capture_output=True, timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                return False
    return any(out_dir.glob("*.png"))


def render(repo: Path, wiki_dir: Path, mermaid_arg: str | None, renderer: str) -> int:
    pages = wiki.collect_pages(repo, wiki_dir)
    fig_failed, fig_wide, drawn = render_figures(repo, wiki_dir)
    preview_dir = wiki_dir / "diagrams" / ".preview"
    look = (f"A picture of each one is in {wiki.posix(preview_dir, repo)}/ (<id>.png, figure-<name>.png; not committed): "
            "open the ones you drew or changed and look at them.")
    jobs, failed, seen = [], fig_failed, {}
    for page in pages:
        for block in wiki.mermaid_blocks(page):
            if not block["id"]:
                print(f"FAIL {page.label}:{block['line']}: a mermaid block has no first line '%% id: <name>'")
                failed += 1
            elif block["id"] in seen:
                print(f"FAIL {page.label}:{block['line']}: diagram id '{block['id']}' is also used in {seen[block['id']]}")
                failed += 1
            else:
                seen[block["id"]] = page.label
                jobs.append((page, block))
    # a picture render drew for a diagram that is gone: it carries render's stamp, so it is render's to remove
    if not failed:
        for old in sorted((wiki_dir / "diagrams").glob("*.svg")) if (wiki_dir / "diagrams").exists() else []:
            if old.stem not in seen and 'code-map-wiki diagram="' in old.read_text(encoding="utf-8", errors="replace")[:300]:
                old.unlink()
                print(f"gone {wiki.posix(old, repo)}: no diagram has this id any more")
    if not jobs:
        if drawn and write_previews(drawn, preview_dir):
            print(look)
        for line in fig_wide:
            print(line)
        print(f"no mermaid blocks; {len(drawn)} figures; {failed} failed")
        return 1 if failed else 0
    keep = "Until then the Mermaid source stays readable in each page, and GitHub renders it."
    try:
        mermaid = mermaid_file(mermaid_arg)
    except Unavailable as e:
        print(f"diagrams not rendered: {e}\n{keep}")
        return NO_BROWSER
    pairs = [(b["id"], *diagram_look(b["source"])) for _, b in jobs]
    results, label, tried = None, "", []
    if renderer in ("auto", "playwright"):
        try:
            import playwright  # noqa: F401
            results, label = render_playwright(pairs, mermaid)
        except ImportError:
            tried.append("Python Playwright is not installed")
        except Unavailable as e:
            tried.append(str(e))
    if results is None and renderer in ("auto", "cli"):
        try:
            results, label = render_cli(pairs, mermaid)
        except Unavailable as e:
            tried.append(str(e))
    if results is None:
        print("diagrams not rendered: " + "; ".join(tried))
        print("To render them on this machine, install Chrome or Edge, or Python Playwright (pip install playwright, then "
              f"python -m playwright install chromium). Nothing was installed. {keep}")
        return NO_BROWSER
    out_dir = wiki_dir / "diagrams"
    out_dir.mkdir(parents=True, exist_ok=True)
    wide = list(fig_wide)
    for (page, block), res in zip(jobs, results):
        if res.get("ok"):
            stamp = f'<!-- code-map-wiki diagram="{block["id"]}" source-sha256="{block["hash"]}" -->\n'
            svg, width = fit_svg(res["svg"])
            (out_dir / f"{block['id']}.svg").write_text(stamp + svg, encoding="utf-8")
            drawn.append((block["id"], svg))
            print(f"ok   {page.label}:{block['line']} -> {wiki.posix(out_dir, repo)}/{block['id']}.svg")
            # a call map's boxes are long file: function names, so a path several calls deep is wider than a column
            # whichever way it runs; pages.md lets it be, drawn in its narrower direction
            call_map = [s.strip() for s in block["source"].split("\n")[1:2]] == ["%% calls"]
            if width > LEGIBLE_PX and not call_map:
                wide.append(f"wide {page.label}:{block['line']} [{block['id']}]: {width:.0f} px")
        else:
            failed += 1
            print(f"FAIL {page.label}:{block['line']} [{block['id']}]: {res.get('error', '')[:400]}")
    for line in wide:
        print(line)
    if wide:
        print(f"GitHub and VS Code shrink a diagram to their Markdown column, about {COLUMN_PX} px; one wider than about "
              f"{LEGIBLE_PX} px ends up with labels too small to read. Draw it top to bottom, break long labels, or split "
              "it (pages.md §Diagrams).")
    if drawn and write_previews(drawn, preview_dir):
        print(look)
    print(f"{len(jobs) - sum(1 for r in results if not r.get('ok'))} rendered, {failed} failed, {len(wide)} too wide "
          f"({label}, Mermaid {MERMAID_VERSION})")
    return 1 if failed else 0


PAGE_BUTTONS = "#nav button[data-id], #foot button[data-id]"


def check_viewer(path: Path) -> int:
    """Open the viewer as a reader would: every page, links between pages, a diagram's zoom and pan, console errors."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("check-viewer needs Python Playwright (pip install playwright); open the file by hand and click through instead.")
        return NO_BROWSER
    problems, notes = [], []
    with sync_playwright() as p:
        try:
            browser, label = launch(p)
        except Unavailable as e:
            print(e)
            return NO_BROWSER
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(path.resolve().as_uri())
        page.wait_for_selector("#nav button")
        ids = page.evaluate("W.pages.map(p => p.id)")
        buttons = page.locator(PAGE_BUTTONS)  # the reading pages in the sidebar, the wiki's rules and log in its footer
        if buttons.count() != len(ids):
            problems.append(f"sidebar lists {buttons.count()} pages, the data holds {len(ids)}")
        for pid in ids:
            page.locator(f'#nav button[data-id="{pid}"], #foot button[data-id="{pid}"]').click()
            text = page.locator("#page .wikipage:not([hidden])").inner_text().strip()
            if not text:
                problems.append(f"{pid}: the page is empty")
            if page.evaluate("current") != pid:
                problems.append(f"{pid}: clicking it in the sidebar did not open it")
        start = ids[0]
        page.locator(f'#nav button[data-id="{start}"]').click()
        link = page.locator("#page .wikipage:not([hidden]) a.page-link").first
        if link.count():
            before = page.evaluate("current")
            link.click()
            if page.evaluate("current") == before:
                problems.append(f"{start}: a link to another wiki page did not open it")
        else:
            notes.append(f"{start} has no link to another wiki page")
        zoomed = False
        for pid in ids:
            page.locator(f'#nav button[data-id="{pid}"], #foot button[data-id="{pid}"]').click()
            img = page.locator("#page .wikipage:not([hidden]) img.zoomable").first
            if not img.count():
                continue
            # a diagram may sit in a fold (the flowchart under a track of steps): a reader opens the fold first
            img.evaluate("im => { for (let d = im.closest('details'); d; d = d.parentElement.closest('details')) d.open = true; }")
            img.scroll_into_view_if_needed()
            y0 = page.evaluate("window.scrollY")
            img.click()
            if page.locator("#zoom").is_hidden():
                problems.append(f"{pid}: clicking a diagram did not open the zoom view")
                break
            level0 = page.locator("#zlevel").inner_text()
            box = page.locator("#zstage").bounding_box()
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.wheel(0, -500)
            page.wait_for_timeout(150)
            if page.locator("#zlevel").inner_text() == level0:
                problems.append(f"{pid}: the mouse wheel did not zoom the diagram")
            if page.evaluate("window.scrollY") != y0:
                problems.append(f"{pid}: the mouse wheel scrolled the page behind the diagram")
            page.keyboard.press("Escape")
            if not page.locator("#zoom").is_hidden():
                problems.append(f"{pid}: Escape did not close the zoom view")
            zoomed = True
            break
        if not zoomed:
            notes.append("no rendered diagram to zoom")
        # every page has been opened above, so the formulas of all of them are in the document now
        for bad in page.evaluate("""[...document.querySelectorAll('.wikipage')].flatMap(s =>
            [...s.querySelectorAll('.math-error')].map(e => s.dataset.page + ': ' + e.dataset.error))"""):
            problems.append(f"a formula does not typeset: {bad}")
        typeset = page.evaluate("document.querySelectorAll('.math-display').length")
        if typeset:
            notes.append(f"{typeset} formulas typeset")
        page.goto(path.resolve().as_uri() + "#" + ids[-1].replace("/", "~"))
        page.wait_for_selector("#nav button")
        if page.evaluate("current") != ids[-1]:
            problems.append("opening the file with a page in its address did not show that page")
        browser.close()
    problems += [f"console error: {e}" for e in errors]
    for n in notes:
        print(f"note {n}")
    for pr in problems:
        print(f"FAIL {pr}")
    print(f"{len(ids)} pages opened ({label}): {len(problems)} problems")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="wiki_browser.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--repo", type=Path)
    r.add_argument("--wiki", type=Path)
    r.add_argument("--mermaid", help="path to mermaid.min.js, instead of the cached download")
    r.add_argument("--renderer", choices=("auto", "playwright", "cli"), default="auto")
    c = sub.add_parser("check-viewer")
    c.add_argument("file", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "check-viewer":
        return check_viewer(a.file)
    repo = (a.repo or wiki.default_repo()).resolve()
    wiki_dir = (repo / a.wiki).resolve() if a.wiki and not a.wiki.is_absolute() else (a.wiki or wiki.default_wiki(repo)).resolve()
    return render(repo, wiki_dir, a.mermaid, a.renderer)


if __name__ == "__main__":
    sys.exit(main())
