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

### 2.1 计量单位（SEED-004）—— 硬差异，必须按版本分化

| 项 | 17.0 / 18.0 | 19.0 |
|---|---|---|
| 单位分类 | `uom.category` 存在 | **模型移除** |
| 单位记录 | `uom.uom` + `category_id` | `uom.uom` + `relative_uom_id` |
| 换算字段 | `uom_type`（reference/smaller/bigger）+ `factor` / `factor_inv` | `uom_type` / `factor_inv` 移除，改用 `relative_factor` |
| 基准单位 | 每个 category 一个 reference 单位 | 参考单位指向自身（`relative_uom_id = self`） |

动作计划必须用 `odoo_versions` 标注两套动作；执行器只执行与 `--odoo-version` 匹配的分支。模板 `templates/project/base-data-actions.template.json` 已按此分化。

依据：Odoo 18→19 迁移说明与社区实测均确认 `uom.category` 被删除、`factor_inv → relative_factor`、以 `relative_uom_id` 直连参考单位。

### 2.2 币种 / 汇率 / 国家 / 语言（SEED-005~007）—— 字段名稳定

`res.currency`、`res.currency.rate`、`res.country`、`res.lang` 在 17/18/19 的上述字段（`symbol`、`decimal_places`、`rate`、`name`、`code`、`active`、`date_format`）未发生破坏性改名，动作计划可用同一份定义。但以下约束仍成立：

- 币种小数位、符号与汇率来源属业务/财务判断，不由执行器决定。
- 语言的激活与翻译质量需业务方确认；执行器不提供机器翻译。
- 不内置全量国家/行政区划数据；仅导入业务方确认的清单。

> 版本升级仍可能带来字段级微调。动作计划在执行前应于目标版本的 staging 环境用 dry-run + 小批量 `--apply` 验证，不得假设跨版本零改动。

### 2.3 产品主数据（SEED-009）—— 已核实三版本一致（引用口径）

产品导入模板 `templates/project/seed-actions.template.json` 使用 `product.category`（`name`）与 `product.template`（`name`、`default_code`、`type`、`categ_id`、`uom_id`、`uom_po_id`、`sale_ok`、`purchase_ok`、`list_price`）。

- 计量单位只引用 `uom.uom` 记录 ID，该 ID 由 `SEED-004` 按 17/18 与 19 的不同字段分化导入后提供；产品动作不引用 `uom.category`，因此不受 §2.1 的模型删除影响。模板中的 ID 均为占位值，项目侧必须替换为实际记录 ID。
- 上述产品字段在 17/18/19 未发生破坏性改名，**核实范围**限于本包模板使用的字段与方法；核实结果写入 SEED-009 定义卡的「版本差异」行。业务取值仍须在目标版本 staging 用 dry-run 与小批量 `--apply` 复核；若发现差异，按动作级 `odoo_versions` 分化并更新本节。
- 编码唯一性、产品分类层级与价格口径属业务判断，不由执行器决定。

### 2.4 组织、编号与会计底座（SEED-010~013）—— 已核实三版本一致

核实范围限于本包初始化动作使用的模型与字段，不覆盖业务含义与专业判断：

| 能力 | 模型 / 字段 | 17/18/19 结论 |
|---|---|---|
| SEED-010 组织与权限 | `res.company` / `res.partner` / `res.users` / `res.groups` | 组织层级与授权字段未发生破坏性改名 |
| SEED-011 编号规则 | `ir.sequence` 的 `prefix` / `padding` / `number_next` | 字段稳定 |
| SEED-012 会计底座 | `account.account` / `account.journal` / `account.fiscal.year` | 初始化字段未发生破坏性改名 |
| SEED-013 期初余额 | `import_data(fields, rows, mode=...)` | 签名一致，见 §3 |

上述结论由 `tests/test_odoo_seed_executor.py::test_22_every_seed_card_has_verified_version_row`
守卫：13 张能力卡必须都有「版本差异」行，且不得出现「待核实 / 尚未核实」。若后续 Odoo 版本升级破坏该
口径，必须同时更新本表、对应能力卡与动作模板，不能只改文档。

## 3. 核心服务方法差异（SEED-001~003）

| 能力 | 方法与签名 | 17.0 / 18.0 | 19.0 | 版本标注 |
|---|---|---|---|---|
| 模块安装（SEED-001） | `ir.module.module.button_immediate_install`（记录集方法，参数 = 模块记录 ID 列表） | 可用 | 可用；新增挂起状态前置检查 | 动作标 `odoo_versions: 17/18/19` |
| 配置参数（SEED-002） | `ir.config_parameter.set_param(key, value, group=None)`（模型级方法） | 可用 | 可用，签名一致 | 通用（三版本一致） |
| 数据导入（SEED-003） | `import_data(fields, rows, mode=...)`（模型级方法） | 可用 | 可用；另有可选 `dryrun` 参数，本包不使用 | 通用（三版本一致） |

依据：

- 模块安装经 XML-RPC 先 `search` 取模块记录 ID，再对 ID 列表调用 `button_immediate_install`；三版本入口均存在。Odoo 19 在 `_button_immediate_function` 前置检查中拒绝存在 `to install`/`to upgrade`/`to remove` 挂起状态的数据库，安装前须确认无挂起操作。
- JSON-2 请求体为扁平对象：`ids`（记录集 ID 数组）与方法的命名参数作顶层 key；模型级方法省略 `ids`。执行器 `_json2_payload()` 据此把 RPC 的位置参数 `args` 转换为命名参数。依据：Odoo 19 官方 `external_api.html` 的 Request 章节。
- `import_data` 的 `dryrun` 为 19.0 可选参数，本包模板不声明以保证一份计划跨版本可用。

动作计划模板：`templates/project/core-services-actions.template.json`。模块安装动作带 `odoo_versions` 标注，未指定版本时执行器 fail-closed（`CT-003`）。

## 4. 动作级版本契约

动作可声明 `odoo_versions`（大版本数组）：

```json
{
  "method": "create",
  "model": "uom.uom",
  "odoo_versions": ["19.0"],
  "args": [{"name": "米", "relative_uom_id": 1, "relative_factor": 1.0}],
  "idempotency_key": "SEED-004:19:uom.uom:米"
}
```

语义：

1. 未声明 `odoo_versions` → 通用动作，所有版本执行。
2. 声明且 `--odoo-version` 命中 → 执行。
3. 声明且版本不匹配 → 跳过，计入报告 `skipped_actions`，不产生 issue。
4. 声明了版本却未给 `--odoo-version` → `CT-003` error，零执行（fail-closed），防止在错误版本上跑错初始化动作。

## 5. 不在本文件范围

- 具体业务数据的取值（由业务方确认，属 G3/FDE 验收范畴）。
- 20.0 及以后版本的支持（当前仅 17/18/19，超出版本改用 `--odoo-version` 会被拒绝）。
- 升级迁移本身（本包只做初始化，不做 17→18→19 的数据迁移）。
