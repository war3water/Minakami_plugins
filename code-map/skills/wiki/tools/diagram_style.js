/* How every flowchart in a wiki is drawn, applied by wiki_browser.py after Mermaid has laid the picture out.
   The page's Mermaid text stays plain and says only what the picture means: its groups (subgraph), the box to notice
   (%% key:), which ends are refusals or successes (class ... stop / ok), and what its arrow kinds stand for
   (%% legend:). The look is added here, so every wiki's pictures are alike, a page never spells a colour, and a change
   in the code is a change to a line of text. Nothing in this file is read by a model. */
window.wikiDress = function (svgText, opt) {
  const C = {
    ink: "#0f172a", muted: "#475569", line: "#64748b", faint: "#94a3b8", box: "#ffffff",
    key: "#ea580c", keyEdge: "#9a3412", keyInk: "#ffffff",
    ask: ["#f5f3ff", "#7c3aed"], stop: ["#fef2f2", "#dc2626"], ok: ["#ecfdf5", "#059669"],
    tiers: [["#eef0fe", "#4f46e5"], ["#e6f3fb", "#0369a1"], ["#fdf5e4", "#b45309"], ["#e8f7ef", "#047857"],
            ["#fcecf2", "#be185d"], ["#e5f5f5", "#0f766e"]],
  };
  const MONO = 'ui-monospace, "Cascadia Mono", "SF Mono", Consolas, "Liberation Mono", monospace';
  const NS = "http://www.w3.org/2000/svg";
  opt = opt || {};
  const legendText = opt.legend || {};

  let svg;
  try {
    const doc = new DOMParser().parseFromString(svgText, "image/svg+xml");
    if (doc.querySelector("parsererror")) return svgText;
    svg = document.importNode(doc.documentElement, true);
  } catch (e) { return svgText; }
  if (svg.getAttribute("aria-roledescription") !== "flowchart-v2") return svgText;
  const host = document.createElement("div");
  host.style.cssText = "position:absolute;left:0;top:0;visibility:hidden";
  host.appendChild(svg);
  document.body.appendChild(host);

  const make = (name, attrs) => {
    const el = document.createElementNS(NS, name);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  };
  const css = (el, props) => { for (const k in props) el.style.setProperty(k, props[k]); };
  // A shape is one element, or (stadium, hexagon) a group of two paths: the fill and the outline.
  const paint = (shape, fill, stroke, width) => {
    if (!shape) return;
    const parts = shape.tagName === "g" ? [...shape.querySelectorAll("path")] : [shape];
    parts.forEach(p => {
      if (shape.tagName === "g" && p.getAttribute("fill") === "none") css(p, {stroke: stroke, "stroke-width": width + "px"});
      else if (shape.tagName === "g") css(p, {fill: fill, stroke: "none"});
      else css(p, {fill: fill, stroke: stroke, "stroke-width": width + "px"});
    });
  };
  const shapeOf = g => g.querySelector(":scope > .label-container") || g.querySelector(":scope > rect, :scope > polygon, :scope > path, :scope > circle");
  const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r]; };

  try {
    const nodes = new Map();
    svg.querySelectorAll("g.node").forEach(g => { const m = /^flowchart-(.+)-\d+$/.exec(g.id); if (m) nodes.set(m[1], g); });

    // ---- groups: a tinted band with its name at the top left, and its boxes outlined in the band's colour
    const clusters = [...svg.querySelectorAll("g.cluster")].map(g => ({g, rect: g.querySelector(":scope > rect")})).filter(c => c.rect);
    clusters.forEach(c => { c.box = c.rect.getBoundingClientRect(); });
    clusters.sort((a, b) => (a.box.top - b.box.top) || (a.box.left - b.box.left));
    clusters.forEach((c, i) => {
      const [tint, colour] = C.tiers[i % C.tiers.length];
      c.colour = colour;
      css(c.rect, {fill: tint, stroke: "none"});
      c.rect.setAttribute("rx", 12); c.rect.setAttribute("ry", 12);
      const x = +c.rect.getAttribute("x"), y = +c.rect.getAttribute("y"), h = +c.rect.getAttribute("height");
      const bar = make("rect", {x: x, y: y + 6, width: 5, height: Math.max(0, h - 12), rx: 2.5});
      css(bar, {fill: colour, stroke: "none"});
      c.rect.after(bar);
      const label = c.g.querySelector(":scope > g.cluster-label");
      if (label) {
        const at = /translate\(\s*([-\d.]+)[ ,]+([-\d.]+)/.exec(label.getAttribute("transform") || "");
        label.setAttribute("transform", `translate(${x + 18}, ${at ? at[2] : y})`);
        // Mermaid wrapped the name for its own size and centred it; at this size it is one line
        const rows = [...label.querySelectorAll("text > tspan")];
        if (rows.length) {
          const name = rows.map(r => r.textContent.trim()).join(" ").replace(/\s+/g, " ").toUpperCase();
          rows.slice(1).forEach(r => r.remove());
          const word = rows[0].querySelector("tspan") || rows[0];
          [...rows[0].querySelectorAll("tspan")].slice(1).forEach(t => t.remove());
          word.textContent = name;
          css(word, {"font-size": "11.5px", "font-weight": "700", "letter-spacing": ".08em", fill: colour});
        }
        const bg = label.querySelector("rect"); if (bg) css(bg, {fill: "none"});
      }
    });
    const groupOf = g => {
      const [cx, cy] = centre(g);
      let best = null;
      clusters.forEach(c => {
        if (cx >= c.box.left && cx <= c.box.right && cy >= c.box.top && cy <= c.box.bottom
            && (!best || c.box.width * c.box.height < best.box.width * best.box.height)) best = c;
      });
      return best;
    };

    // ---- arrows: which boxes each joins, and its kind (thick, dashed, or plain)
    const edges = [];
    const known = new Set([...nodes.keys(), ...clusters.map(c => c.g.id)]);
    svg.querySelectorAll("path.flowchart-link").forEach(p => {
      const m = /^L_(.+)_\d+$/.exec(p.id || "");
      let from = null, to = null;
      if (m) for (let i = m[1].indexOf("_"); i > 0; i = m[1].indexOf("_", i + 1)) {
        const a = m[1].slice(0, i), b = m[1].slice(i + 1);
        if (known.has(a) && known.has(b)) { from = a; to = b; break; }
      }
      const cls = p.getAttribute("class") || "";
      const kind = /edge-pattern-(dotted|dashed)/.test(cls) ? "dashed" : /edge-thickness-thick/.test(cls) ? "thick" : "solid";
      // an arrow the layout was given the other way round (see returning() in wiki_browser.py): it means to -> from
      const turned = kind === "dashed" && (opt.turned || []).some(t => t[0] === from && t[1] === to);
      edges.push(turned ? {p, from: to, to: from, kind, turned} : {p, from, to, kind});
    });
    // A dashed arrow is something coming back or reached indirectly: it does not make its target a later step,
    // unless that target can be reached no other way.
    const joined = edges.filter(e => e.from && e.to);
    const into = (list) => { const m = new Map(); list.forEach(e => { if (!m.has(e.to)) m.set(e.to, []); m.get(e.to).push(e); }); return m; };
    const incoming = into(joined.filter(e => e.kind !== "dashed")), incomingAny = into(joined);
    const outOf = new Map();
    joined.forEach(e => { if (!outOf.has(e.from)) outOf.set(e.from, []); outOf.get(e.from).push(e); });
    const groupId = new Map();
    nodes.forEach((g, id) => { const c = groupOf(g); if (c) groupId.set(id, c.g.id); });
    const reach = from => {
      const seen = new Set([from]), queue = [from];
      while (queue.length) for (const e of outOf.get(queue.shift()) || []) if (!seen.has(e.to)) { seen.add(e.to); queue.push(e.to); }
      return seen;
    };
    let starts = [...nodes.keys()].filter(id => !incoming.has(id) && outOf.has(id) && !incoming.has(groupId.get(id)));
    const reached = new Map(starts.map(id => [id, reach(id)]));
    starts = starts.filter(id => !starts.some(other => other !== id && reached.get(other).has(id) && !reached.get(id).has(other)));

    // ---- the way to the marked box: thick arrows where the page drew them, else the shortest way from a start
    const key = opt.key && nodes.has(opt.key) ? opt.key : null;
    const byHand = edges.some(e => e.kind === "thick");
    const way = new Set();
    if (byHand) edges.forEach(e => { if (e.kind === "thick") way.add(e); });
    else if (key && !starts.includes(key)) {
      const back = (edgesInto) => {
        const via = new Map([[key, null]]), queue = [key];
        while (queue.length) {
          const at = queue.shift();
          for (const e of edgesInto.get(at) || []) {
            if (via.has(e.from)) continue;
            via.set(e.from, e); queue.push(e.from);
            if (starts.includes(e.from)) { const path = []; for (let n = e.from; via.get(n); n = via.get(n).to) path.push(via.get(n)); return path; }
          }
        }
        return [];
      };
      let path = back(incoming);
      if (!path.length) path = back(incomingAny);
      // in a single line of steps every arrow is the way, and colouring half of them says nothing
      if (path.some(e => (outOf.get(e.from) || []).filter(o => o.kind !== "dashed").length > 1)) path.forEach(e => way.add(e));
    }

    // ---- boxes
    const defs = svg.querySelector("defs") || svg.insertBefore(make("defs", {}), svg.firstChild);
    const shadow = svg.id + "-lift";
    const isCode = s => {
      const t = (s.trim().split(/\s+/)[0] || "");
      const ext = /^[\w.\-\\/]+\.([A-Za-z0-9]{1,5}):?$/.exec(t);
      return !!(ext && /[A-Za-z]/.test(ext[1])) || /^[\w.\-]+\/[\w.\-\/]*:?$/.test(t);
    };
    nodes.forEach((g, id) => {
      const shape = shapeOf(g), group = groupOf(g), cls = g.getAttribute("class") || "";
      const isKey = id === key, has = name => new RegExp("(^|\\s)" + name + "(\\s|$)").test(cls);
      // drawn flat (see RENDER_ONE in wiki_browser.py), a box wears its group's colour
      const worn = (opt.flat === true || opt.wear === true) && opt.groups && opt.groups[id] != null ? C.tiers[opt.groups[id] % C.tiers.length] : null;
      let fill = worn ? worn[0] : C.box, stroke = group ? group.colour : worn ? worn[1] : C.faint, width = 1.5, ink = C.ink, soft = C.muted;
      if (has("wikiask")) { fill = C.ask[0]; stroke = C.ask[1]; }
      if (has("stop")) { fill = C.stop[0]; stroke = C.stop[1]; width = 2; }
      if (has("ok")) { fill = C.ok[0]; stroke = C.ok[1]; width = 2; }
      if (starts.includes(id)) { stroke = C.ink; width = 2.25; }
      if (isKey) { fill = C.key; stroke = C.keyEdge; width = 2; ink = C.keyInk; soft = C.keyInk; }
      paint(shape, fill, stroke, width);
      if (shape && shape.tagName === "rect" && !shape.getAttribute("rx")) { shape.setAttribute("rx", 8); shape.setAttribute("ry", 8); }
      if (isKey && shape) shape.setAttribute("filter", `url(#${shadow})`);
      const lines = [...g.querySelectorAll("g.label text > tspan")];
      const squeeze = s => s.replace(/\s+/g, "");
      const title = squeeze((opt.titles || {})[id] || "");
      let soFar = "";
      lines.forEach((line, n) => {
        const code = isCode(line.textContent), words = [...line.querySelectorAll("tspan")];
        soFar += squeeze(line.textContent);
        const first = !!title && title.startsWith(soFar), alone = !title;
        words.forEach((w, k) => {
          if (code) {
            // file.py: function -> the file quiet, the function strong
            const quiet = k === 0 && /[.\\/]/.test(w.textContent) && (words.length > 1 || /:\s*$/.test(w.textContent) || !!title);
            css(w, {"font-family": MONO, "font-size": "12.5px", "font-weight": quiet ? "400" : "600", fill: quiet ? soft : ink});
          } else if (first && opt.calls) css(w, {"font-family": MONO, "font-size": "13px", "font-weight": "700", fill: ink});
          else if (first) css(w, {"font-weight": "650", fill: ink});
          else if (alone) css(w, {"font-weight": "500", fill: ink});
          else css(w, {"font-size": "13.5px", fill: soft});
        });
        // a function name that Mermaid wrapped onto the line under its file
        if (!code && n > 0 && isCode(lines[n - 1].textContent) && /:\s*$/.test(lines[n - 1].textContent))
          words.forEach(w => css(w, {"font-family": MONO, "font-size": "12.5px", "font-weight": "600", fill: ink}));
      });
    });
    if (key) {
      const f = make("filter", {id: shadow, x: "-20%", y: "-20%", width: "140%", height: "160%"});
      f.appendChild(make("feDropShadow", {dx: 0, dy: 3, stdDeviation: 3, "flood-color": "#7c2d12", "flood-opacity": ".28"}));
      defs.appendChild(f);
    }

    // ---- arrows and their heads
    const heads = new Map();
    const headFor = (path, colour, tag, atStart) => {
      const ref = /url\(#([^)]+)\)/.exec(path.getAttribute("marker-end") || "");
      if (!ref) return;
      const from = atStart ? ref[1].replace(/pointEnd$/, "pointStart") : ref[1];
      const name = from + "-" + tag;
      if (!heads.has(name)) {
        const base = svg.querySelector("#" + CSS.escape(from));
        if (!base) return;
        const copy = base.cloneNode(true); copy.id = name;
        copy.querySelectorAll("path, circle").forEach(s => css(s, {fill: colour, stroke: colour}));
        base.after(copy); heads.set(name, copy);
      }
      if (atStart) { path.removeAttribute("marker-end"); path.setAttribute("marker-start", `url(#${name})`); }
      else path.setAttribute("marker-end", `url(#${name})`);
    };
    edges.forEach(e => {
      if (way.has(e)) { css(e.p, {stroke: C.key, "stroke-width": "3px"}); headFor(e.p, C.key, "way", e.turned); }
      else if (e.kind === "dashed") { css(e.p, {stroke: C.faint, "stroke-width": "1.5px", "stroke-dasharray": "5 4"}); headFor(e.p, C.faint, "back", e.turned); }
      else { css(e.p, {stroke: C.line, "stroke-width": "1.5px"}); headFor(e.p, C.line, "plain"); }
    });
    svg.querySelectorAll("g.edgeLabel").forEach(l => {
      // no box behind an arrow's words: a white halo round the letters reads on a tinted band too
      l.querySelectorAll("rect").forEach(r => css(r, {fill: "none", opacity: "0"}));
      l.querySelectorAll("text").forEach(t => css(t, {"paint-order": "stroke", stroke: "#ffffff", "stroke-width": "4px", "stroke-linejoin": "round"}));
      l.querySelectorAll("tspan.text-inner-tspan").forEach(t => css(t, {"font-size": "13px", fill: C.muted}));
    });

    // ---- the legend: only what this picture uses and can name
    const items = [];
    if (key) items.push({mark: "key", text: legendText.key || "what to notice first"});
    if (way.size) {
      const text = byHand ? legendText.thick : (legendText.way || "the way to it from the start");
      if (text) items.push({mark: "way", text: text});
    }
    if (opt.flat === true && opt.groups) (opt.groupNames || []).forEach((name, i) => {
      if (Object.keys(opt.groups).some(id => opt.groups[id] === i && nodes.has(id))) items.push({mark: "group", tint: C.tiers[i % C.tiers.length], text: name});
    });
    if (legendText.solid && edges.some(e => e.kind === "solid" && !way.has(e))) items.push({mark: "plain", text: legendText.solid});
    if (legendText.dashed && edges.some(e => e.kind === "dashed")) items.push({mark: "back", text: legendText.dashed});
    if (legendText.stop && [...nodes.values()].some(g => /(^|\s)stop(\s|$)/.test(g.getAttribute("class") || ""))) items.push({mark: "stop", text: legendText.stop});
    if (legendText.ok && [...nodes.values()].some(g => /(^|\s)ok(\s|$)/.test(g.getAttribute("class") || ""))) items.push({mark: "ok", text: legendText.ok});
    const vb = (svg.getAttribute("viewBox") || "").split(/[ ,]+/).map(Number);
    if (items.length && vb.length === 4) {
      const legend = make("g", {class: "wiki-legend"});
      svg.appendChild(legend);
      const rowH = 26, gap = 28, left = vb[0] + 14;
      let x = left, row = 0, widest = 0;
      items.forEach(it => {
        const g = make("g", {}); legend.appendChild(g);
        const boxMark = (fill, stroke) => g.appendChild(make("rect", {x: 0, y: -11, width: 26, height: 15, rx: 4, fill: fill, stroke: stroke, "stroke-width": 1.5}));
        const lineMark = (colour, w, dash) => {
          const l = make("line", {x1: 0, y1: -4, x2: 20, y2: -4, stroke: colour, "stroke-width": w});
          if (dash) l.setAttribute("stroke-dasharray", "5 4");
          g.appendChild(l);
          g.appendChild(make("path", {d: "M19,-9 L28,-4 L19,1 Z", fill: colour}));
        };
        if (it.mark === "key") boxMark(C.key, C.keyEdge);
        else if (it.mark === "group") boxMark(it.tint[0], it.tint[1]);
        else if (it.mark === "stop") boxMark(C.stop[0], C.stop[1]);
        else if (it.mark === "ok") boxMark(C.ok[0], C.ok[1]);
        else if (it.mark === "way") lineMark(C.key, 3, false);
        else if (it.mark === "back") lineMark(C.faint, 1.5, true);
        else lineMark(C.line, 1.5, false);
        const t = make("text", {x: 36, y: 0}); t.textContent = it.text;
        css(t, {"font-size": "13px", fill: C.muted});
        g.appendChild(t);
        const w = 36 + t.getComputedTextLength();
        if (x > left && x + w > vb[0] + Math.max(vb[2], 420) - 10) { x = left; row += 1; }
        g.setAttribute("transform", `translate(${x}, ${vb[1] + vb[3] + 22 + row * rowH})`);
        widest = Math.max(widest, x + w - vb[0] + 14);
        x += w + gap;
      });
      vb[3] += 22 + (row + 1) * rowH - 4;
      vb[2] = Math.max(vb[2], widest);
      svg.setAttribute("viewBox", vb.join(" "));
      svg.style.maxWidth = vb[2] + "px";
    }
    return new XMLSerializer().serializeToString(svg);
  } catch (e) {
    return svgText;   // a picture in Mermaid's own look is better than none
  } finally {
    host.remove();
  }
};
