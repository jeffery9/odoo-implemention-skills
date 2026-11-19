#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从历史 CT 项目的注册表中移除 obsidian-markdown 条目。

用法：
    python3 clean_capability_registry.py --registry /path/to/capability_registry.json
    CT_LEGACY_PROJECT=/path/to/CT python3 clean_capability_registry.py

默认原地写回；用 --output 指定另存路径。
"""

import argparse
import sys
import json

import legacy_paths


def main():
    parser = argparse.ArgumentParser(description="移除注册表中的 obsidian-markdown 条目")
    parser.add_argument("--registry",
                        help="capability_registry.json 路径"
                             "（缺省读 CT_LEGACY_REGISTRY / CT_LEGACY_PROJECT）")
    parser.add_argument("--output", help="输出文件路径，默认原地覆盖")
    args = parser.parse_args()

    input_file = legacy_paths.registry_path(args.registry)
    output_file = legacy_paths.output_path(args.output, input_file)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "obsidian-markdown" in data:
        del data["obsidian-markdown"]
        print("已移除 obsidian-markdown 的引用")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新能力注册表文件，保存到: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except legacy_paths.UsageError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(2)
