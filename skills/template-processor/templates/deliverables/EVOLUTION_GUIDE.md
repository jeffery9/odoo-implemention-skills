# 系统持续演化与维护指南

## 1. 如何保持知识库更新
*本项目交付的知识资产是动态的。建议客户技术团队定期运行挖掘脚本。*

- **操作**: `python3 scripts/mine_odoo_source.py`
- **目的**: 捕捉 Odoo 19 后续小版本更新中的新模式。

---

## 2. 扩充新的业务场景 (Add New Scenarios)
1. 识别新需求。
2. 调用 `intent-understanding` 技能。
3. 参照本项目的 `SCENARIO_SOLUTION.md` 格式构建新积木。

---

## 3. 知识库维护 (KB Maintenance)
- **位置**: `kb/mem/`
- **格式**: JSONL (可用文本编辑器或脚本流式读取)。
- **备份建议**: 建议将 `kb/mem/` 纳入 Git 版本控制。

---
*Capability Twin 3.5 | Autonomous Evolution*
