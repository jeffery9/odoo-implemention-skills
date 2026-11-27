"""Core primitives for the deterministic Odoo ontology builder.

The builder never imports Odoo, connects to a database, or evaluates source
expressions.  Everything is a derived projection with a physical anchor.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "ontology" / "schema.json"
SCOPE_PATH = REPO_ROOT / "ontology" / "scope.json"


def canonical_json(obj: Any) -> str:
    """Stable serialization: sorted keys, compact separators, UTF-8 text."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_canonical(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(obj) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_hashes(files: Iterable[Path], root: Path) -> tuple[str, dict[str, str]]:
    """Hash canonical artifact bytes; combined hash is manifest.sha256."""
    per_file: dict[str, str] = {}
    for path in sorted(files, key=lambda p: str(p.relative_to(root))):
        rel = str(path.relative_to(root))
        per_file[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    combined = hashlib.sha256(
        "".join(f"{name}\t{digest}\n" for name, digest in per_file.items()).encode("utf-8")
    ).hexdigest()
    return combined, per_file


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    ownership: str
    source_anchor: str
    evidence: str
    odoo_versions: tuple[str, ...] = ()
    carrier: str | None = None
    trigger: str | None = None
    condition: str | None = None
    effect: tuple[str, ...] = ()
    bindings: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["odoo_versions"] = list(self.odoo_versions)
        data["effect"] = list(self.effect)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True)
class Edge:
    id: str
    source: str
    target: str
    type: str
    source_anchor: str
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


def parse_anchor(anchor: str) -> tuple[str, str, str | int] | None:
    """Parse ``path:L123`` or ``path:record:xmlid``."""
    path, sep, rest = anchor.partition(":")
    if not sep or not path or ".." in Path(path).parts:
        return None
    if rest.startswith("L") and rest[1:].isdigit():
        return "line", path, int(rest[1:])
    if rest.startswith("record:") and rest[7:]:
        return "record", path, rest[7:]
    return None


def validate_anchor(anchor: str, source_root: Path) -> str | None:
    """Return an error string when the anchor does not resolve."""
    parsed = parse_anchor(anchor)
    if parsed is None:
        return f"malformed or unsafe anchor: {anchor}"
    kind, rel, value = parsed
    path = source_root / rel
    if not path.is_file():
        return f"anchor file missing: {rel}"
    text = path.read_text(encoding="utf-8", errors="replace")
    if kind == "line":
        lines = text.splitlines()
        if not 1 <= value <= len(lines):
            return f"anchor line out of range: {anchor}"
        if not lines[value - 1].strip():
            return f"anchor line is empty: {anchor}"
        return None
    needle = f'id="{value}"'
    if needle not in text and f"id='{value}'" not in text:
        return f"anchor record id not found: {anchor}"
    return None


def validate_graph(
    nodes: list[Node],
    edges: list[Edge],
    schema: dict,
    source_root: Path,
) -> tuple[list[str], list[str]]:
    """Validate schema, whitelist, anchors and edge endpoints.

    Returns (hard_errors, diagnostics).  Hard errors abort the build.
    """
    errors: list[str] = []
    diagnostics: list[str] = []
    seen: set[str] = set()
    kinds = set(schema["node_kinds"])
    evidence = set(schema["evidence"])
    ownership = set(schema["ownership"])
    framework_kinds = set(schema["framework_record_kinds"])
    whitelist = set(schema["model_whitelist"])
    exclusions = set(schema["model_exclusions"])
    edge_types = set(schema["edge_types"])

    for node in nodes:
        data = node.to_dict()
        for name in schema["required_node_fields"]:
            if not data.get(name):
                errors.append(f"{node.id}: missing required field {name}")
        if data.get("kind") not in kinds:
            errors.append(f"{node.id}: unknown kind {data.get('kind')}")
        if data.get("evidence") not in evidence:
            errors.append(f"{node.id}: unknown evidence {data.get('evidence')}")
        if data.get("ownership") not in ownership:
            errors.append(f"{node.id}: unknown ownership {data.get('ownership')}")
        if node.id in seen:
            errors.append(f"duplicate node id: {node.id}")
        seen.add(node.id)

        if data.get("kind") == "logic":
            for name in schema["required_logic_fields"]:
                if not data.get(name):
                    errors.append(f"{node.id}: logic node missing {name}")
            if (data.get("condition") or data.get("effect")) and not node.source_anchor:
                errors.append(f"{node.id}: condition/effect without source anchor")

        if data.get("kind") in framework_kinds:
            model = data.get("attributes", {}).get("model")
            if model is None and node.kind != "menu":
                errors.append(f"{node.id}: framework record has no model binding")
            elif model is not None and model not in whitelist:
                errors.append(f"{node.id}: framework record model not whitelisted: {model}")
            if model in exclusions:
                errors.append(f"{node.id}: excluded model used as framework record: {model}")
            table = data.get("attributes", {}).get("table", "")
            if table in set(schema["relation_tables"]):
                errors.append(f"{node.id}: m2m relation table must not be a node: {table}")

        anchor_error = validate_anchor(node.source_anchor, source_root)
        if anchor_error:
            errors.append(f"{node.id}: {anchor_error}")

    for edge in edges:
        if edge.type not in edge_types:
            errors.append(f"{edge.id}: unknown edge type {edge.type}")
        if edge.source not in seen:
            errors.append(f"{edge.id}: unresolved source {edge.source}")
        if edge.target not in seen:
            errors.append(f"{edge.id}: unresolved target {edge.target}")
        anchor_error = validate_anchor(edge.source_anchor, source_root)
        if anchor_error:
            errors.append(f"{edge.id}: {anchor_error}")

    if not nodes:
        errors.append("build produced zero nodes")
    return errors, diagnostics


def normalize_evidence(value: str | None) -> str:
    """Unknown evidence degrades to open-question; never silently becomes fact."""
    return value if value in {"platform-fact", "repository-fact", "inference", "open-question"} else "open-question"


def xmlid_to_attribute(xmlid: str) -> str:
    """External id suffix used as the stable technical name."""
    return xmlid.rsplit(".", 1)[-1] if "." in xmlid else xmlid
