# Odoo 实施技能包建设方案（增量扩展版）

> 状态：P0 契约基座已落地并集成进 CT 注册表；P1 及以后未开始。
> 依据：外部实施框架对标分析（机制参照，已归档）；
> Capability Twin 3.5 基线 `91383fe`（main `0e0dd57`）。
> **根本约束：不颠覆现有框架。** 不新建平行体系、不改 `6+3+4+N` 编号、不迁移已有文件、不改现有技能契约。
> 对框架只作为机制参照，其目录层级与专有技术栈不移植。

---

## 1. 立场：借鉴机制，不动骨架

现有框架已经具备四项能力，对标框架的价值在于把它们组织得更严格。因此本方案只做**加挂**，不做替换。

| 现有能力 | 位置 | 本方案动作 |
|---|---|---|
| `6+3+4+N` 工作流 | `skills/capability-twin-orchestrator/references/workflows.md` | 保持阶段与编号不变，只在既有挂载点增加可选分支 |
| 场景唯一事实源与门禁 | `skills/gherkin-bdd/`、`bdd_gate.py` | 复用同一引擎，不另建场景描述语言 |
| 五种质量检查类型 | `skills/quality-gate/main.py:22-24`、`:610` | 复用 `scenario_spec`，不新增 check_type |
| 资源定位与安装布局 | `framework_paths.py`、`skills/<skill>/` 平铺 | 沿用现有路径不变量与 npx 安装结构 |

**明确不做**：独立仓库、新的物理分层顶层目录、重命名或移动现有文件、修改现有 `SKILL.md` 的 `name`/`description`/`skills_used` 字段、改变 `operation` 名称、改变交付模板文件名。

---

## 2. 对标分析：哪些机制值得借用

### 2.1 可借用

| 机制 | 对标框架实证 | 在 CT 中的落点 |
|---|---|---|
| 机器可读契约 | manifest 受 JSON Schema 校验，`additionalProperties: false`，用 `if/then` 限定层级字段 | 在现有 frontmatter 上**追加可选字段**，由新增校验脚本消费；不替换 `name`/`version`/`skills_used` |
| 依赖显式声明 | `depends_on` / `uses_core` 表达技能关系，而不是硬编码顺序 | 映射到现有 `skills_used` 的扩展字段，保持向后兼容 |
| 持久项目状态 | `project/{id}` 的 state、artifacts、runs、baselines | 作为 `template-processor` 新增模板与运行产物，不进入版本库 |
| Fail-closed 路由 | 缺输入或目录歧义即 blocker；REST/OAuth/CLI 不是执行路由 | 复用现有门禁 `status=blocked` 语义；缺模块场景时禁止派生交付物 |
| 证据分级 | 五级证据、三态就绪度、10 类失败分类、变更无幂等键不得重试 | 对齐现有 G2/G3/FDE 边界；"自动化通过 = G2 ≠ 业务验收"已有同类结论 |

### 2.2 不借用

| 对标框架做法 | 不借用原因 |
|---|---|
| 物理分层目录 | 与 `npx skills` 的 `<容器>/<技能>/SKILL.md` 平铺要求冲突；CT 曾为此迁移 45 个文件 |
| 大规模技能与目录数据批量生成 | 依赖专有发布目录与生成器；CT 无对应 Odoo 事实源，硬铺会产生空壳技能 |
| 专有平台的 OAuth / 数据装载 / 作业调度 / 运行手册 | 与 Odoo 技术栈无关 |
| 生成器放在不随包发布的目录 | 该框架自身存在该缺口（文档引用的生成器不在公开发行版中）；CT 的资源必须放在技能包内 |

---

## 3. 增量落点（精确到现有代码）

| 落点 | 文件与位置 | 扩展方式 |
|---|---|---|
| 前置校验 | `skills/capability-twin-orchestrator/scripts/main.py:247` `_bdd_preflight` | 在既有 preflight 结果里追加 Odoo 契约校验；不改变返回结构，只增加可选字段 |
| 阶段门禁 | 同文件 `:285` `_bdd_gate_stage`，调用点 `:354`、`:765`、`:898` | 复用既有 G2 / G2-customization 调用点，不新增阶段 |
| 交付包渲染 | 同文件 `:1050` `render_deliverables_bundle`，分发 `:1349` | 仅在门禁通过时追加 Odoo 实施产物；现有模板输出保持原名 |
| 质量检查 | `skills/quality-gate/main.py:22-24`、`:610` | 复用 `scenario_spec` 检查类型，不新增第五/第六种类型 |
| 能力注册 | `capability_registry.json` 的 `capabilities: {}` 空节点；`capability_registry.py:98` `register_capability` | 用既有 API 注册 Odoo 实施能力，不改动 `agents` / `skills` 两个节点 |
| 路径解析 | `framework_paths.py` 的 `skill_dir()`、`features_dir()`、`templates_deliverables()` | 新增一个只读解析函数，沿用"按 `__file__` 推导容器根"的不变量 |
| 场景事实源 | `skills/gherkin-bdd/features/account/`、`features/mrp/` | 直接复用现有两份 feature，不另建目录 |
| 回归守卫 | `conftest.py`、`tests/test_no_hardcoded_paths.py` | 新文件自动纳入现有守卫，无需改守卫逻辑 |

---

## 4. 目标结构（只新增，不移动）

```text
（现有仓库，21 个技能保持不变）
└── skills/
    ├── capability-twin-orchestrator/        # 仅在既有钩子内追加可选分支
    ├── quality-gate/                        # 复用 scenario_spec，不新增类型
    ├── gherkin-bdd/                         # 复用现有 .feature 与门禁引擎
    ├── template-processor/                  # 新增 Odoo 实施模板（追加，不改名）
    └── odoo-implementation/                 # 唯一新增技能包（可回退）
        ├── SKILL.md                         # 沿用现有 frontmatter 约定
        ├── schemas/odoo-implementation.schema.json
        ├── references/{module-catalog,error-taxonomy,evidence-levels}.md
        ├── scripts/{validate_odoo_manifest.py,odoo_rpc.py}
        └── templates/project/{project-state,artifact-index}.json
```

新增技能 `odoo-implementation` 是唯一的结构性变化；它整包位于 `skills/` 下，因此 `npx skills` 安装后 schema、脚本、模板都能到达目标环境。若停用，只需移除该目录并撤掉两处可选钩子，现有流水线原样工作。

### 4.1 契约扩展方式

现有 `SKILL.md` frontmatter 的 `name`、`description`、`allowed-tools`、`version`、`skills_used` 保持原义。新增字段全部可选，且带 `ct_` 前缀以表明属于本扩展：

| 新增字段 | 含义 |
|---|---|
| `ct_layer` | `router` / `core` / `shared` / `module`，仅用于分类，不建立物理目录 |
| `ct_module` | Odoo 模块名，如 `account`、`mrp` |
| `ct_odoo_versions` | 适用大版本，如 `["17.0", "18.0", "19.0"]` |
| `ct_scenario_refs` | 指向既有 `.feature` 路径与 `@ct-id` |
| `ct_state_outputs` | 声明写入项目工作区的产物类型 |

校验脚本必须能读取"没有这些字段"的既有 21 个技能并通过——这是"不颠覆"的硬性回归条件。

---

## 5. 分阶段路线

| 阶段 | 目标 | 新增内容 | 退出判据 |
|---|---|---|---|
| P0 契约基座 | 建立可回退的扩展点 | `odoo-implementation` 骨架、schema、校验脚本、两处可选钩子；经 `discover_capabilities.py` 登记进注册表 | 195 项测试全绿；21 个既有技能在无新字段时校验通过；负例校验返回非零；注册表 21→22 且幂等 |
| P1 垂直切片 | 用会计模块端到端跑通 | 复用 `shipped_not_invoiced.feature`；保持 CT 原架构，不引入新的分层能力链 | 既有 BDD 门禁照常产出 UAT 与追溯矩阵；G2 通过不等于 G3 的提示仍在 |
| P2 核心服务 | 收敛 Odoo 外部操作 | `odoo_rpc.py` 单一出口、模块安装、配置参数、CSV/XML 导入 | 模块级技能中直接 RPC 调用点数为 0；缺凭据时返回 `status=blocked` |
| P3 横向复制 | 扩展到 mrp / sale / stock | 复用 `mo_completion_posting.feature`；按目录登记新能力 | 每个新模块至少 1 个场景；注册表 `capabilities` 节点可枚举 |
| P4 治理完善 | 补齐长期维护约束 | 错误分类、重试禁令、证据分级说明 | 负向用例证明失败不会被改成 PASS；文档与执行能力差异显式标注 |

P0 → P1 → P2 串行；P3 必须在 P1、P2 完成后启动；P4 可提前准备文档，但判据以 P1 为准。

---

## 6. 验收与防线

1. **零破坏**：每一阶段结束后运行全仓 `pytest`，P0 集成后基线为 195 passed；任何下降视为回归，不进入下一阶段。
2. **零迁移**：`git diff` 中不得出现既有文件的 rename 或删除；只允许新增文件与既有钩子内的追加分支。
3. **零假绿**：校验脚本对"缺字段 / 非法 `ct_layer` / 非法版本 / 多余字段"四类负例必须失败，并做变异验证。
4. **零硬编码**：新文件自动通过 `tests/test_no_hardcoded_paths.py`；源码路径只认 `ODOO_SOURCE_PATH`。
5. **安装可达**：真实 `npx skills add <repo> --list` 能看到新增技能；安装后 schema 与模板存在。
6. **边界清晰**：交付物继续标注"自动化通过 = G2；交付验收 ≠ 价值实现"，不得用 Odoo 实施技能包改变这一结论。

---

## 7. 决策记录

1. 首个模块 `account`，直接复用现有 `shipped_not_invoiced.feature`。**待办（P1）**。
2. 新增独立技能包 `odoo-implementation`，不并入 orchestrator。**已定，P0 已落地。**
3. 保持 CT 原架构：不引入五层分层能力链，`ct_layer` 维持四层分类标签，**不强制任何技能声明**。已否决五层链方案（曾一度改 schema 为五层，已回退）。
4. 注册表集成走既有 `discover_capabilities.py`，`odoo-implementation` 已登记（skills 21→22，`capabilities` 保持空节点）。**已落地并有回归测试锁定。**
5. 是否在 `6+3+4+N` 工作流图补挂载说明，仍**待确认**。

P0 已完成并集成；P1 及以后按阶段独立回退。
