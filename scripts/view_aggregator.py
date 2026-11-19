#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re, json
from pathlib import Path

class OdooEvidenceAggregator:
    def __init__(self, source_root: Path, target_module: str, expansion_modules: list):
        self.source_root = source_root
        self.target_module = target_module
        self.modules = [target_module] + [m for m in expansion_modules if m != target_module]
        self.module_paths = self._find_module_paths()

    def _find_module_paths(self):
        paths = {}
        search_dirs = [self.source_root / "addons", self.source_root / "odoo/addons"]
        for m in self.modules:
            for sd in search_dirs:
                if (sd / m).exists():
                    paths[m] = sd / m
                    break
        return paths

    def get_model_acl(self, model_name):
        """抓取特定模型的 ACL 记录 (model_mrp_production -> mrp.production)"""
        acl_key = f"model_{model_name.replace('.', '_')}"
        results = []
        for m, p in self.module_paths.items():
            csv_path = p / "security" / "ir.model.access.csv"
            if csv_path.exists():
                lines = csv_path.read_text().splitlines()
                header = lines[0]
                for line in lines[1:]:
                    if acl_key in line:
                        results.append({"module": m, "entry": line})
        return results

    def get_aggregated_views(self, model_name):
        """抓取并聚合所有属于该模型的视图定义"""
        views = []
        for m, p in self.module_paths.items():
            v_dir = p / "views"
            if not v_dir.exists(): continue
            for xml_f in v_dir.glob("*.xml"):
                try:
                    content = xml_f.read_text(encoding='utf-8', errors='ignore')
                    # 寻找匹配 model 的 record
                    # 极简模式：匹配包含 model 名且 model="ir.ui.view" 的记录块
                    pattern = rf'<record[^>]*model="ir.ui.view"[^>]*>.*?<field[^>]*name="model"[^>]*>{model_name}</field>.*?</record>'
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        # 识别是基础视图还是继承视图
                        is_inherit = 'name="inherit_id"' in match
                        views.append({
                            "module": m,
                            "file": xml_f.name,
                            "type": "Inherit" if is_inherit else "Base",
                            "content": match.strip()
                        })
                except: continue
        return views

def main():
    if len(sys.argv) < 3: return
    try:
        data = json.loads(sys.argv[1])
        model_to_analyze = sys.argv[2] # e.g. mrp.production
        
        source_root = Path(data.get("shared_context", {}).get("odoo_source_path", ""))
        expansion = data.get("shared_context", {}).get("shared_data", {}).get("expansion_modules", [])
        
        aggregator = OdooEvidenceAggregator(source_root, data.get("target_module"), expansion)
        
        bundle = {
            "model_name": model_to_analyze,
            "acls": aggregator.get_model_acl(model_to_analyze),
            "views": aggregator.get_aggregated_views(model_to_analyze)
        }
        print(json.dumps(bundle, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
