# Gherkin BDD — 快速上手

**一句话定位**：把 Capability Twin 的业务场景、验收标准、UAT 用例收敛为一份 `.feature`，
由同一份文本派生交付文档与自动化测试用例。

## 三个命令起步

在仓库根目录执行：

```bash
# 1. 校验所有业务场景（CI 门槛，零依赖，退出码 0/1）
python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate skills/gherkin-bdd/features --summary

# 2. 由规格派生人工验收脚本与追溯矩阵
python3 skills/gherkin-bdd/scripts/gherkin_gate.py uat    skills/gherkin-bdd/features -o capability_twin_runs/uat
python3 skills/gherkin-bdd/scripts/gherkin_gate.py matrix skills/gherkin-bdd/features -o capability_twin_runs/scenario_matrix.json

# 3. 生成自动化测试步骤桩（pytest-bdd 风格，可直接被 pytest 收集）
python3 skills/gherkin-bdd/scripts/gherkin_gate.py steps  skills/gherkin-bdd/features -o capability_twin_runs/steps
```

本轮实测：`2` 个功能、`5` 个场景、`21` 个步骤，`errors=0 / warnings=0`，退出码 `0`。

## 已在流水线内执行

不必手工跑命令：编排器 `capability-twin-orchestrator` 会在三个边界自动调用门禁
（适配层 `skills/capability-twin-orchestrator/scripts/bdd_gate.py`）：

| 边界 | 行为 |
|---|---|
| 工作流 preflight | 本模块 `.feature` 有 `error` → 整条流水线返回 `blocked`，不进入分析 |
| Step 10 → 11 | 校验并派生 UAT / 步骤桩 / 矩阵；`fail` 立即中止，不打包 |
| 交付包渲染 | 场景变量由规格注入；未通过则跳过 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT` |

`quality-gate` 也新增了 `check_type: scenario_spec`，与命令行判据完全一致。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 能力契约、标签体系、输出契约、挂载点 |
| `references/ubiquitous-language.md` | 统一语言词表（业务词 ↔ Odoo 对象、禁用别名与技术黑话） |
| `references/authoring-rules.md` | zh-CN 方言、编写规则、19+1 条校验码、反模式、DoR 清单 |
| `features/<模块>/*.feature` | 业务场景唯一事实源 |
| `scripts/gherkin_gate.py` | 解析 / 校验 / 生成（纯标准库） |
| `tests/test_gherkin_gate.py` | 23 项自测，覆盖正例与每条规则的违规检出 |
| `steps/README.md` | 步骤定义与 pytest-bdd / behave 执行说明 |
| `INTEGRATION_GUIDE.md` | 工作流挂载、质量门、CI、迁移路径 |

## 五条硬规则

1. 文件首行 `# language: zh-CN`，全中文关键字，禁止英文混写。
2. 场景只用词表里的标准业务词，禁止模型名、字段名、方法名等实现术语。
3. 每个场景必填 `@ct-id` / `@ct-unit` / `@ct-module` / `@ct-gate`，编号全局唯一。
4. 一份 `.feature` 只写一次；UAT 表格、步骤桩、追溯矩阵全部由工具生成，不手工复制。
5. `validate` 有 `error` 时拒绝派生任何交付物；warning 只记录不阻断。

## 示例

```gherkin
# language: zh-CN
@ct-module=account
功能: 发出商品的收入与成本配比
  作为 财务负责人
  我希望 发货未开票时收入暂不确认
  以便 符合中国企业会计准则的配比要求

  @ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G2
  场景: 发货未开票时确认发出商品
    假如 销售订单「SO-001」已确认，商品「A」的可用量为 10 件
    当 仓库按销售订单发货，发出商品「A」10 件且尚未开票
    那么 该批商品计入「发出商品」10 件
```

完整规格见 `features/account/shipped_not_invoiced.feature` 与 `features/mrp/mo_completion_posting.feature`。

## 边界

- 本能力单元**不内置** BDD 执行器；`pytest-bdd` / `behave` 由项目按需安装。
- 生成步骤桩不等于测试通过；未实现的步骤会显式抛 `NotImplementedError`。
- 自动化场景通过 = 工程完成（G2），不等于业务验收（G3），更不等于价值实现。
