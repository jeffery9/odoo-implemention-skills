#!/usr/bin/env python3
"""Ontology consumption closure guard.

The ontology is only useful to the framework if a delegated step has to say
what it did with the subgraph it received.  This guard checks both sides:

1. static wiring: all 18 agents and the orchestrator carry the consumption
   contract;
2. functional gate: evidence_gate rejects missing / stale / fabricated
   ontology consumption, and accepts the four honest status modes.

It deliberately uses --self-test instead of pytest so the documented full-suite
count stays the single source of truth in docs/项目维护指南.md §1.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
ORCHESTRATOR = REPO / "skills" / "capability-twin-orchestrator"
AGENTS_DIR = ORCHESTRATOR / "agents"
SPEC_PATH = (REPO / "skills" / "gherkin-bdd" / "features" / "framework"
             / "ontology_consumption.feature")
EXPECTED_SCENARIO_IDS = (
    "SCN-FWK-001", "SCN-FWK-002", "SCN-FWK-003", "SCN-FWK-004", "SCN-FWK-005",
)
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(ORCHESTRATOR / "scripts"))
sys.path.insert(0, str(REPO / "skills" / "gherkin-bdd" / "scripts"))

import evidence_gate as eg  # noqa: E402
import ontology_context as oc  # noqa: E402
import gherkin_gate  # noqa: E402

AGENT_MARKERS = (
    'shared_context["ontology"]',
    "ontology_contract",
    "ontology_consumption",
    "mode=used",
)
WIRING_MARKERS = {
    ORCHESTRATOR / "scripts" / "evidence_gate.py": (
        "def validate_ontology_consumption", 'contract.get("ontology")'),
    ORCHESTRATOR / "scripts" / "main.py": (
        "ontology_context.consumption_contract", "ontology=ontology_binding"),
    ORCHESTRATOR / "scripts" / "capability_registry.py": (
        '"ontology_context": (params.get("shared_context") or {}).get("ontology")',
        '"ontology_contract": params.get("ontology_contract")'),
}


def expected_agent_count() -> int:
    registry = json.loads((ORCHESTRATOR / "capability_registry.json").read_text("utf-8"))
    return len(registry.get("agents", {}))


def check_static() -> list[str]:
    errors: list[str] = []
    agents = sorted(AGENTS_DIR.rglob("AGENT.md"))
    expected = expected_agent_count()
    if len(agents) != expected:
        errors.append(f"AGENT.md 数量 {len(agents)} 与注册表 {expected} 不一致")
    for path in agents:
        text = path.read_text("utf-8")
        missing = [marker for marker in AGENT_MARKERS if marker not in text]
        if missing:
            errors.append(f"{path.relative_to(REPO)} 缺少本体消费标记：{missing}")

    entrypoints = sorted(AGENTS_DIR.rglob("main.py"))
    if not entrypoints:
        errors.append("未找到任何 agent main.py，无法确认本体字段透传")
    for path in entrypoints:
        text = path.read_text("utf-8")
        missing = [marker for marker in ("_ontology_binding", '"ontology_context"',
                                         '"ontology_contract"') if marker not in text]
        if missing:
            errors.append(f"{path.relative_to(REPO)} 未透传本体字段：{missing}")
    for path, markers in WIRING_MARKERS.items():
        text = path.read_text("utf-8")
        missing = [marker for marker in markers if marker not in text]
        if missing:
            errors.append(f"{path.relative_to(REPO)} 未接好本体消费闭环：{missing}")

    degraded_agents = ("ecosystem-discovery-agent", "technical-analysis-agent")
    for name in degraded_agents:
        path = AGENTS_DIR / name / "main.py"
        text = path.read_text("utf-8")
        missing = [marker for marker in ('"status": "unavailable"',
                                         "reason_code") if marker not in text]
        if missing:
            errors.append(f"{name} 未以 unavailable 降级：{missing}")
    orchestrator = (ORCHESTRATOR / "scripts" / "main.py").read_text("utf-8")
    if '"unavailable"' not in orchestrator or "steps_environment_blocked" not in orchestrator:
        errors.append("编排器未把环境阻塞归一为 delegated 并计数")

    benchmark = REPO / "scripts" / "ontology_benchmark.py"
    if not benchmark.is_file():
        errors.append("缺少语义价值基准脚本 ontology_benchmark.py")
    else:
        bench_text = benchmark.read_text("utf-8")
        for marker in ("def run_benchmark", "framework_nodes_seen", "focus",
                       "consumption_e2e", "genuine_used_status"):
            if marker not in bench_text:
                errors.append(f"语义基准缺少标记：{marker}")
    ci_text = (REPO / ".github" / "workflows" / "ci.yml").read_text("utf-8")
    if "ontology_benchmark.py" not in ci_text:
        errors.append("CI 未接入语义价值基准")
    return errors


def check_spec() -> list[str]:
    """The BDD spec must describe the consumption contract that code enforces."""
    errors: list[str] = []
    if not SPEC_PATH.exists():
        return [f"缺少本体消费行为规格：{SPEC_PATH.relative_to(REPO)}"]
    report = gherkin_gate.validate(SPEC_PATH)
    if report.get("status") != "pass":
        errors.append(f"本体消费规格门禁未通过：{report.get('errors')}")
    ids = {row.get("id") for row in report.get("scenario_index", [])}
    missing = [sid for sid in EXPECTED_SCENARIO_IDS if sid not in ids]
    if missing:
        errors.append(f"本体消费规格缺少场景：{missing}")
    return errors


def _context(status: str, *, module: str = "demo",
             node_id: str = "model:demo.order") -> dict[str, Any]:
    anchor = "addons/demo/models/demo.py:L10"
    if status == "ok":
        nodes = [{"id": node_id, "source_anchor": anchor}]
        anchors = [anchor]
    else:
        nodes, anchors = [], []
    return {
        "enabled": status != "disabled",
        "status": status,
        "source": "/tmp/ontology" if status == "ok" else None,
        "query": {"module": module, "hops": 1},
        "subgraph": {"nodes": nodes, "edges": [], "truncated": False,
                     "returned_nodes": len(nodes), "total_nodes": len(nodes)},
        "anchors": anchors,
        "open_questions": [],
        "consumption": "read-only reasoning context; not step evidence",
    }


def _contract(context: dict[str, Any]) -> dict[str, Any]:
    return eg.build_contract(
        {"step": 2, "name": "Technical Analysis",
         "agent_type": "technical-analysis-agent"},
        ["source-traceability", "fde-methodology"], "wf-1",
        ontology=oc.consumption_contract(context))


def _evidence(tmp: Path, context: dict[str, Any],
              consumption: dict[str, Any] | None) -> dict[str, Any]:
    artifact = tmp / "report.md"
    artifact.write_text("ontology consumption fixture\n", encoding="utf-8")
    evidence: dict[str, Any] = {
        "workflow_id": "wf-1",
        "step": 2,
        "artifacts": [{"path": str(artifact), "kind": "report",
                       "anchor": "addons/demo/models/demo.py:L10"}],
        "fde_records": [
            {"item": i, "result": "pass", "evidence": f"fixture proof {i}"}
            for i in eg.FDE_ITEMS
        ],
    }
    if consumption is not None:
        evidence["ontology_consumption"] = consumption
    return evidence


def _record(context: dict[str, Any], mode: str, **extra: Any) -> dict[str, Any]:
    record = {"fingerprint": oc.fingerprint(context), "mode": mode}
    record.update(extra)
    return record


def self_test_functional() -> None:
    ok = _context("ok")
    assert oc.fingerprint(ok) != oc.fingerprint(_context("ok", node_id="model:demo.line"))
    contract = _contract(ok)
    node_id = ok["subgraph"]["nodes"][0]["id"]
    anchor = ok["anchors"][0]

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        def run(context: dict[str, Any], consumption: dict[str, Any] | None):
            return eg.validate(_evidence(base, context, consumption), _contract(context),
                               base_dir=base)

        report = run(ok, _record(
            ok, "used", node_ids=[node_id], anchors=[anchor],
            statement="本体子图把 demo.order 与 demo 视图载体绑定，用于定位分析入口"))
        assert report["status"] == "pass", report
        assert report["ontology_consumption"]["status"] == "pass"

        missing = run(ok, None)
        assert missing["status"] == "fail", missing
        assert any("缺少 ontology_consumption" in i
                   for i in missing["ontology_consumption"]["issues"])

        fabricated = run(ok, _record(
            ok, "used", node_ids=["model:ghost.order"], anchors=[anchor],
            statement="伪造的节点引用必须被门禁拒绝"))
        assert fabricated["status"] == "fail", fabricated

        stale = _record(ok, "used", node_ids=[node_id], anchors=[anchor],
                        statement="指纹绑定上下文，过期记录不得复用")
        stale["fingerprint"] = "0000000000000000"
        assert run(ok, stale)["status"] == "fail"

        not_applicable = run(ok, _record(
            ok, "not_applicable",
            reason="本步骤处理的是需求措辞归一，不使用 Odoo 框架级语义关系"))
        assert not_applicable["status"] == "pass", not_applicable

        unavailable = _context("unavailable")
        assert run(unavailable, _record(
            unavailable, "used", node_ids=[node_id], anchors=[anchor],
            statement="本体不可用时不得伪造节点"))["status"] == "fail"
        assert run(unavailable, _record(
            unavailable, "unavailable",
            reason="未构建本体 manifest，本步骤不声明语义证据"))["status"] == "pass"

        open_question = _context("open-question")
        assert run(open_question, _record(
            open_question, "open-question",
            reason="当前模块在本体中无节点，保留开放问题"))["status"] == "pass"

        disabled = _context("disabled")
        assert run(disabled, _record(
            disabled, "disabled",
            reason="草稿显式关闭本体，记录为草稿而非完整分析"))["status"] == "pass"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("请显式运行 --self-test")

    errors = check_static() + check_spec()
    if errors:
        print("ontology consumption guard: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    self_test_functional()
    agent_count = expected_agent_count()
    print(f"ontology consumption guard: PASS (agents={agent_count}, modes=4, "
          f"fail-closed checks=4, spec scenarios={len(EXPECTED_SCENARIO_IDS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
