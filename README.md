# Capability Twin 3.0 Framework (Master Reference & Guide)

> **最高指导原则 (Master Mandate)**：只维护唯一一份官方、完备的 `CAPABILITY_TWIN` 框架技术指南，彻底消灭零碎、散乱、重合的历史副本文档。

---

## 1. 框架概述 (Framework Overview)

**Capability Twin 3.0** 是一个专为 Odoo 19 本地化与合规性研究设计的、意图驱动的 **Odoo AI 软件工厂（AI Software Factory）** 核心引擎。它通过先进的 **Agentic Mesh（智能体网格）** 架构，将 13 个专业子智能体和原子技能池有机结合，实现了从“源码挖掘（SCM/MRP/Financial）”到“业务 Gap 对标”再到“方案及代码自动交付”的全生命周期自动化。

---

## 2. 快速开始 (Quick Start)

### 2.1 环境准备
在启动框架之前，请确保正确设置了本地 Odoo 19 源码所在的物理路径，以便各智能体能够通过 `Grep` / `Glob` / `Read` 工具进行精确的底层白盒模式挖掘：
```bash
export ODOO_SOURCE_PATH="/Users/jeffery/_project/topdon/EUx/odoo-19.0"
```

### 2.2 自动盘点与能力注册
当新增或重构了智能体（`agents/` 目录）或原子技能（`skills/` 目录）时，必须执行自动能力盘点脚本，以重建统一 能力孪生注册中心（`capability_registry.json`）：
```bash
python3 CAPABILITY_TWIN/discover_capabilities.py
```

### 2.3 高并发多线程采矿（Continuous Mining）
可以通过启动 `mine_odoo_source.py` 开启 **Parallel Agentic Mesh（并行智能体网格）** 高速采矿。系统将自动分配多线程（默认 4 线程），采用 `threading.Lock` 线程锁，并发对 Odoo 核心模块的 `depends`、模型继承、视图树和 ORM 控制流进行高价值业务感知翻译：
```bash
# 执行语法: python3 CAPABILITY_TWIN/mine_odoo_source.py [模块限制数量] [并发线程数]
# 示例: 并发 8 线程分析 15 个 Odoo 核心模块:
python3 CAPABILITY_TWIN/mine_odoo_source.py 15 8
```

---

## 3. 核心运行逻辑与标准化 6+3+4+N 工作流

框架的全局脑控入口是 `capability-twin-orchestrator`（智能体主编排器），在底层严格遵循极其严密的生命周期闭环：

*   **6 步供给侧研究 (Supply-Side Study)**：彻底查明 Odoo 原生代码能力，拒绝 Speculative 重写。
*   **3 步需求侧对齐 (Demand-Side Study)**：深入分析行业合规 GAP（如 CAS 暂估/发出商品、两级分配）。
*   **4 步提取与交付 (Extraction & Delivery)**：自动化提取复用能力单元（Capability Units），并交付 PR 包与可信审计证据。
*   **N 步敏捷客制化循环 (Customization Iteration)**：通过 Surgical Modification (SMP) 进行像素级、零污染的代码注入。

---

## 4. 意图调度与常用操作命令 (CLI Commands)

### 4.1 完整模块分析 (Full Analysis)
对 Odoo 特定原生模块（如 `stock_account`）执行全量扫描和逆向业务功能树（Capability Tree）翻译：
```python
Skill("capability-twin-orchestrator", params={
    "target_module": "stock_account",
    "workflow_type": "full_analysis"
})
```

### 4.2 业务 Gap 深度对标 (Gap Analysis)
将具体的自然语言业务需求与 Odoo 原生框架进行两阶段语义 Gap 对标，产生零幻觉、带物理代码行号（Traceability）的合规对标解决方案：
```python
Skill("capability-twin-orchestrator", params={
    "target_module": "account",
    "workflow_type": "gap_analysis",
    "user_input": "需要实现符合中国财务规范的‘发出商品（Shipped but not invoiced）’与主营业务成本的严格配比核算"
})
```

---

## 5. 关键配置说明 (config.py)

主控配置文件位于：`CAPABILITY_TWIN/skills/capability-twin-orchestrator/scripts/config.py`。
*   `odoo_source_path`：Odoo 19 源码在本地的物理绝对路径（优先读取环境变量 `ODOO_SOURCE_PATH`）。
*   `knowledge_base_path`：本地持久化知识库（KB）的存放根目录。
*   `output_directory`：分析、渲染及交付物汇总任务的临时输出目录。

---

## 6. 角色化交付物体系（Deliverables Templates）

框架内置了 10+ 种符合企业级标准的标准化文档与交付包模板（位于 `CAPABILITY_TWIN/templates/deliverables/`），提供一键打包：

```python
Skill("capability-twin-orchestrator", params={
    "operation": "render_deliverables_bundle",
    "bundle_type": "handover_package", # 战略包、顾问包、研发技术包、资产移交包
    "context_data": {"project_name": "Odoo 19 Localized Chinese Accounting Project"}
})
```

---

## 7. 持续进化与知识记忆管理 (KB/Mem)

大网格采用 `JSONL` 与本地向量碎片格式管理长期记忆。通过自主进化引擎，每次运行所沉淀出的新 API、废弃警告或业务模式，会自动回写到长期事实中，并在遇到接口变动 warning 时自动启动“自愈修补”（Self-Healing Loop），更新 Agent 自生的 `SKILL.md` 补丁规则（Supplement Rule），让大网格的心智时刻与 Odoo 版本的升级节奏保持神级同步。

---
*Capability Twin 3.5 - 意图驱动的 Odoo 智能交付旗舰引擎 | 唯一官方技术手册*
