# Capability Twin 3.0 Framework

## 框架概述
Capability Twin 3.0 是一个用于 Odoo 19 原生功能分析和实现差距识别的复杂分析框架。它通过 **Agentic Mesh** 架构，将 14 个专业 Agent 和 18 个原子技能组合，实现了从“源码挖掘”到“需求对标”再到“方案交付”的全自动化流水线。

## 快速开始

### 1. 环境准备
确保设置了 Odoo 19 的源码路径，以便框架能够进行模式挖掘：
```bash
export ODOO_SOURCE_PATH="/your/path/to/odoo-19.0"
```

### 2. 意图触发 (CLI)
直接在 Gemini CLI 中输入您的目标即可启动框架。例如：
- `analyze-module(sale)`：对销售模块执行完整的 6+3+4+N 分析。
- `gap-analysis(mrp, "支持敏捷制造排产")`：针对特定需求进行原生对标。

### 3. 查看进度与产出
框架会在执行时自动创建 `capability_twin_runs/` 目录，您可以实时查看：
- `task_plan.md`: 任务执行看板。
- `Complete_Solution/`: (位于项目根目录) 最终生成的解决方案。

## 目录结构
- agents/: 专用 Agent 定义 (6+3+4+N)
- skills/: 原子技能定义 (Intent OS, Knowledge, etc.)
- discover_capabilities.py: 自动化能力发现与注册工具

## 交付产出 (位于项目根目录)
- Complete_Solution/: 完整解决方案包
- Deliverables_Package/: 发布交付物包

