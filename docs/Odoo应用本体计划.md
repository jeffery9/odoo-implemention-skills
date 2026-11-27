# Odoo 应用本体计划

> **目标**：为 AI 建立一层「Odoo 应用认知压缩层」——把分散在 Python 类、ORM 元数据、XML/CSV、
> 权限规则中的**应用结构语义**转成机器可读、按需加载、带物理锚点的语义投影，
> 让 AI 用更少的上下文和工具调用理解 Odoo 应用。
> **明确非目标**：让 AI 理解应用上运行的业务（业务流程、角色语义、工作空间、状态业务含义）。
> **口径**：FDE 2.0——不加权打分，只给证据链与可复现验证；本地只做静态检查，
> 构建、全量测试与运行时验证由 CI 执行（用户约束）。
> **状态**：待用户批准。批准后按工作包实施；未批准前不改动代码。

---

## 0. 一句话定义

**本体 = 从既有事实源派生的、只读的 Odoo 应用语义投影；语义 ID 就是 Odoo 技术名；
覆盖元模型、模型定义、框架级数据记录，以及 Python/View/OWL 三类载体的**逻辑实现结构**；
不覆盖业务数据记录与业务语义解释。**

任何本体设计，如果不能让 AI 更快理解、更准确推理或更可靠执行，就没有理由存在。

---

## 1. 覆盖范围（四层边界 + 逻辑实现层）

| 层 | 内容 | 处置 |
|---|---|---|
| M3 元模型 | 本体自己的 schema：entity / field / relation / view / action / menu / group / rule / acl 的类型定义 | **覆盖**：一份 schema，不建五套子系统 |
| M2/M1 模型定义 | `ir.model`、`ir.model.fields`、Python 类、字段、关系、`_inherit`/`_inherits`、方法 | **覆盖**：每个节点带 `file:line` 锚点 |
| 框架级数据记录 | `ir.ui.view`、`ir.actions.*`、`ir.ui.menu`、`res.groups`、`ir.rule`、`ir.model.access` 的行 | **覆盖（重点）**：完整清单见 §1.1，ownership 见 §1.1.4 |
| 逻辑实现层 | Python 方法/约束/计算、view modifier/domain/context/button、OWL 组件事件与 RPC 调用 | **覆盖（新增）**：见 §1.2；只记"写了什么条件、触发什么效果"与锚点，不解释业务含义 |
| 业务数据记录 | `sale.order`、`mrp.production` 等模型的实例行 | **不覆盖**：只通过锚点关联能力单元与场景 |

**边界判据（可校验）**：本体中出现的记录，其所属**模型**必须在 §1.1「框架元数据模型白名单」内；
出现白名单外的模型即视为越界，CI 门禁失败。白名单按 **ORM 模型名（`_name`）** 枚举，不按物理表名枚举；
many2many 关系表（如 `ir_ui_view_group_rel`）由字段定义派生，不单独建节点。白名单本身是本体 schema 的一部分。

---

## 1.1 框架级数据记录：定义、白名单与排除清单

### 1.1.1 明确定义（可判定）

**框架级数据记录** = 满足以下**全部**条件的 ORM 记录：

1. 其 `_name` 在 §1.1.2 白名单内（模型由 Odoo 框架/base 模块定义）；
2. 记录声明的是 Odoo **应用自身**的结构、呈现、导航、自动化、权限或外部身份映射；
3. 记录不是业务事实，不随日常业务交易增删；
4. 本体只记录其**定义性字段**（标识、绑定、引用、ownership），不记录运行时状态字段。

任一命中即**排除**：属于业务模型实例；属于人员/组织/主数据；属于运行时或运维状态；
只是实现机制或投影关系表。定义与白名单由 WP1 校验器机器执行，不靠人工自觉。

### 1.1.2 首期白名单（证据：Odoo 18.0 官方源码 `odoo/addons/base/models/*.py`）

源文件基准：`https://github.com/odoo/odoo/tree/18.0/odoo/addons/base/models`，
逐文件 raw 核对时间 2026-11-27；表中「证据源文件」列均为该目录下的文件名。

**元模型与权限定义**

| ORM 模型 | 本体语义 | 处置 | 证据源文件 |
|---|---|---|---|
| `ir.model` | 模型定义 | 收录 | `ir_model.py` |
| `ir.model.fields` | 字段定义；`groups` 字段访问限制作为字段属性，不另建模型 | 收录 | `ir_model.py` |
| `ir.model.inherit` | 继承关系投影 | 收录，`derived` | `ir_model.py` |
| `ir.model.relation` | 关系投影 | 收录，`derived` | `ir_model.py` |
| `ir.model.constraint` | 约束定义/投影 | 收录 | `ir_model.py` |
| `ir.model.fields.selection` | 选择项定义 | 收录 | `ir_model.py` |
| `ir.model.data` | XML ID 映射；用 `module/name/noupdate` 判定 ownership | **收录（关键）** | `ir_model.py` |
| `ir.model.access` | ACL 定义（`perm_read/write/create/unlink`） | 收录 | `ir_model.py` |
| `ir.rule` | record rule 定义（`domain_force`/`groups`） | 收录 | `ir_rule.py` |
| `res.groups` | 组定义 | 收录 | `res_users.py` |

**交互与呈现定义**

| ORM 模型 | 本体语义 | 处置 | 证据源文件 |
|---|---|---|---|
| `ir.ui.view` | 视图定义（`model`/`key`/`inherit_id`/`arch` 绑定） | 收录 | `ir_ui_view.py` |
| `ir.ui.view.custom` | 用户定制视图 | 收录，`metadata_first`，只记存在性与引用，不作应用基线 | `ir_ui_view.py` |
| `ir.actions.actions` | 动作基类 | 收录 | `ir_actions.py` |
| `ir.actions.act_window` | 窗口动作 | 收录 | `ir_actions.py` |
| `ir.actions.act_window.view` | 动作-视图绑定 | 收录 | `ir_actions.py` |
| `ir.actions.act_window_close` | 关闭动作 | 收录 | `ir_actions.py` |
| `ir.actions.act_url` | URL 动作 | 收录 | `ir_actions.py` |
| `ir.actions.client` | 客户端动作 | 收录 | `ir_actions.py` |
| `ir.actions.server` | 服务端动作 | 收录 | `ir_actions.py` |
| `ir.actions.todo` | 引导动作 | 收录 | `ir_actions.py` |
| `ir.actions.report` | 报表动作 | 收录 | `ir_actions_report.py` |
| `ir.embedded.actions` | 内嵌动作；仅 `user_id=false` 的共享项作应用定义 | 收录 | `ir_embedded_actions.py` |
| `ir.ui.menu` | 菜单与动作引用 | 收录 | `ir_ui_menu.py` |
| `ir.asset` | 前端资源包 | 收录 | `ir_asset.py` |
| `ir.filters` | 保存的筛选/默认筛选；仅 `user_id=false` 的全局项作应用定义，个人筛选排除 | 收录 | `ir_filters.py` |

**自动化、配置与模块定义**

| ORM 模型 | 本体语义 | 处置 | 证据源文件 |
|---|---|---|---|
| `ir.cron` | 计划动作**定义**（方法、间隔） | 收录；运行状态字段排除 | `ir_cron.py` |
| `ir.default` | 字段默认值定义；仅全局/公司级，个人级排除 | 收录 | `ir_default.py` |
| `ir.sequence` / `ir.sequence.date_range` | 编号规则定义 | 收录 | `ir_sequence.py` |
| `ir.config_parameter` | 系统参数；**只记键与 ownership，不记值**（含密钥） | 条件收录 | `ir_config_parameter.py` |
| `ir.module.module` | 模块技术名、状态、依赖 | 收录（只取定义性字段） | `ir_module.py` |
| `ir.module.category` | 应用分类 | 收录 | `ir_module.py` |
| `ir.module.module.dependency` | 模块依赖 | 收录，`derived` | `ir_module.py` |
| `ir.module.module.exclusion` | 模块互斥 | 收录，`derived` | `ir_module.py` |

> **证据边界**：上表模型名逐项核对自 Odoo 18.0 官方源码；本地 `ODOO_SOURCE_PATH` 未配置，
> 因此 17/19 是否同名同语义一律标 `open-question`，不做跨版本断言（沿用 §10.2 纪律）。
> `ir.module.module` 的存在性由同文件 `class Module` 字段与多处 `self.env['ir.module.module']` 引用证实；
> 精确 `_name` 声明行未捕获，待配置源码路径后补 `file:line` 锚点。

### 1.1.3 排除清单（白名单外，出现即门禁失败）

| 排除对象 | 理由 |
|---|---|
| `sale.order` / `mrp.production` 等一切业务模型的实例行 | 业务事实，不是应用定义 |
| `res.users` / `res.partner` / `res.company` / `res.country` / `res.currency` / `res.lang` / `res.bank` | 人员、组织、主数据；`res.groups` 是例外（仅组定义本身） |
| `ir.attachment` | 二进制内容；视图/图标内容不作为语义节点，必要时只存锚点 |
| `ir.cron.trigger` / `ir.cron.progress` | 计划任务运行时状态 |
| `ir.autovacuum` / `ir.logging` / `ir.profile` | 运维与诊断状态 |
| `ir.mail.server` | 系统邮件配置，不描述应用结构 |
| `ir.http` / `ir.qweb` / `ir.binary` / `ir.fields` | 实现机制，不是可投影的定义记录 |
| `ir_ui_view_group_rel` / `rule_group_rel` / `ir_ui_menu_group_rel` | m2m 关系表，从字段定义展开，不单独建节点 |
| `ir.model.data` 之外的任何“外部 ID 类”自定义表 | 未经核实即越界，fail-closed |

### 1.1.4 ownership 判定（不猜源码归属）

以 `ir.model.data` 为唯一判定入口，字段 `module/name/noupdate` 已核实：

- 有 XML ID 且 `module` 对应仓库内模块 → `code_first`，锚点 = 源码文件 + `module.name`；
- `noupdate=1` → 仍为 `code_first`，但显式标「运行时可改」例外；
- 无 XML ID、或 `module` 为 `__custom__` /  `__export__`、或找不到源码 → `metadata_first + open-question`；
- `ir.model.inherit` / `ir.model.relation` / `ir.model.constraint` / `ir.model.fields.selection` 等由 ORM 从 Python 推导 → `derived`。

**红线**：`ir.config_parameter` 的值、`ir.rule.domain_force` 的执行效果均不写入本体；
本体只回答“定义在哪、绑定什么”，不回答“权限是否正确”。

### 1.1.5 门禁负例（WP1 必须拦截）

- 白名单外模型（如 `res.partner`）作为记录节点 → 越界失败；
- 未经核实的模型名且 `evidence != open-question` → 失败；
- 无 `ir.model.data` 却标 `code_first` → 失败；
- 个人级 `ir.filters` / `ir.default` 冒充应用定义 → 失败；
- 收录 `ir.cron.trigger` 等运行时状态 → 失败。

---

## 1.2 逻辑实现层：Python / View / OWL

### 1.2.1 范围界定

用户要求覆盖"python 代码里面的逻辑、view 里面的逻辑、owl 组件实现的逻辑"。纳入的是**逻辑的实现结构**——
哪个触发点、什么条件、产生什么效果、绑定哪个模型/字段/视图/动作/组件、源码在哪；
**不纳入**业务语义解释（为什么是这个状态、角色的业务含义、工作空间），后者仍按 D5 排除。

**最小充分语义门槛**：只收会改变**可见性、可编辑性、数据写入、导航、方法调用或渲染**的逻辑点；
纯局部变量、字符串格式化、日志、内部工具函数不收。不做完整 AST/CFG 落盘。

### 1.2.2 三类载体与可提取内容

| 载体 | 纳入的逻辑点 | 提取方式 | 不可静态确定时 |
|---|---|---|---|
| Python | 方法入口（含 `action_*`）、`@api.constrains` / `@api.depends` / `@api.onchange`、computed/inverse、SQL 约束、状态写入、`super()` 调用、对外可调用方法 | AST 静态提取装饰器、赋值/调用目标、条件表达式，保留 `file:line` 与源码片段 | 动态调用、`super()` 链受继承与模块加载顺序影响 → 标 `inference`（带推导链）或 `open-question` |
| View | `invisible` / `readonly` / `required` / `column_invisible`、`domain` / `context`、`groups`、button 的 `name` / `type` / `target`、字段绑定、`xpath` 继承点、QWeb `t-if` 等条件 | XML 解析 arch + 可解析的继承链；表达式**原样**保存，不求值 | 最终 arch 由 Odoo 运行时继承解析决定 → 静态结果标 `repository-fact`，**不声明运行时最终形态** |
| OWL | 组件类与模板、事件处理、`useState` / props、RPC 指向的 model/method、条件渲染、patch/扩展点 | JS/TS/XML 静态扫描 + 组件-模板关联 | 17/18/19 OWL API 差异大，未逐版本核实不得跨版本断言；动态绑定标 `open-question` |

### 1.2.3 逻辑单元节点（M3 扩展）

```yaml
id: mrp.production.action_start      # python: <model>.<method>；view: <xmlid>#<element>；owl: <module>.<Component>#<handler>
kind: logic
carrier: python                      # python|view|owl
trigger: method                      # method|constraint|compute|onchange|button|event|lifecycle
condition: "state == 'confirmed'"    # 原样表达式，不求值；无则为 null
effect: ["write(state='progress')"]  # 原样/规范化描述 + 各自锚点
bindings: {model: mrp.production, view: ..., component: ..., method: ...}
source_anchor: addons/mrp/models/mrp_production.py:L512
odoo_versions: ["17.0","18.0","19.0"]
evidence: repository-fact            # platform-fact|repository-fact|inference|open-question
```

- **条件与效果都是语法投影**：只回答"源码写了什么"，不回答"是否正确/是否生效"；
- 逻辑单元通过 `bindings` 连到 §1 的模型、§1.1 的框架记录节点，形成可一跳展开的逻辑图；
- 查询返回"触发点 + 条件 + 效果 + 绑定 + 锚点"，不返回整段源码。

### 1.2.4 事实源与 fail-closed

- 本地无 `ODOO_SOURCE_PATH`、仓库内也无 OWL 源码，试点阶段逻辑节点只能来自：
  仓库固定事实（`.feature` 场景锚点、SEED 卡、版本矩阵）与目标源码的静态扫描；
- 既无源码又无仓库锚点 → 建 `open-question` 占位节点，**不编造条件或效果**；
- 现有 `scripts/ast_analyzer.py` 仅输出 class/field 与少量 `logic_footprints`（SQL 执行、装饰器标记），
  且为一次性打印、不落盘、无锚点；WP4 扩展为专用提取器，输出带锚点的结构化节点，不把它当权威事实源。

### 1.2.5 门禁负例（WP4 必须拦截）

- `logic` 节点缺 `carrier` / `trigger` / `source_anchor` → 失败；
- `condition` / `effect` 只有结论无源码锚点 → 失败；
- `inference` 无推导链、`open-question` 被标成事实 → 失败；
- 跨版本 OWL/ORM 行为断言无逐版本锚点 → 失败；
- 纯格式化/日志等无行为影响的节点混入 → 失败（最小充分语义门槛）。

---

## 2. 关键架构决策

| 编号 | 决策 | 理由 |
|---|---|---|
| D1 | **语义 ID = Odoo 技术名**（`mrp.production`、`mrp.mrp_production_form_view`），不发明独立语义 ID | 目标是理解应用，技术名即身份；另建 ID 会变成第二事实源 |
| D2 | 框架级数据记录按 **ownership 分类**：`code_first`（XML/CSV 定义，DB 行是投影）/ `metadata_first`（运行时权威）/ `derived` | 吸收 EOA §7；防止把投影当权威反向改写源码 |
| D3 | 不填充 `capabilities: {}`，本体是独立产物 | `capabilities` 描述框架工具；本体描述应用构成，是两个语义域；GAP-007 已锁定 |
| D4 | 五域（结构/行为/治理/上下文/交互）只是**观察维度**，不落五个子系统 | 用户已明确修正；避免为了本体完整性牺牲 AI 理解效率 |
| D5 | 覆盖逻辑的**实现结构**（条件/效果/绑定/锚点），不解释业务含义、角色语义、工作空间 | "代码写了什么"属于理解应用；"为什么这么设计"属于理解业务，仍排除 |
| D6 | 本体不可手工编辑，由脚本重建；CI 比对入库哈希与重建哈希 | 复用注册表与 `check_docs_baseline.py` 的防漂移模式 |

---

## 3. 统一节点信封（M3）

每个节点必须携带：

```yaml
id: mrp.production                 # Odoo 技术名，不翻译、不另建 ID
kind: model                        # module|model|field|method|view|action|menu|group|rule|acl|logic
# kind=logic 时追加 carrier / trigger / condition / effect / bindings（见 §1.2.3）
ownership: code_first              # code_first|metadata_first|derived
source_anchor: addons/mrp/models/mrp_production.py:L512
odoo_versions: ["17.0","18.0","19.0"]
evidence: platform-fact            # platform-fact|repository-fact|inference|open-question
```

**证据分级**（吸收 EOA 附录 C，与 FDE 对齐）：

- `platform-fact`：在 Odoo 官方源或目标版本源码中核实；
- `repository-fact`：在本仓库固定事实源（`.feature` 场景、`ct_` 字段、版本矩阵、SEED 卡）中核实；
- `inference`：由已核实事实推导，需标注推导链；
- `open-question`：无法核实——**保留节点并显式标注，不编造、不猜测**。

---

## 4. 事实源与 ownership 矩阵

| 节点类型 | 权威来源 | ownership | 投影/核对 |
|---|---|---|---|
| module | `__manifest__.py` | code_first | 依赖、数据文件清单 |
| model / field / method | Python 类 | code_first | `ir.model`、`ir.model.fields` 为投影 |
| view / action / menu / asset / filter | 模块 XML / CSV | code_first | `ir.ui.view`、`ir.actions.*`、`ir.ui.menu` 等为投影 |
| group / ACL / record rule | XML / CSV | code_first | `res.groups`、`ir.model.access`、`ir.rule` 为投影 |
| cron / default / sequence / config_parameter / module 状态 | XML / CSV / `__manifest__.py` | code_first | 只取定义性字段；运行态字段排除 |
| XML ID 映射 | 模块数据 | code_first | `ir.model.data` 是 ownership 判定入口，见 §1.1.4 |
| 运行时手工创建的框架记录 | Odoo 实例 DB | metadata_first | 仅记录存在性与锚点，标 `open-question` 待源码核对 |
| ORM 推导关系 | Python 定义 | derived | `ir.model.inherit` / `ir.model.relation` 等 |
| 逻辑单元（python/view/owl） | 目标模块源码（Python/XML/JS） | code_first | 静态扫描结果；条件/效果按 §1.2.3 带锚点，运行时效果不声明 |

**红线**：`ir.model.access` / `ir.rule` / `res.groups` 只记录"权限定义在哪、是什么"，
**不声明权限正确**；UI 的 `invisible` / `readonly` / `groups` 不等于服务端授权。

---

## 5. 消费点：按需语义查询

```
lookup(kind=?, id=?, module=?, version=?, carrier=?) -> 带锚点的语义子图
```

- 按 module 分片存储，查询返回子图而非全量本体；
- `kind=logic` 可用 `carrier=python|view|owl` 过滤；返回触发点、条件、效果、绑定与锚点，不返回整段源码；
- 关系展开一跳/两跳可控，避免把整个依赖图灌入上下文；
- 未解析引用返回 `open-question` 与锚点，**不返回裸结论**；
- 首期只提供只读查询，不提供任何写入 Odoo 或改写源码的能力。

---

## 6. 工作包

| 工作包 | 内容 | 出口判据 |
|---|---|---|
| WP1 | M3 schema + 统一信封 + §1.1 模型白名单/排除清单 + 零依赖校验器 | §1.1.5 五类负例全部被拒绝；变异验证 |
| WP2 | 模型层投影（module/model/field/method/inherit） | `mrp` 试点节点全部带锚点且可重建 |
| WP3 | 框架记录层投影（§1.1.2 三类白名单）+ ownership 分类 | 每类至少 1 个真实节点；`code_first`/`metadata_first`/`derived` 均有样例；个人级与运行态负例被拒 |
| WP4 | 逻辑层投影专用提取器（Python / View / OWL），输出带锚点的逻辑单元 | 三类载体各有真实节点；§1.2.5 五类负例被拒；动态项标 `inference`/`open-question` |
| WP5 | `lookup` 消费点 + 按 module 分片 + 一跳/两跳展开（含 `carrier` / `kind=logic`） | 查询只返回相关子图；未解析项标 `open-question` |
| WP6 | CI 门禁 + 基准任务集 + 试点效果验证 | 哈希守卫通过；基准任务有前后对比证据 |

---

## 7. 验收判据（可验证收益，不写死数字）

**基准任务集**：一组固定的"理解 Odoo 应用"问题，例如：

- `mrp.production` 有哪些继承字段与方法？锚点在哪？
- 场景 `SCN-MRP-001` 涉及哪些 view、action 与 ACL？
- 某个 group 被哪些 record rule 约束？
- `SCN-MRP-001` 的按钮触发哪些 Python 条件与状态写入？
- 某视图的 `invisible` 条件绑定了哪个字段，按钮调用哪个方法？
- 哪个 OWL 组件通过 RPC 调用了 `mrp.production.action_start`？

**对比口径**：同一任务集，分别在「无本体」与「有本体」条件下测量：

1. 工具调用次数；
2. 上下文 token 消耗；
3. 锚点命中率（回答引用的 `file:line` 是否真实存在）；
4. 首次回答正确率（由固定判定表裁决，不靠主观评分）。

**门槛**：门槛值从基线实测推导后写入，禁止预先硬编码（FDE 反假绿纪律）。
若测量显示无收益，本计划结论为「不扩大试点」，而不是继续堆本体。

---

## 8. CI 门禁

- 本体重建哈希 == 入库哈希（漂移即失败）；
- 每个节点有 `id / kind / ownership / source_anchor / evidence`；
- 记录所属模型在 §1.1.2 白名单内，§1.1.3 排除清单与 §1.1.5 负例均被拒绝；
- `source_anchor` 指向的文件存在且行号非空；
- `inference` 节点有推导链，`open-question` 节点未被伪装成事实；
- `logic` 节点具备 §1.2.3 必需字段；条件/效果有源码锚点；§1.2.5 负例被拒；
- `compileall`、全量 `pytest`、注册表幂等、Gherkin 门禁保持全绿。

---

## 9. 明确不做

- 不建独立语义 ID 体系、不建五套本体子系统；
- 不处理业务数据记录，不描述业务状态/角色/工作空间语义（但按 §1.2 描述逻辑的实现结构）；
- 不落完整 AST/CFG，不执行或求值条件表达式，不把静态投影声明为运行时事实；
- 不引入 RDF/OWL/图数据库/推理机；不复制 Odoo 的 Registry、ORM、view 引擎、安全引擎；
- 不改 `capabilities: {}`，不改 `6+3+4+N` 骨架；
- 不做运行时 migration / activation / self-bootstrap；
- 不把 UI 可见性当授权，不把权限定义位置当权限正确性结论；
- 不手工编辑本体产物。

---

## 10. 风险与开放项

1. **框架记录的双重身份**：同一张 `ir.ui.view` 行既可能是 XML 投影，也可能是手工权威；
   首期对无法判定者标 `metadata_first + open-question`，不强行归类。
2. **版本差异**：17/18/19 的表结构与字段可能不同；版本敏感声明必须有源码或官方文档锚点，
   无证据不写跨版本结论（沿用 `version-compatibility.md` 纪律）。
3. **试点选择**：建议 `mrp`（已有 `SCN-MRP-001/002` + `CU-MRP-008/009` + SEED-013 引用），
   可在一次试点内验证"场景 → 能力 → 模型 → 框架记录 → 逻辑实现"全链。
4. **收益归因**：token 与工具调用下降需排除任务集变简单造成的假象；基准任务集固定后不得中途替换。
5. **OWL 跨版本差异**：17/18/19 的组件 API 与 RPC 形态不同；无逐版本源码锚点不得写跨版本结论。
6. **逻辑节点膨胀**：若把每个表达式都建成节点将淹没上下文；按 §1.2.1 最小充分语义门槛收敛，
   试点后按实测 token 与命中率决定是否扩围，无收益则不扩大。

---

## 11. 技术实现与构建流程

### 11.1 技术选型：零新增依赖

- Python 3 标准库即可：`ast` / `json` / `hashlib` / `pathlib` / `xml.etree.ElementTree` / `re` / `dataclasses` / `argparse` / `linecache`；
- **不引入** RDF/OWL、图数据库、推理机、JS 解析器；**不 import Odoo、不连数据库、不执行或求值任何表达式**；
- 复用仓库已验证的模式：
  - `scripts/discover_capabilities.py`：锚定 `__file__`、仓库相对路径、重建不刷新时间戳、扫描为 0 即失败；
  - `scripts/mine_odoo_source.py`：只认 `ODOO_SOURCE_PATH`，不写死源码路径；
  - `scripts/check_docs_baseline.py`：`--self-test` 与 CI 守卫双入口；
  - `.github/workflows/ci.yml`：入库哈希与重建哈希比对，漂移即失败。

### 11.2 产物布局：生成物入库，禁止手改

```text
ontology/
  schema.json              # M3 schema，带 schema_version
  manifest.json            # source_commit / odoo_versions / counts / sha256 / _generated
  modules/<module>.json    # 按模块分片，mrp 先试点
  index/by_model.json      # 派生索引，可由分片重建
```

- 每个产物带 `_generated: true` / `_do_not_edit: true`；
- 路径一律仓库相对，不写时间戳、不写机器绝对路径；
- 稳定序列化：所有列表排序后 `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`；
- `source_commit` 取本仓库 HEAD；Odoo 源码版本能从其 git 仓库取则记 revision，取不到写 `open-question`，不伪造。

### 11.3 构建阶段：build 是纯函数

`build(事实源, scope, version) -> 产物字节`；同一输入必须得到同一哈希。

| 阶段 | 处理 | 输出 | 失败模式 |
|---|---|---|---|
| discover | 读 `ontology/scope.json`（模块白名单 + 版本），枚举目标模块与 `__manifest__.py` 依赖 | 模块清单 | 模块缺失或版本未声明 → 退出，不写空产物 |
| extract | Python AST / View XML / OWL 扫描 / 框架记录 XML-CSV 四个提取器 | 带锚点的原始节点 | 解析失败 → 生成 `open-question` 占位 + 诊断，不静默跳过 |
| link | 按技术名**精确**匹配（model / xmlid / method / component），建立 typed edges | 节点 + 边 | 模糊匹配一律不连；未解析标 `open-question` |
| validate | schema + §1.1 白名单 + §1.2.5 负例 + 锚点存在性 + ID 唯一性 | 干净节点集 | 硬错误 exit 1；软错误降级 evidence，不伪装事实 |
| emit | 排序、分片、写 manifest 与 sha256 | `ontology/` 产物 | 空产物或哈希不一致 → exit 1 |

### 11.4 提取器实现要点

- **Python**：`ast.parse` 解析源码，不 import。采集 `ir.model` 类与字段、方法、装饰器（`@api.constrains` / `@api.depends` / `@api.onchange`）、条件表达式、字段写入、`self.env[...]` 与 `super()` 调用；每个节点带 `lineno` 与源码片段。继承/覆盖链无法静态确定 → `inference` 附推导链。
- **View**：`ElementTree` 解析 XML 数据文件；`ir.model.data` 语义从 `<record id=... model=...>` 与 `<data noupdate>` 读取；继承点从 `<field name="inherit_id" ref="...">` 读取；modifier / domain / context / button 原样保存。`ElementTree` 不提供行号，用轻量行索引把 xmlid 映射到源码行。
- **OWL**：无 JS 解析器依赖，做定向扫描——组件类、`xml` 模板、`rpc(` 调用、模板事件属性；只记录可定位的绑定，动态绑定标 `open-question`；17/18/19 差异由版本矩阵门禁。
- **框架记录**：只采集 §1.1.2 白名单模型；ownership 由 `ir.model.data` 的 `module/name/noupdate` 或 `__custom__` 判定；group / ACL / rule 只记定义，不记执行效果。

### 11.5 锚点格式与确定性

- Python：`addons/mrp/models/mrp_production.py:L512`；
- View：`addons/mrp/views/mrp_views.xml:record:mrp.mrp_production_form_view`；
- OWL：`addons/mrp/static/src/...:L..`；
- 校验：文件存在、行号在范围内且该行非空；XML record 锚点还要校验对应 `id` 存在；
- 不变量：同一输入连续构建两次，产物逐字节一致；`manifest.sha256` 是全部分片规范化内容的哈希。

### 11.6 校验入口与 CI 接线

```bash
python scripts/build_ontology.py --self-test
python scripts/build_ontology.py --source "$ODOO_SOURCE_PATH" --out /tmp/ontology-rebuilt
python scripts/check_ontology.py --manifest ontology/manifest.json --out /tmp/ontology-rebuilt
```

- `build_ontology.py --self-test`：临时目录内跑正负例（越界模型、无锚点、未解析引用、空产物）；
- `check_ontology.py`：比对入库与重建哈希、计数、schema、负例拦截结果；
- CI 步骤接在注册表守卫之后、文档守卫之前；源码未配置时该步骤明确 skip 并标注 `open-question`，**不得假绿**。

### 11.7 消费接口

```bash
python scripts/ontology_lookup.py --model mrp.production --carrier python --hops 1 --version 18.0
```

返回带锚点的语义子图（触发点 / 条件 / 效果 / 绑定），不返回整段源码；
未命中返回 `open-question` 与已知锚点，不返回裸结论。首期只读，不提供任何写回能力。

### 11.8 降级矩阵

| 情况 | 处置 |
|---|---|
| `ODOO_SOURCE_PATH` 未配置 | CI 明确 skip 并记 `open-question`，不生成空本体、不假绿 |
| 模块缺失 / 版本未声明 | 构建失败退出 |
| 文件解析失败 | `open-question` 占位 + 诊断，其余节点继续 |
| 引用无法精确解析 | 不连边，标 `open-question` |
| 跨版本行为未核实 | 标 `open-question`，不写跨版本断言 |
| 白名单外模型或运行态记录 | 硬失败（§1.1.3 / §1.1.5） |

### 11.9 与工作包的映射

WP1 落地 §11.1/11.2/11.5；WP2 落地 §11.3 的 discover + 模型/框架记录提取；
WP3 落地 §11.4 的框架记录完整性；WP4 落地 §11.4 的三类逻辑提取器；
WP5 落地 §11.7 查询接口与 §11.3 的 link；WP6 落地 §11.6 CI 接线与基准任务验证。
