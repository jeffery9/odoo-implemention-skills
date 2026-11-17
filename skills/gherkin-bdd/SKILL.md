---
name: gherkin-bdd
description: Gherkin BDD 业务场景统一语言能力单元——将 Capability Twin 的业务场景、验收标准与 UAT 用例统一为 zh-CN Gherkin 可执行规格，并提供解析、静态校验、UAT 生成、步骤桩生成与 CI 门槛判定。用于需求对齐、能力单元提取、交付包验收与自动化测试接入。
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
version: 1.0.0
skills_used: [quality-gate, template-processor, source-traceability, fde-methodology]
---

# Gherkin BDD — 业务场景统一语言

## 1. 定位与硬约束

**`.feature` 文件是业务场景的唯一事实源（Single Source of Truth）。**
业务人员、顾问、方案架构师、测试工程师使用同一份文本；交付文档、UAT 脚本、自动化测试用例全部由它派生，不允许再各自维护一份自然语言副本。

| 约束 | 内容 |
|---|---|
| 描述语言 | Gherkin，`# language: zh-CN`，关键字与术语以 §2、[统一语言词表](references/ubiquitous-language.md) 为准 |
| 事实源唯一 | 场景、前置条件、业务动作、期望结果只写在 `.feature`；其他交付物引用路径，不复制正文 |
| 不新增阶段 | 作为**挂载点**附加在既有 `6+3+4+N` 步骤上，不新增阶段、不改步骤编号（见 [workflows.md](../capability-twin-orchestrator/references/workflows.md)） |
| 不内置执行器 | 本能力单元只做解析、校验与生成；`pytest-bdd` / `behave` 是可选适配层，由项目自行安装并运行 |
| 不假绿 | 未实现的步骤桩必须显式抛错；校验失败返回非零退出码；不把「文件已生成」当成「测试已通过」 |
| 价值边界 | 自动化场景通过 = 工程完成（G2）；**不等于**业务验收（G3），更不等于价值实现（FDE 2.0 §5.5） |

## 2. 统一语言的两层含义

1. **语法层（Dialect）**：统一使用 `zh-CN` 关键字，避免同一仓库内中英文步骤混写。
   `功能 / 规则 / 背景 / 场景 / 场景大纲 / 例子 / 假如 / 当 / 那么 / 而且 / 但是`。
   详细规则见 [编写规范](references/authoring-rules.md) §1。
2. **语义层（Ubiquitous Language）**：业务术语只有一种写法，且与 Odoo 业务对象一一映射。
   场景文本中**禁止出现技术黑话**（模型名、字段名、ORM 方法、菜单 XML ID、CSS 选择器）。
   词表见 [统一语言词表](references/ubiquitous-language.md)；映射关系放在词表，不散落在场景里。

## 3. 目录契约

```
skills/gherkin-bdd/
├── SKILL.md                         # 本文件：能力契约
├── references/
│   ├── ubiquitous-language.md       # 术语表（业务词 ↔ Odoo 业务对象）
│   └── authoring-rules.md           # 编写规范、标签体系、反模式
├── features/<odoo_module>/*.feature # 业务场景唯一事实源
├── steps/README.md                  # 步骤定义接入说明（生成产物落在 capability_twin_runs/，不入库）
├── scripts/gherkin_gate.py          # 解析 / 校验 / 生成 / 报告（纯标准库）
├── tests/test_gherkin_gate.py       # 本能力单元自测
├── README.md
└── INTEGRATION_GUIDE.md             # 工作流挂载、质量门与 CI 接入
```

项目侧的场景文件按 `features/<odoo_module>/<domain>.feature` 组织；模块名必须与 Odoo 原生模块名一致，便于源码追溯。

## 4. 标签与可追溯性

每个 `场景` / `场景大纲` 必须携带下列标签，缺一即为 `error`：

| 标签 | 含义 | 示例 |
|---|---|---|
| `@ct-id` | 场景唯一编号，全局不重复 | `@ct-id=SCN-ACC-001` |
| `@ct-unit` | 关联能力单元 | `@ct-unit=CU-ACC-014` |
| `@ct-module` | Odoo 模块 | `@ct-module=account` |
| `@ct-gate` | 质量门归属 | `@ct-gate=G2` / `G3` |

可选：`@ct-source`（源码证据相对路径，`:` 代替 `#` 行号分隔符）、`@ct-priority`、`@ct-risk`。
标签值允许 `[A-Za-z0-9._=/:-]`，禁止空格与 `#`（`#` 会被 Gherkin 当作注释起始）。

## 5. 自动化链路

```
.features（人写，业务语言）
   │
   ├─ validate  → 结构/术语/标签/占位符校验 → JSON 报告 + 退出码（CI 门槛）
   ├─ matrix    → 场景追溯矩阵（id → 文件:行号 → unit/module/gate）
   ├─ uat       → CONSULTANT_UAT_SCRIPT.md 表格（人工验收用，保留签字栏）
   ├─ steps     → pytest-bdd 步骤定义桩（未实现即显式失败）
   └─ 外部 runner（可选）→ pytest-bdd / behave 执行，结果回写 G2 证据
```

CLI：

```bash
python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate skills/gherkin-bdd/features
python3 skills/gherkin-bdd/scripts/gherkin_gate.py uat      skills/gherkin-bdd/features -o capability_twin_runs/uat
python3 skills/gherkin-bdd/scripts/gherkin_gate.py steps    skills/gherkin-bdd/features -o capability_twin_runs/steps
python3 skills/gherkin-bdd/scripts/gherkin_gate.py matrix   skills/gherkin-bdd/features -o capability_twin_runs/scenario_matrix.json
```

`validate` 的输出契约：

```json
{
  "status": "pass | fail",
  "features": 2,
  "scenarios": 5,
  "steps": 23,
  "issues": [{"severity": "error|warning", "code": "BDD-xxx", "file": "...", "line": 12, "message": "..."}],
  "scenario_index": [{"id": "SCN-ACC-001", "file": "...", "line": 9, "unit": "CU-ACC-014", "module": "account", "gate": "G2"}]
}
```

退出码：`0` = pass（允许 warning）；`1` = fail（存在 error）；`2` = 工具/入参错误。判定只看是否存在 `error`，不设加权分数、不设成熟度等级（与 `fde-methodology` §6 一致）。

## 6. 流水线挂载点（不新增阶段）

门禁由编排器在下列位置**真实调用**（`skills/capability-twin-orchestrator/scripts/bdd_gate.py`），
不是文档约定：

| 既有步骤 | 挂载动作 | 产物 |
|---|---|---|
| Phase 1 → 2 | `_bdd_preflight`：`fail` 直接阻断整条流水线 | `blocked_at` / `gate` 字段 |
| 8 方案架构 / 9 实施指南 | 用 Gherkin 写出目标业务场景，作为方案验收条件 | `.feature` 初稿 |
| 10 能力单元提取 | 为场景补 `@ct-unit`，与能力单元建立 1:N 绑定 | `CAPABILITY_UNIT_SPEC` 引用路径 |
| 10 → 11 | `_bdd_gate_stage("G2", derive=True)`：校验并派生，`fail` 立即中止 | UAT、步骤桩、场景矩阵 |
| 11 交付打包 | 消费 `config["bdd_artifacts"]`，不得复制场景正文 | 交付包引用派生件 |
| 12 可信性审计 | 跑 `validate`；检查 `@ct-source` 证据可达 | gate JSON 报告 |
| 13 人工复核 | 业务方按 UAT 签字；G3 由人裁定 | 验收记录 |
| 交付包渲染 | 场景变量由规格派生；未通过则跳过场景类模板 | `blocked_templates` |
| N 步客制化 第 4 步 | 注册前复核规格仍成立；外部 runner 执行场景，未实现步骤显式失败 | `blocked_at` / G2 自动化证据 |

## 7. 输出契约与反模式

必须做到：
- 场景一动作一断言；`那么` 描述**可观察的业务结果**，不是「系统正常工作」。
- `场景大纲` 的 `<占位符>` 与 `例子` 表头严格闭合；数据表用于业务数据，不用于技术参数。
- 每个场景可独立运行：前置条件写在 `背景` 或 `假如`，数据由 fixture 隔离，不依赖执行顺序。

禁止：
- 在 `.feature` 中写模型名、字段名、方法名、`ir.*` / `res.*` 等实现术语；
- 在 UAT 脚本里手工另写一套步骤（必须由 gate 生成）；
- 用 `And` 堆叠多个业务动作掩盖场景边界；
- 把「UAT 已生成」或「步骤桩已生成」报告为「自动化测试已通过」；
- 运行时自动改写本 `SKILL.md`（指令变更必须由人评审后合入）。

## 8. 快速示例

```gherkin
# language: zh-CN
@ct-module=account
功能: 发出商品的收入与成本配比
  作为 财务负责人
  我希望 发货未开票时收入暂不确认、成本随发出商品归集
  以便 符合中国企业会计准则的配比要求

  @ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G2
  场景: 发货未开票时确认发出商品
    假如 销售订单「SO-001」已确认，商品「A」的可用量为 10 件
    当 仓库按销售订单发货，发出商品「A」10 件且尚未开票
    那么 该批商品计入「发出商品」10 件
    而且 当期主营业务收入不含该批商品金额 1200 元
```

完整示例见 [features/account/shipped_not_invoiced.feature](features/account/shipped_not_invoiced.feature) 与 [features/mrp/mo_completion_posting.feature](features/mrp/mo_completion_posting.feature)。
