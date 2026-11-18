---
name: odoo-implementation
description: Odoo 实施能力的机器可读契约层——以可选 ct_ 前缀字段声明技能分层、模块归属、适用版本、场景引用与工作区产物，并提供零依赖校验。不改动 6+3+4+N 工作流、不替换现有技能契约、不新增物理目录层级。
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
version: 0.1.0
skills_used: [capability-twin-orchestrator, gherkin-bdd, quality-gate, template-processor]
ct_layer: core
ct_odoo_versions: ["17.0", "18.0", "19.0"]
ct_state_outputs: [project-state, artifact-index]
---

# Odoo Implementation — 实施能力契约层

## 1. 定位与边界

本技能包是 Capability Twin 的**增量扩展点**，不是平行框架。四项机制（机器契约、显式依赖、持久状态、fail-closed）在此只以可选字段与只读脚本落地。

| 硬约束 | 内容 |
|---|---|
| 不颠覆骨架 | 保留 `6+3+4+N` 编号、现有 21 个技能、现有 frontmatter 字段原义 |
| 字段可选 | 所有 `ct_` 字段可缺省；无 `ct_` 字段的技能一律判定为 `skipped`（非 error） |
| 不建物理层级 | `ct_layer` 仅作分类标签，不建立 `router/` `core/` `shared/` `module/` 目录 |
| 不内置执行器 | 本包不含 Odoo RPC 实现；外部操作统一由既有门禁与项目侧适配层负责 |
| 事实源复用 | 业务场景仍以 `gherkin-bdd` 的 `.feature` 为唯一事实源，本包只引用路径 |
| 价值边界 | 契约校验通过 = 工程一致（G2 辅助）；不等于业务验收（G3），更不等于价值实现 |

## 2. 目录契约

```text
skills/odoo-implementation/
├── SKILL.md                              # 本文件（含完整 ct_ 字段示例）
├── schemas/odoo-implementation.schema.json  # 机器契约，additionalProperties: false
├── references/contract-guide.md          # 字段语义与迁移指引
├── references/error-taxonomy.md          # 失败分类（10 类）
├── references/evidence-levels.md         # 证据分级与 G2/G3/FDE 边界
├── scripts/validate_odoo_manifest.py     # 零依赖校验（validate / list）
├── templates/project/project-state.template.json
├── templates/project/artifact-index.template.json
└── tests/test_validate_odoo_manifest.py  # 自测（正负例 + 变异验证）
```

整包位于 `skills/` 下，`npx skills add --all` 安装后 schema、脚本、模板均可达。停用只需移除本目录并撤掉两处可选钩子，流水线原样工作。

## 3. 契约字段（全部可选，ct_ 前缀）

| 字段 | 类型 | 约束 | 缺省行为 |
|---|---|---|---|
| `ct_layer` | enum | `router` / `core` / `shared` / `module` | 不校验层级专属字段 |
| `ct_module` | string | 小写字母开头，`[a-z0-9_]*`；仅 `ct_layer=module` 允许 | 不声明模块归属 |
| `ct_odoo_versions` | array[string] | 大版本形如 `17.0`；非空 | 不声明版本约束 |
| `ct_scenario_refs` | array[string] | 指向 `.feature` 路径或 `@ct-id`，非空 | 不声明场景引用 |
| `ct_state_outputs` | array[string] | 项目工作区产物类型，非空 | 不声明状态写入 |

`if/then` 领域规则：`ct_module` 只在 `ct_layer=module` 时允许；非 module 层携带 `ct_module` 判为契约错误。这条规则前移到 schema 与校验脚本，不靠文档自觉。

## 4. CLI

```bash
# 校验单个技能的 frontmatter（含 ct_ 字段）
python3 skills/odoo-implementation/scripts/validate_odoo_manifest.py \
  skills/odoo-implementation/SKILL.md

# 批量校验整个 skills 容器：既有技能 skipped，契约技能 validated
python3 skills/odoo-implementation/scripts/validate_odoo_manifest.py skills/

# 仅列出带 ct_ 字段的技能，不做判定
python3 skills/odoo-implementation/scripts/validate_odoo_manifest.py skills/ --list
```

退出码：`0` = 无 error（允许 skipped）；`1` = 存在契约 error；`2` = 工具/入参错误（路径不存在、JSON 损坏）。报告为 JSON 输出，字段与 `gherkin_gate.py` 对齐：`status` / `issues[{severity,code,file,line,message}]`。

## 5. 与流水线的关系

本包在两处既有挂载点追加**可选分支**，默认关闭，开启后不改变返回结构：

| 挂载点 | 追加动作 | 开关 |
|---|---|---|
| `_bdd_preflight`（main.py） | 追加 `odoo_contract` 只读校验结果字段 | `params["odoo_contract"]["enabled"]` |
| `render_deliverables_bundle`（main.py） | 门禁通过时登记契约校验摘要 | 同上 |

不新增阶段、不改 `operation` 名称、不改交付模板文件名。

## 6. 反模式

- 给既有技能强行补 `ct_` 字段以「通过校验」——缺省本就是合法状态，无字段应判 `skipped`。
- 把 `ct_layer` 落成物理目录——与 `npx skills` 的 `<容器>/<技能>/SKILL.md` 平铺要求冲突。
- 在 `.feature` 或契约字段里写模型名、字段名、RPC 方法等实现术语。
- 用契约校验通过替代场景门禁或业务验收。
