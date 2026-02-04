# Capability Twin 3.0 技术使用手册

本手册详细介绍了如何运行、配置和扩展 Capability Twin 3.0 框架。

## 1. 核心运行逻辑 (Orchestrator)

框架的入口是 `capability-twin-orchestrator` 技能。它遵循 **6+3+4+N** 标准化流程：

- **6步供给侧 (Supply-Side)**: 挖掘 Odoo 19 源码，识别原生能力。
- **3步需求侧 (Demand-Side)**: 分析客户业务需求。
- **3.5步 Gap 对标**: 双向语义匹配，识别功能缺口。
- **4步萃取与 QA**: 知识沉淀与可信度审计。

## 2. 常用操作命令

### 2.1 完整模块分析 (Full Analysis)
对特定模块执行全量扫描和知识沉淀：
```python
Skill("capability-twin-orchestrator", params={
    "target_module": "stock",
    "workflow_type": "full_analysis"
})
```

### 2.2 业务 Gap 对标 (Gap Analysis)
将特定客户需求与 Odoo 原生功能进行对标：
```python
Skill("capability-twin-orchestrator", params={
    "target_module": "account",
    "workflow_type": "gap_analysis",
    "user_input": "需要实现符合中国财务规范的‘四柱清册’报表"
})
```

## 3. 关键配置项 (config.py)

配置文件位于 `skills/capability-twin-orchestrator/scripts/config.py`。您可以修改以下项：

- `odoo_source_path`: Odoo 19 源码所在的物理路径。
- `knowledge_base_path`: 知识库（KB）的持久化目录。
- `output_directory`: 运行时的临时任务目录。

## 4. 扩展框架 (Add new Agent/Skill)

1. **创建目录**: 在 `agents/` 或 `skills/` 下新建文件夹。
2. **编写指令**: 至少包含一个 `AGENT.md` (针对代理) 或 `SKILL.md` (针对技能)。
3. **注册能力**: 运行发现脚本：
   ```bash
   python3 CAPABILITY_TWIN/discover_capabilities.py
   ```

## 5. 交付物模板体系 (Templates)

框架内置了 10+ 种标准化文档模板，位于 `CAPABILITY_TWIN/templates/deliverables/`。

### 5.1 渲染示例
通过 `template-processor` 技能一键生成顾问或研发文档：
```python
Skill("template-processor", params={
    "operation": "render_deliverable",
    "template_name": "CONSULTANT_CONF_GUIDE",
    "context_data": {
        "scenario_name": "多级批次追溯",
        "setup_tip_1": "请确保在‘库存’设置中开启‘多级批次’开关。"
    }
})
```

### 5.2 角色化交付包
- **战略包 (strategic_docs)**: 定义商业使命与 ROI。
- **顾问包 (consultant_toolkit)**: 包含配置手册与 UAT 脚本。
- **技术包 (technical_docs)**: 包含源码挖掘与 Gap 报告。
- **移交包 (handover_package)**: 包含资产清单与演化指南。

一键生成示例：
```python
Skill("capability-twin-orchestrator", params={
    "operation": "render_deliverables_bundle",
    "bundle_type": "handover_package",
    "context_data": {"project_name": "My Odoo Project"}
})
```

## 6. 知识资产管理 (KB/Mem)

遵循 OpenClaw 实践，框架使用 `JSONL` 格式存储记忆。

### 6.1 物理结构
- `kb/mem/long_term_facts.jsonl`: 跨项目的 Odoo 19 技术事实。
- `kb/mem/usage_patterns.jsonl`: 验证过的官方业务模式。
- `kb/mem/snapshots/`: 每次运行的完整上下文快照。

### 6.2 资产维护
系统具备“自主演化”能力。通过运行 `mine_odoo_source.py`，您可以让工厂持续采矿，确保您的知识资产始终与 Odoo 19 官方代码同步。

## 7. 常见问题 (FAQ)

- **Q: 为什么分析结果是 Mock 数据？**
  - A: 请检查 `capability_registry.py` 是否已重构为真实调度模式，并确保 Agent 目录下存在对应的指令文件。
- **Q: 源码挖掘报错？**
  - A: 确保 `ODOO_SOURCE_PATH` 环境变量已正确设置，且当前 Agent 具有 `Grep` 和 `Glob` 工具权限。

---
*Capability Twin 3.0 - 实现“意图即交付”的 Odoo 交付引擎*
