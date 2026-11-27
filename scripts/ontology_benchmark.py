#!/usr/bin/env python3
"""Reproducible semantic-compression benchmark for the Odoo ontology.

This is NOT a claim that AI reasoning quality improved, and NOT a claim that
the ontology is smaller than source text (it is not: nodes carry relations,
evidence levels and logic conditions).  It measures objective properties that
make the ontology useful as a reasoning input:

1. focus        — a scoped query returns a bounded subset of the full graph;
2. coverage     — framework-level carriers (model/view/action/menu/group/ACL/
                   rule) and all three logic carriers survive the queries;
3. traceability — every returned node carries a physical source anchor;
4. honesty      — absent module and unbuilt ontology never fake an "ok".

Everything is built from tests/fixtures/ontology_source through the same
production builder / lookup / context adapter used by the framework, so the
numbers are deterministic and reproducible in CI without an Odoo checkout.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
ORCHESTRATOR_SCRIPTS = (REPO / "skills" / "capability-twin-orchestrator" / "scripts")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(ORCHESTRATOR_SCRIPTS))

from ontology_lib.builder import build  # noqa: E402
from ontology_lib.core import REPO_ROOT, SCHEMA_PATH, SCOPE_PATH, load_json  # noqa: E402
import ontology_context as oc  # noqa: E402

FIXTURE_SOURCE = REPO / "tests" / "fixtures" / "ontology_source"
SCRIPTS = REPO / "scripts"
MODULE = "demo"

# Ground truth is derived from the fixture's declared scope, then checked
# against what the adapter actually returns for representative tasks.
TASKS: tuple[dict[str, Any], ...] = (
    {"id": "structure", "query": {}, "expect_kinds":
     {"model", "view", "action", "menu", "group", "acl", "rule"}},
    {"id": "model_fields", "query": {"model": "demo.order"},
     "expect_kinds": {"model", "field", "method"}},
    {"id": "python_logic", "query": {"carrier": "python"},
     "expect_carriers": {"python"}, "expect_kinds": {"logic"}},
    {"id": "view_logic", "query": {"carrier": "view"},
     "expect_carriers": {"view"}, "expect_kinds": {"logic"}},
    {"id": "owl_logic", "query": {"carrier": "owl"},
     "expect_carriers": {"owl"}, "expect_kinds": {"logic"}},
)

FRAMEWORK_KINDS = {"model", "view", "action", "menu", "group", "acl", "rule"}
LOGIC_CARRIERS = {"python", "view", "owl"}


def _source_bytes() -> int:
    total = 0
    for path in FIXTURE_SOURCE.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            total += len(path.read_bytes())
    return total


def run_benchmark() -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    scope = load_json(SCOPE_PATH)
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp) / "ontology"
        manifest = build(FIXTURE_SOURCE, out, schema, scope)

        task_rows: list[dict[str, Any]] = []
        all_returned: set[str] = set()
        for task in TASKS:
            ctx = oc.build_context(
                ontology_dir=out, ontology_scripts_dir=SCRIPTS,
                target_module=MODULE, **task["query"])
            nodes = ctx["subgraph"]["nodes"]
            returned_ids = {node["id"] for node in nodes}
            all_returned |= returned_ids
            kinds = {node["kind"] for node in nodes}
            carriers = {node.get("carrier") for node in nodes if node.get("carrier")}
            expected_kinds = set(task.get("expect_kinds", ()))
            expected_carriers = set(task.get("expect_carriers", ()))
            missing_kinds = sorted(expected_kinds - kinds)
            missing_carriers = sorted(expected_carriers - carriers)
            anchors_ok = all(node.get("source_anchor") for node in nodes)
            task_rows.append({
                "id": task["id"],
                "status": ctx["status"],
                "query": task["query"],
                "returned_nodes": len(nodes),
                "total_nodes": ctx["subgraph"]["total_nodes"],
                "returned_edges": len(ctx["subgraph"]["edges"]),
                "anchor_count": len(ctx["anchors"]),
                "kinds": sorted(kinds),
                "carriers": sorted(carriers),
                "missing_kinds": missing_kinds,
                "missing_carriers": missing_carriers,
                "anchors_present": anchors_ok,
                "truncated": ctx["subgraph"]["truncated"],
            })

        shard = load_json(out / "modules" / f"{MODULE}.json")
        node_index = {node["id"]: node for node in shard["nodes"]}
        framework_ids = {
            nid for nid, node in node_index.items() if node["kind"] in FRAMEWORK_KINDS
        }
        logic_ids = {
            nid for nid, node in node_index.items()
            if node["kind"] == "logic" and node.get("carrier") in LOGIC_CARRIERS
        }
        source_bytes = _source_bytes()
        context_bytes = len(json.dumps(
            [node_index[nid] for nid in sorted(all_returned)],
            ensure_ascii=False, sort_keys=True).encode("utf-8"))

        # Honesty checks use the exact production adapter, not a reimplementation.
        unbuilt = oc.build_context(
            ontology_dir=None, ontology_scripts_dir=SCRIPTS, target_module=MODULE)
        absent = oc.build_context(
            ontology_dir=out, ontology_scripts_dir=SCRIPTS,
            target_module="absent_module")

        report: dict[str, Any] = {
            "fixture": str(FIXTURE_SOURCE.relative_to(REPO)),
            "manifest": {
                "sha256": manifest["sha256"],
                "nodes": manifest["counts"]["nodes"],
                "edges": manifest["counts"]["edges"],
                "open_questions": manifest["counts"]["open_questions"],
            },
            # Semantic payload, not text compression: the subgraph is larger
            # than raw source because it carries edges, evidence and logic.
            # The useful property is that a scoped query focuses the graph.
            "focus": {
                "full_graph_nodes": len(shard["nodes"]),
                "distinct_nodes_across_tasks": len(all_returned),
                "task_returned_nodes": {
                    row["id"]: row["returned_nodes"] for row in task_rows
                },
                "source_bytes": source_bytes,
                "subgraph_payload_bytes": context_bytes,
                "payload_to_source_ratio": (
                    round(context_bytes / source_bytes, 4) if source_bytes else None
                ),
            },
            "coverage": {
                "framework_nodes_total": len(framework_ids),
                "framework_nodes_seen": len(framework_ids & all_returned),
                "logic_nodes_total": len(logic_ids),
                "logic_nodes_seen": len(logic_ids & all_returned),
                "carriers_seen": sorted({
                    node_index[nid].get("carrier")
                    for nid in logic_ids & all_returned
                }),
            },
            "traceability": {
                "nodes_checked": len(all_returned),
                "missing_anchor": sorted(
                    nid for nid in all_returned if not node_index[nid].get("source_anchor")
                ),
            },
            "honesty": {
                "unbuilt_status": unbuilt["status"],
                "absent_status": absent["status"],
            },
            "tasks": task_rows,
        }

        issues: list[str] = []
        for row in task_rows:
            if row["status"] != "ok":
                issues.append(f"{row['id']}: status={row['status']}")
            if row["missing_kinds"]:
                issues.append(f"{row['id']}: missing kinds {row['missing_kinds']}")
            if row["missing_carriers"]:
                issues.append(f"{row['id']}: missing carriers {row['missing_carriers']}")
            if not row["anchors_present"]:
                issues.append(f"{row['id']}: anchor missing")
        if report["coverage"]["framework_nodes_seen"] != report["coverage"]["framework_nodes_total"]:
            issues.append("framework coverage incomplete")
        if set(report["coverage"]["carriers_seen"]) != LOGIC_CARRIERS:
            issues.append("logic carrier coverage incomplete")
        if not any(row["returned_nodes"] < len(shard["nodes"]) for row in task_rows):
            issues.append("no scoped query narrowed the full graph")
        if report["traceability"]["missing_anchor"]:
            issues.append("source anchor missing")
        if report["honesty"]["unbuilt_status"] != "unavailable":
            issues.append("unbuilt ontology did not degrade honestly")
        if report["honesty"]["absent_status"] != "open-question":
            issues.append("absent module did not degrade honestly")
        report["issues"] = issues
        report["status"] = "pass" if not issues else "fail"
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write JSON report to this path")
    args = parser.parse_args()
    report = run_benchmark()
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
