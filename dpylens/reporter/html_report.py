from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class ReportPaths:
    analysis_dir: Path
    report_dir: Path


DEFAULT_JSON_FILES = [
    "modules.json",
    "module_graph.json",
    "callgraph.json",
    "callgraph_resolved.json",
    "patterns.json",
    "dataflow.json",
]

DEFAULT_IMAGE_FILES = [
    "imports.png",
    "module_graph.png",
    "callgraph.png",
    "callgraph_grouped.png",
    "dataflow.png",
]


def _safe_copy(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_report(paths: ReportPaths) -> None:
    report_dir = paths.report_dir
    analysis_dir = paths.analysis_dir

    (report_dir / "data").mkdir(parents=True, exist_ok=True)
    (report_dir / "img").mkdir(parents=True, exist_ok=True)

    for name in DEFAULT_JSON_FILES:
        _safe_copy(analysis_dir / name, report_dir / "data" / name)

    for name in DEFAULT_IMAGE_FILES:
        _safe_copy(analysis_dir / name, report_dir / "img" / name)

    (report_dir / "index.html").write_text(_INDEX_HTML, encoding="utf-8")


_INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>dPyLens | Analysis Report</title>
  <style>
    :root {
      --bg: #0a0a0a;
      --panel: rgba(18, 18, 18, 0.72);
      --panel-solid: #111214;
      --border: rgba(255,255,255,0.10);
      --border-2: rgba(255,255,255,0.14);
      --text: #e5e7eb;
      --muted: #9ca3af;
      --muted-2: #6b7280;

      --cyan: #22d3ee;
      --blue: #60a5fa;
      --teal: #2dd4bf;
      --ok-bg: rgba(34, 197, 94, 0.14);
      --ok: #22c55e;
      --warn-bg: rgba(245, 158, 11, 0.16);
      --warn: #f59e0b;

      --shadow: 0 24px 80px rgba(0,0,0,0.55);
      --shadow-soft: 0 1px 0 rgba(255,255,255,0.04) inset, 0 16px 40px rgba(0,0,0,0.35);
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      overflow-x: hidden;
    }

    /* Subtle circuit overlay */
    .bg-overlay {
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.055;
      background-image:
        radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
        radial-gradient(rgba(34,211,238,0.08) 1px, transparent 1px);
      background-size: 44px 44px, 88px 88px;
      background-position: 0 0, 22px 22px;
    }
    .bg-glow {
      position: fixed;
      inset: 0;
      pointer-events: none;
      background: radial-gradient(ellipse at top, rgba(34,211,238,0.12), rgba(0,0,0,0));
    }

    .header {
      position: sticky;
      top: 0;
      z-index: 20;
      background: rgba(10,10,10,0.65);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }
    .header-inner {
      max-width: 1400px;
      margin: 0 auto;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }
    .py-mark {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: linear-gradient(135deg, rgba(96,165,250,0.95), rgba(45,212,191,0.95));
      display: grid;
      place-items: center;
      box-shadow: 0 10px 40px rgba(96,165,250,0.20);
      color: #0a0a0a;
      font-weight: 900;
      font-style: italic;
      user-select: none;
    }
    h1 {
      margin: 0;
      font-size: 16px;
      letter-spacing: 0.02em;
      font-weight: 800;
      white-space: nowrap;
    }
    .header-meta {
      font-size: 12px;
      color: var(--muted);
      white-space: nowrap;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 18px 20px 48px;
    }

    .grid-top {
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 16px;
      margin-top: 16px;
      margin-bottom: 16px;
    }
    @media (max-width: 1100px) {
      .grid-top { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: var(--shadow-soft);
      overflow: hidden;
      min-width: 0;
    }
    .card h2 {
      margin: 0 0 10px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--muted);
      font-weight: 800;
    }
    .muted { color: var(--muted); }

    /* Overview stats */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    .stat {
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.03);
      border-radius: 12px;
      padding: 10px 12px;
      min-width: 0;
    }
    .stat .k { font-size: 11px; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; }
    .stat .v { font-size: 18px; font-weight: 800; margin-top: 2px; color: var(--text); }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
    }
    .pill.ok { background: var(--ok-bg); color: var(--ok); border-color: rgba(34,197,94,0.25); }
    .pill.warn { background: var(--warn-bg); color: var(--warn); border-color: rgba(245,158,11,0.28); }

    /* Graph thumbs */
    .graph-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .graph-thumb {
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.20);
      border-radius: 12px;
      padding: 8px;
      overflow: hidden;
      min-width: 0;
    }
    .graph-thumb img {
      width: 100%;
      height: 96px;
      object-fit: cover;
      border-radius: 10px;
      border: 1px solid var(--border);
      cursor: pointer;
      display: block;
    }
    .graph-thumb .t {
      margin-top: 6px;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.14em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Explorer layout */
    .explorer {
      display: grid;
      grid-template-columns: 360px 1fr;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.03);
      border-radius: 16px;
      overflow: hidden;
      min-height: 680px;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    @media (max-width: 1100px) {
      .explorer { grid-template-columns: 1fr; }
    }

    .sidebar {
      background: rgba(0,0,0,0.25);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .sidebar-header {
      padding: 14px;
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 56px;
      z-index: 10;
      background: rgba(10,10,10,0.60);
      backdrop-filter: blur(10px);
    }
    @media (max-width: 1100px) {
      .sidebar-header { top: 56px; }
    }

    .tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }
    .tab {
      padding: 8px 10px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
      cursor: pointer;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      user-select: none;
      text-align: center;
      transition: all 0.15s ease;
    }
    .tab.active {
      border-color: rgba(34,211,238,0.35);
      background: rgba(34,211,238,0.10);
      color: #c8f7ff;
      box-shadow: 0 0 0 1px rgba(34,211,238,0.10) inset;
    }

    .search {
      width: 100%;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.35);
      color: var(--text);
      outline: none;
      font-size: 13px;
    }
    .search::placeholder { color: var(--muted-2); }
    .search:focus { border-color: rgba(34,211,238,0.45); box-shadow: 0 0 0 4px rgba(34,211,238,0.12); }

    .list {
      padding: 10px;
      overflow: auto;
      flex: 1;
      min-width: 0;
    }
    .item {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid transparent;
      cursor: pointer;
      margin-bottom: 6px;
      font-size: 13px;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: all 0.12s ease;
    }
    .item:hover {
      background: rgba(255,255,255,0.05);
      color: var(--text);
      border-color: rgba(255,255,255,0.08);
    }
    .item.active {
      background: rgba(96,165,250,0.12);
      border-color: rgba(96,165,250,0.28);
      color: #dbeafe;
      font-weight: 700;
    }

    .detail {
      background: rgba(0,0,0,0.12);
      padding: 18px 18px 26px;
      overflow: auto;
      min-width: 0;
    }

    /* Prevent tables/long code from overflowing cards */
    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 12px;
      margin-top: 10px;
    }
    th, td {
      padding: 10px 10px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      overflow: hidden;
      text-overflow: ellipsis;
      word-break: break-word;
    }
    th {
      text-align: left;
      color: var(--muted);
      font-weight: 800;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      font-size: 11px;
      background: rgba(255,255,255,0.03);
    }

    pre {
      margin: 10px 0 0 0;
      padding: 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.35);
      overflow: auto;
      max-width: 100%;
      color: #d1d5db;
      font-size: 12px;
      line-height: 1.55;
    }
    code, .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
    }

    .section-title {
      margin: 14px 0 6px 0;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
    }

    /* Image modal */
    .modal {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 28px;
      z-index: 50;
    }
    .modal.open { display: flex; }
    .modal-inner {
      max-width: min(1400px, 96vw);
      width: 100%;
      background: rgba(18,18,18,0.85);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      box-shadow: var(--shadow);
    }
    .modal-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-weight: 900;
    }
    .modal-actions {
      display: inline-flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .close {
      cursor: pointer;
      padding: 6px 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
      color: var(--text);
      font-size: 12px;
      font-weight: 800;
      user-select: none;
    }
    .close:hover {
      background: rgba(255,255,255,0.07);
      border-color: var(--border-2);
    }

    .img-viewport {
      width: 100%;
      height: min(78vh, 820px);
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.35);
      overflow: hidden;
      position: relative;
      cursor: grab;
    }
    .img-viewport:active { cursor: grabbing; }

    #imgModalImg {
      position: absolute;
      top: 50%;
      left: 50%;
      transform-origin: 0 0;
      will-change: transform;
      user-select: none;
      -webkit-user-drag: none;
      max-width: none;
      max-height: none;
    }
  </style>
</head>
<body>
  <div class="bg-overlay"></div>
  <div class="bg-glow"></div>

  <div class="header">
    <div class="header-inner">
      <div class="brand">
        <div class="py-mark">py</div>
        <h1>dPyLens Report</h1>
      </div>
      <div class="header-meta">Static analysis report • open via server for data loading</div>
    </div>
  </div>

  <div class="container">
    <div class="grid-top">
      <div class="card">
        <h2>Overview</h2>
        <div id="overview" class="muted">Loading analysis…</div>
      </div>

      <div class="card">
        <h2>Graphs</h2>
        <div id="graphs" class="graph-grid"></div>
        <div class="muted" style="margin-top:10px;font-size:12px">
          Click a thumbnail to expand. Use wheel to zoom and drag to pan.
        </div>
      </div>
    </div>

    <div class="explorer">
      <div class="sidebar">
        <div class="sidebar-header">
          <div class="tabs">
            <div id="tabFiles" class="tab active">Files</div>
            <div id="tabFunctions" class="tab">Functions</div>
          </div>
          <input id="globalSearch" class="search mono" placeholder="Search files/functions..." />
        </div>
        <div id="masterList" class="list"></div>
      </div>

      <div class="detail">
        <div id="details" class="muted" style="padding: 8px;">
          Select a file or function to view details.
        </div>
      </div>
    </div>
  </div>

  <div id="imgModal" class="modal" role="dialog" aria-modal="true" aria-label="Graph preview">
    <div class="modal-inner">
      <div class="modal-title">
        <span id="imgModalTitle">Graph</span>

        <div class="modal-actions">
          <button id="imgFit" class="close" title="Fit to view">Fit</button>
          <button id="imgZoomOut" class="close" title="Zoom out">−</button>
          <button id="imgZoomIn" class="close" title="Zoom in">+</button>
          <button id="imgReset" class="close" title="Reset zoom">Reset</button>
          <button id="imgModalClose" class="close" title="Close (Esc)">✕</button>
        </div>
      </div>

      <div id="imgViewport" class="img-viewport" title="Scroll/trackpad to zoom • Drag to pan">
        <img id="imgModalImg" alt="Graph preview" draggable="false" />
      </div>
    </div>
  </div>

<script>
async function loadJson(name) {
  const res = await fetch(`data/${name}`);
  if (!res.ok) throw new Error(`Failed to load ${name}: ${res.status}`);
  return await res.json();
}

function el(tag, attrs={}, children=[]) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k,v]) => {
    if (k === "class") e.className = v;
    else if (k === "onclick") e.onclick = v;
    else e.setAttribute(k, v);
  });
  for (const c of children) {
    if (typeof c === "string") e.appendChild(document.createTextNode(c));
    else if (c) e.appendChild(c);
  }
  return e;
}

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

// --- Modal zoom/pan state ---
const modal = document.getElementById("imgModal");
const modalImg = document.getElementById("imgModalImg");
const modalTitle = document.getElementById("imgModalTitle");
const viewport = document.getElementById("imgViewport");

let state = {
  open: false,
  scale: 1,
  minScale: 0.2,
  maxScale: 6,
  tx: 0,
  ty: 0,
  dragging: false,
  dragStartX: 0,
  dragStartY: 0,
  dragOrigTx: 0,
  dragOrigTy: 0,
};

function applyTransform() {
  modalImg.style.transform =
    `translate(-50%, -50%) translate(${state.tx}px, ${state.ty}px) scale(${state.scale})`;
}

function resetView() {
  state.scale = 1;
  state.tx = 0;
  state.ty = 0;
  applyTransform();
}

function fitToView() {
  const vw = viewport.clientWidth;
  const vh = viewport.clientHeight;
  const iw = modalImg.naturalWidth || 1;
  const ih = modalImg.naturalHeight || 1;

  const scale = Math.min(vw / iw, vh / ih);
  state.scale = Math.max(state.minScale, Math.min(scale, state.maxScale));
  state.tx = 0;
  state.ty = 0;
  applyTransform();
}

function zoomAt(factor, anchorX = viewport.clientWidth / 2, anchorY = viewport.clientHeight / 2) {
  const next = Math.max(state.minScale, Math.min(state.scale * factor, state.maxScale));
  const actualFactor = next / state.scale;
  if (actualFactor === 1) return;

  state.tx = (state.tx - (anchorX - viewport.clientWidth / 2)) * actualFactor + (anchorX - viewport.clientWidth / 2);
  state.ty = (state.ty - (anchorY - viewport.clientHeight / 2)) * actualFactor + (anchorY - viewport.clientHeight / 2);
  state.scale = next;
  applyTransform();
}

function openImg(title, src) {
  modalTitle.textContent = title;
  modalImg.src = src;

  state.open = true;
  modal.classList.add("open");

  modalImg.onload = () => {
    fitToView();
  };
}

function closeImg() {
  state.open = false;
  state.dragging = false;
  modal.classList.remove("open");
  modalImg.src = "";
}

// Buttons
document.getElementById("imgModalClose").addEventListener("click", closeImg);
document.getElementById("imgReset").addEventListener("click", resetView);
document.getElementById("imgFit").addEventListener("click", fitToView);
document.getElementById("imgZoomIn").addEventListener("click", () => zoomAt(1.15));
document.getElementById("imgZoomOut").addEventListener("click", () => zoomAt(1 / 1.15));

// Click outside closes
modal.addEventListener("click", (e) => {
  if (e.target.id === "imgModal") closeImg();
});

// ESC closes
document.addEventListener("keydown", (e) => {
  if (!state.open) return;
  if (e.key === "Escape") closeImg();
});

// Wheel zoom (trackpad/mouse)
viewport.addEventListener("wheel", (e) => {
  if (!state.open) return;
  e.preventDefault();

  const rect = viewport.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
  zoomAt(factor, x, y);
}, { passive: false });

// Drag to pan
viewport.addEventListener("mousedown", (e) => {
  if (!state.open) return;
  state.dragging = true;
  state.dragStartX = e.clientX;
  state.dragStartY = e.clientY;
  state.dragOrigTx = state.tx;
  state.dragOrigTy = state.ty;
});

document.addEventListener("mousemove", (e) => {
  if (!state.open || !state.dragging) return;
  state.tx = state.dragOrigTx + (e.clientX - state.dragStartX);
  state.ty = state.dragOrigTy + (e.clientY - state.dragStartY);
  applyTransform();
});

document.addEventListener("mouseup", () => {
  state.dragging = false;
});

function renderOverview({modules, moduleGraph, callgraph, patterns, dataflow}) {
  const errs =
    (modules.errors || []).length +
    (moduleGraph.errors || []).length +
    (callgraph.errors || []).length +
    (patterns.errors || []).length +
    (dataflow.errors || []).length;

  const pill = errs
    ? el("span", {class: "pill warn"}, [`Warnings: ${errs}`])
    : el("span", {class: "pill ok"}, ["OK"]);

  const moduleEdges = (moduleGraph.edges || []).length;
  const fnCount = (callgraph.functions || []).length;
  const callCount = (callgraph.calls || []).length;
  const filesCount = (modules.imports || []).length;
  const patCount = (patterns.patterns || []).reduce((acc, p) => acc + ((p.patterns || []).length), 0);
  const dfCount = (dataflow.functions || []).length;

  return el("div", {}, [
    pill,
    el("div", {class: "stats-grid", style: "margin-top:12px;"}, [
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Files"]), el("div", {class:"v"}, [String(filesCount)])]),
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Functions"]), el("div", {class:"v"}, [String(fnCount)])]),
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Calls"]), el("div", {class:"v"}, [String(callCount)])]),
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Module edges"]), el("div", {class:"v"}, [String(moduleEdges)])]),
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Pattern hits"]), el("div", {class:"v"}, [String(patCount)])]),
      el("div", {class:"stat"}, [el("div", {class:"k"}, ["Dataflow fns"]), el("div", {class:"v"}, [String(dfCount)])]),
    ])
  ]);
}

function renderGraphs() {
  const imgs = [
    {file: "module_graph.png", title: "Module Graph"},
    {file: "callgraph.png", title: "Call Graph"},
    {file: "callgraph_grouped.png", title: "Call Graph (Grouped)"},
    {file: "dataflow.png", title: "Dataflow"},
    {file: "imports.png", title: "Imports"},
  ];

  const wrap = el("div", {class:"graph-grid"});
  imgs.forEach(i => {
    const src = `img/${i.file}`;
    const img = new Image();
    img.src = src;

    img.onload = () => {
      const card = el("div", {class:"graph-thumb"}, []);
      card.appendChild(img);
      card.appendChild(el("div", {class:"t"}, [i.title]));
      img.addEventListener("click", () => openImg(i.title, src));
      wrap.appendChild(card);
    };

    img.onerror = () => {
      // Missing images are common if render step was disabled; ignore silently.
    };
  });

  return wrap;
}

function makeIndex({modules, callgraph, callgraphResolved, patterns, dataflow}) {
  const files = (modules.imports || []).map(r => r.file).sort();

  const importsByFile = new Map();
  (modules.imports || []).forEach(r => importsByFile.set(r.file, r));

  const patternsByFile = new Map();
  (patterns.patterns || []).forEach(p => patternsByFile.set(p.file, p.patterns || []));

  const callsByFile = new Map();
  (callgraph.calls || []).forEach(c => {
    const arr = callsByFile.get(c.file) || [];
    arr.push(c);
    callsByFile.set(c.file, arr);
  });

  const resolvedCallsByFile = new Map();
  (callgraphResolved?.calls || []).forEach(c => {
    const arr = resolvedCallsByFile.get(c.file) || [];
    arr.push(c);
    resolvedCallsByFile.set(c.file, arr);
  });

  const dataflowByFile = new Map();
  (dataflow.functions || []).forEach(f => {
    const arr = dataflowByFile.get(f.file) || [];
    arr.push(f);
    dataflowByFile.set(f.file, arr);
  });

  const functions = (callgraph.functions || []).map(f => f.qualname).sort();
  const functionMeta = new Map();
  (callgraph.functions || []).forEach(f => functionMeta.set(f.qualname, f));

  const calleesByCaller = new Map();
  const callersByCallee = new Map();
  (callgraphResolved?.calls || []).forEach(c => {
    const caller = c.caller;
    const callee = c.callee_resolved || c.callee_raw;

    const out1 = calleesByCaller.get(caller) || [];
    out1.push(c);
    calleesByCaller.set(caller, out1);

    const out2 = callersByCallee.get(callee) || [];
    out2.push(c);
    callersByCallee.set(callee, out2);
  });

  return {
    files,
    importsByFile,
    patternsByFile,
    callsByFile,
    resolvedCallsByFile,
    dataflowByFile,
    functions,
    functionMeta,
    calleesByCaller,
    callersByCallee
  };
}

function renderList(items, filterText, onSelect, selectedValue) {
  const q = (filterText || "").toLowerCase();
  const filtered = items.filter(x => x.toLowerCase().includes(q));

  const list = el("div");
  filtered.forEach(x => {
    list.appendChild(el("div", {
      class: "item" + (x === selectedValue ? " active" : ""),
      onclick: () => onSelect(x),
      title: x
    }, [x]));
  });
  return list;
}

function renderFileDetails(file, index) {
  const importsRec = index.importsByFile.get(file);
  const fileImports = (importsRec?.imports || []);
  const importItems = (importsRec?.items || []);
  const pats = index.patternsByFile.get(file) || [];
  const calls = (index.callsByFile.get(file) || []);
  const rcalls = (index.resolvedCallsByFile.get(file) || []);
  const flows = (index.dataflowByFile.get(file) || []);

  return el("div", {}, [
    el("div", {class:"section-title"}, ["File"]),
    el("pre", {class:"mono"}, [file]),

    el("div", {class:"section-title"}, ["Patterns"]),
    pats.length ? el("pre", {class:"mono"}, [pats.join("\n")]) : el("div", {class:"muted"}, ["None detected."]),

    el("div", {class:"section-title"}, ["Imports (flattened)"]),
    fileImports.length ? el("pre", {class:"mono"}, [fileImports.join("\n")]) : el("div", {class:"muted"}, ["None."]),

    el("div", {class:"section-title"}, ["Imports (structured)"]),
    importItems.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Raw"]),
        el("th", {}, ["Kind"]),
        el("th", {}, ["Module"]),
        el("th", {}, ["Lvl"]),
        el("th", {}, ["Names"]),
      ])]));
      const tb = el("tbody");
      importItems.slice(0, 80).forEach(it => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [it.raw || ""]),
          el("td", {}, [it.kind || ""]),
          el("td", {class:"mono"}, [it.module || ""]),
          el("td", {}, [String(it.level ?? "")]),
          el("td", {class:"mono"}, [(it.names || []).join(", ")]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["None."]),

    el("div", {class:"section-title"}, ["Calls (sample)"]),
    calls.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Callee"]),
        el("th", {}, ["Line"]),
      ])]));
      const tb = el("tbody");
      calls.slice(0, 80).forEach(c => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [c.caller || ""]),
          el("td", {class:"mono"}, [c.callee || ""]),
          el("td", {}, [String(c.lineno || "")]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["None."]),

    el("div", {class:"section-title"}, ["Resolved calls (sample)"]),
    rcalls.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Resolved"]),
        el("th", {}, ["Line"]),
      ])]));
      const tb = el("tbody");
      rcalls.slice(0, 80).forEach(c => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [c.caller || ""]),
          el("td", {class:"mono"}, [c.callee_raw || ""]),
          el("td", {class:"mono"}, [c.callee_resolved || ""]),
          el("td", {}, [String(c.lineno || "")]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["callgraph_resolved.json missing or no calls."]),

    el("div", {class:"section-title"}, ["Dataflow functions (sample)"]),
    flows.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Function"]),
        el("th", {}, ["Inputs"]),
        el("th", {}, ["Transforms"]),
        el("th", {}, ["Outputs"]),
      ])]));
      const tb = el("tbody");
      flows.slice(0, 40).forEach(it => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [it.function || ""]),
          el("td", {class:"mono"}, [(it.inputs || []).join(", ")]),
          el("td", {class:"mono"}, [(it.transforms || []).slice(0, 10).join(", ")]),
          el("td", {class:"mono"}, [(it.outputs || []).join(", ")]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["None."]),
  ]);
}

function renderFunctionDetails(fn, index) {
  const meta = index.functionMeta.get(fn);
  const callers = index.callersByCallee.get(fn) || [];
  const callees = index.calleesByCaller.get(fn) || [];

  return el("div", {}, [
    el("div", {class:"section-title"}, ["Function"]),
    el("pre", {class:"mono"}, [fn]),

    meta ? el("div", {}, [
      el("div", {class:"section-title"}, ["Location"]),
      el("pre", {class:"mono"}, [`${meta.file || ""}:${meta.lineno || ""}`]),
    ]) : el("div", {class:"muted"}, ["No metadata found."]),

    el("div", {class:"section-title"}, ["Calls made (sample)"]),
    callees.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Callee (resolved/raw)"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Line"]),
        el("th", {}, ["File"]),
      ])]));
      const tb = el("tbody");
      callees.slice(0, 120).forEach(c => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [c.callee_resolved || c.callee_raw || ""]),
          el("td", {class:"mono"}, [c.callee_raw || ""]),
          el("td", {}, [String(c.lineno || "")]),
          el("td", {class:"mono"}, [c.file || ""]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["No calls recorded."]),

    el("div", {class:"section-title"}, ["Callers (sample)"]),
    callers.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Line"]),
        el("th", {}, ["File"]),
      ])]));
      const tb = el("tbody");
      callers.slice(0, 120).forEach(c => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [c.caller || ""]),
          el("td", {class:"mono"}, [c.callee_raw || ""]),
          el("td", {}, [String(c.lineno || "")]),
          el("td", {class:"mono"}, [c.file || ""]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["No callers recorded (or callgraph_resolved.json missing)."]),
  ]);
}

function setActiveTab(active) {
  document.getElementById("tabFiles").classList.toggle("active", active === "files");
  document.getElementById("tabFunctions").classList.toggle("active", active === "functions");
}

(async function main() {
  try {
    const [modules, moduleGraph, callgraph, patterns, dataflow] = await Promise.all([
      loadJson("modules.json"),
      loadJson("module_graph.json"),
      loadJson("callgraph.json"),
      loadJson("patterns.json"),
      loadJson("dataflow.json"),
    ]);

    let callgraphResolved = null;
    try { callgraphResolved = await loadJson("callgraph_resolved.json"); } catch (e) {}

    clear(document.getElementById("overview"));
    document.getElementById("overview").appendChild(
      renderOverview({modules, moduleGraph, callgraph, patterns, dataflow})
    );

    const graphsHost = document.getElementById("graphs");
    clear(graphsHost);
    graphsHost.appendChild(renderGraphs());

    const index = makeIndex({modules, callgraph, callgraphResolved, patterns, dataflow});

    let mode = "files";
    let selectedFile = index.files[0] || null;
    let selectedFn = index.functions[0] || null;

    function selectedValue() { return mode === "functions" ? selectedFn : selectedFile; }
    function setSelected(v) { if (mode === "functions") selectedFn = v; else selectedFile = v; }

    function refreshList() {
      const q = document.getElementById("globalSearch").value || "";
      const host = document.getElementById("masterList");
      clear(host);

      const items = mode === "functions" ? index.functions : index.files;

      host.appendChild(renderList(items, q, (v) => {
        setSelected(v);
        refreshDetails();
        refreshList();
      }, selectedValue()));
    }

    function refreshDetails() {
      const host = document.getElementById("details");
      clear(host);

      if (mode === "functions") {
        if (!selectedFn) return host.appendChild(el("div", {class:"muted"}, ["No functions."]));
        host.appendChild(renderFunctionDetails(selectedFn, index));
        return;
      }

      if (!selectedFile) return host.appendChild(el("div", {class:"muted"}, ["No files."]));
      host.appendChild(renderFileDetails(selectedFile, index));
    }

    document.getElementById("globalSearch").addEventListener("input", refreshList);

    document.getElementById("tabFiles").addEventListener("click", () => {
      mode = "files";
      setActiveTab("files");
      refreshList();
      refreshDetails();
    });
    document.getElementById("tabFunctions").addEventListener("click", () => {
      mode = "functions";
      setActiveTab("functions");
      refreshList();
      refreshDetails();
    });

    refreshList();
    refreshDetails();
  } catch (e) {
    console.error(e);
    document.getElementById("overview").textContent =
      "Failed to load report data. Try: cd report && python -m http.server";
  }
})();
</script>
</body>
</html>
"""