#!/usr/bin/env python3
"""Read-only semantic subgraph query over generated ontology shards."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ontology_lib.core import REPO_ROOT, canonical_json, load_json  # noqa: E402


def _load_shards(ontology_dir: Path) -> tuple[list[dict], list[str]]:
    manifest_path = ontology_dir / "manifest.json"
    if not manifest_path.is_file():
        return [], ["ontology manifest missing: build not run (open-question)"]
    shards = []
    for path in sorted((ontology_dir / "modules").glob("*.json")):
        shards.append(load_json(path))
    return shards, []


def lookup(
    ontology_dir: Path,
    model: str | None = None,
    kind: str | None = None,
    carrier: str | None = None,
    module: str | None = None,
    version: str | None = None,
    hops: int = 1,
) -> dict[str, Any]:
    shards, open_questions = _load_shards(Path(ontology_dir))
    nodes: list[dict] = []
    edges: list[dict] = []
    for shard in shards:
        open_questions.extend(shard.get("open_questions", []))
        for node in shard.get("nodes", []):
            if model:
                attrs = node.get("attributes", {})
                bindings = node.get("bindings", {})
                if attrs.get("model") != model and bindings.get("model") != model and node.get("id") != model:
                    continue
            if kind and node.get("kind") != kind:
                continue
            if carrier and node.get("carrier") != carrier:
                continue
            if module and node.get("attributes", {}).get("module") != module:
                continue
            if version and node.get("odoo_versions") and version not in node["odoo_versions"]:
                continue
            nodes.append(node)
        edges.extend(shard.get("edges", []))

    selected = {node["id"] for node in nodes}
    chosen_edges: list[dict] = []
    for _ in range(max(0, hops) + 1):
        frontier = set(selected)
        for edge in edges:
            if edge["source"] in frontier or edge["target"] in frontier:
                chosen_edges.append(edge)
                selected.add(edge["source"])
                selected.add(edge["target"])
        chosen_edges = list({edge["id"]: edge for edge in chosen_edges}.values())
    chosen_edges.sort(key=lambda edge: edge["id"])

    node_by_id = {node["id"]: node for shard in shards for node in shard.get("nodes", [])}
    result_nodes = [node_by_id[node_id] for node_id in sorted(selected) if node_id in node_by_id]
    return {
        "status": "ok" if result_nodes else "open-question",
        "nodes": result_nodes,
        "edges": chosen_edges,
        "open_questions": sorted(set(open_questions)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ontology", type=Path, default=REPO_ROOT / "ontology")
    parser.add_argument("--model")
    parser.add_argument("--kind")
    parser.add_argument("--carrier")
    parser.add_argument("--module")
    parser.add_argument("--version")
    parser.add_argument("--hops", type=int, default=1)
    args = parser.parse_args()
    result = lookup(
        args.ontology, model=args.model, kind=args.kind, carrier=args.carrier,
        module=args.module, version=args.version, hops=args.hops,
    )
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
