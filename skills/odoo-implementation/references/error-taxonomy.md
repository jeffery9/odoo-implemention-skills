# 失败分类

本包定义 11 类失败语义，映射到 Capability Twin 的既有门禁。分类用于阻断与报告，不用于打分——不设成熟度等级、不设加权通过分。

| 码 | 类别 | 触发条件 | 阻断级别 |
|---|---|---|---|
| `CT-001` | input_validation | 缺少必需入参或格式非法 | error |
| `CT-002` | catalog_mismatch | `ct_module` 不在已知模块清单 | error |
| `CT-003` | contract_violation | 字段违反 schema（非法枚举、多余字段、层级冲突） | error |
| `CT-004` | scenario_missing | 声明了 `ct_scenario_refs` 但目标 `.feature` 不存在 | error |
| `CT-005` | state_write_denied | 写工作区产物未经授权 | blocked |
| `CT-006` | credential_missing | 需要外部连接但无凭据 | blocked |
| `CT-007` | idempotency_absent | 外部写操作无幂等键 | blocked |
| `CT-008` | evidence_unreachable | `@ct-source` 证据路径不可达 | warning |
| `CT-009` | partial_success | 多步操作中途失败 | error |
| `CT-010` | external_failure | 外部系统返回错误 | error |
| `CT-011` | idempotency_ledger_corrupt | 幂等账本 JSON/结构损坏，无法判定重放 | error（fail-closed，禁止写操作） |

## 重试禁令

- 只读操作：可重试，最多 2 次，退避递增。
- 凭据类错误（401/403）：只允许刷新凭据后重试 1 次；不得循环刷新。
- 写操作（配置变更、模块安装、数据导入）：无幂等键不得重试；有幂等键才可安全重放。
- 幂等账本损坏时不降级为空账本：先报 `CT-011` 并停止全部写操作，由人确认账本后重跑。
- `blocked` 级别的错误不得由自动化自行解除，必须回到人审批。

## 与质量门的关系

失败分类是**描述性**的：它说明为什么停，不改变 G2/G3/FDE 的判定边界。`status=blocked` 沿用现有门禁语义，不新增状态值。
