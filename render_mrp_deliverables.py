#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to render a complete set of role-based deliverables for the 'mrp' module.
Uses the high-fidelity insights mined from Odoo 19 source.
"""

import sys
import os
import json
from pathlib import Path

# Add framework paths（按本文件定位，避免硬编码某台机器的绝对路径）
_repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_repo_root / "skills" / "capability-twin-orchestrator" / "scripts"))

try:
    from main import execute_skill
except ImportError:
    print("Error: Could not import Orchestrator components.")
    sys.exit(1)

# High-fidelity Context Data for MRP
mrp_context = {
    "project_name": "Odoo 19 智能制造数字化工厂",
    "target_module": "mrp",
    "workflow_id": "cto_mrp_demo_20260204",
    "delivery_vision": "构建账实相符、成本实时、全链追溯的工业 4.0 制造底座。",
    "core_mission_statement": "通过 Odoo 19 数字化制造引擎，将生产黑盒透明化，保护企业每一分利润。",
    "business_situation": "目前生产成本核算滞后，原材料价格波动无法即时反馈，车间报工依赖手工纸单。",
    "efficiency_kpi": "报工自动化率",
    "efficiency_target": "> 90%",
    "finance_kpi": "成本核算误差",
    "finance_target": "< 1%",
    "ux_kpi": "单兵作业效率",
    "ux_target": "提升 40%",
    "core_modules": "mrp, stock, product, resource",
    "scenario_1_name": "原材料涨价下的动态毛利守护场景",
    "scenario_2_name": "车间三步法精细化物流接力场景",
    "module_positioning_human": "企业利润与质量的守护引擎",
    "value_1": "实时利润锁死：防原材料波动侵蚀毛利",
    "value_2": "扫码即报工：解放非生产性劳动力",
    "value_3": "全极速追溯：符合医药/精密电子合规要求",
    "what_happened_human": "由于原材料涨价，BOM 标准成本失真，导致订单表面盈利实际亏损。",
    "how_it_helps_human": "利用 manual_consumption 真实记录物理批次消耗价值，实时修正 WIP 价值。",
    "native_best_at": "多级嵌套 BOM 与副产品管理",
    "do_not_do_this_human": "禁止在未启用 Lot Tracking 的情况下进行回溯配置",
    "upgrade_compatibility_plain": "完全兼容 Odoo 19+ 官方升级路径",
    "setup_tip_1": "需在‘制造’设置中开启‘手动消耗’模式。",
    "step_1_desc": "创建生产订单并点下‘确认’",
    "step_1_expected": "系统自动预留原材料，且状态变为‘待处理’",
    "step_2_desc": "在移动端扫描原材料批次码",
    "step_2_expected": "系统自动填入实际消耗数量，实时重算成本",
    "user_intent": "设计一个能应对价格波动且支持全追溯的制造方案",
    "coverage_percentage": "95",
    "requirement_1": "原材料波动核算",
    "official_pattern_1": "Manual Consumption Pattern",
    "matching_details_1": "原生高度匹配，只需开启设置项。",
    "requirement_2": "批次追溯",
    "official_pattern_2": "Full Lot Traceability",
    "matching_details_2": "原生支持，需在产品层面配置。"
}

def render_all():
    print(f"Starting Deliverable Rendering for MRP...")
    
    # 1. Render Strategic Package
    execute_skill({
        "operation": "render_deliverables_bundle",
        "bundle_type": "strategic_docs",
        "context_data": mrp_context,
        "target_module": "mrp",  # Fix: Pass target_module at top level
        "workflow_id": mrp_context["workflow_id"]
    })
    
    # 2. Render Consultant Toolkit
    execute_skill({
        "operation": "render_deliverables_bundle",
        "bundle_type": "consultant_toolkit",
        "context_data": mrp_context,
        "target_module": "mrp",
        "workflow_id": mrp_context["workflow_id"]
    })
    
    # 3. Render Technical Docs
    execute_skill({
        "operation": "render_deliverables_bundle",
        "bundle_type": "technical_docs",
        "context_data": mrp_context,
        "target_module": "mrp",
        "workflow_id": mrp_context["workflow_id"]
    })

    print(f"All bundles rendered successfully to: Deliverables_Package/{mrp_context['workflow_id']}/")

if __name__ == "__main__":
    render_all()