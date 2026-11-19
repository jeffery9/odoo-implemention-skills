#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
历史项目路径解析（legacy_paths）

`scripts/` 下的 `clean_capability_registry.py`、`clean_extra_components.py`、
`clean_extra_references.py`、`update_capability_registry.py`、`filter_skills.py`
处理的是早期交付目录（下称 CT 项目），不属于框架运行时。这类脚本曾经把
`/Users/<某人>/odoo19-study/CT/...` 直接写成常量，换一台机器或换一个用户名即失效，
且会把个人目录结构泄露进版本库。

解析优先级（越靠前越优先）：

1. 命令行参数：`--registry`、`--ct-dir`
2. 环境变量：`CT_LEGACY_REGISTRY`（注册表文件）、`CT_LEGACY_PROJECT`（CT 项目根）
3. 两者都没有 → 抛 `UsageError`，打印两种可用的调用方式

代码里**不存在**任何默认绝对路径，缺失时必须显式失败。

CT 项目布局约定：

    <ct_dir>/Deliverables_Package/capability_registry.json
    <ct_dir>/skills
    <ct_dir>/agents
"""

import os
from pathlib import Path
from typing import Optional

REGISTRY_ENV = "CT_LEGACY_REGISTRY"
CT_PROJECT_ENV = "CT_LEGACY_PROJECT"

#: CT 项目内注册表的固定相对位置
REGISTRY_RELATIVE = Path("Deliverables_Package") / "capability_registry.json"


class UsageError(RuntimeError):
    """路径未提供或不可用。消息自带修复方法，不做静默猜测。"""


def _hint() -> str:
    return (
        "请显式指定路径，二选一：\n"
        "  1) 命令行：--registry /path/to/CT/Deliverables_Package/capability_registry.json\n"
        f"  2) 环境变量：export {CT_PROJECT_ENV}=/path/to/CT\n"
        f"     或 export {REGISTRY_ENV}=/path/to/capability_registry.json"
    )


def ct_project_dir(explicit: Optional[str] = None) -> Path:
    """定位 CT 项目根目录（含 skills/、agents/、Deliverables_Package/）。"""
    raw = explicit or os.environ.get(CT_PROJECT_ENV)
    if not raw:
        raise UsageError(f"未指定 CT 项目目录。\n{_hint()}")

    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise UsageError(f"CT 项目目录不存在：{path}\n{_hint()}")
    return path


def registry_path(explicit: Optional[str] = None, must_exist: bool = True,
                  ct_dir: Optional[Path] = None) -> Path:
    """定位 capability_registry.json。

    解析顺序：`explicit` > `CT_LEGACY_REGISTRY` > `ct_dir` 参数 >
    `CT_LEGACY_PROJECT` + 固定相对位置。调用方经常直接给了 `--ct-dir`，
    此时不该再要求它重复给一遍注册表路径。
    """
    if explicit:
        path = Path(explicit).expanduser().resolve()
    elif os.environ.get(REGISTRY_ENV):
        path = Path(os.environ[REGISTRY_ENV]).expanduser().resolve()
    elif ct_dir is not None:
        path = Path(ct_dir) / REGISTRY_RELATIVE
    elif os.environ.get(CT_PROJECT_ENV):
        path = ct_project_dir() / REGISTRY_RELATIVE
    else:
        raise UsageError(f"未指定 capability_registry.json。\n{_hint()}")

    if must_exist and not path.is_file():
        raise UsageError(f"注册表文件不存在：{path}\n{_hint()}")
    return path


def output_path(explicit: Optional[str], default: Path) -> Path:
    """输出文件路径：显式给出则用它，否则默认与被处理对象同目录。"""
    return Path(explicit).expanduser().resolve() if explicit else default
