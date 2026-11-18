# 契约字段指南

## 1. 为什么全部可选

现有 21 个技能的 frontmatter 只有 `name` / `description` / `allowed-tools`（12 个）、`version`（1 个）、`skills_used`（1 个）五个字段。若把任何 `ct_` 字段设为必填，等于要求重写全部既有技能——这与「不颠覆现有框架」冲突。

因此校验器的第一原则是：**没有任何 `ct_` 字段的技能判为 `skipped`，不是 `error`。** 只有声明了 `ct_` 字段的技能才进入契约校验。这样契约是「 opted-in 」的：新写的 Odoo 实施技能主动声明，老技能不受影响。

## 2. 字段语义

### ct_layer

分类标签，取 `router` / `core` / `shared` / `module`。它回答「这个技能在能力链中扮演什么角色」，仅用于检索和统计，**不建立目录层级**。之所以不把层级落成物理目录，是因为它与 `npx skills` 的平铺安装结构冲突——CT 曾为此迁移过 45 个文件，故改为标签。

### ct_module

Odoo 原生模块名，如 `account`、`mrp`。约束为 `[a-z][a-z0-9_]*`，与 `config.validate_module_name` 的默认模式一致。仅在 `ct_layer=module` 时允许出现——因为只有模块层的技能才绑定单一模块；router/core/shared 层跨模块，不应声明 `ct_module`。

### ct_odoo_versions

适用大版本数组，元素形如 `17.0`。不采用 `>=19.0` 这类范围表达式：版本约束属于业务元数据，范围语义留给更高层，契约层只做格式校验。

### ct_scenario_refs

指向 `gherkin-bdd` 的 `.feature` 路径（如 `features/account/shipped_not_invoiced.feature`）或场景编号（如 `SCN-ACC-001`）。本字段是引用，不复制场景正文——场景唯一事实源仍是 `.feature`。

### ct_state_outputs

声明该技能写入项目工作区的产物类型，如 `project-state`、`artifact-index`。用于审计「哪些技能会改变持久状态」。校验器只验证格式，不验证产物是否真的生成（生成与否属于运行时证据，归 G2/G3 判定）。

## 3. 从旧技能迁移

不需要迁移。若某个既有技能确实要纳入契约管理，最小改动是加一行 `ct_layer`：

```yaml
name: source-traceability
description: ...
ct_layer: shared
```

加完后校验器从 `skipped` 变为 `validated`。不要为了「看起来完整」一次性补齐所有字段——缺省是合法状态。

## 4. 领域规则的落点

`ct_module` 与 `ct_layer` 的相关性（`ct_layer=module` 才允许 `ct_module`）写在两处，保持同步：

1. `schemas/odoo-implementation.schema.json` 的 `allOf[0].if/then/else`；
2. `scripts/validate_odoo_manifest.py` 的 `validate_manifest()`。

测试对这两处做一致性检查，防止 schema 与脚本漂移。
