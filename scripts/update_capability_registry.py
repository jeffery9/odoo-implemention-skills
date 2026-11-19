#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
把历史 CT 项目注册表里的 `.claude/...` 绝对路径改写成 CT 目录下的实际路径。

用法：
    python3 update_capability_registry.py --ct-dir /path/to/CT
    CT_LEGACY_PROJECT=/path/to/CT python3 update_capability_registry.py

改写规则（与历史版本一致，只是不再把某台机器的绝对前缀写死）：
- 旧值里出现 `.claude/agents`  → agents 目录
- 旧值里出现 `.claude/skills`  → skills 目录
判定改用路径中段标记 `.claude`，与用户名、盘符、挂载点无关。
"""

import argparse
import sys
import json
from pathlib import Path

import legacy_paths

#: 旧注册表里指向安装位置的标记
MARKER = "/.claude"


def _as_posix(value) -> str:
    return str(value).replace("\\", "/")


def main():
    parser = argparse.ArgumentParser(description="改写注册表中的 .claude 绝对路径")
    parser.add_argument("--ct-dir", help="CT 项目根目录（缺省读 CT_LEGACY_PROJECT）")
    parser.add_argument("--registry",
                        help="capability_registry.json 路径"
                             "（缺省读 CT_LEGACY_REGISTRY，或 <ct-dir>/Deliverables_Package/）")
    parser.add_argument("--output", help="输出文件路径，默认 <注册表目录>/capability_registry_updated.json")
    args = parser.parse_args()

    ct_dir = legacy_paths.ct_project_dir(args.ct_dir)
    agents_dir = ct_dir / "agents"
    skills_dir = ct_dir / "skills"
    print(f"CT目录路径: {ct_dir}")
    print(f"Skills目录路径: {skills_dir}")
    print(f"Agents目录路径: {agents_dir}")

    input_file = legacy_paths.registry_path(args.registry, ct_dir=ct_dir)
    output_file = legacy_paths.output_path(
        args.output, input_file.with_name("capability_registry_updated.json"))

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for agent_key, agent_value in data.get("agents", {}).items():
        if "path" in agent_value and MARKER + "/agents" in _as_posix(agent_value["path"]):
            agent_value["path"] = str(agents_dir)
        if "file" in agent_value and MARKER + "/agents" in _as_posix(agent_value["file"]):
            agent_name = agent_key.replace("-", "_")
            agent_dir = agent_name if "agent" in agent_name else agent_name + "_agent"
            agent_value["file"] = str(agents_dir / agent_dir / "AGENT.md")

    for skill_key, skill_value in data.get("skills", {}).items():
        if "path" in skill_value and MARKER + "/skills" in _as_posix(skill_value["path"]):
            skill_value["path"] = str(skills_dir)
        if "file" in skill_value and MARKER + "/skills" in _as_posix(skill_value["file"]):
            skill_value["file"] = str(skills_dir / skill_key / "SKILL.md")

    # 兜底：其余节点里残留的 .claude 路径
    for value in data.values():
        if not isinstance(value, dict):
            continue
        for sub_value in value.values():
            if not isinstance(sub_value, dict) or "path" not in sub_value:
                continue
            original = _as_posix(sub_value["path"])
            if MARKER + "/agents" in original:
                sub_value["path"] = str(agents_dir)
            elif MARKER + "/skills" in original:
                sub_value["path"] = str(skills_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新能力注册表文件，保存到: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except legacy_paths.UsageError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(2)
