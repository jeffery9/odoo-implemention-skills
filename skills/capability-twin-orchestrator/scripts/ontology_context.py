#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read-only ontology context adapter for the Capability Twin workflow.

The ontology is a derived, machine-readable view of the Odoo application.  It
is injected into ``shared_context`` so every sub-agent reasons from the same
anchored subgraph instead of re-discovering structure from scattered sources.

Hard rules:
- never fabricate a graph: no manifest / no script => ``unavailable``;
- no match for the requested module => ``open-question``, not an empty "ok";
- the subgraph is truncated and anchor-bearing; it is reasoning context,
  never a substitute for step evidence or FDE records.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

DEFAULT_MAX_NODES = 40


class OntologyUnavailable(RuntimeError):
    """Ontology scripts are missing; fail closed without a fake context."""


def _load_lookup(scripts_dir: Path):
    name = "ct_ontology_lookup"
    if name in sys.modules:
        return sys.modules[name]
    script = scripts_dir / "ontology_lookup.py"
    if not script.is_file():
        raise OntologyUnavailable(f"本体查询脚本缺失：{script}")
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise OntologyUnavailable(f"本体查询脚本无法加载：{script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_context(
    *,
    ontology_dir: Path | None,
    ontology_scripts_dir: Path,
    target_module: str,
    enabled: bool = True,
    model: str | None = None,
    carrier: str | None = None,
    version: str | None = None,
    hops: int = 1,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> dict[str, Any]:
    """Build a bounded, anchored ontology subgraph for workflow reasoning."""
    query = {
        "module": target_module,
        "model": model or None,
        "carrier": carrier or None,
        "version": version or None,
        "hops": hops,
    }
    base: dict[str, Any] = {
        "enabled": bool(enabled),
        "source": str(ontology_dir) if ontology_dir else None,
        "query": query,
        "subgraph": {"nodes": [], "edges": [], "truncated": False},
        "anchors": [],
        "open_questions": [],
        "consumption": "read-only reasoning context; not step evidence",
    }
    if not enabled:
        base["status"] = "disabled"
        return base

    if ontology_dir is None or not (ontology_dir / "manifest.json").is_file():
        base["status"] = "unavailable"
        base["open_questions"] = [
            "ontology not built: manifest.json missing (open-question)"
        ]
        return base

    lookup = _load_lookup(ontology_scripts_dir)
    raw = lookup.lookup(
        ontology_dir, model=model, carrier=carrier, module=target_module,
        version=version, hops=hops,
    )
    nodes = sorted(raw.get("nodes", []), key=lambda node: node["id"])
    total = len(nodes)
    truncated = total > max(0, max_nodes)
    if truncated:
        nodes = nodes[:max(0, max_nodes)]
    node_ids = {node["id"] for node in nodes}
    edges = [
        edge for edge in raw.get("edges", [])
        if edge.get("source") in node_ids and edge.get("target") in node_ids
    ]
    base["subgraph"] = {
        "nodes": nodes,
        "edges": edges,
        "truncated": truncated,
        "returned_nodes": len(nodes),
        "total_nodes": total,
    }
    base["anchors"] = sorted({
        node["source_anchor"] for node in nodes if node.get("source_anchor")
    })
    base["open_questions"] = sorted(set(raw.get("open_questions", [])))
    base["status"] = "ok" if nodes else "open-question"
    if not nodes:
        base["open_questions"].append(
            f"no ontology node for module {target_module!r} (open-question)"
        )
    return base


def summary(context: dict[str, Any]) -> dict[str, Any]:
    """Small result-level fingerprint; the full subgraph stays in shared_context."""
    subgraph = context.get("subgraph", {})
    return {
        "status": context.get("status"),
        "module": context.get("query", {}).get("module"),
        "source": context.get("source"),
        "returned_nodes": subgraph.get("returned_nodes", 0),
        "total_nodes": subgraph.get("total_nodes", 0),
        "anchor_count": len(context.get("anchors", [])),
        "open_question_count": len(context.get("open_questions", [])),
        "truncated": subgraph.get("truncated", False),
    }
