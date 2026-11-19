# odoo-implementation 维护规范

本文件是 `skills/odoo-implementation/` 的**维护入口**：定义文件职责、变更流程、发布清单与禁止事项。它随技能包安装（`npx skills`），是本包维护事实源；与 `docs/odoo-implementation-skills-plan.md` 冲突时，以本文件与实际代码为准。

根本约束不变：**不颠覆 Capability Twin 骨架**。不新建平行体系、不改 `6+3+4+N` 编号、不迁移既有文件、不改既有技能契约。

---

## 1. 文件职责矩阵

| 文件 | 职责 | 允许的变化 | 变更时必须同步 |
|---|---|---|---|
| `SKILL.md` | 技能入口、frontmatter 契约、能力目录（SEED-001~013）、CLI | 版本、能力卡、CLI 说明 | 版本号 → 注册表；能力卡 → 索引表；CLI → 执行器实际参数 |
| `TODO.md` | 能力缺口 backlog：现状快照、分级缺口、已否决项、维护规则 | 增删 GAP 条目、状态流转、归档 | 缺口落地涉及文件/版本变更时 → 本表与 `SKILL.md` §2；不与规划文档各写各的 |
| `schemas/odoo-implementation.schema.json` | 机器契约，`additionalProperties: false` | `ct_` 字段、枚举、领域规则 | `references/contract-guide.md`、`scripts/validate_odoo_manifest.py`、`tests/test_validate_odoo_manifest.py` |
| `scripts/validate_odoo_manifest.py` | 零依赖契约校验（validate / list） | 校验逻辑 | schema 同名字段规则、正负例测试 |
| `scripts/odoo_seed_executor.py` | 种子动作**单一执行出口**，版本感知 | 通道、版本矩阵、过滤逻辑 | `references/version-compatibility.md`、SKILL.md CLI、执行器测试、模板 |
| `scripts/odoo_onboarding.py` | 项目 onboarding **编排层**：profile 解析、依赖排序、逐阶段委派、链式 fail-closed | 排序规则、profile 契约、门禁；**不得新增 RPC/凭据逻辑** | SKILL.md §4 CLI/§6.4、onboarding profile 模板、编排器测试；执行器语义变更时同步委派调用 |
| `references/contract-guide.md` | 字段语义与迁移指引 | 语义说明 | schema 与校验脚本 |
| `references/error-taxonomy.md` | 10 类失败分类与重试禁令 | **仅随分类体系变更** | 执行器 issue code、所有引用它的文档 |
| `references/evidence-levels.md` | 证据分级与 G2/G3/FDE 边界 | **仅随证据体系变更** | SKILL.md 证据边界表述 |
| `references/version-compatibility.md` | 17/18/19 初始化差异、通道矩阵、动作版本契约、核心服务方法差异 | 核实过的版本差异 | 执行器 `SUPPORTED_VERSIONS`/通道矩阵/写方法白名单/JSON-2 映射、模板版本分化、SKILL.md 版本敏感卡（SEED-001/003/004） |
| `templates/project/*.json` | 动作计划与项目状态模板 | 按业务方确认的数据填充结构 | 对应测试断言、SKILL.md 目录契约 |
| `tests/*.py` | 离线自测（不连真实 Odoo） | 正负例、变异验证 | 被测代码 |

不变量：**结构与职责一一对应**。新增文件必须在本表登记；本表不登记的文件不得存在。

---

## 2. 变更流程

### 2.1 新增/修改种子能力（SEED-xxx）

1. 在 `SKILL.md` §6.1 索引表追加一行，ID 连续、不复用；§6.2 增加同名定义卡（业务目标/前置/步骤/产物/G2/G3/边界）。
2. 若该能力**版本敏感**（如 SEED-004 计量单位），在卡内加「版本差异」行，并在动作计划模板中用 `odoo_versions` 标注各版本分支。
3. 在 §6.3 依赖顺序中声明它与既有能力的前后关系。
4. 无配套 `.feature` 的能力，G3 判据必须写「需 `.feature` 覆盖；当前无配套场景，不得声称场景通过」；场景事实源始终是 `gherkin-bdd` 的 `.feature`，本包只引用路径。
5. 执行器不内置业务动作；任何初始化动作只能写入 `templates/project/` 的计划，由执行器单一出口执行。

### 2.2 修改 `ct_` 契约字段

1. schema 必须先改（`additionalProperties: false` 不可放宽）。
2. `validate_odoo_manifest.py` 同步实现同名字段规则；领域规则（如 `ct_module` 仅在 `ct_layer=module` 允许）必须在 schema `if/then/else` 与脚本 `validate_manifest()` **两处**同步。
3. `contract-guide.md` 更新语义；`tests/test_validate_odoo_manifest.py` 增正负例并做变异验证（去掉检查必须让用例变红）。
4. 新增字段仍遵循「全部可选」：既有 21 个技能无新字段时必须判 `skipped`，不是 `error`。

### 2.3 修改执行器

1. 通道、版本矩阵、凭据要求以 `references/version-compatibility.md` 为事实源；执行器不得出现与文档不一致的版本判断。
2. 新增通道必须定义：支持的版本范围、必需环境变量、dry-run 行为、错误分类映射、退出码。
3. 所有外部写操作必须带 `idempotency_key`；缺键判 `CT-007 blocked`，且不得自动重试。
4. 凭据只能从环境变量读取，禁止写入动作计划、日志或报告。
5. 测试必须全离线：注入假 `transport` / `runner`，绝不连真实 Odoo。

### 2.4 版本升级（SKILL.md `version`）

本包版本语义：`0.x.y` 中 `x` 为能力批次（新增能力族/通道/契约字段），`y` 为修订（文档修正、错误修复）。

**版本升级必须同步注册表**——这是曾经的真实缺陷：SKILL.md 升至 0.4.0 而注册表仍停 0.1.0，因守卫硬编码旧值而全绿。

1. 修改 `SKILL.md` frontmatter `version`。
2. 运行 `python3 discover_capabilities.py` 重建注册表。
3. 确认 `tests/test_registry_integration.py::test_04` 通过（该测试已从 SKILL.md 动态读取版本，漂移即失败）。
4. 禁止在守卫测试中硬编码期望版本值。

### 2.5 新增 Odoo 大版本支持

1. 执行器 `SUPPORTED_VERSIONS` 与 `normalize_version()` 增加版本。
2. `version-compatibility.md` 增加经核实的通道矩阵与模型/字段差异证据；无证据的差异不得写入。
3. 受影响的动作在模板中按 `odoo_versions` 分化；不确定的字段宁可标注「需 staging 验证」，不得假设跨版本零改动。
4. SKILL.md frontmatter `ct_odoo_versions` 与 §6 相关能力卡同步。

---

## 3. 发布前检查清单（全部通过才可提交 PR）

```bash
# 1. 契约校验：本包 SKILL.md 必须 validated、无 issue
python3 skills/odoo-implementation/scripts/validate_odoo_manifest.py \
  skills/odoo-implementation/SKILL.md

# 2. 全量回归：基线不得低于当前 passed 数（见 §5）
python3 -m pytest -q

# 3. 注册表幂等：连续重建，哈希必须一致（用哈希而非 git diff，
#    否则会把「尚未提交的合法版本更新」误判为不幂等）
R=skills/capability-twin-orchestrator/capability_registry.json
H1=$(shasum -a 256 "$R" | cut -d' ' -f1)
python3 discover_capabilities.py >/dev/null
H2=$(shasum -a 256 "$R" | cut -d' ' -f1)
[ "$H1" = "$H2" ] && echo "幂等 PASS" || echo "幂等 FAIL"

# 4. 模板 dry-run：按版本验证过滤，不连 Odoo
python3 skills/odoo-implementation/scripts/odoo_seed_executor.py \
  --odoo-version 18.0 --channel rpc \
  --plan skills/odoo-implementation/templates/project/base-data-actions.template.json < /dev/null
# 期望：status=pass、executed_count=6、skipped 1 条 19 专属

python3 skills/odoo-implementation/scripts/odoo_seed_executor.py \
  --odoo-version 19.0 --channel rpc \
  --plan skills/odoo-implementation/templates/project/base-data-actions.template.json < /dev/null
# 期望：status=pass、executed_count=5、skipped 2 条 17/18 专属、1 条 rpc deprecated warning

# 5. 结构一致性：索引条目数 == 定义卡数，SEED ID 连续无缺
grep -c '^| `SEED-' skills/odoo-implementation/SKILL.md
grep -c '^#### SEED-' skills/odoo-implementation/SKILL.md
```

补充人工核对：本文件 §1 文件职责矩阵与实际目录一致；新增文件已进入矩阵；所有对外展示材料未出现内部技术细节（见 §4）。

---

## 4. 禁止事项

1. **禁止硬编码绝对路径**：新文件自动受 `tests/test_no_hardcoded_paths.py` 守卫；源码路径只认环境变量（如 `ODOO_SOURCE_PATH`）。
2. **禁止五层能力链**：`ct_layer` 保持四层 `router/core/shared/module` 分类标签；不得建立物理目录层级；注册表 `capabilities` 节点保持为空。
3. **禁止假绿守卫**：测试断言不得硬编码会随源码变化的值（如版本号）；必须从事实源动态读取。
4. **禁止技术细节外泄到对外展示页**：Odoo 模块 `static/description/index.html` 与 `__manifest__.py` 的 `description` 属对外口径，只写业务价值、痛点、能力、兼容性、支持方式；严禁内部模型名、`ct_` 字段、脚本名、Sprint/SEC 编号、版本迭代史、测试数量、Gherkin/字段/事件等实现术语。技术细节只放本包内部文档（SKILL.md、references、ARCHITECTURE/ROADMAP/FAQ 等）。
5. **禁止 FSCR 或任何外部框架印记**：本包文档与交付物不得残留对标框架的专有名词或编号。
6. **禁止证据越级**：契约校验通过只等于 G2/E1-E2；不得表述为 G3 场景通过或价值实现（E4/E5）。
7. **禁止直接推送 main**：所有变更经特性分支 PR，用 `--merge --match-head-commit` 合并；HTTPS 代理不稳定时用 SSH 直连推送特性分支。

---

## 5. 当前基线（随版本更新）

| 项 | 值 |
|---|---|
| 技能包版本 | 0.4.0 |
| 支持 Odoo 版本 | 17.0 / 18.0 / 19.0 |
| 种子能力 | SEED-001~013 |
| 注册表 | skills 22 / agents 18 / capabilities 空 |
| 全量测试 | 210 passed（基线 `3df9f5f`） |
| 执行器测试 | 15 项，全离线 |

基线更新规则：仅在合并进 main 后更新本表，并注明对应 merge commit。
