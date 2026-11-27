"""Static extractors.  They parse source text only; nothing is imported or run."""
from __future__ import annotations

import ast
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from .core import Edge, Node

FRAMEWORK_KINDS = {
    "ir.ui.view": "view",
    "ir.ui.view.custom": "view",
    "ir.actions.actions": "action",
    "ir.actions.act_window": "action",
    "ir.actions.act_window.view": "action",
    "ir.actions.act_window_close": "action",
    "ir.actions.act_url": "action",
    "ir.actions.client": "action",
    "ir.actions.server": "action",
    "ir.actions.todo": "action",
    "ir.actions.report": "action",
    "ir.embedded.actions": "action",
    "ir.ui.menu": "menu",
    "res.groups": "group",
    "ir.rule": "rule",
    "ir.model.access": "acl",
}


def _rel(path: Path, source_root: Path) -> str:
    return path.relative_to(source_root).as_posix()


def _line_of(text: str, needle: str) -> int:
    for lineno, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return lineno
    return 1


def extract_python(source_root: Path, module: str, versions: tuple[str, ...]) -> tuple[list[Node], list[Edge], list[str]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    diagnostics: list[str] = []
    module_dir = source_root / "addons" / module

    for path in sorted(module_dir.rglob("*.py")):
        if "test" in path.parts or "__pycache__" in path.parts:
            continue
        rel = _rel(path, source_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            diagnostics.append(f"{rel}: parse failed: {exc.msg}")
            continue

        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            model_name = None
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "_name" for t in stmt.targets
                ) and isinstance(stmt.value, ast.Constant):
                    model_name = stmt.value.value
            if not model_name:
                continue

            model_anchor = f"{rel}:L{cls.lineno}"
            nodes.append(Node(
                id=model_name, kind="model", ownership="code_first",
                source_anchor=model_anchor, evidence="repository-fact",
                odoo_versions=versions,
                attributes={"class": cls.name, "module": module},
            ))

            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    ftype = None
                    if isinstance(func, ast.Attribute):
                        owner = getattr(func.value, "id", None)
                        ftype = f"fields.{func.attr}" if owner == "fields" else func.attr
                    else:
                        ftype = getattr(func, "id", None)
                    target = stmt.targets[0] if len(stmt.targets) == 1 else None
                    if ftype and ftype.startswith("fields.") and isinstance(target, ast.Name):
                        field_id = f"{model_name}.{target.id}"
                        nodes.append(Node(
                            id=field_id, kind="field", ownership="code_first",
                            source_anchor=f"{rel}:L{stmt.lineno}", evidence="repository-fact",
                            odoo_versions=versions,
                            attributes={"type": ftype, "model": model_name, "module": module},
                        ))
                        edges.append(Edge(
                            id=f"e:{model_name}>{field_id}:defines", source=model_name,
                            target=field_id, type="defines", source_anchor=model_anchor,
                            evidence="repository-fact",
                        ))

                if not isinstance(stmt, ast.FunctionDef):
                    continue
                method_id = f"{model_name}.{stmt.name}"
                anchor = f"{rel}:L{stmt.lineno}"
                decorators = [ast.unparse(d) for d in stmt.decorator_list]
                nodes.append(Node(
                    id=method_id, kind="method", ownership="code_first",
                    source_anchor=anchor, evidence="repository-fact",
                    odoo_versions=versions,
                    attributes={"model": model_name, "module": module, "decorators": decorators},
                ))
                edges.append(Edge(
                    id=f"e:{model_name}>{method_id}:defines", source=model_name,
                    target=method_id, type="defines", source_anchor=anchor,
                    evidence="repository-fact",
                ))

                trigger = None
                for decorator in decorators:
                    if "constrains" in decorator:
                        trigger = "constraint"
                    elif "depends" in decorator:
                        trigger = "compute"
                    elif "onchange" in decorator:
                        trigger = "onchange"
                if trigger is None and not stmt.name.startswith(("action_", "_compute_")):
                    continue

                condition = None
                effects: list[str] = []
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.If) and condition is None:
                        condition = ast.unparse(sub.test)
                    elif isinstance(sub, ast.Assign) and len(effects) < 5:
                        if any(isinstance(t, (ast.Attribute, ast.Subscript)) for t in sub.targets):
                            effects.append(ast.unparse(sub))
                    elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                        if sub.func.attr == "super" and "super() chain" not in effects:
                            effects.append("super() chain")

                logic_id = f"{method_id}#logic"
                nodes.append(Node(
                    id=logic_id, kind="logic", ownership="code_first",
                    source_anchor=anchor, evidence="repository-fact",
                    odoo_versions=versions, carrier="python",
                    trigger=trigger or "method", condition=condition,
                    effect=tuple(effects[:5]),
                    bindings={"model": model_name, "method": method_id},
                    attributes={"module": module, "decorators": decorators},
                ))
                edges.append(Edge(
                    id=f"e:{logic_id}>{model_name}:calls", source=logic_id,
                    target=model_name, type="calls", source_anchor=anchor,
                    evidence="repository-fact",
                ))

    return nodes, edges, diagnostics


def extract_xml(source_root: Path, module: str, versions: tuple[str, ...]) -> tuple[list[Node], list[Edge], list[str]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    diagnostics: list[str] = []
    module_dir = source_root / "addons" / module

    for path in sorted(module_dir.rglob("*.xml")):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path, source_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            diagnostics.append(f"{rel}: XML parse failed: {exc}")
            continue

        noupdate = any(el.tag == "data" and el.get("noupdate") == "1" for el in root.iter())
        for elem in root.iter():
            if elem.tag == "record":
                xmlid = elem.get("id")
                model = elem.get("model")
                kind = FRAMEWORK_KINDS.get(model or "")
                if not xmlid or not kind:
                    continue
                node_id = xmlid if "." in xmlid else f"{module}.{xmlid}"
                anchor = f"{rel}:record:{xmlid}"
                attributes = {"model": model, "module": module, "xmlid": xmlid}
                if noupdate:
                    attributes["noupdate"] = True
                field_values = {
                    field.get("name"): (field.get("ref") or (field.text or "").strip())
                    for field in elem.findall("field")
                }
                if model == "ir.ui.view":
                    attributes["view_model"] = field_values.get("model", "")
                if model.startswith("ir.actions."):
                    attributes["action_model"] = field_values.get("res_model", "")
                if model == "ir.model.access":
                    attributes["acl_model"] = field_values.get("model_id", "")
                nodes.append(Node(
                    id=node_id, kind=kind, ownership="code_first",
                    source_anchor=anchor, evidence="repository-fact",
                    odoo_versions=versions, attributes=attributes,
                ))

                bound_model = attributes.get("view_model") or attributes.get("action_model") or attributes.get("acl_model")
                if bound_model and kind in {"view", "action", "acl", "rule"}:
                    edges.append(Edge(
                        id=f"e:{node_id}>{bound_model}:binds", source=node_id,
                        target=bound_model, type="guards" if kind in {"acl", "rule"} else "binds",
                        source_anchor=anchor, evidence="repository-fact",
                    ))
                if kind == "menu" and attributes.get("action"):
                    action_ref = attributes["action"]
                    action_id = action_ref if "." in action_ref else f"{module}.{action_ref}"
                    edges.append(Edge(
                        id=f"e:{node_id}>{action_id}:binds", source=node_id,
                        target=action_id, type="binds",
                        source_anchor=anchor, evidence="repository-fact",
                    ))

                if model == "ir.ui.view":
                    arch = elem.find("./field[@name='arch']")
                    if arch is not None:
                        for button in arch.iter("button"):
                            name = button.get("name")
                            if not name:
                                continue
                            logic_id = f"{node_id}#button.{name}"
                            nodes.append(Node(
                                id=logic_id, kind="logic", ownership="code_first",
                                source_anchor=anchor, evidence="repository-fact",
                                odoo_versions=versions, carrier="view", trigger="button",
                                effect=(f"call {name}",),
                                bindings={"view": node_id, "method": name},
                                attributes={"module": module, "button": name},
                            ))
                            edges.append(Edge(
                                id=f"e:{logic_id}>{node_id}:binds", source=logic_id,
                                target=node_id, type="binds", source_anchor=anchor,
                                evidence="repository-fact",
                            ))
                        for field in arch.iter("field"):
                            field_name = field.get("name")
                            for modifier in ("invisible", "readonly", "required"):
                                if field.get(modifier) is None:
                                    continue
                                logic_id = f"{node_id}#field.{field_name}.{modifier}"
                                nodes.append(Node(
                                    id=logic_id, kind="logic", ownership="code_first",
                                    source_anchor=anchor, evidence="repository-fact",
                                    odoo_versions=versions, carrier="view", trigger="event",
                                    condition=field.get(modifier),
                                    effect=(f"set {modifier} on {field_name}",),
                                    bindings={"view": node_id, "field": field_name or ""},
                                    attributes={"module": module, "modifier": modifier},
                                ))
            elif elem.tag == "menuitem":
                xmlid = elem.get("id")
                if not xmlid:
                    continue
                node_id = xmlid if "." in xmlid else f"{module}.{xmlid}"
                anchor = f"{rel}:record:{xmlid}"
                attributes = {"module": module, "xmlid": xmlid}
                if elem.get("action"):
                    attributes["action"] = elem.get("action")
                nodes.append(Node(
                    id=node_id, kind="menu", ownership="code_first",
                    source_anchor=anchor, evidence="repository-fact",
                    odoo_versions=versions, attributes=attributes,
                ))

    return nodes, edges, diagnostics


def extract_owl(source_root: Path, module: str, versions: tuple[str, ...]) -> tuple[list[Node], list[Edge], list[str]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    diagnostics: list[str] = []
    static_dir = source_root / "addons" / module / "static" / "src"
    if not static_dir.is_dir():
        return nodes, edges, diagnostics

    rpc_re = re.compile(r"rpc\s*\(\s*['\"]([\w.]+)['\"]\s*,\s*['\"](\w+)['\"]")
    component_re = re.compile(r"class\s+(\w+)\s+extends\s+Component")
    event_re = re.compile(r"t-on-[\w-]+=\"(\w+)\"")

    for path in sorted(static_dir.rglob("*")):
        if path.suffix not in {".js", ".ts", ".xml"}:
            continue
        rel = _rel(path, source_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix in {".js", ".ts"}:
            for match in rpc_re.finditer(text):
                model, method = match.group(1), match.group(2)
                lineno = text[: match.start()].count("\n") + 1
                logic_id = f"{module}.OwlRpc:{lineno}"
                nodes.append(Node(
                    id=logic_id, kind="logic", ownership="code_first",
                    source_anchor=f"{rel}:L{lineno}", evidence="repository-fact",
                    odoo_versions=versions, carrier="owl", trigger="event",
                    effect=(f"rpc {model}.{method}",),
                    bindings={"model": model, "method": f"{model}.{method}"},
                    attributes={"module": module, "component": "unknown"},
                ))
                edges.append(Edge(
                    id=f"e:{logic_id}>{model}:calls", source=logic_id, target=model,
                    type="calls", source_anchor=f"{rel}:L{lineno}", evidence="repository-fact",
                ))
            for match in component_re.finditer(text):
                lineno = text[: match.start()].count("\n") + 1
                nodes.append(Node(
                    id=f"{module}.{match.group(1)}", kind="method", ownership="code_first",
                    source_anchor=f"{rel}:L{lineno}", evidence="repository-fact",
                    odoo_versions=versions, attributes={"module": module, "component": match.group(1)},
                ))
        else:
            for match in event_re.finditer(text):
                lineno = text[: match.start()].count("\n") + 1
                logic_id = f"{module}.OwlEvent:{lineno}"
                nodes.append(Node(
                    id=logic_id, kind="logic", ownership="code_first",
                    source_anchor=f"{rel}:L{lineno}", evidence="repository-fact",
                    odoo_versions=versions, carrier="owl", trigger="event",
                    effect=(f"handler {match.group(1)}",),
                    bindings={"handler": match.group(1)},
                    attributes={"module": module, "component": "unknown"},
                ))

    return nodes, edges, diagnostics
