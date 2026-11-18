#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
框架路径解析中枢（Framework Paths）

目标：同一份代码在两种布局下都能定位框架资源，且**不依赖当前工作目录**。

1. 仓库布局
       <repo>/skills/<skill>/scripts/framework_paths.py
2. 安装布局（`npx skills add <repo> --all`，symlink 或 --copy）
       <project>/.claude/skills/<skill>/scripts/framework_paths.py
       ~/.claude/skills/<skill>/scripts/framework_paths.py

两者共享同一结构不变量：`<容器>/<技能>/scripts/`。因此这里只按相对深度推导，
不硬编码容器目录名（`skills` / `.claude/skills` / `.agents/skills` 均成立）。

设计约束（与此前 84 处 `parents[N]` 写法相比的改进）：
- 任何一处资源定位失败都抛出带诊断信息的异常，不静默回退到"碰巧存在的目录"，
  否则安装态会拿别处的资源凑数并产生假绿。
- 唯一允许的回退是历史布局 `<framework_root>/templates/deliverables`，
  且回退结果会被 `diagnostics()` 明确标注 `templates_source`，便于审计。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

# <container>/<skill>/scripts/framework_paths.py
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_ROOT.parent
FRAMEWORK_ROOT = SKILLS_ROOT.parent

ORCHESTRATOR_SKILL = "capability-twin-orchestrator"
TEMPLATE_SKILL = "template-processor"
GHERKIN_SKILL = "gherkin-bdd"
ODOO_IMPLEMENTATION_SKILL = "odoo-implementation"


class SkillNotFound(RuntimeError):
    """兄弟技能未安装或路径不匹配时抛出，附带可执行的修复提示。"""


def _siblings() -> list:
    try:
        return sorted(p.name for p in SKILLS_ROOT.iterdir()
                      if p.is_dir() and not p.name.startswith("."))
    except OSError:
        return []


def installed_as() -> str:
    """
    区分仓库布局与安装布局，用于诊断与报告。

    判定依据（两者同时成立才算仓库布局）：
    1. 框架根存在 `discover_capabilities.py` —— 源码仓库专有，不被任何技能收录；
    2. 技能容器父目录不是隐藏目录（安装目标形如 `.claude/skills`、`.agents/skills`）。

    注意：symlink 安装时 `Path.resolve()` 会跟随链接回到源仓库，
    此时判定为 `repository` 是**正确**的 —— 运行的就是源仓库那份代码。
    """
    container = SKILLS_ROOT.parent
    has_repo_marker = (FRAMEWORK_ROOT / "discover_capabilities.py").is_file()
    hidden_container = container.name.startswith(".")
    return "repository" if has_repo_marker and not hidden_container else "install"


def skill_dir(name: str, required: bool = True) -> Optional[Path]:
    """
    定位兄弟技能目录。

    Args:
        name: 技能目录名（与 SKILL.md 的 `name` 一致）
        required: True 时找不到即抛 SkillNotFound；False 时返回 None

    说明：`npx skills add --all` 会把全部技能装进同一容器，兄弟关系成立；
    只安装部分技能时依赖会真的缺失，此时必须显式失败而不是降级。
    """
    candidate = SKILLS_ROOT / name
    if candidate.is_dir():
        return candidate
    if not required:
        return None
    siblings = _siblings()
    raise SkillNotFound(
        f"框架依赖的技能 `{name}` 未找到。技能容器为 `{SKILLS_ROOT}`，"
        f"其中现有 {len(siblings)} 个技能：{', '.join(siblings) or '（空）'}。\n"
        f"修复：整套安装 `npx skills add <owner>/<repo> --all`，"
        f"或单独补装 `npx skills add <owner>/<repo> --skill {name}`。"
    )


def templates_deliverables() -> Path:
    """交付模板目录。首选 template-processor 技能内，回退历史仓库根布局。"""
    in_skill = SKILLS_ROOT / TEMPLATE_SKILL / "templates" / "deliverables"
    if in_skill.is_dir():
        return in_skill
    legacy = FRAMEWORK_ROOT / "templates" / "deliverables"
    if legacy.is_dir():
        return legacy
    raise SkillNotFound(
        f"交付模板目录不存在：期望 `{in_skill}`。"
        f"`{TEMPLATE_SKILL}` 技能可能未安装；请用 `--all` 安装整套技能。"
    )


def gherkin_engine() -> Path:
    """规格门禁引擎路径，供 bdd_gate 按路径加载（不复制规则）。"""
    engine = skill_dir(GHERKIN_SKILL) / "scripts" / "gherkin_gate.py"
    if not engine.is_file():
        raise SkillNotFound(f"规格门禁引擎缺失：`{engine}`")
    return engine


def features_dir() -> Path:
    """业务场景规格根目录（`.feature` 唯一事实源）。"""
    return skill_dir(GHERKIN_SKILL) / "features"


def odoo_implementation_dir(required: bool = False) -> Optional[Path]:
    """
    Odoo 实施契约技能目录。

    这是**可选**扩展：默认 required=False，技能未安装时返回 None 而不抛错，
    使既有流水线在只安装核心技能时仍原样工作。显式 required=True 时才走
    skill_dir 的强校验与安装提示，供主动启用契约校验的调用方使用。
    """
    return skill_dir(ODOO_IMPLEMENTATION_SKILL, required=required)


def agents_dir() -> Path:
    """能力单元（提示型代理）目录，随 orchestrator 技能一起分发。"""
    return SKILL_ROOT / "agents"


def registry_path() -> Path:
    """能力注册表文件，随 orchestrator 技能一起分发。"""
    return SKILL_ROOT / "capability_registry.json"


def default_run_dir() -> Path:
    """
    运行时产物根目录，恒为 `<工作区>/capability_twin_runs`。

    不看安装布局：产物属于用户项目，不属于技能包。技能目录可能被 npx 更新覆盖，
    写进去会丢；而仓库布局下从仓库根运行，工作区即仓库根，行为与历史一致。
    """
    return workspace_root() / "capability_twin_runs"


def workspace_root() -> Path:
    """
    用户项目的产出根目录（`docs/`、`kb/` 等写在这里，不属于技能包）。

    优先级：环境变量 CAPABILITY_TWIN_WORKSPACE > 当前工作目录。
    绝不回退到 `__file__` 的相对深度 —— 技能装在哪里与产出写在哪里无关，
    用文件位置推测工作区会在安装布局下把产物写进 agent 的只读目录。
    """
    import os
    env = os.environ.get("CAPABILITY_TWIN_WORKSPACE")
    return Path(env).expanduser().resolve() if env else Path.cwd()


def tool_script(name: str) -> Path:
    """随 orchestrator 分发的工具脚本（如 odoo_module_graph.py）。"""
    script = SCRIPT_DIR / name
    if not script.is_file():
        raise SkillNotFound(f"框架工具脚本缺失：`{script}`")
    return script


def diagnostics() -> Dict[str, object]:
    """一次性输出全部解析结果，用于问题定位与安装自检。"""
    try:
        tpl = str(templates_deliverables())
        tpl_source = "skill" if SKILLS_ROOT in Path(tpl).parents else "legacy"
    except SkillNotFound as exc:
        tpl, tpl_source = f"<missing: {exc}>", "missing"
    return {
        "layout": installed_as(),
        "framework_root": str(FRAMEWORK_ROOT),
        "skills_root": str(SKILLS_ROOT),
        "skill_root": str(SKILL_ROOT),
        "siblings": _siblings(),
        "templates": tpl,
        "templates_source": tpl_source,
        "features": str(SKILLS_ROOT / GHERKIN_SKILL / "features"),
        "agents": str(agents_dir()),
        "registry": str(registry_path()),
        "run_dir": str(default_run_dir()),
    }


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
    missing = [k for k in ("templates", "features")
               if not Path(str(diagnostics()[k])).exists()]
    sys.exit(1 if missing else 0)
