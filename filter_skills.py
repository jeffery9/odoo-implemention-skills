#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从历史 CT 项目的 skills 目录移除指定的非核心组件。

用法：
    # 先看会删什么（默认就是干跑，不删任何东西）
    python3 filter_skills.py --ct-dir /path/to/CT
    # 确认后真正执行
    python3 filter_skills.py --ct-dir /path/to/CT --yes

删除是不可逆的目录移除（shutil.rmtree），因此默认只打印计划；
必须显式 `--yes` 才动手，避免换机器后路径指错位置而误删。
"""

import argparse
import sys
import shutil

import legacy_paths

#: 历史交付中判定为非核心的技能（业务口径，非环境相关配置）
DEFAULT_NON_CORE = {"obsidian-markdown"}


def main():
    parser = argparse.ArgumentParser(description="移除 CT 项目 skills 目录下的非核心组件")
    parser.add_argument("--ct-dir", help="CT 项目根目录（缺省读 CT_LEGACY_PROJECT）")
    parser.add_argument("--components", nargs="+", metavar="NAME",
                        help=f"要移除的技能目录名，默认 {sorted(DEFAULT_NON_CORE)}")
    parser.add_argument("--yes", action="store_true",
                        help="确认执行删除；不加此参数只打印计划（干跑）")
    args = parser.parse_args()

    ct_dir = legacy_paths.ct_project_dir(args.ct_dir)
    skills_dir = ct_dir / "skills"
    if not skills_dir.is_dir():
        raise legacy_paths.UsageError(f"skills 目录不存在：{skills_dir}")

    targets = args.components or sorted(DEFAULT_NON_CORE)
    print(f"CT skills 目录: {skills_dir}")
    print(f"待处理组件: {', '.join(targets)}")

    for component in targets:
        component_path = skills_dir / component
        if not component_path.exists():
            print(f"组件不存在或已被移除: {component}")
            continue
        if not args.yes:
            print(f"[干跑] 将删除: {component_path}")
            continue
        print(f"移除非核心组件: {component}")
        shutil.rmtree(component_path)
        print(f"已移除: {component}")

    if not args.yes:
        print("干跑结束，未做任何改动。确认无误后加 --yes 执行。")
    print("非核心组件清理完成。")


if __name__ == "__main__":
    try:
        main()
    except legacy_paths.UsageError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(2)
