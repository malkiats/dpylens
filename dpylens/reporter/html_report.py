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


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>dPyLens Report</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }
    .muted { color: #555; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
    h1, h2, h3 { margin-top: 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #eee; text-align: left; padding: 6px 8px; vertical-align: top; }
    code { background: #f6f6f6; padding: 2px 4px; border-radius: 4px; }
    img { max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 8px; }
    .pill { display: inline-block; padding: 2px 8px; border: 1px solid #ddd; border-radius: 999px; margin-right: 6px; font-size: 12px; }
    .ok { border-color: #9ad29a; background: #f0fff0; }
    .warn { border-color: #e6c37a; background: #fff9ea; }
    .row3 { display: grid; grid-template-columns: 320px 320px 1fr; gap: 16px; margin-top: 8px; }
    .list { max-height: 520px; overflow: auto; border: 1px solid #eee; border-radius: 8px; }
    .list-item { padding: 8px 10px; cursor: pointer; border-bottom: 1px solid #f2f2f2; }
    .list-item:hover { background: #fafafa; }
    .list-item.active { background: #eef6ff; }
    .k { font-weight: 600; }
    .search { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #ddd; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    .tabs { display: flex; gap: 8px; margin: 8px 0 0 0; }
    .tab { padding: 6px 10px; border: 1px solid #ddd; border-radius: 999px; cursor: pointer; user-select: none; }
    .tab.active { background: #eef6ff; border-color: #a6c8ff; }
  </style>
</head>
<body>
  <h1>dPyLens Report</h1>
  <p class="muted">
    If data doesn't load when opening this file directly, run:
    <code>python -m http.server</code> in the <code>report/</code> folder and open <code>http://localhost:8000</code>.
  </p>

  <div class="card">
    <h2>Overview</h2>
    <div id="overview">Loading...</div>
  </div>

  <div class="card">
    <h2>Explorer</h2>
    <div class="tabs">
      <div id="tabFiles" class="tab active">Files</div>
      <div id="tabFunctions" class="tab">Functions</div>
    </div>

    <div class="row3">
      <div class="card" style="margin:0;">
        <h3 style="margin-top:0">Files</h3>
        <input id="fileSearch" class="search mono" placeholder="Search files..." />
        <div id="fileList" class="list" style="margin-top:10px;"></div>
      </div>

      <div class="card" style="margin:0;">
        <h3 style="margin-top:0">Functions</h3>
        <input id="fnSearch" class="search mono" placeholder="Search functions..." />
        <div id="fnList" class="list" style="margin-top:10px;"></div>
      </div>

      <div class="card" style="margin:0;">
        <h3 style="margin-top:0">Details</h3>
        <div id="details" class="muted">Select a file or function.</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Graphs</h2>
    <div class="muted" style="margin-bottom:8px;">Rendered from DOT via Graphviz if available.</div>
    <div id="graphs"></div>
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

function renderGraphs() {
  const imgs = [
    {file: "module_graph.png", title: "Module Graph"},
    {file: "callgraph.png", title: "Call Graph"},
    {file: "callgraph_grouped.png", title: "Call Graph (Grouped)"},
    {file: "dataflow.png", title: "Dataflow"},
    {file: "imports.png", title: "Imports"},
  ];
  const wrap = el("div");
  imgs.forEach(i => {
    const img = new Image();
    img.src = `img/${i.file}`;
    img.onload = () => {
      wrap.appendChild(el("div", {style:"margin-bottom:12px"}, [
        el("div", {class:"muted", style:"margin-bottom:6px"}, [i.title]),
        img
      ]));
    };
  });
  return wrap;
}

function renderOverview({modules, moduleGraph, callgraph, patterns, dataflow}) {
  const importsCount = (modules.imports || []).length;
  const moduleEdges = (moduleGraph.edges || []).length;
  const localEdges = (moduleGraph.edges || []).filter(e => e.kind === "local").length;
  const externalEdges = moduleEdges - localEdges;

  const fnCount = (callgraph.functions || []).length;
  const callCount = (callgraph.calls || []).length;

  const patternCount = (patterns.patterns || []).length;
  const dataflowFns = (dataflow.functions || []).length;

  const errs =
    (modules.errors || []).length ||
    (moduleGraph.errors || []).length ||
    (callgraph.errors || []).length ||
    (patterns.errors || []).length ||
    (dataflow.errors || []).length;

  const status = errs ? el("span", {class: "pill warn"}, [`Warnings: ${errs}`]) : el("span", {class: "pill ok"}, ["OK"]);

  return el("div", {}, [
    status,
    el("div", {style:"margin-top:8px"}, [
      el("div", {}, [`Files analyzed: `, el("code", {}, [String(importsCount)])]),
      el("div", {}, [`Functions: `, el("code", {}, [String(fnCount)])]),
      el("div", {}, [`Calls: `, el("code", {}, [String(callCount)])]),
      el("div", {}, [`Module edges: `, el("code", {}, [String(moduleEdges)]), ` (local: ${localEdges}, external: ${externalEdges})`]),
      el("div", {}, [`Pattern hits: `, el("code", {}, [String(patternCount)])]),
      el("div", {}, [`Dataflow functions: `, el("code", {}, [String(dataflowFns)])]),
    ]),
  ]);
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
  const list = el("div");
  const q = (filterText || "").toLowerCase();
  const filtered = items.filter(x => x.toLowerCase().includes(q));

  filtered.forEach(x => {
    list.appendChild(el("div", {
      class: "list-item" + (x === selectedValue ? " active" : ""),
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

  const wrap = el("div", {}, [
    el("div", {}, [el("span", {class:"k"}, ["File: "]), el("code", {class:"mono"}, [file])]),

    el("h4", {style:"margin-top:12px"}, ["Patterns"]),
    pats.length ? el("div", {}, [pats.map(p => el("span", {class:"pill ok"}, [p]))]) : el("div", {class:"muted"}, ["None detected."]),

    el("h4", {style:"margin-top:12px"}, ["Imports (flattened)"]),
    fileImports.length ? el("pre", {class:"mono", style:"white-space:pre-wrap;margin:0"}, [fileImports.join("\\n")]) : el("div", {class:"muted"}, ["None."]),

    el("h4", {style:"margin-top:12px"}, ["Imports (structured)"]),
    importItems.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Raw"]),
        el("th", {}, ["Kind"]),
        el("th", {}, ["Module"]),
        el("th", {}, ["Level"]),
        el("th", {}, ["Names"]),
      ])]));
      const tb = el("tbody");
      importItems.slice(0, 50).forEach(it => {
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

    el("h4", {style:"margin-top:12px"}, ["Calls from this file (sample)"]),
    calls.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Callee"]),
        el("th", {}, ["Line"]),
      ])]));
      const tb = el("tbody");
      calls.slice(0, 50).forEach(c => {
        tb.appendChild(el("tr", {}, [
          el("td", {class:"mono"}, [c.caller || ""]),
          el("td", {class:"mono"}, [c.callee || ""]),
          el("td", {}, [String(c.lineno || "")]),
        ]));
      });
      t.appendChild(tb);
      return t;
    })() : el("div", {class:"muted"}, ["None."]),

    el("h4", {style:"margin-top:12px"}, ["Resolved calls (sample)"]),
    rcalls.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Resolved"]),
        el("th", {}, ["Line"]),
      ])]));
      const tb = el("tbody");
      rcalls.slice(0, 50).forEach(c => {
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

    el("h4", {style:"margin-top:12px"}, ["Dataflow functions (sample)"]),
    flows.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Function"]),
        el("th", {}, ["Inputs"]),
        el("th", {}, ["Transforms"]),
        el("th", {}, ["Outputs"]),
      ])]));
      const tb = el("tbody");
      flows.slice(0, 30).forEach(it => {
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

  return wrap;
}

function renderFunctionDetails(fn, index) {
  const meta = index.functionMeta.get(fn);
  const callers = index.callersByCallee.get(fn) || [];
  const callees = index.calleesByCaller.get(fn) || [];

  const wrap = el("div", {}, [
    el("div", {}, [el("span", {class:"k"}, ["Function: "]), el("code", {class:"mono"}, [fn])]),
    meta ? el("div", {style:"margin-top:8px"}, [
      el("div", {}, [el("span", {class:"k"}, ["File: "]), el("code", {class:"mono"}, [meta.file || ""])]),
      el("div", {}, [el("span", {class:"k"}, ["Line: "]), String(meta.lineno || "")]),
    ]) : el("div", {class:"muted"}, ["No metadata found."]),

    el("h4", {style:"margin-top:12px"}, ["Calls made by this function (sample)"]),
    callees.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Callee (resolved/raw)"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Line"]),
        el("th", {}, ["File"]),
      ])]));
      const tb = el("tbody");
      callees.slice(0, 80).forEach(c => {
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

    el("h4", {style:"margin-top:12px"}, ["Callers of this function (sample)"]),
    callers.length ? (() => {
      const t = el("table");
      t.appendChild(el("thead", {}, [el("tr", {}, [
        el("th", {}, ["Caller"]),
        el("th", {}, ["Raw"]),
        el("th", {}, ["Line"]),
        el("th", {}, ["File"]),
      ])]));
      const tb = el("tbody");
      callers.slice(0, 80).forEach(c => {
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

  return wrap;
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
    document.getElementById("overview").appendChild(renderOverview({modules, moduleGraph, callgraph, patterns, dataflow}));

    document.getElementById("graphs").appendChild(renderGraphs());

    const index = makeIndex({modules, callgraph, callgraphResolved, patterns, dataflow});

    let mode = "files";
    let selectedFile = index.files[0] || null;
    let selectedFn = index.functions[0] || null;

    function refreshFileList() {
      const q = document.getElementById("fileSearch").value || "";
      const host = document.getElementById("fileList");
      clear(host);
      host.appendChild(renderList(index.files, q, (f) => {
        mode = "files";
        setActiveTab("files");
        selectedFile = f;
        refreshDetails();
        refreshFileList();
      }, selectedFile));
    }

    function refreshFnList() {
      const q = document.getElementById("fnSearch").value || "";
      const host = document.getElementById("fnList");
      clear(host);
      host.appendChild(renderList(index.functions, q, (fn) => {
        mode = "functions";
        setActiveTab("functions");
        selectedFn = fn;
        refreshDetails();
        refreshFnList();
      }, selectedFn));
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

    document.getElementById("fileSearch").addEventListener("input", () => refreshFileList());
    document.getElementById("fnSearch").addEventListener("input", () => refreshFnList());

    document.getElementById("tabFiles").addEventListener("click", () => {
      mode = "files";
      setActiveTab("files");
      refreshDetails();
    });
    document.getElementById("tabFunctions").addEventListener("click", () => {
      mode = "functions";
      setActiveTab("functions");
      refreshDetails();
    });

    refreshFileList();
    refreshFnList();
    refreshDetails();
  } catch (e) {
    console.error(e);
    document.getElementById("overview").textContent = "Failed to load report data. Try: cd report && python -m http.server";
  }
})();
</script>
</body>
</html>
"""