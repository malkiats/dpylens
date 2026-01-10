from __future__ import annotations

from dpylens.analyzer.dataflow import FunctionDataFlow


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_dataflow_dot(items: list[FunctionDataFlow]) -> str:
    """
    Simple DOT:
      input_node -> function -> output_node

    This is an MVP visualization so you can quickly render a diagram.
    """
    lines = [
        "digraph dataflow {",
        '  rankdir="LR";',
        '  node [fontsize=10];',
        '  edge [fontsize=9];',
    ]

    for it in items:
        fn = _dot_escape(it.function)
        lines.append(f'  "{fn}" [shape="ellipse"];')

        for inp in it.inputs:
            inp_e = _dot_escape(inp)
            lines.append(f'  "{inp_e}" [shape="box"];')
            lines.append(f'  "{inp_e}" -> "{fn}";')

        for out in it.outputs:
            out_e = _dot_escape(out)
            lines.append(f'  "{out_e}" [shape="box"];')
            lines.append(f'  "{fn}" -> "{out_e}";')

    lines.append("}")
    return "\n".join(lines)