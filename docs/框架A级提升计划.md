# Capability Twin 框架 A 级提升计划

> **目标**：把当前六维判定（A− / B+ / B− / B / B− / A−）全部提升到 **A− 及以上**，且不存在未关闭的 P0/P1。
> **历史评审基线**：`docs/框架评审-2026-11-17.md`、评审时 worktree `f48b163`。
> **当前基线**：PR #12 合并提交 `331257b` + CI run `45954685180`，见 `docs/项目维护指南.md` §1（唯一事实源）。
> **口径**：本地只做静态检查；构建、全量测试与运行时冒烟统一由 CI 验证（用户明确约束）。
> **状态**：用户已同意方案；WP1~WP5 均已实施并经 CI 验收。§6 决策项采用保守默认并逐项标注。
> **治理 A+ 加固**：见 §8——把「一次性同步数字」升级为机制化防漂移守卫，避免再次出现基线滞后。

---

## 0. A 级的可验收定义

满足以下全部条件才算达到 A 级，缺一不可：

1. **六维全部 ≥ A−**：架构边界、工程完整性、运行可信度、交付规格、Odoo 实施、治理文档。
2. **无未关闭的 P0/P1**；P2 必须落入三态之一：`DONE` / `BLOCKED（写明外部依赖）` / `刻意不做（写明理由）`。
3. **状态不冒充证据**：顶层 `status=completed` 仅当所有步骤均有通过校验的证据；`delegated` 是显式的未完成状态。
4. **结论可回溯**：每条交付结论都有物理锚点（文件 + 行号 / `§x.y` / 场景 ID）与可复现验证命令。
5. **CI 全绿**：`compileall`、全量 `pytest`、注册表幂等、安装布局自检、硬编码路径守卫、BDD 门禁。
6. **文档与代码一致**：技能/agent 数、版本、模板数、测试基线均由代码或 CI 结果推导，不在文档里写死期望值。

**A 级刻意不做**（沿用 FDE 2.0 反博弈纪律，禁止靠这些项刷级）：FDE 成熟度 L1–L6、AI 乘数、加权总分/排名、价值流七阶段枚举、G0–G4 门禁状态机、运行时自动改写 `SKILL.md` / `AGENT.md`。

---

## 1. 差距快照

| 维度 | 当前 | 目标 | 阻断项 |
|---|---|---|---|
| 架构与边界 | A− | A | 2 个 Obsidian 离群技能；3 个意图技能重叠；`capabilities:{}` 与规划 P3 判据冲突 |
| 工程完整性 | B+ | A | 幂等/版本守卫缺失；测试基线未由 CI 复核；worktree 落后 `origin/main` 三个合并 |
| 运行可信度 | B− | A | `delegated` 仍是终态且无回填；`fde_checkpoint.recorded` 恒 `False` 且无消费方 |
| 交付与规格 | B | A | 6/16 模板缺证据字段；A-1~A-5 未闭环；8/13 SEED 能力无场景引用 |
| Odoo 实施 | B− | A | GAP-001 幂等键仅标签（P0）；GAP-003/005/006 未关闭 |
| 治理与文档 | A− | A | 规划文档滞后；基线未随合并更新；本计划尚无指针 |

---

## 2. 工作包

### WP1 · 运行态证据闭环（B− → A，最高优先）

> 这是其余工作包的前置：结果 schema 变更后，测试、文档与门禁都要跟随。

| 编号 | 动作 | 落点 |
|---|---|---|
| W1.1 | 定义 `StepEvidence` 契约：`{workflow_id, step, status, artifacts:[{path, anchor, kind}], fde_records:[{item, result, evidence}], produced_at}` | `skills/capability-twin-orchestrator/scripts/evidence_gate.py`（新增） |
| W1.2 | 实现 `StepEvidenceGate.validate(result, step_contract)`：校验产物存在且非空、必需锚点存在、FDE 9 条逐条有 `pass/fail/n/a + 证据` | 同上 |
| W1.3 | `execute_subagent()` 为每步附带 `evidence_contract`；`fde_checkpoint.recorded` 改由 gate 回填，不再恒 `False` | `scripts/main.py:1226` |
| W1.4 | 新增 `submit_step_evidence(workflow_id, step, evidence)`：宿主智能体提交证据 → gate 校验 → 通过后归一为 `success`，失败为 `failed`，未提交保持 `delegated` | `scripts/main.py` |
| W1.5 | `_workflow_outcome()` 只把「证据校验通过的 success」计入 `steps_completed`；`completed` 条件收紧为全部步骤证据通过 | `scripts/main.py:1377` |
| W1.6 | 增测试：无证据不得跃迁；缺 FDE 记录拦截；伪造锚点拦截；完整证据通过；重复提交幂等 | `tests/test_evidence_gate.py`（新增） |

**验收**：全 `delegated` 场景顶层为 `delegated` 且 `requires_semantic_execution=true`；提交合格证据后变 `completed`；提交残次证据保持 `partial`/`delegated`。

---

### WP2 · Odoo 写操作正确性与版本证据（B− → A）

| 编号 | 动作 | 落点 |
|---|---|---|
| W2.1 | **GAP-001**：执行器引入幂等账本 `artifacts/idempotency_ledger.json`，键 = 计划 ID + 动作序号 + 幂等键；`--apply` 前查账，命中即 `skipped` 并记原因；账本损坏 fail-closed | `skills/odoo-implementation/scripts/odoo_seed_executor.py` |
| W2.2 | **GAP-008**：新增守卫——能力卡「版本差异」行 ↔ 模板 `odoo_versions` 一致；账本重放行为 | `skills/odoo-implementation/tests/` |
| W2.3 | **GAP-005**：逐项核实 SEED-005/006/007/008/009/012/013 在 17/18/19 的版本状态，写入定义卡，无空白 | `skills/odoo-implementation/` 定义卡 + `references/version-compatibility.md` |
| W2.4 | **GAP-003**：补基础数据族 `.feature`（初始化 → 核对 → 冻结基线），建立 mrp 场景与 SEED 的引用关系；更新能力卡 G3 判据 | `skills/gherkin-bdd/features/` + SEED 卡 |
| W2.5 | **GAP-006/007**：规划文档状态行与文件引用改为实际产物；追加 P3 判据作废的决策记录 | `docs/odoo-implementation-skills-plan.md` |
| W2.6 | **GAP-004**：保持 `BLOCKED`，登记外部依赖；不得假设 20.0+ 跨版本零改动 | `skills/odoo-implementation/TODO.md` |

**验收**：TODO §2 无 `TODO` 状态项；GAP-004/007 为 `BLOCKED` 且有依据；执行器离线测试 + 新守卫 CI 全绿。

---

### WP3 · 交付物与 FDE 证据字段（B → A）

| 编号 | 动作 | 落点 |
|---|---|---|
| W3.1 | 为 6 份缺字段模板补「证据 / 溯源 / 验收」章节：`CONSULTANT_DISCOVERY_NOTE`、`BEST_PRACTICES_REPORT`、`CONSULTANT_CONF_GUIDE`、`GAP_ANALYSIS_REPORT`、`PURPOSE_AND_STRATEGY`、`CAPABILITY_ANALYSIS_REPORT` | `skills/template-processor/templates/deliverables/` |
| W3.2 | **A-1**：`GAP_ANALYSIS_REPORT` / `HANDOVER_MANIFEST` 增「价值三态（基线/目标/实测）+ 交付验收 ≠ 价值实现」说明级小节，**不新增必填字段** | 同上 |
| W3.3 | **A-5**：`CAPABILITY_UNIT_SPEC` 复用章节补「适用边界 + 验证证据 + 版本」，与 FDE `SKILL.md` §5.8 一致 | 同上 |
| W3.4 | **A-2**：`quality-gate` 与 `human-review-gatekeeper` 分别列工程质量/业务质量证据与「两门不得互相替代」判据 | 两技能包 + agent 指令 |
| W3.5 | **A-3**：定义 KB 回流消费点——只消费带 `approved_by` + `source_anchor` 的候选；`quality-gate` 检查复用元数据完整性 | `knowledge-manager` / `autonomous-evolution` + 决策记录 |
| W3.6 | **A-4**：登记为「刻意不做（无事实源）」，不实现 Lead Time / TTV 数字 | `docs/FDE-2.0对齐说明.md` §6 |

**验收**：16/16 模板具备证据字段；A-1~A-5 全部有「已解决 / 维持不做」登记；既有模板向后兼容。

---

### WP4 · 范围收敛与架构纯度（A− → A）

| 编号 | 动作 | 前置 |
|---|---|---|
| W4.1 | 删除或移出 `json-canvas`、`obsidian-bases` 两个与 Odoo 交付链无关的技能（需用户决策，见 §6-1） | 用户确认 |
| W4.2 | 意图三技能划界：保留 `intent-understanding` 为入口，另外两个并入其内部模块或写明边界；重建注册表 | 用户确认（§6-2） |
| W4.3 | 记录 `capabilities:{}` 保持空节点、规划 P3 判据作废的决策（GAP-007） | 用户确认（§6-3） |

**验收**：技能数变更同步 README / 维护指南 / 注册表；无零引用离群技能；连续重建注册表逐字节一致。

---

### WP5 · 工程基线与治理（A− → A）

| 编号 | 动作 | 落点 |
|---|---|---|
| W5.1 | 同步 worktree 到 `origin/main`（PR #9–#11 的脚本收敛、恢复、去厂商化），确认 `framework_paths.py` 与路径守卫仍通过 | 工作区 |
| W5.2 | CI 门禁固化：`compileall` + `pytest -q` + 注册表幂等 + 安装布局自检 + 硬编码路径守卫 + BDD 门禁 | CI 配置 |
| W5.3 | 维护指南 §1 基线表更新为合并后 merge commit 与 CI 测试数；§8 增加本计划指针 | `docs/项目维护指南.md` |
| W5.4 | 文档数字一致性扫描：技能数、agent 数、版本、模板数、测试数全部由代码/CI 推导 | README、维护指南、FDE 对齐说明 |

**验收**：CI 全绿；基线表与代码一致；无文档数字与代码不符。

---

## 3. 里程碑与依赖

| 里程碑 | 包含工作包 | 出口判据 |
|---|---|---|
| **M1 信任底座** | WP1 + W5.1 + W5.2 | 顶层状态不再把委派当完成；CI 可复现全部门禁 |
| **M2 写操作正确** | WP2 | GAP-001 P0 关闭；版本/场景证据闭合 |
| **M3 证据完整** | WP3 | A-1~A-5 全部关闭或登记维持不做 |
| **M4 纯度与基线** | WP4 + W5.3 + W5.4 | 六维全部 ≥ A−；无未关闭 P0/P1 |

WP1 是 M1 的硬前置；M2/M3 可并行但都依赖 M1 的证据 schema；M4 依赖 M2/M3 的数字定稿。

---

## 4. 验证门禁（CI 执行，本地只做静态检查）

```bash
# 静态检查（本地允许）
python3 -m compileall -q skills *.py

# 以下由 CI 执行
python3 -m pytest -q
python3 scripts/discover_capabilities.py
R=skills/capability-twin-orchestrator/capability_registry.json
H1=$(shasum -a 256 "$R" | cut -d' ' -f1)
python3 scripts/discover_capabilities.py >/dev/null
H2=$(shasum -a 256 "$R" | cut -d' ' -f1)
[ "$H1" = "$H2" ] || exit 1
python3 skills/capability-twin-orchestrator/scripts/framework_paths.py
python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate skills/gherkin-bdd/features
```

附加断言：结束态为 `completed` 的工作流，其 `steps_completed` 必须等于 `steps_total` 且全部步骤带通过校验的证据；任何 `delegated` 步骤存在时顶层不得为 `completed`。

---

## 5. 风险与约束

- **不扩大运行边界**：语义执行仍由宿主智能体完成，本计划只补“证据回填 + 校验”，不把框架改造成独立执行引擎（见 §6-4）。
- **外部依赖不是代码缺口**：GAP-004（Odoo 20.0+ 通道）在官方 API 文档可用前保持 `BLOCKED`，不计未关闭 P1。
- **不得靠改文档掩盖落差**：文档与代码不符时以代码为准，落差登记到对应 TODO。
- **禁止硬编码期望值**：守卫测试不得写死版本号或测试数，避免重演版本假绿。

---

## 6. 需用户确认的决策项

1. `json-canvas` / `obsidian-bases`：用户同意方案后按**保守默认归档到 `docs/retired/`**执行
   （不删除、不被 `npx skills --all` 发现；如需彻底删除可再确认）。**已执行。**
2. 三个意图技能：按**保留三者并明确单向边界**执行；入口为 `intent-understanding`，
   `enhanced-intent-understanding` 只在需要置信度推导时使用，`intent-to-action-mapper`
   只在 `mapping_ready=true` 后使用。**已执行。**
3. GAP-007：按**正式作废规划 P3 判据**执行；`capabilities` 保持空 `{}` 并由测试锁定。**已执行。**
4. 运行态方案：按**证据回填 API + 校验门禁**执行，不把框架改成独立执行引擎。**已执行。**
5. A 级口径：按**六维全部 ≥ A− 且无未关闭 P0/P1** 执行；P2 允许 `BLOCKED（外部依赖）`。**已执行。**

---

## 7. 实施记录（2026-11-27）

| 工作包 | 结果 |
|---|---|
| WP1 | 新增 `scripts/evidence_gate.py`、`submit_step_evidence()`；`_workflow_outcome()` 只计证据通过的 `success`；新增 `tests/test_evidence_gate.py`；FDE `fde_checkpoint.recorded` 由门禁回填 |
| WP2 | 执行器幂等账本 + `CT-011` fail-closed；13/13 能力卡版本行；新增 `base_initialization.feature`；规划文档与 TODO 同步；GAP-004 保留 `BLOCKED` |
| WP3 | 16/16 模板具备证据字段；A-1/A-2/A-3/A-5 已解决，A-4 登记维持不做；新增 KB `approved_only` 消费点 |
| WP4 | 2 个 Obsidian 技能归档到 `docs/retired/`；注册表降为 20 skills / 18 agents；三意图技能边界写明 |
| WP5 | 快进到 `origin/main` `375c472`；新增 `.github/workflows/ci.yml`；更新维护指南基线与 `.gitignore`；全仓 `compileall` 通过 |

### CI 验收结果（2026-11-27，PR #12）

| 门禁 | 结论 | 证据 |
|---|---|---|
| `compileall` / 全量 `pytest -q` | PASS | CI run `45954685180`；实测数字见 `docs/项目维护指南.md` §1 |
| 注册表重建幂等（入库哈希 vs 重建哈希） | PASS | 同上，`framework-ci/gate` 单 check SUCCESS |
| 安装布局自检 / 硬编码路径守卫 | PASS | 同上 |
| Gherkin 门禁 | PASS | 3 features / 9 scenarios / 40 steps，0 errors / 0 warnings |

本地遵循用户约束未运行构建或全量测试；以上数字来自 CI，仓库内只在 `docs/项目维护指南.md` §1 登记。

---

## 8. 治理 A+ 加固（2026-11-27）

> A 级要求「文档与代码一致」；A+ 要求「不一致在 CI 阶段被自动拒绝」，不依赖人工记得同步。

| 编号 | 动作 | 落点 |
|---|---|---|
| G+1 | 基线提交、测试数只在 `docs/项目维护指南.md` §1 出现；其它文档只写指针 | `MAINTENANCE.md`、`TODO.md`、本计划 |
| G+2 | 文档守卫校验 §1 基线提交为 HEAD 祖先、测试数等于 CI 传入值 | `scripts/check_docs_baseline.py` + CI |
| G+3 | 全仓扫描「待 CI 复核 / 待 CI 验收」等过期时态词与 GAP-001 旧状态表述 | 同上 |
| G+4 | 守卫自带 `--self-test`，用临时目录验证解析与扫描逻辑，不增加 pytest 用例数 | 同上 |
| G+5 | 决策与缺口三态可回溯：A-4 维持不做、GAP-004 BLOCKED、§6 五项均已执行 | `docs/FDE-2.0对齐说明.md` §5/§6、`TODO.md` |

**A+ 验收判据**：CI 全绿且文档守卫在「改测试数不同步文档」「写入过期时态词」「基线哈希非祖先」三类注入下均失败；
本轮 CI 复核完成后，治理与文档由 B+ → A+。
