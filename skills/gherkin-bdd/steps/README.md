# 步骤定义（Step Definitions）接入说明

本目录只放接入说明。生成的步骤桩属于**运行时产物**，默认输出到 `capability_twin_runs/`（已由 `.gitignore` 排除），不入库。

## 1. 生成

```bash
# pytest-bdd 风格（主推）
python3 skills/gherkin-bdd/scripts/gherkin_gate.py steps skills/gherkin-bdd/features \
  -o capability_twin_runs/steps

# behave 风格
python3 skills/gherkin-bdd/scripts/gherkin_gate.py steps skills/gherkin-bdd/features \
  -o capability_twin_runs/steps_behave --style behave
```

生成规则：

- 按「步骤类型 + 步骤文本」去重，同一句话在多个场景中只生成一个函数。
- 场景大纲的 `<占位符>` 转成 `{占位符}`（`parsers.parse` 语法），并成为函数参数。
- 每个函数体都是 `raise NotImplementedError(...)`：**未实现的步骤会显式失败，不会静默通过**。
- 步骤文本来自 `.feature`，请勿手工编辑；需要改句子时改规格并重新生成。

## 2. pytest-bdd 执行（主推路径）

生成文件形如 `test_<module>_<feature>_pytest_bdd.py`，其中已包含：

```python
from pytest_bdd import given, when, then, parsers, scenarios

scenarios('../../skills/gherkin-bdd/features/account/shipped_not_invoiced.feature')
```

`scenarios()` 把 `.feature` 中的场景注册为 pytest 测试用例，因此**无需再写一份测试清单**。

```bash
pip install pytest-bdd
# 在仓库根目录执行（相对路径基于生成文件所在目录）
pytest capability_twin_runs/steps -q
```

实现步骤时，把桩函数体替换为真实断言。示例：

```python
@given(parsers.parse('销售订单「SO-001」已确认，商品「A」的可用量为 10 件'))
def step_003():
    order = sales_order_fixture("SO-001")
    assert order.confirmed is True
    assert available_qty("A") == 10

@then(parsers.parse('该批商品计入「发出商品」10 件'))
def step_005():
    assert shipped_not_invoiced_balance("A") == 10
```

建议：

- 用 pytest fixture 提供账套、会计期间、商品主数据，保证每个场景可独立执行、不依赖顺序。
- 步骤定义只做「业务语言 → 系统断言」的翻译；业务规则写在被测代码，不写在步骤里。
- 参数化场景用 `parsers.parse` 的函数参数接收 `<占位符>` 值，注意做类型转换。

## 3. behave 执行

behave 的约定是 `features/*.feature` + `features/steps/*.py`。生成的 `steps_*.py` 使用
`use_step_matcher("parse")`，把文件放入 behave 的 `features/steps/` 目录后执行：

```bash
pip install behave
# 需把 .feature 放在 behave 的 features 根（或用软链接），再执行
behave <features_dir> --no-capture
```

由于本仓库按 `features/<odoo_module>/` 分目录组织规格，**pytest-bdd 是更省适配的路径**；
behave 模式主要用于已有 behave 工程复用步骤定义。

## 4. 证据与判据

| 层级 | 命令 | 判据 |
|---|---|---|
| L1 规格门禁 | `gherkin_gate.py validate ...` | error=0，退出码 0 |
| L2 场景执行 | `pytest capability_twin_runs/steps -q` | 全部用例通过，且无跳过/未实现桩 |
| G3 人工验收 | 由 `uat` 生成的脚本签字 | 业务方裁定，独立于自动化结果 |

> 生成步骤桩、UAT 表格或追溯矩阵**都不构成** L2 证据。
> 自动化通过 = 工程完成（G2）；交付验收 ≠ 价值实现（FDE 2.0 §5.5）。
