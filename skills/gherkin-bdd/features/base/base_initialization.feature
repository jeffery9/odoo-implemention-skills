# language: zh-CN
@ct-module=base
@ct-source=templates/project/base-data-actions.template.json
功能: 基础数据初始化的可核对基线
  作为 实施顾问
  我希望 按确认清单完成基础数据初始化并冻结基线
  以便 后续主数据与业务单据有统一、可追溯的参照

  @ct-id=SCN-BAS-001 @ct-unit=CU-BAS-004 @ct-gate=G2 @ct-priority=P0
  @ct-source=templates/project/base-data-actions.template.json
  场景: 计量单位、币种、国家与语言初始化后冻结基线
    假如 业务方已确认计量单位、币种、国家与语言的初始化清单
    而且 目标版本与执行通道已明确
    当 按确认清单逐项初始化并读回核对
    那么 每项初始化结果都与确认清单一致
    而且 初始化清单与核对记录被冻结为可追溯的基线版本

  @ct-id=SCN-BAS-002 @ct-unit=CU-BAS-008 @ct-gate=G2 @ct-priority=P1
  @ct-source=templates/project/base-data-actions.template.json
  场景: 汇率初始化覆盖全部启用币种
    假如 本位币与启用币种基线已经冻结
    而且 汇率来源与生效日期已由财务确认
    当 按生效日期导入初始汇率并读回核对
    那么 每个启用币种都有对应汇率记录
    而且 汇率表、来源与生效日期被冻结为可追溯的基线版本

  @ct-id=SCN-BAS-003 @ct-unit=CU-BAS-009 @ct-gate=G2 @ct-priority=P1
  @ct-source=templates/project/seed-actions.template.json
  场景: 主数据初始化保持编码唯一且引用可达
    假如 客户、供应商与产品的编码规则已确认
    而且 计量单位基线已冻结
    当 按编码规则建立主数据并抽样读回核对
    那么 产品编码唯一，分类与计量单位引用都可达
    而且 主数据清单与去重记录被冻结为可追溯的基线版本

  @ct-id=SCN-BAS-004 @ct-unit=CU-BAS-010 @ct-gate=G2 @ct-priority=P1
  @ct-source=templates/project/onboarding-profile.template.json
  场景: 组织权限与编号规则初始化后可核对
    假如 公司部门结构、权限矩阵与编号规则已由业务方确认
    当 按确认基线建立组织、权限分组与单据序列
    那么 角色权限与权限矩阵一致，且各单据序列格式与重置策略正确
    而且 授权基线与编号规则被冻结为可追溯的版本
