#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
可移植性守卫：仓库内不允许出现机器特定的绝对路径。

背景：这批脚本曾经把 `/Users/<某人>/odoo19-study/CT/...`、
`/Users/<某人>/_project/.../odoo-19.0` 直接写成常量。后果有三个：

1. 换机器、换用户名、换挂载点即失效，报错位置离真因很远；
2. 把个人目录结构提交进公开仓库；
3. 更隐蔽的一种：代码里写 `<父目录>/CAPABILITY_TWIN/...`，看似相对路径，
   实际把仓库目录名也一起写死了，`git worktree` 或改名后立刻错位。

本测试扫描受版本控制的文本文件，发现上述模式即失败。
`docs/` 下的历史评审记录引用这些路径作为缺陷证据，故排除。
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
# 历史脚本统一收口在 scripts/，legacy_paths 从仓库根迁至此处
sys.path.insert(0, str(REPO_ROOT / "scripts"))

TEXT_SUFFIXES = {".py", ".md", ".json", ".sh", ".yaml", ".yml",
                 ".toml", ".feature", ".txt", ".cfg", ".ini"}

#: 机器相关的家目录绝对路径
HOME_PATH_PATTERNS = (
    ("macOS 家目录", re.compile(r"/Users/[A-Za-z0-9._-]+/")),
    ("Linux 家目录", re.compile(r"/home/[A-Za-z0-9._-]+/")),
    ("Windows 家目录", re.compile(r"[A-Za-z]:\\+[Uu]sers\\+")),
)

#: 把仓库目录名当路径前缀用（看似相对、实则写死目录名）
FIXED_REPO_NAME = re.compile(r"""["']CAPABILITY_TWIN/""")

#: 本文件自身包含上述模式的字面量，须排除
SELF_RELATIVE = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

#: 历史评审文档刻意保留缺陷证据，不参与扫描
EXCLUDED_PREFIXES = ("docs/", "capability_twin_runs/", ".workbuddy/")


def _tracked_files():
    """参与扫描的文件：已跟踪 + 未跟踪但未被忽略。

    包含未跟踪文件是有意的 —— 守卫要在 `git add` 之前就能拦住新写进去的路径。
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        names = [n for n in out.split("\0") if n]
    except (subprocess.CalledProcessError, FileNotFoundError):
        names = [p.relative_to(REPO_ROOT).as_posix()
                 for p in REPO_ROOT.rglob("*") if p.is_file()]
    return [n for n in names if not n.startswith(EXCLUDED_PREFIXES)]


class PortabilityGuardTest(unittest.TestCase):

    def test_no_machine_specific_paths(self):
        """任何受版本控制的文本文件都不得包含家目录绝对路径"""
        offenders = []
        for rel in _tracked_files():
            if rel == SELF_RELATIVE or Path(rel).suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
            for label, pattern in HOME_PATH_PATTERNS:
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    offenders.append(f"{rel}:{line}  {label}  {match.group(0)}")

        self.assertEqual(offenders, [],
                         "发现机器特定路径，请改为环境变量或命令行参数：\n  "
                         + "\n  ".join(offenders))

    def test_no_hardcoded_repository_directory_name(self):
        """不得用 `CAPABILITY_TWIN/...` 这样的字面量拼路径"""
        offenders = []
        for rel in _tracked_files():
            if rel == SELF_RELATIVE or Path(rel).suffix != ".py":
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
            for match in FIXED_REPO_NAME.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                offenders.append(f"{rel}:{line}")

        self.assertEqual(offenders, [],
                         "发现写死仓库目录名的路径拼接，请用 Path(__file__).resolve() 推导：\n  "
                         + "\n  ".join(offenders))


class LegacyPathsContractTest(unittest.TestCase):
    """历史脚本的路径解析：必须显式提供，绝不回退到某个默认绝对路径"""

    def setUp(self):
        self._saved = {k: os.environ.pop(k, None)
                       for k in ("CT_LEGACY_REGISTRY", "CT_LEGACY_PROJECT")}

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_missing_location_raises_with_usage(self):
        import legacy_paths

        with self.assertRaises(legacy_paths.UsageError) as ctx:
            legacy_paths.registry_path()
        message = str(ctx.exception)
        self.assertIn("CT_LEGACY_PROJECT", message)
        self.assertIn("--registry", message)

    def test_env_variable_resolves_relative_registry(self):
        import legacy_paths

        os.environ["CT_LEGACY_PROJECT"] = str(REPO_ROOT)
        expected = REPO_ROOT / legacy_paths.REGISTRY_RELATIVE
        self.assertEqual(legacy_paths.registry_path(must_exist=False), expected)

    def test_explicit_ct_dir_implies_registry_location(self):
        """给了 --ct-dir 就不该再要求重复给出注册表路径"""
        import legacy_paths

        expected = REPO_ROOT / legacy_paths.REGISTRY_RELATIVE
        self.assertEqual(
            legacy_paths.registry_path(ct_dir=REPO_ROOT, must_exist=False), expected)

    def test_missing_registry_file_is_reported(self):
        import legacy_paths

        with self.assertRaises(legacy_paths.UsageError):
            legacy_paths.registry_path(str(REPO_ROOT / "no_such_registry.json"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
