#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BDD Spec Gate —— 把 Gherkin 规格接入 Capability Twin 流水线的适配层。

设计原则：
1. **单一事实源**：解析/校验逻辑只在 `skills/gherkin-bdd/scripts/gherkin_gate.py`
   实现，本模块按文件路径加载它，不复制规则、不维护第二套判定。
2. **不改阶段编号**：门禁挂在既有步骤边界（Step 8/9 写作 → Step 10 绑定 →
   Step 11 派生 → Step 12 证据 → Step 13 G3），不新增 `6+3+4+N` 之外的阶段。
3. **不宣称通过**：`status` 只由 `gherkin_gate.validate()` 的结果决定；
   生成 UAT / 步骤桩 / 矩阵都不构成 L2 证据。
4. **缺规格与坏规格区别对待**：`missing`（该模块尚无 `.feature`）不阻断分析类
   流水线，但阻断「场景类交付物」打包；`fail`（有规格但违规）一律阻断。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# scripts -> capability-twin-orchestrator -> skills -> 仓库根
FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FEATURES_DIR = FRAMEWORK_ROOT / "skills" / "gherkin-bdd" / "features"
DEFAULT_OUTPUT_DIR = FRAMEWORK_ROOT / "capability_twin_runs" / "bdd"
ENGINE_PATH = FRAMEWORK_ROOT / "skills" / "gherkin-bdd" / "scripts" / "gherkin_gate.py"

# 场景类交付物：没有可用规格时不允许打包，否则模板只能填占位符
SCENARIO_DEPENDENT_TEMPLATES = ("SCENARIO_SOLUTION", "CONSULTANT_UAT_SCRIPT")

MAX_ISSUES = 20
MAX_FEATURE_CHARS = 6000


def _rel(path: Path) -> str:
    """相对仓库根的路径，保证报告在任何 CWD 下稳定。"""
    try:
        return Path(path).resolve().relative_to(FRAMEWORK_ROOT).as_posix()
    except ValueError:
        return str(path)


def _slug(module: Optional[str]) -> str:
    return (module or "all").replace("/", "_")


class BDDGate:
    """规格门禁适配器：scope 解析 → 校验 → 覆盖率 → 派生 → 模板上下文。"""

    def __init__(self, features_dir: Optional[str] = None,
                 output_dir: Optional[str] = None,
                 allow_en: bool = False,
                 enabled: bool = True):
        self.features_dir = Path(features_dir) if features_dir else DEFAULT_FEATURES_DIR
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.allow_en = allow_en
        self.enabled = enabled
        self._engine_module = None
        self.last_run: Dict[str, Any] = {}
        self._last_features: List[Any] = []

    # ------------------------------------------------------------------
    # 引擎加载
    # ------------------------------------------------------------------
    def engine(self):
        """按路径加载 gherkin_gate，避免把 skills 目录伪装成包。"""
        if self._engine_module is not None:
            return self._engine_module
        if not ENGINE_PATH.is_file():
            raise FileNotFoundError(f"未找到规格门禁引擎：{_rel(ENGINE_PATH)}")
        spec = importlib.util.spec_from_file_location("ct_gherkin_gate", ENGINE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        # 3.13 起 dataclasses 需要模块先注册到 sys.modules，否则取 __dict__ 时报 None
        sys.modules.setdefault("ct_gherkin_gate", module)
        spec.loader.exec_module(module)
        self._engine_module = module
        return module

    # ------------------------------------------------------------------
    # scope 解析
    # ------------------------------------------------------------------
    def resolve_scope(self, module: Optional[str] = None) -> Tuple[Path, str]:
        """
        优先校验该模块自己的规格目录；没有则回落到全仓基线。

        回落时必须把 scope 标成 baseline —— 否则会把「整个仓库的 5 个场景」
        当成「该模块的验收覆盖」，属于典型的假绿。
        """
        if module:
            module_dir = self.features_dir / module
            if module_dir.is_dir() and any(module_dir.rglob("*.feature")):
                return module_dir, f"module:{module}"
        return self.features_dir, "baseline"

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(self, module: Optional[str] = None,
            target: Optional[str] = None,
            derive: bool = True,
            unit_ids: Optional[List[str]] = None,
            stage: str = "G2",
            write_report: bool = True) -> Dict[str, Any]:
        """执行一次规格门禁，返回结构化结果（可直接并入流水线结果）。"""
        started = datetime.now().isoformat()

        if not self.enabled:
            return {
                "stage": stage, "status": "disabled", "blocking": False,
                "satisfies_module": False,
                "reason": "调用方显式关闭规格门禁（bdd.enabled=false）",
                "timestamp": started,
            }

        scope_path, scope = (Path(target), "explicit") if target else self.resolve_scope(module)

        if not scope_path.exists():
            result = {
                "stage": stage, "status": "missing", "blocking": False,
                "scope": scope, "features_dir": _rel(scope_path),
                "satisfies_module": False,
                "reason": f"规格路径不存在：{_rel(scope_path)}",
                "features": 0, "scenarios": 0, "steps": 0,
                "errors": 0, "warnings": 0, "blocking_issues": [],
                "coverage": {}, "derived": {},
                "timestamp": started,
            }
            self.last_run = result
            return result

        engine = self.engine()
        report = engine.validate(scope_path, allow_en=self.allow_en)
        features = report.pop("_features", [])
        self._last_features = features

        scenario_index = report.get("scenario_index", [])
        status = "fail" if report["errors"] else ("missing" if report["features"] == 0 else "pass")

        blocking_issues = [
            i for i in report["issues"] if i["severity"] == "error"
        ][:MAX_ISSUES]

        coverage = self._coverage(scenario_index, unit_ids)

        out_dir = self.output_dir / _slug(module)
        derived: Dict[str, Any] = {}
        if status == "pass" and derive:
            derived = self._derive(features, out_dir)

        report_path = None
        if write_report:
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = out_dir / "gherkin_gate.json"
            payload = {k: v for k, v in report.items()}
            payload.update({
                "stage": stage,
                "status": status,
                "scope": scope,
                "coverage": coverage,
                "derived": derived,
                "generated_at": started,
            })
            report_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        result = {
            "stage": stage,
            "status": status,
            "blocking": status == "fail",
            "scope": scope,
            "features_dir": _rel(scope_path),
            # 只有「该模块自己的规格通过」才算 G2 成立；
            # 回落到全仓基线通过 ≠ 该模块有验收场景（否则会把别模块的场景当成自己的覆盖）。
            "satisfies_module": (
                status == "pass" and (not module or scope == f"module:{module}")
            ),
            "features": report["features"],
            "scenarios": report["scenarios"],
            "steps": report["steps"],
            "errors": report["errors"],
            "warnings": report["warnings"],
            "blocking_issues": blocking_issues,
            "coverage": coverage,
            "scenario_index": scenario_index,
            "derived": derived,
            "report_path": _rel(report_path) if report_path else None,
            "timestamp": started,
        }
        self.last_run = result
        return result

    # ------------------------------------------------------------------
    # 覆盖率
    # ------------------------------------------------------------------
    def _coverage(self, scenario_index: List[Dict[str, Any]],
                  unit_ids: Optional[List[str]]) -> Dict[str, Any]:
        by_module = Counter(s.get("module") or "(未标注)" for s in scenario_index)
        by_gate = Counter(s.get("gate") or "(未标注)" for s in scenario_index)
        by_unit = Counter(s.get("unit") or "(未绑定)" for s in scenario_index)
        unbound = sorted(s["id"] or "(无编号)" for s in scenario_index if not s.get("unit"))

        coverage: Dict[str, Any] = {
            "by_module": dict(by_module),
            "by_gate": dict(by_gate),
            "by_unit": dict(by_unit),
            "scenarios_without_unit": unbound,
        }
        if unit_ids:
            declared = {u for u in unit_ids if u}
            covered = {u for u in by_unit if u not in ("(未绑定)",)}
            missing = sorted(declared - covered)
            coverage["units_declared"] = len(declared)
            coverage["units_covered"] = len(declared & covered)
            coverage["units_without_scenario"] = missing
        return coverage

    # ------------------------------------------------------------------
    # 派生（仅在 status=pass 时）
    # ------------------------------------------------------------------
    def _derive(self, features: List[Any], out_dir: Path) -> Dict[str, Any]:
        engine = self.engine()
        uat_dir = out_dir / "uat"
        steps_dir = out_dir / "steps"
        matrix_path = out_dir / "scenario_matrix.json"

        uat_files = engine.generate_uat(features, uat_dir)
        step_files = engine.generate_steps(features, steps_dir, style="pytest-bdd")
        engine.generate_matrix(features, matrix_path)

        return {
            "uat_dir": _rel(uat_dir),
            "uat_files": [_rel(p) for p in uat_files],
            "steps_dir": _rel(steps_dir),
            "steps_files": [_rel(p) for p in step_files],
            "matrix": _rel(matrix_path),
        }

    # ------------------------------------------------------------------
    # 模板上下文注入
    # ------------------------------------------------------------------
    def deliverable_context(self, module: Optional[str] = None,
                            scenario_id: Optional[str] = None,
                            run: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        由规格派生三份模板所需的变量，取代人工填写。

        只填「可从 `.feature` 机械得到」的字段；验收人、遗留问题等人类判断
        一律不代填 —— 自动编造验收结论比留空更危险。
        """
        run = run or self.last_run or {}
        if not run:
            run = self.run(module=module)

        features = self._last_features
        selected = self._select_features(features, module)

        index = run.get("scenario_index") or []
        if module:
            scoped = [s for s in index if s.get("module") == module]
        else:
            scoped = list(index)

        primary = next((s for s in scoped if s.get("id") == scenario_id), None)
        if primary is None and scoped:
            primary = scoped[0]

        ids = [s.get("id") for s in scoped if s.get("id")]
        scenario_ids = "、".join(ids[:12])
        if len(ids) > 12:
            scenario_ids += f" 等 {len(ids)} 个"

        feature_paths = [_rel(f.path) for f in selected]
        context: Dict[str, Any] = {
            # 模板本身已用反引号包裹，这里只给纯路径，避免出现 ``path``
            "gherkin_feature_path": "、".join(feature_paths) or "（未找到规格）",
            "gherkin_feature": self._feature_text(selected),
            "scenario_ids": scenario_ids or "（该模块尚未建立场景规格）",
            "scenario_id": primary.get("id", "") if primary else "",
            "scenario_name": primary.get("name", "") if primary else "",
            "scenario_description": self._describe(primary, selected) if primary else "",
            "test_prerequisites": self._background_text(primary, selected),
            "test_scenario_feature": (
                f"{primary.get('file')} #{primary.get('id')}" if primary else "（未绑定场景）"),
            "gate_level": self._gate_level(scoped),
            "generated_uat_table": self._uat_table(scoped),
            "generated_uat_path": (run.get("derived", {}).get("uat_files") or ["（未生成）"])[0],
            "gated_report_path": run.get("report_path") or "（未生成）",
            "bdd_status": run.get("status", "unknown"),
            "bdd_scope": run.get("scope", ""),
            "bdd_satisfies_module": run.get("satisfies_module", False),
            "bdd_errors": run.get("errors", 0),
            "bdd_warnings": run.get("warnings", 0),
        }
        return context

    # -- 内部工具 ------------------------------------------------------
    @staticmethod
    def _select_features(features: List[Any], module: Optional[str]) -> List[Any]:
        if not module:
            return list(features)
        hit = [f for f in features
               if f.tags.get("ct-module") == module
               or any(s.tags.get("ct-module") == module for s in f.scenarios)]
        # 指定模块时不做跨模块回落：拿别模块的场景充数会让交付物与模块无关
        return hit

    @staticmethod
    def _feature_text(features: List[Any]) -> str:
        if not features:
            return "（该模块尚未建立 .feature 规格；请在 skills/gherkin-bdd/features/ 下补充）"
        chunks: List[str] = []
        for f in features:
            body = f.path.read_text(encoding="utf-8").strip()
            chunks.append(f"# file: {_rel(f.path)}\n{body}")
        text = "\n\n".join(chunks)
        if len(text) > MAX_FEATURE_CHARS:
            text = text[:MAX_FEATURE_CHARS] + "\n\n# ... 已截断，完整内容见规格文件"
        return text

    @staticmethod
    def _describe(primary: Dict[str, Any], features: List[Any]) -> str:
        for f in features:
            for sc in f.scenarios:
                if sc.sid == primary.get("id"):
                    # 只取场景自身步骤；背景另由 test_prerequisites 表达，避免重复
                    return "；".join(f"{s.keyword} {s.text}" for s in sc.steps)
        return primary.get("name", "")

    @staticmethod
    def _background_text(primary: Optional[Dict[str, Any]], features: List[Any]) -> str:
        if not primary:
            return "（未绑定场景）"
        for f in features:
            for sc in f.scenarios:
                if sc.sid == primary.get("id"):
                    bg = list(sc.background) or list(f.background)
                    if bg:
                        return "；".join(f"{s.keyword} {s.text}" for s in bg)
                    return "见规格文件（该场景无独立背景步骤）"
        return "见规格文件"

    @staticmethod
    def _gate_level(scoped: List[Dict[str, Any]]) -> str:
        gates = sorted({s.get("gate") for s in scoped if s.get("gate")})
        if not gates:
            return "未标注"
        return " / ".join(gates)

    @staticmethod
    def _uat_table(scoped: List[Dict[str, Any]]) -> str:
        if not scoped:
            return "> 该模块尚未建立场景规格，无可派生的验收步骤。"
        lines = [
            "| 用例编号 | 场景编号 | 场景名称 | 门禁 | 步骤数 | 步骤来源 |",
            "|---|---|---|---|---|---|",
        ]
        for s in scoped:
            lines.append(
                f"| UAT-{s.get('id') or 'NA'}-01 | {s.get('id') or '—'} | {s.get('name', '')} | "
                f"{s.get('gate') or '—'} | {s.get('steps', 0)} | `{s.get('file')}` |")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 摘要
    # ------------------------------------------------------------------
    @staticmethod
    def summary_line(run: Dict[str, Any]) -> str:
        if run.get("status") == "disabled":
            return "规格门禁已关闭（bdd.enabled=false）"
        if run.get("status") == "missing":
            return f"无场景规格（{run.get('features_dir')}），场景类交付物将被阻断"
        line = (
            f"{run.get('status')} · {run.get('features')} features / "
            f"{run.get('scenarios')} scenarios / {run.get('steps')} steps · "
            f"error={run.get('errors')} warning={run.get('warnings')} · scope={run.get('scope')}"
        )
        if run.get("status") == "fail":
            line += " · 规格存在 error，禁止派生与交付"
        elif not run.get("satisfies_module"):
            line += " · 未满足模块级验收（缺该模块 .feature）"
        return line
