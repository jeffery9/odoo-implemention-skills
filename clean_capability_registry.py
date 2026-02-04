import json

# 读取capability_registry.json文件
input_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry.json"
output_file = "/Users/jeffery/odoo19-study/CT/Deliverables_Package/capability_registry.json"

# 读取capability_registry.json文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 移除obsidian-markdown的引用
if "obsidian-markdown" in data:
    del data["obsidian-markdown"]
    print("已移除obsidian-markdown的引用")

# 保存更新后的文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已更新能力注册表文件，保存到: {output_file}")