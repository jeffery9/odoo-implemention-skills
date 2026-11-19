#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discovery and Registration script for Capability Twin framework.
Scans the framework directory and registers all Agents and Skills.

设计要点（与早期版本的差异）：
1. 路径锚定到本文件，不依赖 CWD，也不假设仓库目录名叫 CAPABILITY_TWIN。
2. 注册表内存**仓库相对路径**，换机器可直接使用。
3. allowed_tools 读取 frontmatter 的真实声明，而非硬编码。
4. registered_at 仅在首次注册时写入，重建不刷新，避免整文件 diff 噪声。
5. 扫描到 0 个单元时直接报错退出，不写空注册表。
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = FRAMEWORK_ROOT / "skills"
ORCHESTRATOR_DIR = SKILLS_DIR / "capability-twin-orchestrator"
# 提示型代理随 orchestrator 技能一起分发，npx skills 才认得并安装；
# 放在仓库根时不会被任何技能包收录，安装后必然缺失。
AGENTS_DIR = ORCHESTRATOR_DIR / "agents"
REGISTRY_PATH = ORCHESTRATOR_DIR / "capability_registry.json"


def _parse_list(raw: str):
    """解析 `[a, b]` 形式的内联列表"""
    if raw.startswith("[") and raw.endswith("]"):
        items = re.findall(r'["\']?([^,\[\]"\']+)["\']?', raw)
        return [i.strip() for i in items if i.strip()]
    return [i.strip() for i in raw.split(",") if i.strip()]


def _frontmatter(md_path: Path) -> dict:
    """
    解析 YAML frontmatter 中的标量字段（不引入 PyYAML 依赖）。

    支持：`key: value`、`key: [a, b]`、`key: "quoted"`。
    不解析嵌套结构——注册表只需要标量字段。
    """
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\s*(\r?\n|$)", text, re.S)
    if not m:
        return {}

    fm = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or line[0].isspace():
            continue
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key, raw = key.strip(), raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            fm[key] = _parse_list(raw)
        elif raw:
            fm[key] = raw.strip('"').strip("'")
    return fm


def _rel(path: Path) -> str:
    """
    返回相对**技能容器根**的 POSIX 路径。

    容器根在仓库布局下是 `skills/`，安装布局下是 `.claude/skills/`；
    注册表消费者（capability_registry）以同一基准解析，因此两种布局通用。
    例：`capability-twin-orchestrator/agents/xxx`、`quality-gate`。
    """
    return path.relative_to(SKILLS_DIR).as_posix()


def _load_previous() -> dict:
    """读取旧注册表，用于保留首次注册时间"""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        merged = {}
        merged.update(data.get("agents", {}))
        merged.update(data.get("skills", {}))
        return merged
    except Exception as exc:                       # 损坏时重建，但要出声
        print(f"[warn] 旧注册表无法解析，将重建：{exc}", file=sys.stderr)
        return {}


def _entry(kind: str, directory: Path, md_file: Path, previous: dict) -> dict:
    fm = _frontmatter(md_file)
    name = directory.name

    description = fm.get("description") or f"Capability unit: {name}"
    if isinstance(description, list):
        description = " ".join(description)

    allowed = fm.get("allowed-tools") or fm.get("allowed_tools")
    if isinstance(allowed, str):
        allowed = _parse_list(allowed)
    if not allowed:
        allowed = ["Read", "Grep", "Glob", "Bash"]   # 缺省最小集，非“全量授权”

    skills_used = fm.get("skills_used")
    if isinstance(skills_used, str):
        skills_used = _parse_list(skills_used)

    prev = previous.get(name, {})
    registered_at = prev.get("registered_at") or datetime.now().isoformat()

    entry = {
        "name": name,
        "type": kind,
        "description": description,
        "path": _rel(directory),
        "file": _rel(md_file),
        "allowed_tools": allowed,
        "registered_at": registered_at,
        "metadata": {
            "file_format": "Agent file" if kind == "agent" else "Skill file",
            "has_frontmatter": bool(fm),
        },
    }
    if fm.get("version"):
        entry["version"] = fm["version"]
    if skills_used:
        entry["skills_used"] = skills_used
    return entry


def scan(directory: Path, md_name: str, kind: str, previous: dict) -> dict:
    found = {}
    if not directory.is_dir():
        return found
    for unit_dir in sorted(directory.iterdir()):
        if not unit_dir.is_dir():
            continue
        md_file = unit_dir / md_name
        if md_file.exists():
            found[unit_dir.name] = _entry(kind, unit_dir, md_file, previous)
    return found


def main() -> int:
    print(f"Starting capability discovery in {FRAMEWORK_ROOT}")

    previous = _load_previous()
    agents = scan(AGENTS_DIR, "AGENT.md", "agent", previous)
    skills = scan(SKILLS_DIR, "SKILL.md", "skill", previous)

    if not agents and not skills:
        print(
            "[error] 未扫描到任何 Agent 或 Skill。为避免覆盖现有注册表，已中止写入。\n"
            f"        请确认 {AGENTS_DIR} 与 {SKILLS_DIR} 存在。",
            file=sys.stderr,
        )
        return 1

    # 一致性校验：引用不存在的技能时出声（不阻断，便于先建后补）
    known = set(skills)
    missing = {}
    for name, entry in list(agents.items()) + list(skills.items()):
        bad = [s for s in entry.get("skills_used", []) if s not in known]
        if bad:
            missing[name] = bad
    if missing:
        print("[warn] skills_used 引用了未注册的技能：", file=sys.stderr)
        for name, bad in missing.items():
            print(f"       {name}: {bad}", file=sys.stderr)

    registry = {"agents": agents, "skills": skills, "capabilities": {}}
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    no_desc = [n for n, e in list(agents.items()) + list(skills.items())
               if e["description"].startswith("Capability unit:")]
    print(f"Registry updated with {len(agents)} agents and {len(skills)} skills.")
    if no_desc:
        print(f"[warn] 以下单元缺 description，已使用占位描述：{no_desc}", file=sys.stderr)
    print(f"Registry saved to: {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
