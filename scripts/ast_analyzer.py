import ast
import json
import os
import sys
from pathlib import Path

class DeepOdooVisitor(ast.NodeVisitor):
    def __init__(self):
        self.data = {
            "classes": [],
            "imports": [],
            "performance_patterns": [], # 记录 precompute, stored 等
            "logic_footprints": []      # 记录 SQL 执行等关键逻辑
        }

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "odoo_name": None,
            "methods": [],
            "fields": []
        }
        for item in node.body:
            # 识别字段与性能指纹
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "_name":
                            class_info["odoo_name"] = item.value.value if hasattr(item.value, 'value') else None
                        
                        # 抓取字段定义中的性能属性
                        val_str = ast.dump(item.value)
                        if "fields." in val_str:
                            field_name = target.id
                            is_stored = "store=True" in val_str
                            is_precomputed = "precompute=True" in val_str
                            if is_precomputed:
                                self.data["performance_patterns"].append(f"{class_info['name']}.{field_name} (Precomputed)")
            
            # 识别方法细节
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    "name": item.name,
                    "is_api": any(isinstance(dec, ast.Call) and getattr(dec.func, 'id', '') in ['api', 'depends', 'onchange'] for dec in item.decorator_list),
                    "has_sql": "execute(" in ast.dump(item)
                }
                class_info["methods"].append(method_info)
                if method_info["has_sql"]:
                    self.data["logic_footprints"].append(f"SQL execution in {class_info['name']}.{item.name}")

        self.data["classes"].append(class_info)
        self.generic_visit(node)

def analyze_file(file_path):
    try:
        tree = ast.parse(file_path.read_text(encoding='utf-8', errors='ignore'))
        visitor = DeepOdooVisitor()
        visitor.visit(tree)
        return visitor.data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    print(json.dumps(analyze_file(Path(sys.argv[1])), indent=2))