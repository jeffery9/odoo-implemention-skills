---
name: odoo-implementation
description: Odoo 实施能力的机器可读契约层——以可选 ct_ 前缀字段声明技能分层、模块归属、适用版本、场景引用与工作区产物，并提供零依赖校验。不改动 6+3+4+N 工作流、不替换现有技能契约、不新增物理目录层级。
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
version: 0.4.0
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
| 执行单一出口 | 初始化动作可通过 Odoo RPC 或 Odoo shell 执行，但必须收敛到 `scripts/odoo_seed_executor.py` 一个出口；禁止在能力定义或技能中散落调用 |
| 事实源复用 | 业务场景仍以 `gherkin-bdd` 的 `.feature` 为唯一事实源，本包只引用路径 |
| 价值边界 | 契约校验通过 = 工程一致（G2 辅助）；不等于业务验收（G3），更不等于价值实现 |
| 维护规范 | 文件职责、变更流程、发布清单与禁止事项见 `MAINTENANCE.md`；本文件为技能入口，不替代维护规范 |
| 能力缺口 | 尚缺能力与下一步排期见 `TODO.md`（backlog）；本文件只声明已落地能力，不预告未完成项 |

## 2. 目录契约

```text
skills/odoo-implementation/
├── SKILL.md                              # 本文件（含完整 ct_ 字段示例）
├── MAINTENANCE.md                        # 维护规范（文件职责、变更流程、发布清单、禁止事项）
├── TODO.md                               # 能力缺口 backlog（现状快照、分级缺口、已否决项、维护规则）
├── schemas/odoo-implementation.schema.json  # 机器契约，additionalProperties: false
├── references/contract-guide.md          # 字段语义与迁移指引
├── references/error-taxonomy.md          # 失败分类（10 类）
├── references/evidence-levels.md         # 证据分级与 G2/G3/FDE 边界
├── references/version-compatibility.md   # 17/18/19 初始化差异（通道矩阵、UoM 硬差异）
├── scripts/validate_odoo_manifest.py     # 零依赖校验（validate / list）
├── scripts/odoo_seed_executor.py         # 种子动作单一执行出口（RPC / JSON-2 / shell，版本感知，默认 dry-run）
├── templates/project/project-state.template.json
├── templates/project/artifact-index.template.json
├── templates/project/seed-actions.template.json   # 种子动作计划（项目侧填充）
├── templates/project/base-data-actions.template.json  # 基础数据初始化动作计划（计量单位/币种/汇率/国家/语言）
├── tests/test_validate_odoo_manifest.py  # 自测（正负例 + 变异验证）
└── tests/test_odoo_seed_executor.py      # 执行器自测（全离线，注入假通道）
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

种子动作执行（仅在项目侧明确要求初始化且已备好动作计划时调用）。**初始化方式随 Odoo 版本变化，必须显式指定目标版本**，差异见 `references/version-compatibility.md`：

```bash
# Odoo 17/18：XML-RPC，默认 dry-run，不连 Odoo、不产生写操作
python3 skills/odoo-implementation/scripts/odoo_seed_executor.py \
  --odoo-version 18.0 --channel rpc --plan project/base-data-actions.json

# Odoo 19：JSON-2 + API key；--apply 才真实执行，缺凭据即 CT-006 blocked
ODOO_URL=... ODOO_DB=... ODOO_API_KEY=... \
python3 skills/odoo-implementation/scripts/odoo_seed_executor.py \
  --odoo-version 19.0 --channel json2 --plan project/base-data-actions.json --apply

# 跨版本通用：odoo shell（shell_code 必须按目标版本模型/字段编写）
python3 skills/odoo-implementation/scripts/odoo_seed_executor.py \
  --odoo-version 18.0 --channel shell --plan project/seed-actions.json
```

通道矩阵：`rpc` 适用 17/18（19 可用但告警 deprecated）；`json2` 仅 19；`shell` 三版本通用。动作可用 `odoo_versions` 标注适用版本，执行器按 `--odoo-version` 过滤（不匹配跳过计入 `skipped_actions`）；含版本敏感动作却未指定版本 → `CT-003` error 零执行（fail-closed）。模板见 `templates/project/seed-actions.template.json` 与 `templates/project/base-data-actions.template.json`。执行器不内置业务动作；写操作必须带 `idempotency_key`（缺失判 `CT-007 blocked`），且不自动重试。退出码：`0` = 无阻断；`1` = error/blocked；`2` = 工具/入参错误。

## 5. 与流水线的关系

本包在两处既有挂载点追加**可选分支**，默认关闭，开启后不改变返回结构：

| 挂载点 | 追加动作 | 开关 |
|---|---|---|
| `_bdd_preflight`（main.py） | 追加 `odoo_contract` 只读校验结果字段 | `params["odoo_contract"]["enabled"]` |
| `render_deliverables_bundle`（main.py） | 门禁通过时登记契约校验摘要 | 同上 |

不新增阶段、不改 `operation` 名称、不改交付模板文件名。

## 6. 种子级基本能力

本节定义一组**种子级基本能力**——Odoo 实施中最基础、跨项目复用的起步能力。它们是 skill 的能力目录，不是新增技能包、不是物理目录、`capabilities` 注册表节点保持为空，也不改变 `6+3+4+N` 工作流。

每条种子能力是**声明式定义**：写清业务目标、前置条件、关键步骤、产物与完成判据。业务动作由项目侧填入动作计划，统一走第 1 节约定的单一执行出口；执行器不内置业务语义，也不替代场景门禁。

### 6.1 能力索引

| ID | 名称 | ct_layer | 一句话定位 | 配套场景 |
|---|---|---|---|---|
| `SEED-001` | 主数据初始化 | `shared` | 建立客户、供应商、产品、计量单位等主数据基线 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-002` | 会计模块初始化 | `module` | 建立科目表、会计期间、日记账等会计底座 | `features/account/shipped_not_invoiced.feature` |
| `SEED-003` | 组织架构与权限初始化 | `shared` | 建立公司、部门、用户与权限分组基线 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-004` | 编号规则初始化 | `core` | 建立单据序列与编号规则，保证单据可追溯 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-005` | 期初余额导入 | `module` | 将科目期初余额导入并核对，形成可对账起点 | `features/account/shipped_not_invoiced.feature` |
| `SEED-006` | 计量单位初始化 | `shared` | 建立单位分类、基准单位与换算关系，作为产品与库存的度量基线 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-007` | 币种初始化 | `shared` | 建立本位币与启用币种清单，确定符号、小数位与计价口径 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-008` | 汇率初始化 | `module` | 建立可追溯的汇率基线，支撑跨币种折算与报表换算 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-009` | 国家与地区初始化 | `shared` | 建立国家/地区与地址格式基线，供地址、税务与组织引用 | 暂无，需由 `gherkin-bdd` 补充 |
| `SEED-010` | 语言与本地化初始化 | `shared` | 建立启用语言、默认语言与时区基线，支撑多语言呈现 | 暂无，需由 `gherkin-bdd` 补充 |

其中 `SEED-006`~`SEED-010` 是**基础数据族**：它们位于主数据与会计底座之前，其它种子能力只引用其声明、不重复定义。`SEED-008` 汇率依赖 `SEED-007` 币种与会计本位币的确定。

「配套场景」是**建议引用**，不是能力自造的事实源。真实场景始终以 `gherkin-bdd` 的 `.feature` 为准；标注「暂无」的能力在被场景覆盖前，不得声称已达 G3。

### 6.2 能力定义卡

#### SEED-001 主数据初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 在实施开始前建立干净、唯一、可追溯的主数据基线，避免重复建档污染后续业务 |
| 前置条件 | 主数据来源清单已由业务方确认；去重与编码规则已定；目标环境可写 |
| 关键步骤 | ① 盘点现有主数据并标记重复项 ② 确认编码与命名规范 ③ 分批建立客户/供应商/产品/计量单位 ④ 抽样核对关键字段 ⑤ 冻结基线并记录版本 |
| 产物 | 主数据基线清单、去重记录、基线版本号（写入项目工作区 `artifacts/`） |
| 完成判据（G2 静态） | 四类产品均已建档；编码规范声明完整；基线清单与去重记录存在 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景，不得声称场景通过 |
| 边界 | 不判断主数据的业务正确性；不替代数据治理；不做批量删除 |

#### SEED-002 会计模块初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立可过账、可对账的会计底座，使后续业务单据有确定的科目与期间归属 |
| 前置条件 | 会计政策与科目体系已由财务确认；启用期间已确定；本位币与汇率来源已定 |
| 关键步骤 | ① 确认科目表结构 ② 建立会计期间与财年 ③ 建立日记账与序列 ④ 配置本位币与汇率 ⑤ 核对初始科目余额为零或已记录 |
| 产物 | 科目表版本、期间清单、日记账清单、初始化核对记录 |
| 完成判据（G2 静态） | 科目表/期间/日记账三类声明齐全；配置引用可达；无悬空的期间或科目 |
| 完成判据（G3 场景） | 由 `shipped_not_invoiced.feature` 覆盖发货未开票链路；通过属 G3，不等于价值实现 |
| 边界 | 不提供过账专用执行接口（通用动作走统一执行出口）；不判定会计政策合规性（属专业判断）；期初余额见 `SEED-005` |

#### SEED-003 组织架构与权限初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立与公司实际相符的组织与权限边界，使「谁能看到什么」在开始时即确定 |
| 前置条件 | 公司/部门结构已确认；岗位职责与权限矩阵已由业务方签字 |
| 关键步骤 | ① 建立公司与部门层级 ② 建立用户与角色 ③ 按权限矩阵分组授权 ④ 用最小权限原则复核 ⑤ 记录授权基线 |
| 产物 | 组织层级清单、角色权限矩阵、授权基线版本 |
| 完成判据（G2 静态） | 层级/角色/矩阵三者声明齐全；无越权的最小权限复核记录缺失 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不判定权限设置的业务合理性；不做运行中权限变更；不存储凭据 |

#### SEED-004 编号规则初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 为各类单据建立统一、连续、可追溯的编号规则，避免手工编号造成的断号与重号 |
| 前置条件 | 单据类型清单已确认；编号前缀、位数与重置周期已定 |
| 关键步骤 | ① 盘点单据类型 ② 确认编号格式与重置策略 ③ 建立各类型序列 ④ 验证连续性与唯一性 ⑤ 冻结规则版本 |
| 产物 | 编号规则清单、序列清单、规则版本 |
| 完成判据（G2 静态） | 每种单据都有对应序列声明；格式与重置策略完整；无重复前缀冲突 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不提供序列重置专用执行接口（通用动作走统一执行出口）；不修改历史单据编号 |

#### SEED-005 期初余额导入

| 项 | 内容 |
|---|---|
| 业务目标 | 将科目期初余额准确导入并对账，形成上线后可验证的财务起点 |
| 前置条件 | `SEED-002` 已完成；期初余额表已由财务签字；有可核对的科目映射 |
| 关键步骤 | ① 核对期初余额表与科目映射 ② 试导入并生成差异报告 ③ 确认差异已清理 ④ 正式导入 ⑤ 生成对账记录并冻结版本 |
| 产物 | 差异报告、对账记录、导入批次版本 |
| 完成判据（G2 静态） | 期初余额表与科目映射齐全；试导入差异报告存在且差异已标记处理 |
| 完成判据（G3 场景） | 由 `shipped_not_invoiced.feature` 覆盖后续发货开票链路；期初对账本身需补充场景 |
| 边界 | 不提供导入专用执行接口（通用动作走统一执行出口）；不自动核销差异；非零起点的差异必须由人确认 |

#### SEED-006 计量单位初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立统一、可换算的计量单位体系，使产品、库存、采购与销售对同一物料的度量口径一致 |
| 前置条件 | 计量单位清单与换算关系已由业务方确认；采用公制/英制基线已定 |
| 关键步骤 | ① 建立单位分类（长度/重量/数量/时间等） ② 建立基准单位与换算单位 ③ 录入换算系数并核对精度 ④ 设定产品默认单位 ⑤ 冻结基线版本 |
| 产物 | 单位分类清单、换算关系表、精度核对记录、基线版本号 |
| 完成判据（G2 静态） | 分类/基准单位/换算单位声明齐全；换算系数无环且精度声明完整 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景，不得声称场景通过 |
| 边界 | 不判定度量口径的业务正确性；不自动改写已有产品的计量单位 |
| 版本差异 | **硬差异**：17/18 用 `uom.category` + `uom_type`/`factor`；19 移除 `uom.category`，改用 `relative_uom_id`/`relative_factor`。动作必须按 `odoo_versions` 分化，见 `references/version-compatibility.md` |

#### SEED-007 币种初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立本位币与启用币种清单，使多币种业务的计价、展示与折算有确定口径 |
| 前置条件 | 本位币、启用币种清单、货币符号与小数位规则已由财务确认 |
| 关键步骤 | ① 确认本位币 ② 启用业务所需币种 ③ 核对符号与小数位 ④ 设定默认计价币种 ⑤ 冻结基线版本 |
| 产物 | 启用币种清单、本位币声明、符号与小数位核对记录 |
| 完成判据（G2 静态） | 本位币唯一；启用币种清单非空；符号与小数位声明完整 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不提供实时汇率接入（见 `SEED-008`）；不判定汇率与会计政策合规性 |

#### SEED-008 汇率初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立可追溯的汇率基线，使跨币种单据折算与报表换算有确定的取数依据 |
| 前置条件 | `SEED-007` 已完成且本位币已定；汇率来源、生效日期与更新频率已由财务确认 |
| 关键步骤 | ① 确认汇率来源与生效日期策略 ② 导入初始汇率 ③ 核对本位币对各启用币种的覆盖 ④ 记录来源与生效日期 ⑤ 冻结版本并约定维护频率 |
| 产物 | 汇率表、来源与生效日期记录、覆盖性核对报告、版本 |
| 完成判据（G2 静态） | 每个启用币种都有对应汇率声明；来源与生效日期齐全；无缺失币种对 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不自动抓取实时汇率；不重算历史单据；非零差异必须由人确认 |

#### SEED-009 国家与地区初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立国家/地区与地址格式基线，使客户、供应商、公司地址与税务辖区有统一参照 |
| 前置条件 | 业务涉及的国家/地区清单与默认国家已确认 |
| 关键步骤 | ① 确认国家/地区清单 ② 导入国家与地区数据 ③ 配置地址格式与默认国家 ④ 核对国家与税务辖区的对应 ⑤ 冻结基线版本 |
| 产物 | 国家/地区清单、地址格式配置、默认国家声明、版本 |
| 完成判据（G2 静态） | 清单非空；默认国家唯一；地址格式声明完整且无悬空引用 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不判定税务辖区规则；不自动同步行政区划变更；不内置全量国家数据 |

#### SEED-010 语言与本地化初始化

| 项 | 内容 |
|---|---|
| 业务目标 | 建立语言与时区基线，使界面、单据与报表按目标语言一致呈现 |
| 前置条件 | 启用语言清单、默认语言与时区已由业务方确认 |
| 关键步骤 | ① 安装并激活所需语言 ② 设定默认语言与时区 ③ 核对关键单据与报表的翻译可用性 ④ 记录本地化参数 ⑤ 冻结基线版本 |
| 产物 | 启用语言清单、默认语言与时区声明、翻译可用性核对记录 |
| 完成判据（G2 静态） | 启用语言清单非空；默认语言唯一；时区声明完整 |
| 完成判据（G3 场景） | 需 `.feature` 覆盖；当前无配套场景 |
| 边界 | 不提供机器翻译；不判定翻译质量；不覆盖用户个人语言偏好 |

### 6.3 组合与边界

- **依赖顺序**：基础数据族 `SEED-006`/`007`/`009`/`010` 可并行，且应先于 `SEED-001`/`003`（主数据与组织引用其声明）；`SEED-008` 汇率依赖 `SEED-007` 与会计本位币的确定；在此之上 `SEED-001`/`SEED-003`/`SEED-004` 可并行；`SEED-002` 先于 `SEED-005`；会计底座应先于依赖过账的业务场景。
- **证据边界**：本节的完成判据（G2 静态）只产出 E1/E2 证据；场景通过才进 E4，业务方确认才进 E5，见 `references/evidence-levels.md`。
- **失败处理**：种子能力不定义新的失败码，沿用 `references/error-taxonomy.md` 的 10 类分类；写操作无幂等键按 `CT-007` 阻断，不得由自动化自行解除。
- **版本适配**：初始化方式随 Odoo 版本变化——17/18 走 XML-RPC、19 推荐 JSON-2；`SEED-006` 的计量单位在 19 模型结构改变，必须按 `odoo_versions` 分化动作。`--odoo-version` 必填于任何含版本敏感动作的初始化，详见 `references/version-compatibility.md`。
- **不覆盖**：五层分层能力链、`capabilities` 注册表登记、业务专用执行接口（通用 RPC/shell 动作已收敛到统一执行出口）——三者均不在本包范围。

## 7. 反模式

- 给既有技能强行补 `ct_` 字段以「通过校验」——缺省本就是合法状态，无字段应判 `skipped`。
- 把 `ct_layer` 落成物理目录——与 `npx skills` 的 `<容器>/<技能>/SKILL.md` 平铺要求冲突。
- 在 `.feature` 或契约字段里写模型名、字段名、RPC 方法等实现术语。
- 用契约校验通过替代场景门禁或业务验收。
