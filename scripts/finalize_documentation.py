#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys, glob
from pathlib import Path

def find_root():
    """定位框架仓库根：以 scripts/ 与 skills/ 两个必备目录同时存在为锚。

    早期版本依赖已不存在的 GEMINI.md，且以 CWD 为起点会随调用目录漂移；
    现按本文件所在位置向上查找，避免 worktree / 改名后错位。
    """
    for parent in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
        if (parent / 'scripts').is_dir() and (parent / 'skills').is_dir():
            return parent
    return Path(__file__).resolve().parent.parent

def main():
    if len(sys.argv) < 2: return
    target_module = sys.argv[1]
    root = find_root()
    
    snapshot_dir = root / "kb/mem/snapshots"
    snapshots = glob.glob(str(snapshot_dir / "*.jsonl"))
    if not snapshots:
        print("Error: No snapshots found.")
        return
    latest_snapshot = max(snapshots, key=os.path.getmtime)
    print(f"Finalizing documentation using snapshot: {os.path.basename(latest_snapshot)}")
    
    with open(latest_snapshot, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 提取 LLM 产出的深度分析结果 (从 Comprehensive Analysis 或 Capability Extraction 中提取)
    comp_res = {}
    for step in data.get("results", []):
        if step.get("name") in ["Comprehensive Analysis", "Capability Extraction"]:
            res = step.get("result", {})
            # 如果 Agent 返回了实际的分析内容，则累加
            if isinstance(res, dict):
                comp_res.update(res)

    # 2. 构造全量功能表格 (Level-2/3)
    # 我们优先使用 LLM 产出的 capability_tree，如果没有，则尝试从 AST evidence 中生成
    capability_tree = comp_res.get("capability_tree", {})
    
    if not capability_tree:
        # 后备逻辑：从 Technical Analysis 的 AST 证据中提取所有类名作为功能点
        for step in data.get("results", []):
            if step.get("name") == "Technical Analysis":
                evidence = step.get("result", {}).get("evidence_bundle", {}).get("ecosystem_structure", {})
                for mod, files in evidence.items():
                    category = f"Module: {mod}"
                    capability_tree[category] = []
                    for f in files:
                        for cls in f.get("ast", {}).get("classes", []):
                            if cls.get("odoo_name"):
                                capability_tree[category].append({
                                    "sub": cls["odoo_name"],
                                    "desc": f"Technical model implementation in {f['file']}.",
                                    "flow": "Logistics/Value",
                                    "diff": "AST Probed Native"
                                })

    # 构造 Markdown 表格
    table_rows = "| Category (L1) | Logic Unit (L2) | Business Context & Mechanics | Flow | V19 Innovation |\n| :--- | :--- | :--- | :--- | :--- |\n"
    for category, units in capability_tree.items():
        if not units: continue
        first = True
        for unit in units:
            cat_display = f"**{category}**" if first else '"'
            table_rows += f"| {cat_display} | {unit.get('sub', 'N/A')} | {unit.get('desc', 'N/A')} | {unit.get('flow', 'N/A')} | {unit.get('diff', 'N/A')} |\n"
            first = False

    # 3. 构造 How-To 库
    how_tos = comp_res.get("how_tos", [])
    how_to_markdown = ""
    if how_tos:
        for i, ht in enumerate(how_tos, 1):
            how_to_markdown += f"### 5.{i} {ht.get('title', 'Operational Guide')}\n"
            how_to_markdown += f"- **Setup**: {ht.get('setup', 'N/A')}\n"
            how_to_markdown += f"- **Action**: {ht.get('action', 'N/A')}\n"
            how_to_markdown += f"- **Logic**: {ht.get('logic', 'N/A')}\n"
            how_to_markdown += f"- **Verification**: {ht.get('verification', 'N/A')}\n\n"
    else:
        how_to_markdown = comp_res.get("operational_how_to", "Pending detailed analysis...")

    # 4. 最终 Mapping 填充
    mapping = {
        "{MODULE_NAME}": target_module.upper(),
        "{WORKFLOW_ID}": data.get("workflow_id", "N/A"),
        "{SITUATION_OVERVIEW}": comp_res.get("situation", "Odoo 19 implementation context."),
        "{BUSINESS_PAIN_POINTS}": comp_res.get("complication", "Legacy bottlenecks and synchronization gaps."),
        "{CORE_VALUE_PROPOSITION}": comp_res.get("answer", "3-Flows atomic synchronization."),
        "{FUNCTIONAL_MAP_TABLE}": table_rows,
        "{INF_FLOW_TRIGGERS}": comp_res.get("flows", {}).get("information", "Status updates and scans."),
        "{INF_FLOW_INSIGHTS}": "Derived from AST model metadata.",
        "{LOG_FLOW_STATES}": comp_res.get("flows", {}).get("logistics", "Physical move states."),
        "{LOG_FLOW_TRACE}": "Traceability DNA via SVL.",
        "{VAL_FLOW_IMPACT}": comp_res.get("flows", {}).get("value", "Ledger realization."),
        "{VAL_FLOW_SYNC}": "Precomputed balance reconciliation.",
        "{PERMISSION_MATRIX}": comp_res.get("permissions", "Standard Odoo RBAC."),
        "{OPERATIONAL_HOW_TO}": how_to_markdown,
        "{SCENARIOS}": comp_res.get("scenarios", "Industrial use cases."),
        "{PITFALLS}": comp_res.get("pitfalls", "Common configuration errors.")
    }

    # 模板随 template-processor 技能分发（仓库布局与安装布局通用）
    candidates = [
        root / "skills/template-processor/templates/deliverables/STRATEGIC_FUNCTIONAL_SPEC_V6.md",
        root / ".claude/skills/template-processor/templates/deliverables/STRATEGIC_FUNCTIONAL_SPEC_V6.md",
        root / "templates/deliverables/STRATEGIC_FUNCTIONAL_SPEC_V6.md",   # 历史布局
    ]
    template_path = next((p for p in candidates if p.is_file()), None)
    if template_path is None:
        raise SystemExit(
            "未找到 STRATEGIC_FUNCTIONAL_SPEC_V6.md；"
            "请确认 template-processor 技能已就位（skills/template-processor/templates/deliverables）。"
        )
    template = template_path.read_text(encoding='utf-8')
    for k, v in mapping.items():
        template = template.replace(k, str(v))

    output_path = root / f"docs/functional/{target_module}_v19_functional.md"
    output_path.write_text(template, encoding='utf-8')
    print(f"🏆 DYNAMIC SPEC GENERATED: {output_path} ({len(table_rows.splitlines())} units found)")

if __name__ == "__main__":
    main()
