import json

# 读取capability_registry.json文件
input_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry.json"
output_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry.json"

# 读取capability_registry.json文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 定义非核心组件
non_core_components = {
    "obsidian-markdown",
    "obsidian-bases",
    "json-canvas",
    "planning-with-files",
    "capability-twin-orchestrator"
}

# 移除非核心组件
removed_count = 0
for component in non_core_components:
    if component in data:
        del data[component]
        removed_count += 1
        print(f"已移除非核心组件: {component}")

# 保存更新后的文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已更新能力注册表文件，移除了 {removed_count} 个非核心组件")
print(f"已保存到: {output_file}")