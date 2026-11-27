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

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

FDE_ITEMS: tuple = tuple(range(1, 10))
FDE_RESULTS = {"pass", "fail", "n/a"}


def build_contract(step: Any, skills_granted: Optional[Iterable[str]] = None,
                   workflow_id: Optional[str] = None) -> Dict[str, Any]:
    """Build the evidence contract attached to a delegated step."""
    skills = set(skills_granted or ())
    info = step if isinstance(step, dict) else {"step": step}
    return {
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
    }
