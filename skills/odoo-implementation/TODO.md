# odoo-implementation 能力缺口 TODO

本文件是 `skills/odoo-implementation/` 的**能力缺口 backlog**，随技能包安装（`npx skills`）。它回答一个问题：**这个包现在还缺什么、下一步该补什么**。与 `MAINTENANCE.md`（怎么改）分工：TODO 管「做什么」，MAINTENANCE 管「怎么做、怎么验」。

状态口径以**当前代码与 SKILL.md**为准，不以规划文档的阶段标签为准。`docs/odoo-implementation-skills-plan.md` 仍写「P0 已落地、P1 及以后未开始」，但种子能力族（SEED-001~013）与版本感知执行器已实际落地——规划文档的阶段描述已滞后，见 GAP-007。

---

## 1. 能力现状快照（已具备，勿重复登记）

| 能力族 | 已落地产物 | 状态 |
|---|---|---|
| 契约层 | `schema.json`（5 个可选 `ct_` 字段 + `if/then`）、`validate_odoo_manifest.py` | 已落地 |
| 单一执行出口 | `odoo_seed_executor.py`：rpc/json2/shell 三通道、版本感知、dry-run 默认；写白名单含三类核心服务方法 | 已落地 |
| 种子能力 | SEED-001~013（核心服务族 001~003 + 基础数据族 004~008），索引与定义卡 13/13 闭合；编号按 onboarding 执行顺序 | 已落地 |
| 项目模板 | project-state / artifact-index / seed-actions（客户 + 产品主数据）/ base-data-actions / core-services-actions | 已落地 |
| 参考文档 | contract-guide / error-taxonomy / evidence-levels / version-compatibility | 已落地 |
| 流水线挂载 | orchestrator 两处可选钩子（`_bdd_preflight` / `render_deliverables_bundle`），默认关闭 | 已落地 |
| 注册与守卫 | 注册表 0.4.0 同步、版本假绿守卫已修复；全量测试基线见 `docs/项目维护指南.md` §1 | 已落地 |
| 维护规范 | `MAINTENANCE.md`（文件职责、变更流程、发布清单、禁止事项） | 已落地 |

「已落地」仅指工程产物存在，不等于场景通过（G3）或价值实现，见 GAP-003。

---

## 2. 缺口清单

优先级：**P0** = 正确性/一致性风险，先补；**P1** = 影响可用性或证据完整；**P2** = 增强，可排期。
状态：`TODO` 未开始 / `WIP` 进行中 / `BLOCKED` 依赖外部 / `DONE` 已完成（完成后移入 §4 归档，不删除编号）。

### GAP-001 · 写操作的幂等键只是「必填标签」，未真正实现幂等保护 · P0

- **现状**：`odoo_seed_executor.py` 中 `idempotency_key` 仅出现 3 处——写操作校验（必须有）、报告展示（打印键值）。执行器**不读取、不存储、不比对**该键；`--apply` 重复执行同一计划会重复写入。
- **与文档的落差**：SKILL.md §1「执行单一出口」、§4「写操作必须带 `idempotency_key`」、`MAINTENANCE.md` §2.3 均把幂等键表述为安全机制，但实际只防「没写键」，不防「写了键仍重复执行」。
- **建议动作**：在执行器内引入幂等账本（写入项目工作区 `artifacts/`，键 = 计划 ID + 动作序号 + 幂等键），`--apply` 执行前先查账；命中即 `skipped` 并记原因，不再写 Odoo。账本属于运行产物，不入库。
- **完成判据**：① 同一计划 `--apply` 连续执行两次，第二次所有写动作 `skipped` 且 Odoo 侧无新增记录；② 离线测试覆盖「首写成功 + 重放跳过 + 账本损坏 fail-closed」；③ `MAINTENANCE.md` §1 登记账本产物归属。
- **状态**：DONE（执行器 `--ledger-path` 默认 `artifacts/idempotency_ledger.json`；重放测试 `test_20`，账本损坏 `CT-011` fail-closed 测试 `test_21`；见 §4 归档）

### GAP-003 · 10 个种子能力中 8 个无配套场景，G3 证据链断裂 · P1

- **现状**：SEED-004/005/006/007/008/009/010/011 的「配套场景」列均为「暂无，需由 `gherkin-bdd` 补充」。只有 SEED-012/013 引用 `features/account/shipped_not_invoiced.feature`；`features/mrp/mo_completion_posting.feature` 存在但**没有任何 SEED 能力引用**。
- **影响**：按 SKILL.md §6.2，这些能力的 G3 判据只能写「不得声称场景通过」，因此只能产出 E1/E2 证据，无法进入 G3/E4。
- **建议动作**：优先为基础数据族（SEED-004~008，已可直接执行）补一份 `.feature` 覆盖「初始化 → 核对 → 冻结基线」；再补 SEED-010/011 的权限与编号场景；mrp 场景与 SEED 能力建立引用关系。
- **完成判据**：至少 1 个新 `.feature` 纳入 `gherkin-bdd` 门禁且被对应 SEED 卡引用；相关能力卡 G3 判据由「暂无场景」改为真实场景结论；证据等级按 `evidence-levels.md` 标注。
- **状态**：DONE（新增 `features/base/base_initialization.feature`，SCN-BAS-001~004 覆盖 SEED-004~011；MRP 场景以 `@ct-seed=SEED-013` 建立引用）
- **注意**：场景事实源始终是 `gherkin-bdd` 的 `.feature`，本包只引用路径，不得自造场景语言。

### GAP-004 · 执行器版本矩阵只覆盖 3 个通道，20.0+ 无就绪路径 · P2

- **现状**：`SUPPORTED_VERSIONS = ("17.0", "18.0", "19.0")`；`references/version-compatibility.md` 记录 XML-RPC 计划 22.0 移除、Online 21.1 移除。JSON-2 仅 19.0 可用。
- **影响**：若目标环境升级到 20.0+，执行器会直接拒绝（版本不在集合内），而 JSON-2 作为推荐通道却绑定在 19.0 单一版本上。
- **建议动作**：把 `json2` 通道的版本范围从「仅 19.0」放宽为「19.0 及以上」（需核实 20.0 的认证与端点未变），或新增版本到集合时同步更新通道矩阵。无官方证据前不得假设跨版本零改动。
- **完成判据**：`version-compatibility.md` 增加经核实的 20.0 条目；执行器通道矩阵与文档一致；19.0 及 20.0 的 dry-run 用例通过。
- **状态**：BLOCKED（依赖 Odoo 20.0 稳定版官方外部 API 文档）

### GAP-005 · 版本分化目前只有 SEED-004 一处，其余能力未经版本核实 · P1

- **现状**：只有 SEED-004 定义卡带「版本差异」行、`base-data-actions.template.json` 对 UoM 做了 `odoo_versions` 分化。SEED-005/006/007/008 因字段名稳定标为「通用」，但这是**推断**而非逐版本核实；SEED-012/013（会计科目/期初余额）完全未标注版本。
- **风险**：把「未核实」当成「通用」会在错误版本上跑错初始化——正是执行器 CT-003 fail-closed 要防的场景，但 fail-closed 只对**已标注版本敏感**的动作生效。
- **建议动作**：逐项核实 SEED-005/006/007/008/009/012/013 在 17/18/19 的字段与模型差异；把确认无差异的项在定义卡写明「已核实三版本一致」（带依据），未核实的加 `odoo_versions` 标注。
- **完成判据**：10 张卡的版本状态全部为「已核实一致」或「已分化」之一，无空白；`version-compatibility.md` 记录核实依据。
- **状态**：DONE（13/13 能力卡均有「版本差异」行；`version-compatibility.md` §2.2/§2.3/§2.4 记录核实范围；守卫测试 `test_22`）

### GAP-006 · 规划文档阶段标签与文件引用滞后 · P1

- **现状**：`docs/odoo-implementation-skills-plan.md` 多处与事实不符：开头状态仍为「P0 已落地；P1 及以后未开始」；§4 目标结构写 `references/{module-catalog,error-taxonomy,evidence-levels}.md` 与 `scripts/{validate_odoo_manifest.py,odoo_rpc.py}`，其中 `module-catalog.md` 与 `odoo_rpc.py` 从未存在；§5 P2 退出判据「模块级技能中直接 RPC 调用点数为 0」未被验证；§7 决策 5「是否补工作流图挂载说明」仍待确认。
- **影响**：规划文档是阶段性事实源，滞后会让后续维护者误判已完成范围（本 TODO 的存在本身即因此）。
- **建议动作**：不重写历史，改用「决策记录 + 状态更新」方式：状态行改为「P0/种子族/执行器已落地；P1~P4 部分完成，详见 TODO.md」；§4 文件名改为实际产物；§7 决策 5 给出明确结论。
- **完成判据**：文档中不再出现不存在的文件名；阶段标签与 SKILL.md/本 TODO 一致；`MAINTENANCE.md` §1 若引用规划文档则同步。
- **状态**：DONE（规划文档状态行、§4 目标结构、§5 P3 判据、§7 决策 5/6 已更新）

### GAP-007 · `capabilities` 注册表节点为空，P3「可枚举」判据与当前设计冲突 · P2

- **现状**：注册表 `capabilities: {}`，由测试锁定为空（防止五层能力链复活）。规划 §5 P3 退出判据要求「注册表 `capabilities` 节点可枚举」。
- **判定**：这是**设计决策冲突**，不是实现遗漏。用户已明确否决五层链、保持四层分类标签。因此 P3 判据应视为作废，而非待实现。
- **建议动作**：在规划文档 §7 追加决策记录，说明 P3 的 `capabilities` 判据被「保持空节点」决策取代；本 TODO 不安排实现。
- **完成判据**：规划文档与 `MAINTENANCE.md` §4「禁止事项 2」口径一致，不再把 `capabilities` 可枚举列为待办。
- **状态**：DONE（规划文档 §7 决策 6 已记录 P3 判据作废；A 级提升计划 §6-3 用户已确认）

### GAP-008 · 质量守卫未覆盖「执行器幂等账本」与「版本标注完整性」 · P2

- **现状（修复前）**：现有守卫——`test_no_hardcoded_paths.py`（路径）、`test_registry_integration.py`（版本/引用闭合）、执行器离线自测（项数以 CI 结果为准）。但无守卫检查：① SEED 卡的「版本差异」行是否存在且与模板 `odoo_versions` 一致；② GAP-001 修复后的幂等账本行为。
- **建议动作**：在 `tests/test_odoo_seed_executor.py` 增加「能力卡版本行 ↔ 模板版本标注」一致性断言；账本实现后补重放测试。
- **完成判据**：manifest 版本漂移与模板版本标注缺失都能让测试变红（变异验证）。
- **状态**：DONE（幂等账本重放/损坏测试 `test_20`/`test_21`；版本行守卫 `test_22`；依赖 GAP-001/GAP-005 已关闭）

---

## 3. 明确不做（已否决 / 超出范围，勿当 TODO 补）

| 项 | 决策依据 |
|---|---|
| 五层能力链 `router→shared→module→core→validation` | 用户明确否决；`ct_layer` 保持四层分类标签，注册表 `capabilities` 保持空 |
| 物理分层目录 | 与 `npx skills` 平铺布局冲突；曾为此迁移 45 个文件 |
| 在能力定义或 `.feature` 里写模型名/字段名/RPC 方法 | 实现术语不进场景与能力语义层 |
| 新增质量检查类型 / 新阶段 / 改 `operation` 名称 | 复用现有 `scenario_spec`（第五种类型已够），不颠覆 `6+3+4+N` |
| 把种子能力包做成独立仓库或迁移既有技能 | 「不颠覆骨架」根本约束 |
| 从外部框架移植目录层级、生成器、OAuth/作业调度 | 与技术栈无关且违反不颠覆约束 |
| 自动抓取实时汇率 / 机器翻译 / 判定会计政策合规 | 属专业判断或超出种子能力边界，见各能力卡「边界」行 |

---

## 4. 完成归档（DONE 的编号移到这里，保留编号不删除）

| 编号 | 完成内容 | 完成提交 |
|---|---|---|
| GAP-001 | 执行器新增幂等账本（计划 ID + 动作序号 + 幂等键），成功写入才记账；重放即 `skipped`；账本损坏 `CT-011` error 且零执行 | `ee5b90f` |
| GAP-003 | 新增 `base_initialization.feature`（SCN-BAS-001~004），覆盖 SEED-004~011；MRP 场景以 `@ct-seed=SEED-013` 建立引用 | `ee5b90f` |
| GAP-005 | 13/13 能力卡补齐「版本差异」行与核实范围；`version-compatibility.md` §2.4 登记组织/编号/会计底座 | `ee5b90f` |
| GAP-006 | 规划文档状态行、目标结构文件名、P3 判据与决策 5/6 与代码对齐 | `ee5b90f` |
| GAP-007 | 正式记录 `capabilities` 空节点决策，P3 可枚举判据作废 | `ee5b90f` |
| GAP-008 | 新增幂等账本与版本标注守卫测试（test_20~22） | `ee5b90f` |
| GAP-002 | P2 核心服务三类能力落地：SEED-001 模块安装（`button_immediate_install`）、SEED-002 配置参数（`set_param`）、SEED-003 CSV/XML 导入（`import_data`）；新增 `core-services-actions.template.json`、执行器写白名单与 JSON-2 映射、`version-compatibility.md` §3、核心服务离线测试；索引与定义卡 13/13。模块安装按版本标注 `odoo_versions`，未指定版本 fail-closed。 | `501cf48` |
| GAP-009 | SEED-009 定义卡声明覆盖产品，但动作模板原先只有客户导入；补齐 `product.category` 与 `product.template` 建档动作、按编码读回核对、幂等键与 shell_code；SEED-009 卡明确产品编码唯一性与计量单位引用判据，`version-compatibility.md` §2.3 记录「字段未逐版本核实 + staging 验证」口径；新增 1 项离线测试。 | `501cf48` |

---

## 5. 维护规则

1. **新增缺口**：追加 `GAP-0xx`（序号连续、不复用），写清「现状 / 与文档落差 / 建议动作 / 完成判据 / 状态」五项，缺一不可。没有完成判据的条目不得进入清单。
2. **状态流转**：`TODO → WIP → DONE`；依赖外部或他人决策用 `BLOCKED` 并写明依赖项。DONE 条目移入 §4 归档，编号永久保留。
3. **优先级**：P0 正确性/一致性，P1 可用性/证据，P2 增强。同一优先级按编号顺序处理。
4. **与 MAINTENANCE.md 联动**：本文件新增/归档条目不改变技能包版本；若缺口修复涉及版本升级或新增文件，按 `MAINTENANCE.md` §2.4 与 §1 文件职责矩阵同步。
5. **事实源优先**：本文档的状态以当前代码与 SKILL.md 为准；与规划文档冲突时以本文档与实际代码为准，并把冲突登记为 GAP（如 GAP-006、GAP-007）。
6. **不建平行清单**：仓库根 `docs/odoo-implementation-skills-plan.md` 保留为阶段性建设方案；本文件是本包的运行时 backlog，二者通过 GAP 条目互相引用，不各写各的。
