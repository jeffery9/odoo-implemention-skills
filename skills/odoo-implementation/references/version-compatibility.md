# Odoo 版本兼容性（初始化方式差异）

本文件记录 `17.0` / `18.0` / `19.0` 三个受支持大版本在**初始化方式**上的差异，供种子能力动作计划选用通道与字段。执行器 `scripts/odoo_seed_executor.py` 已把这些差异固化为可执行的契约：通道与版本兼容矩阵、动作级 `odoo_versions` 过滤、fail-closed 校验。

## 1. 通道选择矩阵

| 通道 | 17.0 | 18.0 | 19.0 | 凭据 | 说明 |
|---|---|---|---|---|---|
| `rpc` | 推荐 | 推荐 | 可用但 deprecated（warning） | `ODOO_URL/DB/USER/PASSWORD` | XML-RPC `/xmlrpc/2/common` + `/xmlrpc/2/object` |
| `json2` | 不支持（CT-003 error） | 不支持（CT-003 error） | 推荐 | `ODOO_URL/DB/ODOO_API_KEY` | JSON-2 `POST /json/2/<model>/<method>` + bearer key |
| `shell` | 可用 | 可用 | 可用 | 同上（RPC 凭据） | `odoo shell`，`shell_code` 必须按目标版本模型/字段编写 |

依据：Odoo 官方外部 API 文档将 `/xmlrpc`、`/xmlrpc/2`、`/jsonrpc` 在 19.0 标记为 deprecated，并引入 JSON-2 作为替代；XML-RPC/JSON-RPC 计划于 22.0（自托管/Odoo.sh）与 Online 21.1 移除。API key 自 14.0 起支持，可代替密码用于 RPC 调用。

版本与通道的匹配由 `validate_channel_version()` 校验：`json2` 只能配 `19.0`；`rpc` 配 `19.0` 产生 warning 但不阻断（兼容存量）。

## 2. 基础数据模型差异

### 2.1 计量单位（SEED-006）—— 硬差异，必须按版本分化

| 项 | 17.0 / 18.0 | 19.0 |
|---|---|---|
| 单位分类 | `uom.category` 存在 | **模型移除** |
| 单位记录 | `uom.uom` + `category_id` | `uom.uom` + `relative_uom_id` |
| 换算字段 | `uom_type`（reference/smaller/bigger）+ `factor` / `factor_inv` | `uom_type` / `factor_inv` 移除，改用 `relative_factor` |
| 基准单位 | 每个 category 一个 reference 单位 | 参考单位指向自身（`relative_uom_id = self`） |

动作计划必须用 `odoo_versions` 标注两套动作；执行器只执行与 `--odoo-version` 匹配的分支。模板 `templates/project/base-data-actions.template.json` 已按此分化。

依据：Odoo 18→19 迁移说明与社区实测均确认 `uom.category` 被删除、`factor_inv → relative_factor`、以 `relative_uom_id` 直连参考单位。

### 2.2 币种 / 汇率 / 国家 / 语言（SEED-007~010）—— 字段名稳定

`res.currency`、`res.currency.rate`、`res.country`、`res.lang` 在 17/18/19 的上述字段（`symbol`、`decimal_places`、`rate`、`name`、`code`、`active`、`date_format`）未发生破坏性改名，动作计划可用同一份定义。但以下约束仍成立：

- 币种小数位、符号与汇率来源属业务/财务判断，不由执行器决定。
- 语言的激活与翻译质量需业务方确认；执行器不提供机器翻译。
- 不内置全量国家/行政区划数据；仅导入业务方确认的清单。

> 版本升级仍可能带来字段级微调。动作计划在执行前应于目标版本的 staging 环境用 dry-run + 小批量 `--apply` 验证，不得假设跨版本零改动。

## 3. 动作级版本契约

动作可声明 `odoo_versions`（大版本数组）：

```json
{
  "method": "create",
  "model": "uom.uom",
  "odoo_versions": ["19.0"],
  "args": [{"name": "米", "relative_uom_id": 1, "relative_factor": 1.0}],
  "idempotency_key": "SEED-006:19:uom.uom:米"
}
```

语义：

1. 未声明 `odoo_versions` → 通用动作，所有版本执行。
2. 声明且 `--odoo-version` 命中 → 执行。
3. 声明且版本不匹配 → 跳过，计入报告 `skipped_actions`，不产生 issue。
4. 声明了版本却未给 `--odoo-version` → `CT-003` error，零执行（fail-closed），防止在错误版本上跑错初始化动作。

## 4. 不在本文件范围

- 具体业务数据的取值（由业务方确认，属 G3/FDE 验收范畴）。
- 20.0 及以后版本的支持（当前仅 17/18/19，超出版本改用 `--odoo-version` 会被拒绝）。
- 升级迁移本身（本包只做初始化，不做 17→18→19 的数据迁移）。
