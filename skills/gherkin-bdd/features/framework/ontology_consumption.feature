# language: zh-CN
@ct-module=framework
@ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
功能: 每个执行环节如实交代对应用结构说明的消费
  作为 交付架构师
  我希望 每个环节都声明它如何使用应用结构说明
  以便 推理结论能够锚定到可核对的应用结构上

  @ct-id=SCN-FWK-001 @ct-unit=CU-FWK-001 @ct-gate=G2 @ct-priority=P0
  @ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
  场景: 结构可用时引用子图中的条目并说明用途
    假如 目标模块的应用结构说明已经生成
    而且 当前环节拿到了本次专属的说明范围
    当 环节引用范围内的结构条目写明所支撑的判断
    那么 引用条目与本次说明范围逐条吻合
    而且 用途说明被记录到该环节的执行凭据中

  @ct-id=SCN-FWK-002 @ct-unit=CU-FWK-002 @ct-gate=G2 @ct-priority=P0
  @ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
  场景: 环节不推理应用结构时声明不适用而不编造引用
    假如 目标模块的应用结构说明已经生成
    而且 当前环节只处理文字措辞的归一
    当 环节声明本次不适用并写明具体原因
    那么 环节不产生任何结构条目引用
    而且 不适用结论与原因被记录到执行凭据中

  @ct-id=SCN-FWK-003 @ct-unit=CU-FWK-003 @ct-gate=G2 @ct-priority=P0
  @ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
  场景: 引用说明范围之外的条目时不得放行
    假如 当前环节拿到了本次专属的说明范围
    而且 存在不属于该范围的结构条目
    当 环节引用范围之外的条目充当依据
    那么 该引用被判定为无效
    而且 该环节停留在待凭据状态不得声明完成

  @ct-id=SCN-FWK-004 @ct-unit=CU-FWK-004 @ct-gate=G2 @ct-priority=P1
  @ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
  场景: 说明版本变化后旧引用不得复用
    假如 环节已收到某一版本的应用结构说明
    而且 该说明随后发生了更新
    当 环节沿用更新前的引用声明完成
    那么 引用与当前说明版本的比对判定为不一致
    而且 该环节停留在待凭据状态不得声明完成

  @ct-id=SCN-FWK-005 @ct-unit=CU-FWK-005 @ct-gate=G2 @ct-priority=P1
  @ct-source=skills/capability-twin-orchestrator/scripts/evidence_gate.py
  场景: 无法取得结构说明时如实标记不可用
    假如 目标模块的应用结构说明尚未构建
    而且 当前环节无法取得任何结构条目
    当 环节按不可用的状态确认并记录原因
    那么 环节不产生任何结构条目引用
    而且 不可用状态与原因被记录到执行凭据中
