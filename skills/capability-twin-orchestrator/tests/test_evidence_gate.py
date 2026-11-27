# -*- coding: utf-8 -*-
"""运行态证据闭环守卫：状态不得冒充证据，委派步骤只有证据通过才计为完成。"""

import logging
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import evidence_gate as eg  # noqa: E402
import main as ct_main  # noqa: E402


def _fde_records(result="pass"):
    return [
        {"item": i, "result": result,
         "evidence": f"FDE 第 {i} 项依据：addons/account/models/account_move.py:L128"}
        for i in range(1, 10)
    ]


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())
        self.report = self.tmp / "technical_report.md"
        self.report.write_text("# Technical Analysis\nEvidence body\n", encoding="utf-8")
        self.step = {
            "step": 2, "name": "Technical Analysis",
            "agent_type": "technical-analysis-agent",
        }
        self.skills = ["source-traceability", "fde-methodology"]
        self.contract = eg.build_contract(self.step, self.skills, "wf-1")
        self.evidence = {
            "workflow_id": "wf-1",
            "step": 2,
            "artifacts": [{
                "path": "technical_report.md",
                "kind": "report",
                "anchor": "addons/account/models/account_move.py:L128",
            }],
            "fde_records": _fde_records(),
        }

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_contract_requires_anchor_and_nine_fde_items(self):
        self.assertEqual(self.contract["required_anchors"], 1)
        self.assertEqual(len(self.contract["fde_items"]), 9)
        self.assertTrue(self.contract["required"])

    def test_empty_artifacts_fail(self):
        report = eg.validate({"step": 2, "artifacts": []}, self.contract, self.tmp)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("产物数量不足" in i for i in report["issues"]))

    def test_artifact_outside_base_is_rejected(self):
        evidence = dict(self.evidence)
        evidence["artifacts"] = [{"path": str(self.tmp.parent / "outside.md"),
                                  "anchor": "outside:L1"}]
        report = eg.validate(evidence, self.contract, self.tmp)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("越界" in i or "不存在" in i for i in report["issues"]))

    def test_missing_anchor_is_rejected(self):
        evidence = dict(self.evidence)
        evidence["artifacts"] = [{"path": "technical_report.md", "kind": "report"}]
        report = eg.validate(evidence, self.contract, self.tmp)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("锚点不足" in i for i in report["issues"]))

    def test_fde_fail_blocks_even_with_valid_artifacts(self):
        evidence = dict(self.evidence)
        evidence["fde_records"] = _fde_records()
        evidence["fde_records"][2]["result"] = "fail"
        report = eg.validate(evidence, self.contract, self.tmp)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("判定为 fail" in i for i in report["issues"]))

    def test_complete_evidence_passes(self):
        report = eg.validate(self.evidence, self.contract, self.tmp)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(len(report["artifacts"]), 1)
        self.assertEqual(len(report["fde_records"]), 9)


class OrchestratorEvidenceTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())
        self.orch = ct_main.CapabilityTwinOrchestratorSkill(
            config=ct_main.CapabilityTwinConfig(output_directory=str(self.tmp / "runs")))
        self.orch.evidence_base_dir = self.tmp
        self.name = "Technical Analysis"
        self.result = {
            "status": "pending_instruction",
            "skills_granted": ["source-traceability", "fde-methodology"],
            "evidence_contract": eg.build_contract(
                {"step": 2, "name": self.name, "agent_type": "technical-analysis-agent"},
                ["source-traceability", "fde-methodology"], self.orch.workflow_id),
            "evidence_validation": {"status": "pending", "issues": ["尚未提交步骤证据"]},
            "fde_checkpoint": {"required": True, "recorded": False},
        }
        self.orch._register_step(2, self.name, self.result)
        (self.tmp / "report.md").write_text("# Evidence\n", encoding="utf-8")
        self.evidence = {
            "workflow_id": self.orch.workflow_id,
            "step": 2,
            "artifacts": [{"path": "report.md", "kind": "report",
                           "anchor": "addons/account/models/account_move.py:L128"}],
            "fde_records": _fde_records(),
        }

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_delegated_step_is_not_completed(self):
        outcome = self.orch._workflow_outcome()
        self.assertEqual(outcome["status"], "delegated")
        self.assertEqual(outcome["steps_total"], 1)
        self.assertEqual(outcome["steps_completed"], 0)
        self.assertTrue(outcome["requires_semantic_execution"])

    def test_success_status_without_evidence_does_not_promote(self):
        self.result["status"] = "success"
        outcome = self.orch._workflow_outcome()
        self.assertEqual(outcome["status"], "delegated")
        self.assertEqual(outcome["steps_completed"], 0)

    def test_invalid_submission_keeps_delegated(self):
        report = self.orch.submit_step_evidence(2, {"step": 2, "artifacts": []})
        self.assertEqual(report["status"], "fail")
        self.assertEqual(self.result["status"], "delegated")
        self.assertFalse(self.result["fde_checkpoint"]["recorded"])

    def test_valid_submission_promotes_and_is_idempotent(self):
        report = self.orch.submit_step_evidence(2, self.evidence)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(self.result["status"], "success")
        self.assertTrue(self.result["fde_checkpoint"]["recorded"])
        self.assertEqual(report["workflow_outcome"]["status"], "completed")
        self.assertEqual(report["workflow_outcome"]["steps_completed"], 1)

        replay = self.orch.submit_step_evidence(2, self.evidence)
        self.assertEqual(replay["status"], "pass")
        self.assertEqual(replay["workflow_outcome"]["steps_total"], 1)

    def test_unknown_step_returns_error(self):
        report = self.orch.submit_step_evidence(99, self.evidence)
        self.assertEqual(report["status"], "error")

    def test_registry_survives_new_instance_and_closes_step(self):
        wid = self.orch.workflow_id
        self.assertIsNotNone(self.orch.persist_step_registry())
        resumed = ct_main.CapabilityTwinOrchestratorSkill(
            config=ct_main.CapabilityTwinConfig(output_directory=str(self.tmp / "runs")))
        self.assertTrue(resumed.restore_step_registry(wid))
        self.assertEqual(resumed._workflow_outcome()["status"], "delegated")
        report = resumed.submit_step_evidence(2, self.evidence)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["workflow_outcome"]["status"], "completed")

    def test_corrupt_registry_fails_closed(self):
        wid = self.orch.workflow_id
        path = self.tmp / "runs" / wid / eg.STORE_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json", encoding="utf-8")
        resumed = ct_main.CapabilityTwinOrchestratorSkill(
            config=ct_main.CapabilityTwinConfig(output_directory=str(self.tmp / "runs")))
        self.assertFalse(resumed.restore_step_registry(wid))
        self.assertEqual(resumed._workflow_outcome()["status"], "failed")

    def test_public_entry_submits_evidence(self):
        wid = self.orch.workflow_id
        self.assertIsNotNone(self.orch.persist_step_registry())
        real_config = ct_main.CapabilityTwinConfig
        ct_main.CapabilityTwinConfig = lambda: real_config(
            output_directory=str(self.tmp / "runs"))
        try:
            report = ct_main.execute_skill({
                "operation": "submit_step_evidence",
                "workflow_id": wid,
                "step": 2,
                "evidence": self.evidence,
            })
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["workflow_outcome"]["status"], "completed")
            outcome = ct_main.execute_skill({
                "operation": "workflow_outcome", "workflow_id": wid})
            self.assertEqual(outcome["status"], "completed")
            self.assertEqual(outcome["steps_completed"], 1)
        finally:
            ct_main.CapabilityTwinConfig = real_config

    def test_public_entry_rejects_workflow_id_traversal(self):
        for bad in ("../etc", "/tmp/x", "", None, "a/b"):
            report = ct_main.execute_skill({
                "operation": "workflow_outcome", "workflow_id": bad})
            self.assertEqual(report["status"], "error", bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
