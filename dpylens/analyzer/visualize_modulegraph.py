from __future__ import annotations

from dpylens.analyzer.modulegraph import ModuleEdge, ModuleNode


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_module_graph_dot(nodes: list[ModuleNode], edges: list[ModuleEdge]) -> str:
    """
    DOT graph:
      local module -> local module (blue)
      local module -> external import string (gray)
    """
    lines = [
        "digraph module_graph {",
        '  rankdir="LR";',
        '  node [fontsize=10, shape="box"];',
        '  edge [fontsize=9];',
    ]

    # nodes
    for n in nodes:
        m = _dot_escape(n.module)
        lines.append(f'  "{m}" [shape="box"];')

    # edges
    for e in edges:
        src = _dot_escape(e.src_module)
        dst = _dot_escape(e.dst_module)

        if e.kind == "local":
            lines.append(f'  "{src}" -> "{dst}" [color="blue"];')
        else:
            lines.append(f'  "{src}" -> "{dst}" [color="gray"];')

    lines.append("}")
    return "\n".join(lines)