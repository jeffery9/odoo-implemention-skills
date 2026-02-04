import os
import shutil
from pathlib import Path

# 定义Capability Twin 3.0框架的核心组件
core_skills = {
    "autonomous-evolution",
    "cache-management",
    "configuration-management", 
    "context-memory-manager",
    "data-exchange",
    "enhanced-intent-understanding",
    "file-operations",
    "generic-analyzer",
    "intent-to-action-mapper",
    "intent-understanding",
    "json-canvas",
    "knowledge-manager",
    "obsidian-bases",
    "obsidian-markdown",
    "quality-gate",
    "relationship-analysis",
    "source-traceability",
    "template-processor",
    "planning-with-files",
    "workflow-engine"
}

core_agents = {
    "ecosystem-discovery-agent",
    "technical-analysis-agent",
    "function-analysis-agent",
    "domain-analysis-agent",
    "business-process-agent",
    "comprehensive-analysis-agent",
    "industry-requirements-agent",
    "solution-architect-agent",
    "implementation-guide-agent",
    "capability-extractor-agent",
    "delivery-packager-agent",
    "trustworthiness-auditor-agent",
    "human-review-gatekeeper-agent",
    "solution-builder-master"
}

core_orchestrators = {
    "capability-twin-orchestrator"
}

# 定义非核心组件（用户提到的markdown等）
non_core_components = {
    "obsidian-markdown",  # 这是用户提到的需要移除的组件
    # 其他非核心组件...
}

# 获取所有非核心组件
all_non_core = non_core_components

# 检查并移除非核心组件
ct_skills_dir = Path("/Users/jeffery/odoo19-study/CT/skills")
ct_agents_dir = Path("/Users/jeffery/odoo19-study/CT/agents")

print("检查并移除非核心组件...")

# 移除指定的非核心组件
for component in all_non_core:
    component_path = ct_skills_dir / component
    if component_path.exists():
        print(f"移除非核心组件: {component}")
        shutil.rmtree(component_path)
        print(f"已移除: {component}")
    else:
        print(f"组件不存在或已被移除: {component}")

print("非核心组件清理完成。")
