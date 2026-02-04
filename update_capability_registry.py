import json
import os
from pathlib import Path

# 读取原始的capability_registry.json文件
input_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry.json"
output_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry_updated.json"

# 读取CT目录的路径
ct_dir = Path("/Users/jeffery/odoo19-study/CT").resolve()
print(f"CT目录路径: {ct_dir}")

# 读取skills目录的路径
skills_dir = ct_dir / "skills"
print(f"Skills目录路径: {skills_dir}")

# 读取agents目录的路径
agents_dir = ct_dir / "agents"
print(f"Agents目录路径: {agents_dir}")

# 读取capability_registry.json文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 更新路径
for agent_key, agent_value in data.get("agents", {}).items():
    if "path" in agent_value and "/Users/jeffery/odoo19-study/.claude/agents" in agent_value["path"]:
        agent_value["path"] = str(agents_dir)
    if "file" in agent_value and "/Users/jeffery/odoo19-study/.claude/agents" in agent_value["file"]:
        # 提取AGENT.md文件名并构建新路径
        agent_name = agent_key.replace("-", "_")
        # 确保目录名正确
        if "agent" in agent_name:
            agent_dir = agent_name
        else:
            agent_dir = agent_name + "_agent"
        agent_value["file"] = str(agents_dir / agent_dir / "AGENT.md")

for skill_key, skill_value in data.get("skills", {}).items():
    if "path" in skill_value and "/Users/jeffery/odoo19-study/.claude/skills" in skill_value["path"]:
        skill_value["path"] = str(skills_dir)
    if "file" in skill_value and "/Users/jeffery/odoo19-study/.claude/skills" in skill_value["file"]:
        # 提取SKILL.md文件名并构建新路径
        skill_name = skill_key
        skill_dir = skill_name
        skill_value["file"] = str(skills_dir / skill_dir / "SKILL.md")

# 为其他部分更新路径
for key, value in data.items():
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            if isinstance(sub_value, dict):
                if "path" in sub_value and "/Users/jeffery/odoo19-study/.claude" in sub_value["path"]:
                    # 更新路径为相对路径或CT目录下的路径
                    original_path = sub_value["path"]
                    if "/Users/jeffery/odoo19-study/.claude/agents" in original_path:
                        sub_value["path"] = str(agents_dir)
                    elif "/Users/jeffery/odoo19-study/.claude/skills" in original_path:
                        sub_value["path"] = str(skills_dir)

# 保存更新后的文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已更新能力注册表文件，保存到: {output_file}")