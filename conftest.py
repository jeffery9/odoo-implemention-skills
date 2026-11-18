# -*- coding: utf-8 -*-
"""仓库级 pytest 配置。

## 为什么需要它

各技能的实现文件都叫 `scripts/main.py`，对应测试一律写 `from main import <Class>`，
并先执行 `sys.path.insert(0, "<本技能>/scripts")`。

问题在于 Python 的模块缓存按**裸名**索引：`main` 这个槽位被第一个导入它的技能永久占据。
于是第二个技能的 `from main import ...` 命中缓存，拿到的是别人家的模块，抛
`ImportError: cannot import name 'X' from 'main' (.../skills/<别的技能>/scripts/main.py)`。
失败与测试内容无关，纯粹是技能之间的命名撞车，而且结果依赖收集顺序。

在每个测试模块被导入之前清掉 `main` 槽位，即可让 `from main import ...` 重新按该测试
自己刚插入的 `sys.path[0]`（它自己的 `scripts/`）解析。这样既不用改各技能的实现文件，
也不用给 20 多个测试文件逐一加 importlib 样板。

## 为什么忽略 capability_twin_runs/

该目录是运行期产物（已 gitignore），其中 `steps/` 下由 `.feature` 派生的
`test_*_pytest_bdd.py` 依赖可选的 `pytest-bdd`。它们属于交付时的现场生成物，
不是框架自身的测试，收集进来只会让全仓测试依赖于一个非必需的可选包。
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
_RUNS_DIR = _ROOT / "capability_twin_runs"

# 运行期工作区存在时才忽略，避免在干净检出中引入无意义的配置项
if _RUNS_DIR.is_dir():
    collect_ignore = [str(_RUNS_DIR)]


def pytest_collectstart(collector):
    """在收集某个测试模块之前，清掉 `main` 的模块缓存。"""
    if type(collector).__name__ == "Module":
        sys.modules.pop("main", None)
