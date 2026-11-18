#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Odoo 实施契约校验器（零依赖）。

读取 SKILL.md 的 YAML frontmatter，校验可选 `ct_` 扩展字段。设计原则：

1. **Opt-in**：没有任何 `ct_` 字段的技能判为 `skipped`，不是 error。
   现有 21 个技能因此全部通过，不需要为了「合规」而改写。
2. **机器契约**：字段集合、枚举、正则、层级相关性全部与
   `schemas/odoo-implementation.schema.json` 一致；测试校验两者不漂移。
3. **不假绿**：声明了契约就严格校验；未知字段、非法枚举、非法版本、
   层级冲突、场景引用不可达都会产生 error 并以非零码退出。
4. **不依赖 CWD**：默认 features 根按 `__file__` 推导，产物只写工作区。

退出码：0 = 无 error（允许 skipped / warning）；1 = 存在 error；2 = 入参或工具错误。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
DEFAULT_FEATURES_DIR = SKILLS_ROOT / "gherkin-bdd" / "features"

# 与 schema 保持同步（tests/test_validate_odoo_manifest.py 做一致性断言）
BASE_FIELDS = frozenset({"name", "description", "allowed-tools", "version", "skills_used"})
CT_FIELDS = frozenset({
    "ct_layer", "ct_module", "ct_odoo_versions",
    "ct_scenario_refs", "ct_state_outputs",
})
ALLOWED_FIELDS = BASE_FIELDS | CT_FIELDS
VALID_LAYERS = frozenset({"router", "core", "shared", "module"})
MODULE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


class ToolError(RuntimeError):
    """入参或文件系统错误，对应退出码 2。"""


# ---------------------------------------------------------------------------
# 极简 frontmatter 解析（不引入 PyYAML 依赖）
# ---------------------------------------------------------------------------

def _parse_scalar(raw: str) -> Any:
    """解析单个 YAML 标量：内联数组 / 带引号字符串 / 裸字符串。"""
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        items: List[str] = []
        for part in value[1:-1].split(","):
            item = part.strip().strip('"').strip("'").strip()
            if item:
                items.append(item)
        return items
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    解析 SKILL.md 的 frontmatter，返回 (字段字典, 字段首行行号)。

    支持顶格 `key: value`、内联数组 `[a, b]`、以及缩进续行（长 description
    或块数组 `- item`）。不解析嵌套映射——本契约不需要。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ToolError("SKILL.md 缺少 frontmatter 起始标记 `---`")

    manifest: Dict[str, Any] = {}
    line_map: Dict[str, int] = {}
    current: Optional[str] = None
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if match:
            key, raw = match.group(1), match.group(2)
            manifest[key] = _parse_scalar(raw)
            line_map[key] = index
            current = key
        elif line[:1].isspace() and current:
            continuation = line.strip()
            if continuation.startswith("- "):
                existing = manifest.get(current)
                if not isinstance(existing, list):
                    existing = [] if not existing else [existing]
                existing.append(_parse_scalar(continuation[2:]))
                manifest[current] = existing
            elif continuation:
                existing = manifest.get(current, "")
                manifest[current] = f"{existing} {continuation}".strip()
    return manifest, line_map


# ---------------------------------------------------------------------------
# 契约校验
# ---------------------------------------------------------------------------

def _issue(severity: str, code: str, key: str, message: str,
           file: str, line_map: Dict[str, int]) -> Dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "file": file,
        "line": line_map.get(key, 0),
        "message": message,
    }


def _scenario_refs_reachable(refs: List[str], features_dir: Path) -> List[str]:
    """返回不可达的引用列表；不读取 feature 以外的任何路径。"""
    missing: List[str] = []
    feature_files = sorted(features_dir.rglob("*.feature")) if features_dir.is_dir() else []
    corpus: Optional[str] = None
    for ref in refs:
        if "/" in ref or ref.endswith(".feature"):
            if any((features_dir / ref).resolve() == f.resolve() for f in feature_files):
                continue
            if (SKILLS_ROOT / ref).is_file():
                continue
            missing.append(ref)
            continue
        if corpus is None:
            corpus = "\n".join(f.read_text(encoding="utf-8") for f in feature_files)
        if ref not in corpus:
            missing.append(ref)
    return missing


def validate_manifest(manifest: Dict[str, Any], *, file: str,
                      line_map: Optional[Dict[str, int]] = None,
                      features_dir: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    校验一份 frontmatter，返回 (issues, status)。

    status ∈ {validated, skipped}。skipped 表示未声明任何 ct_ 字段，
    属于合法状态；校验器不对 opt-out 的技能做任何断言。
    """
    line_map = line_map or {}
    issues: List[Dict[str, Any]] = []
    ct_present = sorted(k for k in manifest if k.startswith("ct_"))

    if not ct_present:
        return issues, "skipped"

    def add(severity: str, code: str, key: str, message: str) -> None:
        issues.append(_issue(severity, code, key, message, file, line_map))

    for key in sorted(manifest):
        if key not in ALLOWED_FIELDS:
            add("error", "CT-003", key,
                f"未知字段 `{key}`：仅允许既有字段与 {sorted(CT_FIELDS)} 中的 ct_ 扩展字段")

    layer = manifest.get("ct_layer")
    if "ct_layer" in manifest and (not isinstance(layer, str) or layer not in VALID_LAYERS):
        add("error", "CT-003", "ct_layer",
            f"ct_layer 必须为 {sorted(VALID_LAYERS)} 之一，实际为 {layer!r}")

    if "ct_module" in manifest:
        module = manifest["ct_module"]
        if not isinstance(module, str) or not MODULE_PATTERN.match(module):
            add("error", "CT-003", "ct_module",
                "ct_module 必须匹配 ^[a-z][a-z0-9_]*$")
        if layer != "module":
            add("error", "CT-003", "ct_module",
                "ct_module 仅允许 ct_layer=module 时声明（与 schema 的 if/then 一致）")
    elif layer == "module":
        add("error", "CT-001", "ct_layer",
            "ct_layer=module 时必须声明 ct_module")

    if "ct_odoo_versions" in manifest:
        versions = manifest["ct_odoo_versions"]
        if not isinstance(versions, list) or not versions:
            add("error", "CT-003", "ct_odoo_versions",
                "ct_odoo_versions 必须是非空数组")
        else:
            for version in versions:
                if not isinstance(version, str) or not VERSION_PATTERN.match(version):
                    add("error", "CT-003", "ct_odoo_versions",
                        f"版本 `{version!r}` 非法，须形如 17.0 / 18.0 / 19.0")

    for key in ("ct_scenario_refs", "ct_state_outputs"):
        if key in manifest:
            values = manifest[key]
            if not isinstance(values, list) or not values or not all(
                isinstance(v, str) and v for v in values
            ):
                add("error", "CT-003", key, f"{key} 必须是非空字符串数组")

    if "ct_scenario_refs" in manifest:
        refs = manifest.get("ct_scenario_refs")
        root = features_dir if features_dir is not None else DEFAULT_FEATURES_DIR
        if isinstance(refs, list) and all(isinstance(v, str) for v in refs):
            if not root.is_dir():
                add("warning", "CT-008", "ct_scenario_refs",
                    f"场景引用未验证：features 目录不可达（{root}）")
            else:
                missing = _scenario_refs_reachable(refs, root)
                if missing:
                    add("error", "CT-004", "ct_scenario_refs",
                        "场景引用不可达：" + ", ".join(missing))

    return issues, "validated"


# ---------------------------------------------------------------------------
# 批量入口
# ---------------------------------------------------------------------------

def _iter_skill_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(p for p in path.rglob("SKILL.md") if p.is_file())
    raise ToolError(f"路径不存在：{path}")


def run(path: Path, *, features_dir: Optional[Path] = None,
        list_only: bool = False) -> Dict[str, Any]:
    files = _iter_skill_files(path)
    reports: List[Dict[str, Any]] = []
    all_issues: List[Dict[str, Any]] = []

    for skill_file in files:
        text = skill_file.read_text(encoding="utf-8")
        manifest, line_map = parse_frontmatter(text)
        ct_fields = sorted(k for k in manifest if k.startswith("ct_"))
        if list_only:
            if ct_fields:
                reports.append({
                    "file": str(skill_file),
                    "name": manifest.get("name", ""),
                    "ct_fields": ct_fields,
                })
            continue
        display = str(skill_file.relative_to(Path.cwd())) if skill_file.is_relative_to(Path.cwd()) else str(skill_file)
        issues, status = validate_manifest(manifest, file=display,
                                           line_map=line_map, features_dir=features_dir)
        all_issues.extend(issues)
        reports.append({
            "file": display,
            "name": manifest.get("name", ""),
            "status": status,
            "ct_fields": ct_fields,
        })

    if list_only:
        return {"status": "pass", "mode": "list", "manifests": reports}

    errors = [i for i in all_issues if i["severity"] == "error"]
    return {
        "status": "fail" if errors else "pass",
        "mode": "file" if path.is_file() else "directory",
        "manifest_checked": sum(1 for r in reports if r["status"] == "validated"),
        "manifest_skipped": sum(1 for r in reports if r["status"] == "skipped"),
        "issues": all_issues,
        "manifests": reports,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="校验 Odoo 实施契约（SKILL.md frontmatter）")
    parser.add_argument("path", type=Path, help="SKILL.md 文件或包含技能包的目录")
    parser.add_argument("--features-dir", type=Path, default=None,
                        help=".feature 根目录；默认按 __file__ 推导兄弟 gherkin-bdd 技能")
    parser.add_argument("--list", action="store_true", help="仅列出声明 ct_ 字段的技能")
    args = parser.parse_args(argv)

    try:
        report = run(args.path, features_dir=args.features_dir, list_only=args.list)
    except (ToolError, OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
