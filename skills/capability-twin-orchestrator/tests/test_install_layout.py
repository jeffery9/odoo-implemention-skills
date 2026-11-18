#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安装布局回归测试（npx skills）

目的：证明框架在「技能被装到 <project>/.claude/skills/ 下」时仍然可运行，
而不是只在源码仓库里碰巧能跑。

测试用的是 `--copy` 语义的真实副本，并且断言：
1. 临时根目录里**不存在**任何源码仓库残留（没有 templates/、agents/、scripts/）；
2. 所有资源路径都解析到技能容器内部；
3. 交付包能渲染，UAT 里是真实场景 ID 而非占位符；
4. 缺依赖技能时抛 SkillNotFound 并带修复提示，不静默降级；
5. 运行时产物写到用户工作区，技能目录文件清单零变化（不被污染）。

若将来有人把路径改回 `parents[N]` 硬编码，本测试会失败。
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent

# 渲染交付包所需的最小技能集合（缺一个就跑不通，正好用于验证依赖判断）
REQUIRED_SKILLS = ("capability-twin-orchestrator", "gherkin-bdd", "template-processor", "quality-gate")

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")


def _snapshot(root: Path) -> set:
    """技能目录的文件相对路径清单，用于检测运行时是否被写入。"""
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


class InstallLayoutTest(unittest.TestCase):
    """在模拟的 .claude/skills 布局下验证框架可用性"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ct_install_"))
        cls.skills = cls.tmp / ".claude" / "skills"
        cls.workspace = cls.tmp / "project"
        cls.skills.mkdir(parents=True)
        cls.workspace.mkdir(parents=True)

        for name in REQUIRED_SKILLS:
            shutil.copytree(SKILLS_ROOT / name, cls.skills / name, ignore=_IGNORE)

        # 记录技能目录初始状态，之后用于「未被污染」断言
        cls.before = _snapshot(cls.skills)

        # 按文件路径加载安装态副本，确保用的是副本里的代码而不是源码树
        sys.path.insert(0, str(cls.skills / "capability-twin-orchestrator" / "scripts"))
        import framework_paths                                    # noqa: E402
        import main as ct_main                                    # noqa: E402

        cls.fp = framework_paths
        cls.ct_main = ct_main
        cls._cwd = Path.cwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._cwd)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        # 产物与相对路径都以工作区为基准，模拟用户项目目录
        os.chdir(self.workspace)

    def test_01_install_root_has_no_repository_leftovers(self):
        """临时根目录必须干净：源码仓库的 templates/、agents/ 不应存在"""
        children = {p.name for p in self.tmp.iterdir()}
        self.assertEqual(children, {".claude", "project"},
                         f"安装根目录出现了非预期内容：{children}")
        self.assertFalse((self.tmp / "templates").exists())
        self.assertFalse((self.tmp / "agents").exists())
        self.assertFalse((self.tmp / "scripts").exists())
        self.assertFalse((self.tmp / "discover_capabilities.py").exists())

    def test_02_layout_detected_as_install(self):
        self.assertEqual(self.fp.installed_as(), "install")

    def test_03_resources_resolve_inside_skill_container(self):
        """所有资源必须在技能容器内，且不得走 legacy 回退"""
        diag = self.fp.diagnostics()
        self.assertEqual(Path(diag["skills_root"]).resolve(),
                         self.skills.resolve())
        self.assertEqual(diag["templates_source"], "skill",
                         "模板走了历史仓库根回退，说明技能内模板缺失")
        for key in ("templates", "features", "agents", "registry"):
            path = Path(diag[key])
            self.assertTrue(path.exists(), f"{key} 不存在：{path}")
            self.assertIn(self.skills.resolve(), [path.resolve(), *path.resolve().parents],
                          f"{key} 未解析到技能容器内：{path}")

    def test_04_run_dir_is_workspace_scoped(self):
        self.assertEqual(self.fp.default_run_dir().resolve(),
                         (self.workspace / "capability_twin_runs").resolve())

    def test_05_workspace_env_override(self):
        custom = self.tmp / "custom_ws"
        old = os.environ.get("CAPABILITY_TWIN_WORKSPACE")
        os.environ["CAPABILITY_TWIN_WORKSPACE"] = str(custom)
        try:
            self.assertEqual(self.fp.workspace_root().resolve(), custom.resolve())
        finally:
            if old is None:
                os.environ.pop("CAPABILITY_TWIN_WORKSPACE", None)
            else:
                os.environ["CAPABILITY_TWIN_WORKSPACE"] = old

    def test_06_render_bundle_works_and_uses_real_scenarios(self):
        out = self.workspace / "out"
        orch = self.ct_main.CapabilityTwinOrchestratorSkill()
        res = orch.render_deliverables_bundle({
            "bundle_type": "consultant",
            "target_module": "account",
            "output_directory": str(out),
        })
        self.assertEqual(res["status"], "success", f"failed={res['failed']}")
        self.assertEqual(res["failed"], [])
        self.assertEqual(res["blocked_templates"], [])
        self.assertTrue(res["gate"]["satisfies_module"])

        uat = out / "CONSULTANT_UAT_SCRIPT.md"
        self.assertTrue(uat.is_file(), "UAT 脚本未生成")
        text = uat.read_text(encoding="utf-8")
        self.assertIn("SCN-ACC-001", text, "UAT 未注入真实场景编号")
        self.assertNotIn("{{", text, "UAT 存在未替换的模板占位符")

    def test_07_derived_artifacts_go_to_workspace(self):
        """派生的 UAT / 步骤桩 / 矩阵应落在工作区，而非技能包"""
        # 独立触发一次渲染，避免依赖 test_06 的执行顺序
        self.ct_main.CapabilityTwinOrchestratorSkill().render_deliverables_bundle({
            "bundle_type": "consultant",
            "target_module": "account",
            "output_directory": str(self.workspace / "out_derived"),
        })
        run_dir = self.workspace / "capability_twin_runs" / "bdd" / "account"
        self.assertTrue(run_dir.is_dir(), f"派生产物未落到工作区：{run_dir}")
        uat_files = list((run_dir / "uat").glob("*_UAT.md"))
        self.assertTrue(uat_files, "工作区内未生成 UAT 文件")

    def test_08_skill_tree_not_polluted_by_runtime(self):
        """跑完渲染后，技能目录文件清单必须与安装时一致"""
        after = _snapshot(self.skills)
        self.assertEqual(after - self.before, set(),
                         f"运行时往技能目录写入了文件：{sorted(after - self.before)}")

    def test_09_missing_dependency_fails_loudly(self):
        """只装 orchestrator 时应抛 SkillNotFound，并给出可执行的修复提示"""
        bare = self.tmp / "bare"
        (bare / ".claude" / "skills").mkdir(parents=True)
        shutil.copytree(self.skills / "capability-twin-orchestrator",
                        bare / ".claude" / "skills" / "capability-twin-orchestrator",
                        ignore=_IGNORE)
        probe = (
            "import sys\n"
            f"sys.path.insert(0, {str(bare / '.claude' / 'skills' / 'capability-twin-orchestrator' / 'scripts')!r})\n"
            "import framework_paths as fp\n"
            "try:\n"
            "    fp.gherkin_engine()\n"
            "    print('NO_ERROR')\n"
            "except fp.SkillNotFound as exc:\n"
            "    print('SKILLNOTFOUND:' + str(exc))\n"
        )
        import subprocess
        proc = subprocess.run([sys.executable, "-c", probe],
                              capture_output=True, text=True, cwd=str(self.workspace))
        out = proc.stdout.strip()
        self.assertIn("SKILLNOTFOUND", out, f"未按预期报错：{out} / {proc.stderr[-400:]}")
        self.assertIn("gherkin-bdd", out)
        self.assertIn("--all", out, "错误信息缺少修复命令")

    def test_10_gate_still_blocks_invalid_spec(self):
        """安装态下门禁仍然拦截违规规格（不只是仓库态有效）"""
        bad = self.tmp / "badspec" / "stock"
        bad.mkdir(parents=True)
        (bad / "bad.feature").write_text(
            "# language: zh-CN\n@ct-module=stock\n功能: 坏规格\n  场景: 缺标签\n    假如 有库存\n",
            encoding="utf-8")

        orch = self.ct_main.CapabilityTwinOrchestratorSkill()
        res = orch.render_deliverables_bundle({
            "bundle_type": "consultant",
            "target_module": "stock",
            "output_directory": str(self.workspace / "out_bad"),
            "bdd": {"features_dir": str(self.tmp / "badspec")},
        })
        # consultant 包里的场景类模板是 CONSULTANT_UAT_SCRIPT（SCENARIO_SOLUTION 属其他包）
        self.assertIn("CONSULTANT_UAT_SCRIPT", res["blocked_templates"],
                      "违规规格未被拦截，场景类模板仍被渲染")


if __name__ == "__main__":
    unittest.main(verbosity=2)
