"""Pure deterministic build: sources -> ontology shards + manifest."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .core import (
    Edge, Node, REPO_ROOT, SCHEMA_PATH, SCOPE_PATH, file_hashes, load_json,
    validate_graph, write_canonical,
)
from .extractors import extract_owl, extract_python, extract_xml

GENERATED = {"_generated": True, "_do_not_edit": True}


class BuildError(RuntimeError):
    pass


def _repo_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "open-question"


def build(source_root: Path, out_dir: Path, schema: dict | None = None, scope: dict | None = None) -> dict[str, Any]:
    source_root = Path(source_root).resolve()
    out_dir = Path(out_dir).resolve()
    schema = schema or load_json(SCHEMA_PATH)
    scope = scope or load_json(SCOPE_PATH)
    versions = tuple(scope.get("odoo_versions", ()))

    nodes: list[Node] = []
    edges: list[Edge] = []
    diagnostics: list[str] = []

    for module in sorted(scope.get("modules", ())):
        module_dir = source_root / "addons" / module
        manifest = module_dir / "__manifest__.py"
        if not module_dir.is_dir() or not manifest.is_file():
            diagnostics.append(f"module {module}: source missing, marked open-question")
            continue
        nodes.append(Node(
            id=f"module.{module}", kind="module", ownership="code_first",
            source_anchor=f"addons/{module}/__manifest__.py:L1",
            evidence="repository-fact", odoo_versions=versions,
            attributes={"module": module},
        ))
        for extract in (extract_python, extract_xml, extract_owl):
            extracted_nodes, extracted_edges, extracted_diagnostics = extract(source_root, module, versions)
            nodes.extend(extracted_nodes)
            edges.extend(extracted_edges)
            diagnostics.extend(extracted_diagnostics)

    node_ids = {node.id for node in nodes}
    module_by_id = {node.id: node.attributes.get("module") for node in nodes}
    resolved_edges = [
        edge for edge in edges
        if edge.source in node_ids and edge.target in node_ids
    ]
    unresolved = [edge for edge in edges if edge not in resolved_edges]
    diagnostics.extend(
        f"unresolved edge {edge.id}: {edge.source} -> {edge.target}" for edge in unresolved
    )

    errors, _ = validate_graph(nodes, resolved_edges, schema, source_root)
    if errors:
        raise BuildError("ontology validation failed:\n" + "\n".join(errors))

    shard_paths: list[Path] = []
    by_model: dict[str, dict[str, list[str]]] = {}
    for module in sorted({node.attributes.get("module") for node in nodes if node.attributes.get("module")}):
        module_nodes = [n.to_dict() for n in nodes if n.attributes.get("module") == module]
        module_node_ids = {n["id"] for n in module_nodes}
        module_edges = [
            e.to_dict() for e in resolved_edges
            if e.source in module_node_ids or module_by_id.get(e.source) == module
        ]
        shard = {
            **GENERATED,
            "module": module,
            "nodes": module_nodes,
            "edges": module_edges,
            "open_questions": sorted(d for d in diagnostics if module in d) or [],
        }
        path = out_dir / "modules" / f"{module}.json"
        write_canonical(path, shard)
        shard_paths.append(path)
        for node in module_nodes:
            model = node.get("attributes", {}).get("model")
            if model:
                by_model.setdefault(model, {"nodes": [], "edges": []})["nodes"].append(node["id"])

    for edge in resolved_edges:
        model = edge.target
        if model in by_model:
            by_model[model]["edges"].append(edge.id)

    for value in by_model.values():
        value["nodes"].sort()
        value["edges"].sort()

    index_path = out_dir / "index" / "by_model.json"
    write_canonical(index_path, {**GENERATED, "models": by_model})
    shard_paths.append(index_path)

    combined, per_file = file_hashes(shard_paths, out_dir)
    manifest = {
        **GENERATED,
        "schema_version": schema["schema_version"],
        "repo_commit": _repo_commit(),
        "odoo_source_revision": "open-question",
        "odoo_versions": list(versions),
        "modules": sorted({n.attributes.get("module") for n in nodes if n.attributes.get("module")}),
        "counts": {
            "nodes": len(nodes),
            "edges": len(resolved_edges),
            "open_questions": len(diagnostics),
        },
        "files": per_file,
        "sha256": combined,
    }
    write_canonical(out_dir / "manifest.json", manifest)
    return manifest


def read_manifest(ontology_dir: Path) -> dict[str, Any]:
    path = Path(ontology_dir) / "manifest.json"
    if not path.is_file():
        raise BuildError(f"missing ontology manifest: {path}")
    return load_json(path)
