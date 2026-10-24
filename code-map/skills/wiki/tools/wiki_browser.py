#!/usr/bin/env python3
"""The parts of wiki upkeep that need a browser: render Mermaid diagrams to SVG, and test the viewer like a reader.

  python wiki_browser.py render       [--repo R] [--wiki W] [--mermaid FILE] [--renderer auto|playwright|cli]
  python wiki_browser.py check-viewer FILE

Why render at all: GitHub renders Mermaid, but VS Code's built-in Markdown preview and many viewers show the raw code.
Pages therefore show the rendered SVG and keep the Mermaid source beside it in a <details> block. Rendering is also
the only real syntax check: a diagram that does not parse fails here, not in a reader's browser.

Which browser, in order: Python Playwright with its own Chromium; Playwright driving an installed Edge or Chrome;
without Playwright, an installed Chrome, Edge or Chromium run headless from the command line. Nothing is installed.
Mermaid itself (pinned version, checked by SHA-256) is downloaded once into a user cache folder, or taken from
--mermaid or WIKI_MERMAID. Exit codes: 0 ok, 1 a diagram or check failed, 3 no browser or Mermaid available.
"""
from __future__ import annotations

import argparse
import html
import json
import os
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
MERMAID_INIT = ('mermaid.initialize({startOnLoad: false, theme: "neutral", securityLevel: "strict", htmlLabels: false, '
                'flowchart: {htmlLabels: false}});')
RENDER_ONE = """async ([id, src]) => {
  try { const r = await mermaid.render("wiki-" + id, src); return {ok: true, svg: r.svg}; }
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


def render_playwright(jobs: list[tuple[str, str]], mermaid: Path) -> tuple[list[dict], str]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser, label = launch(p)
        try:
            page = browser.new_page()
            page.set_content("<!doctype html><html><head><meta charset='utf-8'></head><body></body></html>")
            page.add_script_tag(path=str(mermaid))
            page.evaluate(MERMAID_INIT)
            return [dict(page.evaluate(RENDER_ONE, [i, s]), id=i) for i, s in jobs], label
        finally:
            browser.close()


def render_cli(jobs: list[tuple[str, str]], mermaid: Path) -> tuple[list[dict], str]:
    """No Playwright: load a page that renders every diagram into the DOM, and read it back with --dump-dom."""
    exe = browser_binary()
    if not exe:
        raise Unavailable("no Playwright and no Chrome, Edge or Chromium found")
    with tempfile.TemporaryDirectory(prefix="wiki-render-") as tmp:
        tmpd = Path(tmp)
        shutil.copy(mermaid, tmpd / "mermaid.min.js")
        jobs_js = json.dumps(jobs).replace("</", "<\\/")
        (tmpd / "render.html").write_text(f"""<!doctype html><html><head><meta charset="utf-8"></head><body>
<pre id="out"></pre><script src="mermaid.min.js"></script><script>
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


def render(repo: Path, wiki_dir: Path, mermaid_arg: str | None, renderer: str) -> int:
    pages = wiki.collect_pages(repo, wiki_dir)
    jobs, failed, seen = [], 0, {}
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
    if not jobs:
        print(f"no mermaid blocks; {failed} failed")
        return 1 if failed else 0
    keep = "Until then the Mermaid source stays readable in each page, and GitHub renders it."
    try:
        mermaid = mermaid_file(mermaid_arg)
    except Unavailable as e:
        print(f"diagrams not rendered: {e}\n{keep}")
        return NO_BROWSER
    pairs = [(b["id"], b["source"]) for _, b in jobs]
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
    for (page, block), res in zip(jobs, results):
        if res.get("ok"):
            stamp = f'<!-- code-map-wiki diagram="{block["id"]}" source-sha256="{block["hash"]}" -->\n'
            (out_dir / f"{block['id']}.svg").write_text(stamp + res["svg"], encoding="utf-8")
            print(f"ok   {page.label}:{block['line']} -> {wiki.posix(out_dir, repo)}/{block['id']}.svg")
        else:
            failed += 1
            print(f"FAIL {page.label}:{block['line']} [{block['id']}]: {res.get('error', '')[:400]}")
    print(f"{len(jobs) - sum(1 for r in results if not r.get('ok'))} rendered, {failed} failed ({label}, Mermaid {MERMAID_VERSION})")
    return 1 if failed else 0


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
        buttons = page.locator("#nav button[data-id]")
        if buttons.count() != len(ids):
            problems.append(f"sidebar lists {buttons.count()} pages, the data holds {len(ids)}")
        for pid in ids:
            page.locator(f'#nav button[data-id="{pid}"]').click()
            text = page.locator("#page").inner_text().strip()
            if not text:
                problems.append(f"{pid}: the page is empty")
            if page.evaluate("current") != pid:
                problems.append(f"{pid}: clicking it in the sidebar did not open it")
        start = ids[0]
        page.locator(f'#nav button[data-id="{start}"]').click()
        link = page.locator("#page a.page-link").first
        if link.count():
            before = page.evaluate("current")
            link.click()
            if page.evaluate("current") == before:
                problems.append(f"{start}: a link to another wiki page did not open it")
        else:
            notes.append(f"{start} has no link to another wiki page")
        zoomed = False
        for pid in ids:
            page.locator(f'#nav button[data-id="{pid}"]').click()
            img = page.locator("#page img.zoomable").first
            if not img.count():
                continue
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
