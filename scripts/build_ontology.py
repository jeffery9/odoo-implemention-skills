#!/usr/bin/env python3
"""Build the deterministic Odoo ontology from static sources.

Usage:
  python scripts/build_ontology.py --self-test
  python scripts/build_ontology.py --source "$ODOO_SOURCE_PATH" --out /tmp/ontology
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_ontology import check as guard_check  # noqa: E402
from ontology_lib.builder import build  # noqa: E402
from ontology_lookup import lookup  # noqa: E402
from ontology_lib.core import (  # noqa: E402
    REPO_ROOT, SCHEMA_PATH, SCOPE_PATH, Node, canonical_json, load_json,
    validate_graph,
)

FIXTURE_SOURCE = REPO_ROOT / "tests" / "fixtures" / "ontology_source"


def run_self_test() -> int:
    schema = load_json(SCHEMA_PATH)
    scope = load_json(SCOPE_PATH)
    with tempfile.TemporaryDirectory() as temp:
        first = Path(temp) / "first"
        second = Path(temp) / "second"
        manifest_a = build(FIXTURE_SOURCE, first, schema, scope)
        manifest_b = build(FIXTURE_SOURCE, second, schema, scope)
        assert manifest_a["sha256"] == manifest_b["sha256"], "rebuild hash drift"
        assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()

        shard = load_json(first / "modules" / "demo.json")
        ids = {node["id"] for node in shard["nodes"]}
        for expected in (
            "module.demo", "demo.order", "demo.order.state",
            "demo.order.action_start", "demo.demo_order_form",
            "demo.demo_order_action", "demo.demo_order_menu",
            "demo.group_demo_user", "demo.demo_order_acl", "demo.demo_order_rule",
        ):
            assert expected in ids, f"missing fixture node: {expected}"
        logic = [node for node in shard["nodes"] if node["kind"] == "logic"]
        assert {node["carrier"] for node in logic} == {"python", "view", "owl"}, logic
        assert any(node.get("condition") for node in logic), "no condition captured"
        assert any(node.get("effect") for node in logic), "no effect captured"

        queried = lookup(first, model="demo.order", carrier="python", hops=1)
        assert queried["status"] == "ok", "lookup failed"
        assert "demo.order" in {node["id"] for node in queried["nodes"]}
        assert queried["edges"], "lookup returned no edges"

        # 框架集成：本体必须以有界、带锚点的只读子图进入 shared_context。
        import importlib.util
        adapter_script = (REPO_ROOT / "skills" / "capability-twin-orchestrator"
                          / "scripts" / "ontology_context.py")
        spec = importlib.util.spec_from_file_location("ct_ontology_context", adapter_script)
        assert spec and spec.loader, "ontology context adapter not loadable"
        adapter = importlib.util.module_from_spec(spec)
        sys.modules["ct_ontology_context"] = adapter
        spec.loader.exec_module(adapter)

        ctx = adapter.build_context(
            ontology_dir=first, ontology_scripts_dir=REPO_ROOT / "scripts",
            target_module="demo")
        assert ctx["status"] == "ok", ctx
        assert ctx["anchors"], "context has no physical anchors"
        assert all(node.get("source_anchor") for node in ctx["subgraph"]["nodes"])
        assert ctx["consumption"].startswith("read-only")

        bounded = adapter.build_context(
            ontology_dir=first, ontology_scripts_dir=REPO_ROOT / "scripts",
            target_module="demo", max_nodes=2)
        assert bounded["subgraph"]["truncated"], "context was not bounded"
        assert len(bounded["subgraph"]["nodes"]) <= 2

        unbuilt = adapter.build_context(
            ontology_dir=None, ontology_scripts_dir=REPO_ROOT / "scripts",
            target_module="demo")
        assert unbuilt["status"] == "unavailable" and unbuilt["open_questions"], unbuilt

        absent = adapter.build_context(
            ontology_dir=first, ontology_scripts_dir=REPO_ROOT / "scripts",
            target_module="absent_module")
        assert absent["status"] == "open-question", absent

        disabled = adapter.build_context(
            ontology_dir=first, ontology_scripts_dir=REPO_ROOT / "scripts",
            target_module="demo", enabled=False)
        assert disabled["status"] == "disabled" and not disabled["subgraph"]["nodes"]

        assert guard_check(first / "manifest.json", second)["status"] == "pass"
        manifest_path = first / "manifest.json"
        drifted = json.loads(manifest_path.read_text(encoding="utf-8"))
        drifted["sha256"] = "deadbeef"
        manifest_path.write_text(json.dumps(drifted), encoding="utf-8")
        drift = guard_check(manifest_path, second)
        assert drift["status"] == "fail", "manifest drift was not detected"

        errors, _ = validate_graph(
            [Node(
                id="bad.view", kind="view", ownership="code_first",
                source_anchor="addons/demo/views/demo_views.xml:record:demo_order_form",
                evidence="repository-fact", attributes={"model": "sale.order"},
            )], [], schema, FIXTURE_SOURCE,
        )
        assert any("not whitelisted" in error for error in errors), errors

        errors, _ = validate_graph(
            [Node(
                id="bad.logic", kind="logic", ownership="code_first",
                source_anchor="addons/demo/models/demo_model.py:L10",
                evidence="repository-fact",
            )], [], schema, FIXTURE_SOURCE,
        )
        assert any("missing carrier" in error for error in errors), errors

        errors, _ = validate_graph(
            [Node(
                id="bad.anchor", kind="model", ownership="code_first",
                source_anchor="addons/demo/models/does_not_exist.py:L1",
                evidence="repository-fact", attributes={"module": "demo"},
            )], [], schema, FIXTURE_SOURCE,
        )
        assert any("anchor file missing" in error for error in errors), errors

        errors, _ = validate_graph([], [], schema, FIXTURE_SOURCE)
        assert any("zero nodes" in error for error in errors), errors

    print("ontology self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--scope", type=Path, default=SCOPE_PATH)
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if not args.source or not args.out:
        parser.error("--source and --out are required unless --self-test is used")

    schema = load_json(args.schema)
    scope = load_json(args.scope)
    manifest = build(args.source, args.out, schema, scope)
    print(canonical_json({"sha256": manifest["sha256"], "counts": manifest["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
