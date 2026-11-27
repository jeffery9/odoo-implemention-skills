# Capability Twin 3.5 Framework

> **文档分工 (Document Charter)**：本文件聚焦框架的**使用向**内容——
> 「框架是什么、怎么调用、怎么安装、怎么用」。仓库的**维护向**内容（改哪里、同步什么、
> 怎么验证、怎么发布）见 `docs/项目维护指南.md`；两类文档按职能分工，不重复正文。
> 内容按职能归位：使用说明写入本文件，维护流程写入维护指南。

> 读者定位：使用者只需读到本文件即可；维护者请先读本文件了解系统，再读 `docs/项目维护指南.md` 执行变更。

---

## 1. 框架概述 (Framework Overview)

**Capability Twin 3.5** 是一个专为 Odoo 19 本地化与合规性研究设计的、意图驱动的 **Odoo AI 软件工厂（AI Software Factory）** 核心引擎。它通过先进的 **Agentic Mesh（智能体网格）** 架构，将 18 个专业子智能体和 20 个原子技能有机结合，实现了从“源码挖掘（SCM/MRP/Financial）”到“业务 Gap 对标”再到“方案及代码自动交付”的全生命周期自动化。

准确的技能/智能体数量以能力注册表为准（`skills/capability-twin-orchestrator/capability_registry.json`，当前 20 skills / 18 agents）；本数字随注册表达成变化时更新，维护约束见 `docs/项目维护指南.md` §3。

---

## 2. 快速开始 (Quick Start)

### 2.1 环境准备
在启动框架之前，请确保正确设置了本地 Odoo 19 源码所在的物理路径，以便各智能体能够通过 `Grep` / `Glob` / `Read` 工具进行精确的底层白盒模式挖掘：
```bash
# 指向你自己的 Odoo 19 源码根目录（该目录下应包含 odoo/addons 或 addons）。
# 仓库不提供任何默认路径：未设置时白盒分析会显式报错，而不是猜一个"碰巧存在"的目录。
export ODOO_SOURCE_PATH="/path/to/odoo-19.0"
```

### 2.2 高并发多线程采矿（Continuous Mining）
可以通过启动 `scripts/mine_odoo_source.py` 开启 **Parallel Agentic Mesh（并行智能体网格）** 高速采矿。系统将自动分配多线程（默认 4 线程），采用 `threading.Lock` 线程锁，并发对 Odoo 核心模块的 `depends`、模型继承、视图树和 ORM 控制流进行高价值业务感知翻译：
```bash
# 执行语法: python3 scripts/mine_odoo_source.py [模块限制数量] [并发线程数]
# 示例: 并发 8 线程分析 15 个 Odoo 核心模块:
python3 scripts/mine_odoo_source.py 15 8
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

主控配置文件位于：`skills/capability-twin-orchestrator/scripts/config.py`（按技能容器相对定位，安装态下位于 `.claude/skills/...`）。
*   `registry_path`：能力注册表位置，默认仓内 `capability_registry.json`。
*   `output_directory`：运行时产物根目录，默认 `<工作区>/capability_twin_runs`。
*   `file_tracking_enabled` / `enable_backup_files`：文件追踪与备份开关。

Odoo 源码路径不写入配置，只读环境变量 `ODOO_SOURCE_PATH`；知识库位置由 `context-memory-manager` 决定（`<工作区>/kb/mem`）。

---

## 6. 角色化交付物体系（Deliverables Templates）

框架内置 16 份企业级交付模板（位于 `skills/template-processor/templates/deliverables/`），按角色分四类打包：

| `bundle_type` | 中文名 | 包含模板 |
|---|---|---|
| `strategy` | 战略包 | `PURPOSE_AND_STRATEGY`、`PROJECT_SOLUTION`、`STATEMENT_OF_WORK` |
| `consultant` | 顾问包 | `CONSULTANT_CONF_GUIDE`、`CONSULTANT_UAT_SCRIPT`、`CONSULTANT_DISCOVERY_NOTE`、`IMPLEMENTATION_METHODOLOGY` |
| `developer` | 研发技术包 | `CAPABILITY_ANALYSIS_REPORT`、`GAP_ANALYSIS_REPORT`、`SOLUTION_SPECIFICATION`、`CAPABILITY_UNIT_SPEC`、`SCENARIO_SOLUTION`、`FUNCTIONAL_DOC_SPEC` |
| `handover` | 资产移交包 | `HANDOVER_MANIFEST`、`EVOLUTION_GUIDE`、`BEST_PRACTICES_REPORT` |

```python
Skill("capability-twin-orchestrator", params={
    "operation": "render_deliverables_bundle",
    "bundle_type": "handover",          # strategy / consultant / developer / handover
    "context_data": {"project_name": "Odoo 19 Localized Chinese Accounting Project",
                     "target_module": "account"},
    "output_directory": None            # 缺省写入 capability_twin_runs/deliverables/<bundle>/
})
```

渲染结果以「文件是否真的生成」判定：返回 `rendered` / `failed` 两份清单与三态 `status`。
模板变量未替换时，`quality-gate` 的文档检查会判 `error`，避免半成品被当作成品交付。

---

## 7. 持续进化与知识记忆管理 (KB/Mem)

框架的记忆分三层，各自职责不同：

*   **会话内**：`context-memory-manager` 维护工作记忆与快照，写入 `kb/mem/`（JSONL）。
*   **跨会话事实**：`knowledge-manager` 与能力注册中心（`capability_registry.json`）保存能力单元与结论索引。
*   **能力演化**：`autonomous-evolution` 负责漂移检测与知识抽取，**仅生成候选知识并写入 `kb/`**；
    它不修改任何 `SKILL.md` 或 `AGENT.md` 指令文件——指令变更必须由人评审后合入。

> 说明：早期文档曾描述「自动更新 Agent 自身的 SKILL.md 补丁规则」，该能力并未实现，
> 也不计划实现：让运行时自动改写指令会破坏可审计性。

---

## 8. FDE 2.0 方法论对齐（摘要内置）

框架遵循 **FDE（Forward Deployed Engineering, 前沿部署工程）2.0** 的价值流、
证据与度量纪律；但 `6+3+4+N` 是引擎的研究与交付生命周期，**不是** FDE 价值流
七活动，两者不做一一绑定、不互相改名（2.0 §6.4）。

*   **能力单元**（执行检查清单）：`skills/fde-methodology/SKILL.md`
*   **边界裁定与刻意不做项**：`docs/FDE-2.0对齐说明.md`
*   **内置摘要**（`skills/fde-methodology/references/`）：[F] 基础标准 / [M] 详解 v1.3 /
    四册方法论 / 对齐先例，共 580 行、对应原文 5784 行（10.0%），带 `§x.y` 条款号锚点，
    即该能力单元的全部依据，离线可用、不依赖仓外文档。
*   **流水线检查点**：四条流水线（供给侧 6 / 需求侧 3 / 提取与 QA 4 / N 步客制化）在
    步骤 2、6、7、9、10、12、13 与 N 步第 4 步挂载该能力单元，按 §5 清单逐条记录
    「通过 / 不通过 / 不适用 + 依据」；不新增阶段、不改 `6+3+4+N` 编号，
    详见 `skills/capability-twin-orchestrator/references/workflows.md`。

---

## 9. 业务场景统一语言（Gherkin BDD）

业务场景、验收标准与 UAT 用例统一为 `zh-CN` Gherkin，规格位于
`skills/gherkin-bdd/features/<odoo_module>/*.feature`，是**唯一事实源**。
UAT 脚本、追溯矩阵与自动化步骤定义均由工具派生，交付模板不再复制场景正文。

| 能力 | 命令 / 入口 | 判据 |
|---|---|---|
| 规格门禁 | `python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate <features_dir>` | `error=0`，退出码 0 |
| UAT 派生 | `... uat <features_dir> -o capability_twin_runs/uat` | 与 `.feature` 同源 |
| 步骤桩 | `... steps <features_dir> -o capability_twin_runs/steps` | 未实现步骤显式失败 |
| 追溯矩阵 | `... matrix <features_dir> -o <json>` | 场景 ↔ 能力单元 ↔ 源码证据 |
| 质量门检查 | `quality-gate` 的 `check_type: scenario_spec` | 委托同一引擎，`error=0` 才通过 |

**流水线内执行**（不是文档约定，由编排器真实调用）：

| 位置 | 时机 | 行为 |
|---|---|---|
| `execute_workflow` preflight | Phase 1 之后、Phase 2 之前 | 校验本模块 `.feature`；`fail` 返回 `status=blocked`、`blocked_at`，不进入分析 |
| Step 10 → 11 | 能力单元抽取完成 | 生成 UAT / 步骤桩 / 矩阵，并通过 `config["bdd_artifacts"]` 交给打包；`fail` 立即中止 |
| `render_deliverables_bundle` | 交付包渲染前 | 场景变量由 `.feature` 派生，人工同名字段不得覆盖；未通过则跳过 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT` 并列入 `blocked_templates` |

- 入参：`{"bdd": {"enabled": true, "blocking": true, "features_dir": "...", "output_dir": "..."}}`
- **回落不算通过**：模块无规格时门禁回落全仓基线，`satisfies_module=false`，
  基线通过不能替该模块背书，也不允许渲染其场景类交付物。
- 统一语言词表：`skills/gherkin-bdd/references/ubiquitous-language.md`
- 编写规范与 20 条校验码：`skills/gherkin-bdd/references/authoring-rules.md`
- 工作流挂载点：`skills/capability-twin-orchestrator/references/workflows.md` 的
  “Business Scenario Contract” 一节（挂载，不新增阶段、不改 `6+3+4+N` 编号）
- 边界：自动化通过 = 工程完成（G2）；交付验收 ≠ 价值实现（FDE 2.0 §5.5）

本轮基线：2 个功能 / 5 个场景 / 21 个步骤，`errors=0`、`warnings=0`；能力单元自测 23/23 通过。
外部 runner（pytest-bdd / behave）未安装，L2 场景执行未计入通过项。

---

## 10. 安装与分发（npx skills）

本仓库遵循 Agent Skills 开放格式：20 个技能平铺于 `skills/<name>/SKILL.md`，
无需额外清单文件，`skills` CLI 可直接发现。

### 10.1 安装命令

```bash
# 整套安装（推荐）：20 个技能一次装齐，技能间依赖天然可解析
npx skills add <owner>/<repo> --all

# 装到用户级（跨项目可用）
npx skills add <owner>/<repo> --all -g

# 先浏览不安装
npx skills add <owner>/<repo> --list

# 文件系统不支持符号链接时（Windows / 部分 CI），改为复制
npx skills add <owner>/<repo> --all --copy
```

安装位置由 CLI 决定。以 Claude Code 为例，项目级安装会创建两份：

| 路径 | 作用 |
|---|---|
| `./skills/<name>/` | 规范副本（单一事实源） |
| `./.claude/skills/<name>/` | agent 实际加载的副本（symlink 或 `--copy`） |
| `./skills-lock.json` | 来源与内容哈希，用于 `npx skills update` 校验 |

`--global` 装到用户级 `~/.claude/skills/`；Cursor / Codex 等落到 `.agents/skills/`。
`npx skills ls` 可查看已装清单。

实测（`npx skills add <repo> --all --copy -a claude-code -y`，记录于新增 `odoo-implementation`
之前，故为 21 个技能）：CLI 报告 `Found 21 skills`，装完后 `./skills` 与 `.claude/skills`
各 21 份；当前技能数见 §1（20 个）。注意 `--all` 在该 CLI 中表示
**所有技能 × 所有已检测 agent**，会生成多个 agent 目录；只想装一个 agent 时用 `-a claude-code`。

### 10.2 必须整套安装的原因

框架内存在真实的技能间依赖，**只装单个框架技能会缺资源**：

| 依赖方 | 被依赖 | 用途 |
|---|---|---|
| `capability-twin-orchestrator` | `gherkin-bdd` | 加载规格门禁引擎与 `.feature` |
| `capability-twin-orchestrator` | `template-processor` | 渲染 16 份交付模板 |
| `capability-twin-orchestrator` | `quality-gate` | 质量门检查 |
| `intent-understanding` | `capability-twin-orchestrator` | 读取能力注册表与公共模块 |

缺依赖时不会静默降级，而是抛出 `SkillNotFound` 并给出补装命令：

```
框架依赖的技能 `gherkin-bdd` 未找到。技能容器为 `.../.claude/skills`，其中现有 1 个技能：...
修复：整套安装 `npx skills add <owner>/<repo> --all`，或单独补装 `... --skill gherkin-bdd`。
```

可独立单装的能力：`quality-gate`、`file-operations`、`data-exchange`、
`configuration-management`、`cache-management`、`knowledge-manager` 等。

### 10.3 运行前提

- **Python 3.9+**，仅用标准库；`pytest-bdd` / `behave` 只在执行场景时才需要。
- `ODOO_SOURCE_PATH`：Odoo 源码根目录，供白盒分析使用。
- `CAPABILITY_TWIN_WORKSPACE`（可选）：产出根目录，缺省为当前工作目录。

### 10.4 安装后自检

```bash
python3 <skills_root>/capability-twin-orchestrator/scripts/framework_paths.py
```

输出 `layout=install` 且 `templates_source=skill` 表示资源全部解析到技能包内部；
若 `templates_source=legacy`，说明仍在读历史仓库根布局，属异常。

### 10.5 路径与产物约定

| 类别 | 位置 |
|---|---|
| 技能资源（模板、`.feature`、`agents/`、注册表） | 技能包内部，随安装一起分发 |
| 运行时产物（`capability_twin_runs/`、`docs/`、`kb/`） | 用户工作区，**不写入技能目录** |

> 边界提醒：安装成功只代表工具可用，不代表任何业务场景已通过验收。
> 自动化通过 = 工程完成（G2）；交付验收 ≠ 价值实现（FDE 2.0 §5.5）。

> 安装布局守卫与路径解析实现约束属维护事项，见 `docs/项目维护指南.md` §2、§4.4；
> 仓库根下不随技能分发的历史维护脚本清单见同文件 §2"历史脚本"小节。

---
*Capability Twin 3.5 - 意图驱动的 Odoo 智能交付旗舰引擎*
