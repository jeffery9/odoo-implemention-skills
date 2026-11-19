#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
把历史 CT 项目注册表里的旧技能容器绝对路径改写成 CT 目录下的实际路径。

用法：
    python3 update_capability_registry.py --ct-dir /path/to/CT
    CT_LEGACY_PROJECT=/path/to/CT python3 update_capability_registry.py

改写规则（与历史版本一致，只是不绑定任何工具厂商的容器名）：
- 路径中含 `agents` 目录段 → agents 目录
- 路径中含 `skills` 目录段 → skills 目录

判定只看路径结构中的目录段，与容器名（`.claude` / `.agents` / 其它）、
用户名、盘符、挂载点均无关；历史数据里出现的容器名不写进代码。
"""

import argparse
import re
import sys
import json
from pathlib import Path

import legacy_paths

#: 技能容器内的标准目录段，作为识别依据（不含任何厂商容器名）
_CONTAINER_SEGMENT = re.compile(r"/(agents|skills)(?:/|$)")


def _as_posix(value) -> str:
    return str(value).replace("\\", "/")


def _legacy_kind(value):
    """识别旧路径归属的目录段（agents / skills）；不匹配返回 None。

    用路径段而非某一厂商容器名判定，故 `.claude/agents`、`.agents/skills`
    或其它容器布局的历史数据都能识别。
    """
    match = _CONTAINER_SEGMENT.search(_as_posix(value))
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description="把注册表中的旧容器绝对路径改写为 CT 目录路径")
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
        if "path" in agent_value and _legacy_kind(agent_value["path"]) == "agents":
            agent_value["path"] = str(agents_dir)
        if "file" in agent_value and _legacy_kind(agent_value["file"]) == "agents":
            agent_name = agent_key.replace("-", "_")
            agent_dir = agent_name if "agent" in agent_name else agent_name + "_agent"
            agent_value["file"] = str(agents_dir / agent_dir / "AGENT.md")

    for skill_key, skill_value in data.get("skills", {}).items():
        if "path" in skill_value and _legacy_kind(skill_value["path"]) == "skills":
            skill_value["path"] = str(skills_dir)
        if "file" in skill_value and _legacy_kind(skill_value["file"]) == "skills":
            skill_value["file"] = str(skills_dir / skill_key / "SKILL.md")

    # 兜底：其余节点里残留的旧容器路径
    for value in data.values():
        if not isinstance(value, dict):
            continue
        for sub_value in value.values():
            if not isinstance(sub_value, dict) or "path" not in sub_value:
                continue
            kind = _legacy_kind(sub_value["path"])
            if kind == "agents":
                sub_value["path"] = str(agents_dir)
            elif kind == "skills":
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
