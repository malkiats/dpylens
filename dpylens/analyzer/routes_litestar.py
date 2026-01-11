from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import ast
import json


@dataclass(frozen=True)
class LitestarRoute:
    file: str
    controller: str | None
    controller_path: str | None
    router_path: str | None
    http_method: str
    path: str
    handler: str  # qualname-ish
    auth: str | None
    source: str  # "controller" | "function"


@dataclass(frozen=True)
class LitestarRouteReport:
    framework: str
    routes: list[LitestarRoute]
    warnings: list[str]


_HTTP_DECORATORS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _get_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _get_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _get_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _call_kw(call: ast.Call, key: str) -> ast.AST | None:
    for kw in call.keywords or []:
        if kw.arg == key:
            return kw.value
    return None


def _decorator_http_method(dec: ast.AST) -> tuple[str | None, str | None]:
    """
    Returns (method, path) if decorator matches Litestar style:
      @litestar.get()
      @get()
      @litestar.post("/x")
      @post("/{id:int}")
    """
    if isinstance(dec, ast.Call):
        name = _get_name(dec.func) or ""
        short = name.split(".")[-1]
        if short in _HTTP_DECORATORS:
            method = short.upper()
            path = _get_str(dec.args[0]) if dec.args else None
            return method, path
    return None, None


def _join_paths(*parts: str | None) -> str:
    segs: list[str] = []
    for p in parts:
        if not p:
            continue
        segs.append(p.strip())
    s = "/".join([x.strip("/") for x in segs if x.strip("/")])
    return "/" + s if s else "/"


def _is_controller_base(node: ast.ClassDef) -> bool:
    for b in node.bases:
        n = _get_name(b) or ""
        if n.endswith("Controller") or n.endswith("LitestarController"):
            return True
    return False


def _extract_controller_path(cls: ast.ClassDef) -> str | None:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "path":
                    return _get_str(stmt.value)
    return None


def _extract_controller_auth(cls: ast.ClassDef) -> str | None:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id in {"auth_middleware", "middleware"}:
                    if hasattr(ast, "unparse"):
                        try:
                            return ast.unparse(stmt.value)
                        except Exception:
                            return t.id
                    return t.id
    return None


def _extract_router_path_assignments(tree: ast.AST) -> dict[str, str]:
    """
    Find Router(...) assignments like:
      v1_router = Router(path="/v1", route_handlers=[...])
    Returns dict var_name -> router_path
    """
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = (_get_name(node.value.func) or "").split(".")[-1]
            if func != "Router":
                continue
            p = _call_kw(node.value, "path")
            pv = _get_str(p) if p else None
            if not pv:
                continue
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = pv
    return out


def _extract_route_handlers_list(call: ast.Call) -> list[str]:
    """
    Extracts handler identifiers from a `route_handlers=[...]` kwarg.
    Returns list of string names (best-effort).
    """
    rh = _call_kw(call, "route_handlers")
    if not isinstance(rh, (ast.List, ast.Tuple)):
        return []
    out: list[str] = []
    for elt in rh.elts:
        n = _get_name(elt)
        if n:
            out.append(n)
    return out


def _extract_router_handlers_assignments(tree: ast.AST) -> dict[str, list[str]]:
    """
    Map Router var_name -> list of handler names, from `route_handlers=[...]`
    """
    out: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = (_get_name(node.value.func) or "").split(".")[-1]
            if func != "Router":
                continue
            handlers = _extract_route_handlers_list(node.value)
            if not handlers:
                continue
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = handlers
    return out


def _extract_app_handlers_assignments(tree: ast.AST) -> dict[str, list[str]]:
    """
    Find Litestar(...) assignments like:
      app = Litestar(route_handlers=[...])
    Returns dict var_name -> list of handler names
    """
    out: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = (_get_name(node.value.func) or "").split(".")[-1]
            if func != "Litestar":
                continue
            handlers = _extract_route_handlers_list(node.value)
            if not handlers:
                continue
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = handlers
    return out


def _extract_top_level_http_functions(tree: ast.AST, file_rel: str) -> dict[str, dict[str, Any]]:
    """
    Returns mapping: function_name -> { file, endpoints: [{method,path,handler}] }
    Only for top-level functions in a module (not inside classes).
    """
    out: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fn_name = node.name

        endpoints: list[dict[str, Any]] = []
        for dec in node.decorator_list:
            method, path = _decorator_http_method(dec)
            if not method:
                continue
            endpoints.append({"http_method": method, "path": path or "", "handler": fn_name})

        if endpoints:
            out[fn_name] = {"file": file_rel, "endpoints": endpoints}
    return out


def analyze_litestar_routes(root: Path, out_dir: Path) -> LitestarRouteReport:
    warnings: list[str] = []
    routes: list[LitestarRoute] = []

    py_files = list(root.rglob("*.py"))

    # Controller definitions
    controllers: dict[str, dict[str, Any]] = {}
    # Top-level functions with HTTP decorators
    http_functions: dict[str, dict[str, Any]] = {}

    # Router / app wiring
    router_paths_by_var: dict[str, str] = {}
    router_handlers_by_var: dict[str, list[str]] = {}
    app_handlers_by_var: dict[str, list[str]] = {}

    for fp in py_files:
        try:
            src = fp.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(fp))
        except Exception as e:
            warnings.append(f"parse_failed: {fp}: {e}")
            continue

        file_rel = str(fp.relative_to(root))

        router_paths_by_var.update(_extract_router_path_assignments(tree))

        rhs = _extract_router_handlers_assignments(tree)
        for k, v in rhs.items():
            router_handlers_by_var[k] = v

        ahs = _extract_app_handlers_assignments(tree)
        for k, v in ahs.items():
            app_handlers_by_var[k] = v

        http_functions.update(_extract_top_level_http_functions(tree, file_rel))

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not _is_controller_base(node):
                continue

            c_name = node.name
            c_path = _extract_controller_path(node)
            c_auth = _extract_controller_auth(node)

            endpoints: list[dict[str, Any]] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in item.decorator_list:
                        method, path = _decorator_http_method(dec)
                        if not method:
                            continue
                        endpoints.append({"http_method": method, "path": path or "", "handler": item.name})

            controllers[c_name] = {
                "file": file_rel,
                "path": c_path,
                "auth": c_auth,
                "endpoints": endpoints,
            }

    # Build router->path mapping
    router_to_path: dict[str, str] = dict(router_paths_by_var)

    # Helper: resolve "route handler name" to base symbol name
    # e.g. "lapwing_api.v1_router" -> "v1_router"
    def leaf(name: str) -> str:
        return name.split(".")[-1]

    # Router var -> list of handler leaf-names
    router_handlers_leaf: dict[str, list[str]] = {
        router_var: [leaf(x) for x in handlers] for router_var, handlers in router_handlers_by_var.items()
    }

    # App var -> list of handler leaf-names
    app_handlers_leaf: dict[str, list[str]] = {app_var: [leaf(x) for x in handlers] for app_var, handlers in app_handlers_by_var.items()}

    # controller -> router_paths list (Router(route_handlers=[Controller...]))
    controller_to_router_paths: dict[str, list[str]] = {}
    # function -> router_paths list (Router(route_handlers=[fn...]))
    function_to_router_paths: dict[str, list[str]] = {}

    for router_var, handlers in router_handlers_leaf.items():
        rpath = router_to_path.get(router_var)
        if not rpath:
            continue
        for h in handlers:
            if h in controllers:
                controller_to_router_paths.setdefault(h, []).append(rpath)
            if h in http_functions:
                function_to_router_paths.setdefault(h, []).append(rpath)

    # Also handle app = Litestar(route_handlers=[...])
    # For app-level, there's no router_path; but handlers might include Router vars or direct functions/controllers.
    # We'll:
    # - if handler is Router var, attach its router_path when emitting its contained items (already handled above)
    # - if handler is controller, no router_path
    # - if handler is function, no router_path
    app_level_controllers: set[str] = set()
    app_level_functions: set[str] = set()
    for _app_var, handlers in app_handlers_leaf.items():
        for h in handlers:
            if h in controllers:
                app_level_controllers.add(h)
            if h in http_functions:
                app_level_functions.add(h)

    # Emit controller routes
    for c_name, meta in controllers.items():
        c_file = meta["file"]
        c_path = meta.get("path") or ""
        c_auth = meta.get("auth")

        router_paths = controller_to_router_paths.get(c_name)
        if not router_paths:
            # if controller is directly attached to Litestar(route_handlers=[...]) then no router_path
            router_paths = [None] if c_name in app_level_controllers else [None]

        for ep in meta.get("endpoints") or []:
            for rp in router_paths:
                full_path = _join_paths(rp, c_path, ep.get("path"))
                routes.append(
                    LitestarRoute(
                        file=c_file,
                        controller=c_name,
                        controller_path=c_path or None,
                        router_path=rp,
                        http_method=ep["http_method"],
                        path=full_path,
                        handler=f"{c_name}.{ep['handler']}",
                        auth=c_auth,
                        source="controller",
                    )
                )

    # Emit top-level function routes
    for fn_name, meta in http_functions.items():
        f_file = meta["file"]
        router_paths = function_to_router_paths.get(fn_name)
        if not router_paths:
            router_paths = [None] if fn_name in app_level_functions else [None]

        for ep in meta.get("endpoints") or []:
            for rp in router_paths:
                full_path = _join_paths(rp, ep.get("path"))
                routes.append(
                    LitestarRoute(
                        file=f_file,
                        controller=None,
                        controller_path=None,
                        router_path=rp,
                        http_method=ep["http_method"],
                        path=full_path,
                        handler=fn_name,
                        auth=None,
                        source="function",
                    )
                )

    routes.sort(key=lambda r: (r.path, r.http_method, r.handler))

    report = LitestarRouteReport(framework="litestar", routes=routes, warnings=warnings)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "routes.json").write_text(
        json.dumps(
            {"framework": report.framework, "routes": [asdict(r) for r in report.routes], "warnings": report.warnings},
            indent=2,
        ),
        encoding="utf-8",
    )

    return report