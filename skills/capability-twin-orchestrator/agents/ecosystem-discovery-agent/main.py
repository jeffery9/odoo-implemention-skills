#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys, subprocess, re
from pathlib import Path

# 框架路径中枢随 orchestrator 分发：本文件位于 <orchestrator>/agents/<agent>/main.py
_scripts = Path(__file__).resolve().parents[2] / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
import framework_paths

def main():
    if len(sys.argv) < 2: return
    try:
        params = json.loads(sys.argv[1])
        target = params.get("config", {}).get("target_module") or params.get("target_module")
        shared_context = params.get("shared_context", {})
        source_root_str = os.environ.get("ODOO_SOURCE_PATH") or shared_context.get("odoo_source_path", "")
        
        if not source_root_str:
            print(json.dumps({"status": "error", "message": "ODOO_SOURCE_PATH not found"}))
            return
        
        source_root = Path(source_root_str)
        # 工具脚本随 orchestrator 技能分发，按技能内位置定位，不假设仓库根
        graph_script = framework_paths.tool_script("odoo_module_graph.py")

        # 1. 物理调用用户提供的 odoo_module_graph.py
        # 探测全量模块依赖 (使用 -p 指定多个插件目录)
        addons_paths = [str(source_root / "addons"), str(source_root / "odoo/addons")]
        cmd = [sys.executable, str(graph_script)]
        for p in addons_paths:
            if os.path.exists(p):
                cmd.extend(["-p", p])
        
        # 为了获取全量数据，我们先不传参数运行，或者传 target 运行
        # 这里的策略是传 target 获取该模块相关的依赖树
        cmd.append(target)
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        dot_output = proc.stdout

        # 2. 解析 DOT 结构获取依赖关系
        # 提取 'a -> b;' 模式
        dependencies = re.findall(r'(\w+)\s*->\s*(\w+);', dot_output)
        
        module_map = {} # {module: set(depends)}
        for parent, child in dependencies:
            if parent not in module_map: module_map[parent] = set()
            module_map[parent].add(child)

        # 3. 寻找业务交集 (胶水模块探测)
        core_pillars = {'account', 'stock', 'sale', 'purchase', 'mrp', 'project', 'hr'}
        glue_modules = []
        all_related = []

        # 扫描所有模块 (这里需要二次确认全量模块列表，因为 DOT 只包含 target 相关)
        # 我们遍历整个 addons 目录
        for p_str in addons_paths:
            p = Path(p_str)
            if not p.exists(): continue
            for item in p.iterdir():
                if item.is_dir() and (item / "__manifest__.py").exists():
                    # 读取 manifest (这里可以重用 graph_script 的逻辑)
                    manifest_path = item / "__manifest__.py"
                    try:
                        with open(manifest_path, 'r') as f:
                            m_data = eval(f.read())
                            deps = set(m_data.get('depends', []))
                            if target in deps:
                                all_related.append(item.name)
                                # 业务交集判断
                                if any(pillar in deps for pillar in core_pillars if pillar != target):
                                    glue_modules.append(item.name)
                    except:
                        continue

        print(json.dumps({
            "status": "success",
            "target_module": target,
            "layers": {
                "core": target,
                "glue_modules": list(set(glue_modules)),
                "all_related": list(set(all_related))
            },
            "source": "odoo_module_graph.py + proactive_intersection",
            "message": f"Successfully mapped {target} ecosystem using industrial graph script."
        }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()