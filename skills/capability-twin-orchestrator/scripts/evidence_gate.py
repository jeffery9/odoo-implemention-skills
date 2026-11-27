#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step evidence contract and validation gate.

The orchestrator must not turn a delegated step into ``success`` merely because
an agent returned a success-looking status.  A step is evidence-valid only when
its produced artifacts exist, are non-empty, carry the required traceability
anchors, and (when FDE 2.0 is mounted) contain a complete 9-item checklist with
per-item evidence.

This module has no third-party dependencies and never executes business logic;
it only validates the evidence submitted for a step.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

FDE_ITEMS: tuple = tuple(range(1, 10))
FDE_RESULTS = {"pass", "fail", "n/a"}

# 跨调用持久化：step registry 必须能在新的编排器实例中恢复，
# 否则宿主无法从技能公开入口为上一次运行的步骤回填证据。
STORE_SCHEMA = "1.0"
STORE_FILENAME = "step_registry.json"
MAX_STORE_BYTES = 5_000_000
WORKFLOW_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class EvidenceStoreError(Exception):
    """步骤登记不可用；一律 fail-closed，不得降级为空登记。"""


def valid_workflow_id(value: Any) -> bool:
    """防止 workflow_id 被用作路径穿越载荷。"""
    return isinstance(value, str) and bool(WORKFLOW_ID_RE.fullmatch(value))


def store_path(base_dir: Path, workflow_id: str) -> Path:
    if not valid_workflow_id(workflow_id):
        raise EvidenceStoreError(f"非法 workflow_id：{workflow_id!r}")
    base = Path(base_dir).resolve()
    path = (base / workflow_id / STORE_FILENAME).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise EvidenceStoreError("步骤登记路径越界") from exc
    return path


def save_step_registry(base_dir: Path, workflow_id: str,
                       registry: Dict[str, Any], aliases: Dict[str, str],
                       evidence_base_dir: Optional[Path] = None) -> Path:
    """原子写入步骤登记；返回文件路径。"""
    path = store_path(base_dir, workflow_id)
    payload = {
        "schema": STORE_SCHEMA,
        "workflow_id": workflow_id,
        "saved_at": datetime.now().isoformat(),
        "evidence_base_dir": str(evidence_base_dir) if evidence_base_dir else None,
        "step_registry": registry,
        "step_aliases": aliases,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    tmp.replace(path)
    return path


def load_step_registry(base_dir: Path, workflow_id: str) -> Dict[str, Any]:
    """读取并校验步骤登记；损坏/结构非法一律抛错，不降级。"""
    path = store_path(base_dir, workflow_id)
    if not path.is_file():
        raise EvidenceStoreError(f"未找到步骤登记：{path}")
    if path.stat().st_size > MAX_STORE_BYTES:
        raise EvidenceStoreError("步骤登记超过大小上限，拒绝加载")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceStoreError(f"步骤登记损坏：{path} ({exc})") from exc
    if (not isinstance(data, dict)
            or data.get("schema") != STORE_SCHEMA
            or data.get("workflow_id") != workflow_id
            or not isinstance(data.get("step_registry"), dict)
            or not isinstance(data.get("step_aliases"), dict)):
        raise EvidenceStoreError("步骤登记结构非法，拒绝加载")
    for key, entry in data["step_registry"].items():
        if (not isinstance(entry, dict) or not isinstance(entry.get("result"), dict)
                or not isinstance(entry.get("evidence_contract"), dict)):
            raise EvidenceStoreError(f"步骤登记条目非法：{key}")
    return data


def build_contract(step: Any, skills_granted: Optional[Iterable[str]] = None,
                   workflow_id: Optional[str] = None,
                   ontology: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the evidence contract attached to a delegated step."""
    skills = set(skills_granted or ())
    info = step if isinstance(step, dict) else {"step": step}
    contract = {
        "required": True,
        "workflow_id": workflow_id,
        "step": info.get("step"),
        "name": info.get("name", ""),
        "agent_type": info.get("agent_type", ""),
        "required_artifacts": 1,
        # Traceability is mandatory whenever the step grants source-traceability.
        "required_anchors": 1 if "source-traceability" in skills else 0,
        "fde_items": list(FDE_ITEMS) if "fde-methodology" in skills else [],
    }
    if ontology is not None:
        contract["ontology"] = ontology
    return contract


def validate_ontology_consumption(record: Any,
                                  contract: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a step really accounted for the ontology context it received.

    The ontology never counts as step evidence by itself.  This check only
    certifies the *usage record*: the agent referenced nodes/anchors from the
    exact subgraph it was given, or explicitly declared an applicable reason.
    """
    issues: List[str] = []
    validated: Dict[str, Any] = {
        "status": "fail", "issues": issues,
        "mode": None, "node_ids": [], "anchors": [],
    }
    if not contract.get("required", False):
        validated["status"] = "not_required"
        return validated
    if not isinstance(record, dict):
        issues.append("缺少 ontology_consumption 对象")
        return validated

    expected_fp = contract.get("fingerprint")
    actual_fp = record.get("fingerprint")
    if not isinstance(expected_fp, str) or actual_fp != expected_fp:
        issues.append(
            f"本体上下文指纹不匹配：期望 {expected_fp!r}，实际 {actual_fp!r}")

    mode = record.get("mode")
    allowed_modes = contract.get("allowed_modes") or []
    if mode not in allowed_modes:
        issues.append(f"ontology_consumption.mode 无效：{mode!r}（允许 {allowed_modes}）")
    validated["mode"] = mode

    node_ids = record.get("node_ids") or []
    anchors = record.get("anchors") or []
    if not isinstance(node_ids, list) or any(not isinstance(i, str) for i in node_ids):
        issues.append("ontology_consumption.node_ids 必须是字符串数组")
        node_ids = []
    if not isinstance(anchors, list) or any(not isinstance(i, str) for i in anchors):
        issues.append("ontology_consumption.anchors 必须是字符串数组")
        anchors = []
    allowed_nodes = set(contract.get("allowed_node_ids") or [])
    allowed_anchors = set(contract.get("allowed_anchors") or [])
    unknown_nodes = sorted(set(node_ids) - allowed_nodes)
    unknown_anchors = sorted(set(anchors) - allowed_anchors)
    if unknown_nodes:
        issues.append(f"引用了不在本体子图中的 node_id：{unknown_nodes}")
    if unknown_anchors:
        issues.append(f"引用了不在本体子图中的 anchor：{unknown_anchors}")
    validated["node_ids"] = sorted(set(node_ids) & allowed_nodes)
    validated["anchors"] = sorted(set(anchors) & allowed_anchors)

    def text_field(name: str, minimum: int = 10) -> str:
        value = record.get(name)
        if not isinstance(value, str) or len(value.strip()) < minimum:
            issues.append(f"ontology_consumption.{name} 缺失或过短（至少 {minimum} 字）")
            return ""
        return value.strip()

    if mode == "used":
        if not validated["node_ids"]:
            issues.append("mode=used 必须至少引用一个子图内的 node_id")
        if not validated["anchors"]:
            issues.append("mode=used 必须至少引用一个子图内的 source_anchor")
        statement = text_field("statement")
        if statement:
            validated["statement"] = statement
    elif mode in ("not_applicable", "open-question", "unavailable", "disabled"):
        reason = text_field("reason")
        if reason:
            validated["reason"] = reason
        if node_ids or anchors:
            issues.append(f"mode={mode} 不得引用本体节点或锚点")

    validated["status"] = "pass" if not issues else "fail"
    return validated


def _resolve(base_dir: Path, raw: Any) -> Optional[Path]:
    """Resolve an artifact path inside base_dir; reject escapes and bad types."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    base = base_dir.resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = base / path
    try:
        resolved = path.resolve()
        resolved.relative_to(base)
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def validate(evidence: Any, contract: Any,
             base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Validate submitted step evidence.

    Returns a report with ``status`` in ``pass`` / ``fail`` / ``error``.  Any
    ``fail`` on the FDE checklist is blocking, per fde-methodology SKILL.md §4.
    """
    issues: List[str] = []
    validated: Dict[str, Any] = {
        "status": "fail",
        "issues": issues,
        "validated_at": datetime.now().isoformat(),
        "artifacts": [],
        "fde_records": [],
        "ontology_consumption": {"status": "not_required", "issues": []},
    }
    if not isinstance(evidence, dict):
        issues.append("证据必须是对象")
        validated["status"] = "error"
        return validated
    if not isinstance(contract, dict) or not contract.get("required", True):
        issues.append("步骤未提供有效的证据契约")
        validated["status"] = "error"
        return validated

    for key in ("workflow_id", "step"):
        expected = contract.get(key)
        actual = evidence.get(key)
        if expected is not None and actual is not None and actual != expected:
            issues.append(f"{key} 不匹配：期望 {expected!r}，实际 {actual!r}")

    base = Path(base_dir) if base_dir is not None else Path.cwd()
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list):
        issues.append("artifacts 必须是非空数组")
        artifacts = []
    required_artifacts = int(contract.get("required_artifacts", 1) or 0)
    if len(artifacts) < required_artifacts:
        issues.append(f"产物数量不足：需要 {required_artifacts}，实际 {len(artifacts)}")

    anchors = 0
    for i, item in enumerate(artifacts):
        if not isinstance(item, dict):
            issues.append(f"artifacts[{i}] 必须是对象")
            continue
        path = _resolve(base, item.get("path"))
        if path is None:
            issues.append(f"artifacts[{i}].path 不存在、不可读或越界：{item.get('path')!r}")
            continue
        size = path.stat().st_size
        if size == 0:
            issues.append(f"artifacts[{i}] 是空文件：{path}")
            continue
        anchor = item.get("anchor")
        if anchor is not None and (not isinstance(anchor, str) or len(anchor.strip()) < 3):
            issues.append(f"artifacts[{i}].anchor 无效")
        elif isinstance(anchor, str) and anchor.strip():
            anchors += 1
        validated["artifacts"].append({
            "path": str(path.relative_to(base.resolve())),
            "kind": item.get("kind", "artifact"),
            "anchor": anchor,
            "bytes": size,
        })

    required_anchors = int(contract.get("required_anchors", 0) or 0)
    if anchors < required_anchors:
        issues.append(f"可追溯锚点不足：需要 {required_anchors}，实际 {anchors}")

    fde_items = contract.get("fde_items") or []
    if fde_items:
        records = evidence.get("fde_records")
        if records is None:
            records = evidence.get("fde_checklist")
        if not isinstance(records, list):
            issues.append("FDE 检查点缺少 fde_records / fde_checklist")
            records = []
        seen = {}
        for i, rec in enumerate(records):
            if not isinstance(rec, dict):
                issues.append(f"fde_records[{i}] 必须是对象")
                continue
            item = rec.get("item")
            result = rec.get("result")
            proof = rec.get("evidence")
            if item not in fde_items:
                issues.append(f"fde_records[{i}].item 不在清单内：{item!r}")
                continue
            if item in seen:
                issues.append(f"FDE 检查项 {item} 重复")
                continue
            if result not in FDE_RESULTS:
                issues.append(f"FDE 检查项 {item} 的 result 无效：{result!r}")
                continue
            if not isinstance(proof, str) or not proof.strip():
                issues.append(f"FDE 检查项 {item} 缺少证据")
                continue
            if result == "fail":
                issues.append(f"FDE 检查项 {item} 判定为 fail，步骤不得声明成功")
            seen[item] = True
            validated["fde_records"].append({
                "item": item, "result": result, "evidence": proof.strip()})
        missing = [i for i in fde_items if i not in seen]
        if missing:
            issues.append(f"FDE 检查项缺失：{missing}")

    ontology_contract = contract.get("ontology")
    if isinstance(ontology_contract, dict) and ontology_contract.get("required", False):
        ontology_report = validate_ontology_consumption(
            evidence.get("ontology_consumption"), ontology_contract)
        validated["ontology_consumption"] = ontology_report
        issues.extend(ontology_report["issues"])

    validated["status"] = "pass" if not issues else (
        "error" if validated["status"] == "error" else "fail")
    return validated


def summarize_step(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return the evidence-related view of a step result for reports."""
    return {
        "status": result.get("status"),
        "evidence_contract": result.get("evidence_contract", {}),
        "evidence_validation": result.get("evidence_validation", {}),
        "fde_checkpoint": result.get("fde_checkpoint", {}),
        "ontology_consumption": result.get("ontology_consumption", {}),
    }
