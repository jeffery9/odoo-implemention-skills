#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gherkin Gate — Capability Twin 业务场景统一语言的可执行判定器。

职责：解析 zh-CN Gherkin、静态校验、生成 UAT / 步骤桩 / 追溯矩阵。
设计约束：
1. 纯标准库，无第三方依赖，可在任何 CI 环境直接运行；
2. 只做规格层校验，不假装执行了自动化测试；
3. 存在 error 即返回退出码 1，不设加权分数、不设成熟度等级；
4. 路径以相对当前工作目录的形式写入报告，保证可移植与可复现。

用法见 skills/gherkin-bdd/INTEGRATION_GUIDE.md。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# 关键字表（zh-CN 为唯一标准方言；英文关键字仅用于迁移期检测）
# --------------------------------------------------------------------------

ZH = {
    "feature": ["功能"],
    "rule": ["规则"],
    "background": ["背景"],
    "scenario": ["场景"],
    "outline": ["场景大纲"],
    "examples": ["例子"],
    "given": ["假如", "假设", "假定"],
    "when": ["当"],
    "then": ["那么"],
    "and": ["而且", "并且", "同时"],
    "but": ["但是"],
}
EN = {
    "feature": ["Feature"],
    "rule": ["Rule"],
    "background": ["Background"],
    "scenario": ["Scenario"],
    "outline": ["Scenario Outline", "Scenario Template"],
    "examples": ["Examples", "Scenarios"],
    "given": ["Given"],
    "when": ["When"],
    "then": ["Then"],
    "and": ["And"],
    "but": ["But"],
}

STRUCT_TOKENS: List[Tuple[str, str, str]] = []
STEP_TOKENS: List[Tuple[str, str, str]] = []
for _kind in ("feature", "rule", "background", "scenario", "outline", "examples"):
    for _kw in ZH[_kind]:
        STRUCT_TOKENS.append((_kw, _kind, "zh"))
    for _kw in EN[_kind]:
        STRUCT_TOKENS.append((_kw, _kind, "en"))
for _kind in ("given", "when", "then", "and", "but"):
    for _kw in ZH[_kind]:
        STEP_TOKENS.append((_kw, _kind, "zh"))
    for _kw in EN[_kind]:
        STEP_TOKENS.append((_kw, _kind, "en"))
STEP_TOKENS.append(("*", "wildcard", "any"))

# 长关键字优先，避免 "Scenario" 抢先匹配 "Scenario Outline"
STRUCT_TOKENS.sort(key=lambda item: len(item[0]), reverse=True)
STEP_TOKENS.sort(key=lambda item: len(item[0]), reverse=True)

STRUCT_RE = re.compile(
    r"^\s*(?P<kw>" + "|".join(re.escape(k) for k, _, _ in STRUCT_TOKENS)
    + r")\s*(?P<colon>[:：])\s*(?P<title>.*)$"
)
STEP_RE = re.compile(
    r"^\s*(?P<kw>" + "|".join(re.escape(k) for k, _, _ in STEP_TOKENS)
    + r")\s+(?P<text>.*)$"
)
STRUCT_KIND = {k: (kind, lang) for k, kind, lang in STRUCT_TOKENS}
STEP_KIND = {k: (kind, lang) for k, kind, lang in STEP_TOKENS}

LANG_RE = re.compile(r"^#\s*language\s*:\s*(\S+)\s*$", re.I)
TAG_RE = re.compile(r"@[^\s@]+")
TAG_SPLIT_RE = re.compile(r"[=:]")
TAG_VALUE_RE = re.compile(r"^[A-Za-z0-9._=/:-]*$")
PLACEHOLDER_RE = re.compile(r"<([^<>]+)>")
ROW_RE = re.compile(r"^\s*\|.*\|\s*$")

REQUIRED_TAGS = ("ct-id", "ct-unit", "ct-module", "ct-gate")
ID_RE = re.compile(r"^SCN-[A-Z0-9]+-\d{3,}$")

# --------------------------------------------------------------------------
# 统一语言禁用词（详见 references/ubiquitous-language.md）
# --------------------------------------------------------------------------

BANNED_ALIASES = (
    "客户订单", "出库单", "交货单", "收货单", "生产订单", "作业单", "工序单",
    "采购发票", "供应商发票", "预估入账", "暂估入库", "已发货未开票", "在途商品",
    "现货量", "可用库存", "批号", "营收", "销售成本", "草稿订单", "SO 单", "PO 单",
    "MO 单", "配方", "存货估值", "成本计价", "在途库存",
)
BANNED_TECH = (
    "click(", "xpath", "selector", "@api", "create(", "write(", "button_validate",
    "AbstractModel", "mixin", "Sprint", "SEC-", "XML ID", "menu_id", "view_id",
    "ir.model", "res.groups", "account.move", "stock.picking", "mrp.production",
    "sale.order", "res.partner", "purchase.order", "mrp.bom", "stock.quant",
)
MODEL_RE = re.compile(r"(?<![A-Za-z0-9_])(?:[a-z][a-z0-9_]*)\.(?:[a-z][a-z0-9_]*)(?![A-Za-z0-9_])")
FIELD_RE = re.compile(r"(?<![A-Za-z0-9_])(?:[a-z][a-z0-9]*_[a-z0-9_]+)(?![A-Za-z0-9_])")
ABBR_RE = re.compile(r"(?<![A-Za-z])(?:WIP|BOM|COGS|AR|AP|ORM)(?![A-Za-z])")
VAGUE_WORDS = (
    "系统正常", "操作成功", "符合预期", "正确显示", "正常工作",
    "成功", "正确", "合理", "适当", "若干", "稍后", "尽快", "等等",
)

# --------------------------------------------------------------------------
# 数据模型
# --------------------------------------------------------------------------


@dataclass
class Issue:
    severity: str
    code: str
    file: str
    line: int
    message: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity, "code": self.code, "file": self.file,
            "line": self.line, "message": self.message,
        }


@dataclass
class Step:
    line: int
    kind: str
    keyword: str
    text: str
    data_table: List[List[str]] = field(default_factory=list)
    docstring: List[str] = field(default_factory=list)


@dataclass
class Examples:
    line: int
    header: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    bad_rows: List[int] = field(default_factory=list)


@dataclass
class Scenario:
    line: int
    name: str
    is_outline: bool
    tags: Dict[str, str]
    own_tags: Dict[str, str]
    steps: List[Step] = field(default_factory=list)
    examples: List[Examples] = field(default_factory=list)
    rule: str = ""
    file: str = ""
    feature: str = ""
    background: List[Step] = field(default_factory=list)

    @property
    def sid(self) -> str:
        return self.tags.get("ct-id", "")


@dataclass
class Feature:
    path: Path
    rel: str
    name: str
    line: int
    language: Optional[str]
    tags: Dict[str, str]
    description: List[str] = field(default_factory=list)
    background: List[Step] = field(default_factory=list)
    scenarios: List[Scenario] = field(default_factory=list)


def _rel(path: Path) -> str:
    """报告中的路径一律相对 CWD，避免绝对路径造成 diff 噪声。"""
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _cells(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _issue(sev: str, code: str, rel: str, line: int, msg: str) -> Issue:
    return Issue(sev, code, rel, line, msg)


# --------------------------------------------------------------------------
# 解析器
# --------------------------------------------------------------------------


def parse_feature(path: Path, allow_en: bool = False) -> Tuple[Optional[Feature], List[Issue]]:
    issues: List[Issue] = []
    rel = _rel(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    language: Optional[str] = None
    feature: Optional[Feature] = None
    current: Optional[Scenario] = None
    current_examples: Optional[Examples] = None
    current_rule = ""
    in_background = False
    last_struct = ""
    last_step: Optional[Step] = None
    last_kind: Optional[str] = None
    pending_tags: List[Tuple[str, int]] = []
    docstring_open = False

    def parse_tag_line(raw: str, lineno: int) -> Dict[str, str]:
        nonlocal issues
        out: Dict[str, str] = {}
        if "#" in raw:
            issues.append(_issue("error", "BDD-010", rel, lineno,
                                 "标签行含 '#'，Gherkin 会将其后内容视为注释"))
        for token in TAG_RE.findall(raw.strip()):
            body = token[1:]
            parts = TAG_SPLIT_RE.split(body, maxsplit=1)
            key, value = parts[0], (parts[1] if len(parts) > 1 else "")
            if value and not TAG_VALUE_RE.match(value):
                issues.append(_issue("error", "BDD-010", rel, lineno,
                                     f"标签 @{key} 的值含非法字符：{value}"))
            out[key] = value
        return out

    def merge_tags(raw_map: Dict[str, str]) -> Dict[str, str]:
        merged = dict(feature.tags) if feature else {}
        merged.update(raw_map)
        return merged

    for lineno, raw in enumerate(lines, 1):
        stripped = raw.strip()

        if docstring_open:
            if stripped.startswith('"""'):
                docstring_open = False
            elif last_step is not None:
                last_step.docstring.append(raw)
            continue

        if not stripped:
            continue

        if stripped.startswith('"""'):
            if last_step is None:
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     "DocString 未挂在任何步骤下"))
            docstring_open = True
            continue

        if stripped.startswith("#"):
            m = LANG_RE.match(stripped)
            if m:
                language = m.group(1)
            continue

        if stripped.startswith("@"):
            # 标签出现在上一个场景的步骤之后是合法的（它属于下一个场景）；
            # 只有「标签后直接跟步骤」才是不归属，由步骤分支判定。
            if "#" in stripped:
                issues.append(_issue("error", "BDD-010", rel, lineno,
                                     "标签行含 '#'，Gherkin 会将其后内容视为注释"))
            pending_tags.extend((t, lineno) for t in TAG_RE.findall(stripped))
            continue

        if ROW_RE.match(raw):
            cells = _cells(raw)
            if current_examples is not None:
                if not current_examples.header:
                    current_examples.header = cells
                else:
                    if len(cells) != len(current_examples.header):
                        current_examples.bad_rows.append(lineno)
                    current_examples.rows.append(cells)
            elif last_step is not None:
                last_step.data_table.append(cells)
            else:
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     "数据表 / 例子表没有归属（缺少场景或例子声明）"))
            continue

        sm = STRUCT_RE.match(raw)
        if sm:
            kw, colon, title = sm.group("kw"), sm.group("colon"), sm.group("title").strip()
            kind, lang = STRUCT_KIND[kw]
            if lang == "en":
                sev = "warning" if allow_en else "error"
                issues.append(_issue(sev, "BDD-002", rel, lineno,
                                     f"使用了英文结构关键字 '{kw}'，标准方言为 zh-CN"))
            if colon == "：":
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     f"'{kw}' 后必须使用半角冒号 ':'"))

            tag_map: Dict[str, str] = {}
            for _tok, _ln in pending_tags:
                tag_map.update(parse_tag_line(_tok, _ln))
            own = dict(tag_map)
            pending_tags.clear()
            current_examples = None
            last_step = None

            if kind == "feature":
                if feature is not None:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "单个 .feature 文件只允许一个 功能"))
                else:
                    feature = Feature(path=path, rel=rel, name=title, line=lineno,
                                      language=None, tags=own)
                    if "ct-id" in own:
                        issues.append(_issue("error", "BDD-003", rel, lineno,
                                             "@ct-id 必须逐场景声明，禁止写在功能级"))
                last_struct, in_background, current = "feature", False, None
            elif kind == "rule":
                if feature is None:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "规则 出现在 功能 之前"))
                current_rule, last_struct, in_background, current = title, "rule", False, None
                last_kind = None
            elif kind == "background":
                if feature is None:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "背景 出现在 功能 之前"))
                if own:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "背景 不接受标签"))
                last_struct, in_background, current = "background", True, None
                last_kind = None
            elif kind in ("scenario", "outline"):
                if feature is None:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "场景 出现在 功能 之前"))
                    continue
                merged = merge_tags(own)
                current = Scenario(line=lineno, name=title, is_outline=(kind == "outline"),
                                   tags=merged, own_tags=own, rule=current_rule,
                                   file=rel, feature=feature.name,
                                   background=list(feature.background))
                feature.scenarios.append(current)
                last_struct, in_background = "scenario", False
                # 场景的 And/But 可继承背景最后一步的语义
                last_kind = feature.background[-1].kind if feature.background else None
            elif kind == "examples":
                if current is None or not current.is_outline or own:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         "例子 只能位于 场景大纲 内且不接受标签"))
                elif current is not None:
                    current_examples = Examples(line=lineno)
                    current.examples.append(current_examples)
                    last_struct = "examples"
            continue

        tm = STEP_RE.match(raw)
        if tm:
            kw, text = tm.group("kw"), tm.group("text").strip()
            kind, lang = STEP_KIND[kw]
            if lang == "en":
                sev = "warning" if allow_en else "error"
                issues.append(_issue(sev, "BDD-002", rel, lineno,
                                     f"使用了英文步骤关键字 '{kw}'，标准方言为 zh-CN"))
            if pending_tags:
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     "存在未归属的标签（标签后必须是 功能 / 场景）"))
                pending_tags.clear()
            if not text:
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     f"步骤 '{kw}' 的文本为空"))
            if kind in ("and", "but", "wildcard"):
                if last_kind is None:
                    issues.append(_issue("error", "BDD-018", rel, lineno,
                                         f"'{kw}' 之前没有可承接的步骤"))
                    resolved = "unknown"
                else:
                    resolved = last_kind
            else:
                resolved = kind
                last_kind = kind
            step = Step(line=lineno, kind=resolved, keyword=kw, text=text)
            if in_background and feature is not None and current is None:
                feature.background.append(step)
            elif current is not None:
                current.steps.append(step)
            else:
                issues.append(_issue("error", "BDD-018", rel, lineno,
                                     "步骤出现在 功能描述 或 背景 之外的非法位置"))
            last_step, last_struct = step, "step"
            current_examples = None
            continue

        # 功能描述行（作为 / 我希望 / 以便）
        if feature is not None and current is None and not in_background and last_struct in ("feature", "rule"):
            feature.description.append(stripped)
            continue

        issues.append(_issue("error", "BDD-018", rel, lineno,
                             f"无法解析的行：{stripped[:60]}"))

    if docstring_open:
        issues.append(_issue("error", "BDD-018", rel, len(lines),
                             "DocString 未闭合"))
    if feature is not None:
        feature.language = language
        for sc in feature.scenarios:
            sc.background = list(feature.background)
    return feature, issues


# --------------------------------------------------------------------------
# 校验器
# --------------------------------------------------------------------------


def _banned_hits(text: str) -> List[str]:
    hits: List[str] = []
    for alias in BANNED_ALIASES:
        if alias in text:
            hits.append(f"禁用别名「{alias}」")
    for tech in BANNED_TECH:
        if tech.lower() in text.lower():
            hits.append(f"技术黑话「{tech}」")
    for rex, label in ((MODEL_RE, "Odoo 对象名"), (FIELD_RE, "字段/方法名"), (ABBR_RE, "技术缩写")):
        for m in rex.finditer(text):
            hits.append(f"{label}「{m.group(0)}」")
    return sorted(set(hits))


def validate_feature(feature: Feature, issues: List[Issue], allow_en: bool = False) -> None:
    rel = feature.rel

    if feature.language is None:
        issues.append(_issue("error", "BDD-001", rel, 1,
                             "缺少 '# language: zh-CN' 声明（必须是文件首行）"))
    elif feature.language.lower() != "zh-cn":
        sev = "warning" if allow_en else "error"
        issues.append(_issue(sev, "BDD-002", rel, 1,
                             f"方言声明为 {feature.language}，标准要求 zh-CN"))

    desc = "\n".join(feature.description)
    if not all(word in desc for word in ("作为", "我希望", "以便")):
        issues.append(_issue("warning", "BDD-017", rel, feature.line,
                             "功能描述建议包含「作为 / 我希望 / 以便」业务价值三段式"))

    if not feature.scenarios:
        issues.append(_issue("error", "BDD-011", rel, feature.line,
                             f"功能「{feature.name}」没有任何场景"))

    for label, text in [("功能名称", feature.name)] + [("描述", d) for d in feature.description]:
        hits = _banned_hits(text)
        if hits:
            issues.append(_issue("error", "BDD-007", rel, feature.line,
                                 f"{label}含统一语言违规：{'、'.join(hits)}"))

    module_dir = ""
    parts = Path(rel).parts
    if "features" in parts:
        idx = parts.index("features")
        if idx + 1 < len(parts) - 1:
            module_dir = parts[idx + 1]

    for sc in feature.scenarios:
        loc = sc.line
        missing = [t for t in REQUIRED_TAGS if not sc.tags.get(t)]
        if missing:
            issues.append(_issue("error", "BDD-003", rel, loc,
                                 f"场景「{sc.name}」缺少必填标签：{', '.join('@' + t for t in missing)}"))

        sid = sc.sid
        if sid and not ID_RE.match(sid):
            issues.append(_issue("error", "BDD-013", rel, loc,
                                 f"@ct-id={sid} 不符合 SCN-<域>-<3位序号> 格式"))
        expected_module = sc.tags.get("ct-module", "")
        if module_dir and expected_module and expected_module != module_dir:
            issues.append(_issue("warning", "BDD-014", rel, loc,
                                 f"@ct-module={expected_module} 与目录 features/{module_dir}/ 不一致"))
        if not sc.tags.get("ct-source"):
            issues.append(_issue("warning", "BDD-019", rel, loc,
                                 f"场景「{sc.name}」缺少 @ct-source 源码证据"))

        if not sc.steps:
            issues.append(_issue("error", "BDD-011", rel, loc,
                                 f"场景「{sc.name}」没有任何步骤"))
            continue

        seq = [s.kind for s in sc.background] + [s.kind for s in sc.steps]
        for key, label in (("given", "假如"), ("when", "当"), ("then", "那么")):
            if key not in seq:
                issues.append(_issue("error", "BDD-005", rel, loc,
                                     f"场景「{sc.name}」缺少 {label}（假如可由背景提供）"))

        state = 0  # 0=前置, 1=动作, 2=结果
        for step in sc.steps:
            if step.kind == "given" and state >= 1:
                issues.append(_issue("error", "BDD-006", rel, step.line,
                                     "假如 出现在 当 / 那么 之后"))
            elif step.kind == "when" and state >= 2:
                issues.append(_issue("error", "BDD-006", rel, step.line,
                                     "当 出现在 那么 之后"))
            if step.kind == "when":
                state = max(state, 1)
            elif step.kind == "then":
                state = 2
            if step.kind == "unknown":
                issues.append(_issue("error", "BDD-018", rel, step.line,
                                     f"步骤 '{step.keyword}' 无法确定语义类型"))

        if seq.count("when") > 1:
            issues.append(_issue("warning", "BDD-012", rel, loc,
                                 f"场景「{sc.name}」含 {seq.count('when')} 个业务动作，建议拆分"))

        seen_texts: Dict[str, int] = {}
        for step in list(sc.background) + list(sc.steps):
            if step.text in seen_texts:
                issues.append(_issue("warning", "BDD-016", rel, step.line,
                                     f"重复步骤文本：{step.text[:40]}"))
            seen_texts[step.text] = step.line
            if len(step.text) < 6 or any(w in step.text for w in VAGUE_WORDS):
                issues.append(_issue("warning", "BDD-015", rel, step.line,
                                     f"结果不可判定或步骤过短：{step.text[:40]}"))
            hits = _banned_hits(step.text)
            if hits:
                issues.append(_issue("error", "BDD-007", rel, step.line,
                                     f"步骤含统一语言违规：{'、'.join(hits)}"))

        name_hits = _banned_hits(sc.name)
        if name_hits:
            issues.append(_issue("error", "BDD-007", rel, loc,
                                 f"场景名称含统一语言违规：{'、'.join(name_hits)}"))

        if sc.is_outline:
            placeholders = set()
            for step in sc.steps:
                placeholders.update(PLACEHOLDER_RE.findall(step.text))
            if not sc.examples:
                issues.append(_issue("error", "BDD-008", rel, loc,
                                     f"场景大纲「{sc.name}」缺少 例子 数据表"))
            for ex in sc.examples:
                if not ex.header:
                    issues.append(_issue("error", "BDD-009", rel, ex.line,
                                         "例子 缺少表头"))
                    continue
                if not ex.rows:
                    issues.append(_issue("error", "BDD-009", rel, ex.line,
                                         "例子 缺少数据行"))
                if ex.bad_rows:
                    issues.append(_issue("error", "BDD-009", rel, ex.bad_rows[0],
                                         f"例子 数据行列数与表头不一致（行 {ex.bad_rows}）"))
                header = set(ex.header)
                unused = header - placeholders
                undefined = placeholders - header
                if unused or undefined:
                    pieces = []
                    if undefined:
                        pieces.append("步骤占位符未在表头定义：" + ", ".join(sorted(undefined)))
                    if unused:
                        pieces.append("表头列未被步骤使用：" + ", ".join(sorted(unused)))
                    issues.append(_issue("error", "BDD-008", rel, ex.line, "；".join(pieces)))
        elif sc.examples:
            issues.append(_issue("error", "BDD-018", rel, sc.line,
                                 "普通 场景 不允许携带 例子 数据表"))


def collect_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target] if target.suffix == ".feature" else []
    if target.is_dir():
        return sorted(target.rglob("*.feature"))
    return []


def validate(target: Path, allow_en: bool = False) -> Dict[str, Any]:
    issues: List[Issue] = []
    features: List[Feature] = []
    files = collect_files(target)

    if not files:
        issues.append(_issue("error", "BDD-020", _rel(target), 0,
                             f"未在 {_rel(target)} 发现任何 .feature 文件"))

    for path in files:
        feature, parse_issues = parse_feature(path, allow_en=allow_en)
        issues.extend(parse_issues)
        if feature is not None:
            features.append(feature)
            validate_feature(feature, issues, allow_en=allow_en)

    seen_ids: Dict[str, str] = {}
    for feature in features:
        for sc in feature.scenarios:
            sid = sc.sid
            if not sid:
                continue
            if sid in seen_ids:
                issues.append(_issue("error", "BDD-004", feature.rel, sc.line,
                                     f"@ct-id={sid} 与 {seen_ids[sid]} 重复"))
            else:
                seen_ids[sid] = f"{feature.rel}:{sc.line}"

    scenario_index = []
    for feature in features:
        for sc in feature.scenarios:
            scenario_index.append({
                "id": sc.sid,
                "name": sc.name,
                "file": feature.rel,
                "line": sc.line,
                "unit": sc.tags.get("ct-unit", ""),
                "module": sc.tags.get("ct-module", ""),
                "gate": sc.tags.get("ct-gate", ""),
                "source": sc.tags.get("ct-source", ""),
                "priority": sc.tags.get("ct-priority", ""),
                "outline": sc.is_outline,
                "steps": len(sc.steps),
                "examples": sum(len(ex.rows) for ex in sc.examples),
            })

    errors = [i for i in issues if i.severity == "error"]
    return {
        "status": "fail" if errors else "pass",
        "target": _rel(target),
        "features": len(features),
        "scenarios": len(scenario_index),
        "steps": sum(len(s.steps) for f in features for s in f.scenarios),
        "errors": len(errors),
        "warnings": len(issues) - len(errors),
        "issues": [i.as_dict() for i in issues],
        "scenario_index": scenario_index,
        "_features": features,
    }


# --------------------------------------------------------------------------
# 生成器：UAT / 步骤桩 / 追溯矩阵
# --------------------------------------------------------------------------


def generate_uat(features: List[Feature], out_dir: Path) -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for feature in features:
        module = Path(feature.rel).parent.name
        target = out_dir / f"{module}_{feature.path.stem}_UAT.md"
        lines: List[str] = [
            f"# 用户验收测试 (UAT) 脚本：{feature.name}",
            "",
            "> 本文件由 `gherkin_gate.py uat` 自动生成，**请勿手工编辑**。",
            "> 业务场景的唯一事实源是下方「来源规格」，任何修改请回到 `.feature`。",
            "",
            f"- **来源规格**: `{feature.rel}`",
            f"- **场景数**: {len(feature.scenarios)}",
            f"- **步骤数**: {sum(len(s.steps) for s in feature.scenarios)}",
            "",
            "---",
            "",
        ]
        for sc in feature.scenarios:
            lines.extend([
                f"## {sc.sid or '未编号'}：{sc.name}",
                "",
                f"- 能力单元: {sc.tags.get('ct-unit', '—')} | 模块: {sc.tags.get('ct-module', '—')} "
                f"| 质量门: {sc.tags.get('ct-gate', '—')} | 优先级: {sc.tags.get('ct-priority', '—')}",
                f"- 源码证据: {sc.tags.get('ct-source', '待补充')}",
                f"- 规格位置: `{sc.file}:{sc.line}`",
                "",
            ])
            if sc.background:
                lines.append("**背景（全部场景共有的前置条件）**")
                lines.append("")
                for step in sc.background:
                    lines.append(f"- {step.keyword} {step.text}")
                lines.append("")
            lines.extend([
                "| 步骤 | 类型 | 操作 / 前置 | 预期结果 | 实际结果 | 状态 |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ])
            last_kind = sc.background[-1].kind if sc.background else "given"
            for idx, step in enumerate(sc.steps, 1):
                kind = last_kind if step.kind in ("and", "but", "wildcard", "unknown") else step.kind
                last_kind = kind
                expected = step.text if kind == "then" else "—"
                lines.append(
                    f"| {idx} | {kind} | {step.keyword} {step.text} | {expected} | | [ ] |"
                )
            if sc.examples:
                lines.extend(["", "**参数化数据（例子）**", ""])
                for ex in sc.examples:
                    if not ex.header:
                        continue
                    lines.append("| " + " | ".join(ex.header) + " |")
                    lines.append("| " + " | ".join([":---"] * len(ex.header)) + " |")
                    for row in ex.rows:
                        lines.append("| " + " | ".join(row) + " |")
            lines.extend(["", "---", ""])
        lines.extend([
            "## 验收确认",
            "",
            "- **验收人**: ________________",
            "- **验收日期**: ________________",
            "- **遗留问题 (Issues)**: ________________",
            "",
            "> **边界声明**：本脚本通过仅代表交付验收（G3）或工程完成（G2）的判定，",
            "> **交付验收 ≠ 价值实现**；客户侧价值裁定独立于交付方。",
            "> 价值三态（基线 / 目标 / 实测）另按 FDE 2.0 §5.3–5.5 记录。",
            "",
            "*Capability Twin 3.5 | 由 Gherkin BDD 统一语言派生*",
            "",
        ])
        target.write_text("\n".join(lines), encoding="utf-8")
        written.append(_rel(target))
    return written


def _parse_expression(text: str) -> str:
    """把 Gherkin <占位符> 转成 pytest-bdd / behave 的 parse 表达式。"""
    return PLACEHOLDER_RE.sub(lambda m: "{" + m.group(1) + "}", text)


def generate_steps(features: List[Feature], out_dir: Path, style: str = "pytest-bdd") -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for feature in features:
        module = Path(feature.rel).parent.name
        if style == "behave":
            # behave 按 features/steps/*.py 收集，不依赖 test_ 前缀；
            # 不带 test_ 也避免被 pytest 误收集后 import behave 失败。
            target = out_dir / f"steps_{module}_{feature.path.stem}_behave.py"
        else:
            target = out_dir / f"test_{module}_{feature.path.stem}_pytest_bdd.py"
        unique: Dict[Tuple[str, str], Step] = {}
        for sc in feature.scenarios:
            for step in list(sc.background) + list(sc.steps):
                key = (step.kind, step.text)
                unique.setdefault(key, step)

        lines: List[str] = [
            "# -*- coding: utf-8 -*-",
            f"# 由 gherkin_gate.py steps 生成，来源：{feature.rel}",
            "# 请勿手工编辑步骤文本；实现完成后删除 NotImplementedError。",
            "# 未实现的步骤会显式抛错，避免自动化「假绿」。",
            "",
        ]
        if style == "behave":
            lines.extend([
                "from behave import given, when, then, use_step_matcher",
                "",
                'use_step_matcher("parse")',
                "",
            ])
        else:
            feature_rel = Path(os.path.relpath(
                feature.path.resolve(), target.parent.resolve())).as_posix()
            lines.extend([
                "# 依赖：pip install pytest-bdd；在仓库根执行 pytest 即可收集本文件的场景",
                "from pytest_bdd import given, when, then, parsers, scenarios",
                "",
                f"scenarios({feature_rel!r})",
                "",
            ])

        decorator = {"given": "given", "when": "when", "then": "then"}
        for idx, ((kind, text), step) in enumerate(sorted(
                unique.items(), key=lambda item: (item[1].line, item[0][0])), 1):
            deco = decorator.get(kind, "given")
            expression = _parse_expression(text)
            matcher = f"parsers.parse({expression!r})" if style != "behave" else repr(expression)
            params = [m.group(1) for m in PLACEHOLDER_RE.finditer(text)]
            signature = ["context"] if style == "behave" else []
            signature.extend(params)
            lines.extend([
                f"@{deco}({matcher})",
                f"def step_{idx:03d}({', '.join(signature)}):",
                f'    """{step.keyword} {text}"""',
                f'    raise NotImplementedError("步骤未实现：{step.keyword} {text}")',
                "",
            ])
        target.write_text("\n".join(lines), encoding="utf-8")
        written.append(_rel(target))
    return written


def generate_matrix(features: List[Feature], out_path: Path) -> str:
    scenarios = []
    for feature in features:
        for sc in feature.scenarios:
            scenarios.append({
                "id": sc.sid, "name": sc.name, "feature": feature.name,
                "file": feature.rel, "line": sc.line,
                "unit": sc.tags.get("ct-unit", ""), "module": sc.tags.get("ct-module", ""),
                "gate": sc.tags.get("ct-gate", ""), "source": sc.tags.get("ct-source", ""),
                "steps": len(sc.steps),
                "examples": sum(len(ex.rows) for ex in sc.examples),
            })
    by_unit: Dict[str, List[str]] = {}
    by_gate: Dict[str, List[str]] = {}
    for item in scenarios:
        by_unit.setdefault(item["unit"] or "UNASSIGNED", []).append(item["id"])
        by_gate.setdefault(item["gate"] or "UNASSIGNED", []).append(item["id"])
    payload = {
        "generated_from": "gherkin_gate.py matrix",
        "scenarios": scenarios,
        "by_unit": by_unit,
        "by_gate": by_gate,
        "disclaimer": "场景矩阵是规格索引，不是自动化测试结果；G2 证据以外部 runner 输出为准。",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _rel(out_path)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _report(report: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in report.items() if k != "_features"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capability Twin Gherkin BDD 场景判定器（纯标准库）")
    parser.add_argument("command", choices=("validate", "uat", "steps", "matrix"))
    parser.add_argument("path", help=".feature 文件或目录")
    parser.add_argument("-o", "--output", help="输出路径（uat/steps 为目录，matrix 为 JSON 文件）")
    parser.add_argument("--allow-en", action="store_true",
                        help="迁移期：把英文关键字降级为 warning")
    parser.add_argument("--style", choices=("pytest-bdd", "behave"), default="pytest-bdd",
                        help="步骤桩风格，默认 pytest-bdd")
    parser.add_argument("--force", action="store_true",
                        help="即使 validate 失败也生成（仅供草稿期使用，CI 禁用）")
    parser.add_argument("--summary", action="store_true",
                        help="validate 时额外打印人类可读摘要到 stderr")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(json.dumps({"status": "error", "message": f"路径不存在：{_rel(target)}"},
                         ensure_ascii=False), file=sys.stderr)
        return 2

    report = validate(target, allow_en=args.allow_en)
    clean = _report(report)

    if args.command == "validate":
        print(json.dumps(clean, ensure_ascii=False, indent=2))
        if args.summary:
            print(f"[gherkin-gate] {report['status']} | features={report['features']} "
                  f"scenarios={report['scenarios']} steps={report['steps']} "
                  f"errors={report['errors']} warnings={report['warnings']}", file=sys.stderr)
        return 0 if report["status"] == "pass" else 1

    if report["status"] != "pass" and not args.force:
        print(json.dumps({
            "status": "blocked",
            "message": "规格校验未通过，拒绝派生交付物；修正 error 后重试（草稿可用 --force）",
            "errors": [i for i in clean["issues"] if i["severity"] == "error"],
        }, ensure_ascii=False, indent=2))
        return 1

    features: List[Feature] = report["_features"]
    if args.command == "uat":
        out = Path(args.output) if args.output else Path("capability_twin_runs/uat")
        written = generate_uat(features, out)
    elif args.command == "steps":
        out = Path(args.output) if args.output else Path("capability_twin_runs/steps")
        written = generate_steps(features, out, style=args.style)
    else:
        out = Path(args.output) if args.output else Path("capability_twin_runs/scenario_matrix.json")
        written = [generate_matrix(features, out)]

    print(json.dumps({
        "status": "success" if written else "empty",
        "command": args.command,
        "generated": written,
        "source_status": report["status"],
        "warnings": report["warnings"],
    }, ensure_ascii=False, indent=2))
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
