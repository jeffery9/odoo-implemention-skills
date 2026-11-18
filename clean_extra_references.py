#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重建历史 CT 项目的注册表，只保留 `agents` 与 `skills` 两个顶级节点。

用法：
    python3 clean_extra_references.py --registry /path/to/capability_registry.json
    CT_LEGACY_PROJECT=/path/to/CT python3 clean_extra_references.py
"""

import argparse
import sys
import json

import legacy_paths


def main():
    parser = argparse.ArgumentParser(description="只保留 agents / skills 顶级节点")
    parser.add_argument("--registry",
                        help="capability_registry.json 路径"
                             "（缺省读 CT_LEGACY_REGISTRY / CT_LEGACY_PROJECT）")
    parser.add_argument("--output", help="输出文件路径，默认原地覆盖")
    args = parser.parse_args()

    input_file = legacy_paths.registry_path(args.registry)
    output_file = legacy_paths.output_path(args.output, input_file)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 只保留实际被引用的 agents / skills，其余顶级节点一律丢弃
    new_data = {
        "agents": dict(data.get("agents", {})),
        "skills": dict(data.get("skills", {})),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print("已重新构建能力注册表文件，只包含实际引用的组件")
    print(f"Agents: {len(new_data['agents'])}")
    print(f"Skills: {len(new_data['skills'])}")
    print(f"已保存到: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except legacy_paths.UsageError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(2)
