#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
context-memory-manager 测试。

## 这个文件曾经的问题（保留说明，避免有人改回去）

旧版本测的是一个**从未实现过**的 API：`ContextMemoryManager.store_context /
retrieve_context / update_preferences / get_user_context_summary / clear_context`，
那是技能早期的设计稿，`scripts/main.py` 改写成 OpenClaw 三层记忆后只剩
`MemoryManager.remember / recall / snapshot_run`。旧测试的写法是

    except Exception:
        return False

于是 `ImportError` 被吞掉，测试函数返回 `False`。pytest 只把非 None 返回值视作
`PytestReturnNotNoneWarning`，**不计为失败**——这个文件因此长期「绿着」，实际上
一行断言都没执行过。现在的原则：断言失败就是失败，异常就向上抛。

## 隔离措施

各技能的实现都叫 `scripts/main.py`，测试若写 `from main import ...` 会命中
`sys.modules["main"]` 缓存，拿到别家技能的模块。本文件按**文件路径**加载实现，
挂在唯一模块名 `ctm_main` 下，与收集顺序无关。
"""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _load_impl():
    """按路径加载本技能实现，避免与其它技能的 scripts/main.py 撞名。"""
    spec = importlib.util.spec_from_file_location("ctm_main", SCRIPTS / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryManagerTest(unittest.TestCase):
    """MemoryManager 的三层记忆契约：语义事实 / 使用模式 / 运行快照"""

    @classmethod
    def setUpClass(cls):
        cls.impl = _load_impl()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="ctm_")
        self.kb = Path(self._tmp.name) / "kb" / "mem"
        self.manager = self.impl.MemoryManager(self.kb)

    def tearDown(self):
        self._tmp.cleanup()

    # --- 存储初始化 ---------------------------------------------------

    def test_init_creates_storage_files(self):
        """首次使用时自动建立 JSONL 文件，调用方不必预建目录"""
        self.assertTrue(self.kb.is_dir())
        self.assertTrue((self.kb / "long_term_facts.jsonl").is_file())
        self.assertTrue((self.kb / "usage_patterns.jsonl").is_file())

    # --- remember -----------------------------------------------------

    def test_remember_fact_appends_one_jsonl_line(self):
        """一次 remember 只追加一行 JSONL，而非重写整个文件"""
        self.manager.remember("fact", "mrp_consumption", "以 _action_confirm 触发库存检查",
                              {"module": "mrp", "version": "19.0"})
        self.manager.remember("fact", "account_lock", "过账后不可改金额")

        lines = (self.kb / "long_term_facts.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        self.assertEqual(first["key"], "mrp_consumption")
        self.assertEqual(first["metadata"], {"module": "mrp", "version": "19.0"})
        self.assertTrue(first["timestamp"])

    def test_remember_pattern_goes_to_separate_file(self):
        """fact 与 pattern 分文件存放，互不污染"""
        self.manager.remember("pattern", "wizard_default_get", "先 super 再取默认值")

        facts = (self.kb / "long_term_facts.jsonl").read_text(encoding="utf-8")
        patterns = (self.kb / "usage_patterns.jsonl").read_text(encoding="utf-8")
        self.assertEqual(facts.strip(), "")
        self.assertIn("wizard_default_get", patterns)

    def test_remember_rejects_unknown_category(self):
        """拼错 category 必须报错：否则会静默落到 usage_patterns 里查不到"""
        with self.assertRaises(ValueError) as ctx:
            self.manager.remember("facts", "k", "v")
        self.assertIn("facts", str(ctx.exception))

    def test_remember_rejects_empty_key(self):
        with self.assertRaises(ValueError):
            self.manager.remember("fact", "", "v")

    # --- recall -------------------------------------------------------

    def test_recall_empty_store_returns_empty_dict(self):
        self.assertEqual(self.manager.recall("fact"), {})

    def test_recall_latest_entry_wins(self):
        """同一 key 多次写入按「后写覆盖」读取，且不删除历史行"""
        self.manager.remember("fact", "res_currency_rounding", "旧值")
        self.manager.remember("fact", "res_currency_rounding", "新值")

        result = self.manager.recall("fact")
        self.assertEqual(result["res_currency_rounding"]["value"], "新值")
        # 历史行仍在（append-only，便于审计），只是读取时取最新
        lines = (self.kb / "long_term_facts.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)

    def test_recall_query_filters_by_key_case_insensitively(self):
        self.manager.remember("fact", "MRP_consumption", "a")
        self.manager.remember("fact", "account_lock", "b")

        self.assertEqual(list(self.manager.recall("fact", "mrp")), ["MRP_consumption"])
        self.assertEqual(list(self.manager.recall("fact", "ACCOUNT")), ["account_lock"])
        self.assertEqual(self.manager.recall("fact", "stock"), {})

    def test_recall_reports_corrupted_line_with_location(self):
        """坏行要指出文件与行号；静默返回空字典等于丢数据"""
        path = self.kb / "long_term_facts.jsonl"
        path.write_text('{"key": "ok", "value": 1}\n不是 JSON\n', encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            self.manager.recall("fact")
        self.assertIn("long_term_facts.jsonl:2", str(ctx.exception))

    def test_recall_tolerates_missing_optional_fields(self):
        """手工写入的非标准记录（缺 metadata/timestamp）不应让整个查询崩掉"""
        path = self.kb / "long_term_facts.jsonl"
        path.write_text('{"key": "legacy"}\n', encoding="utf-8")

        result = self.manager.recall("fact")["legacy"]
        self.assertIsNone(result["value"])
        self.assertEqual(result["metadata"], {})

    # --- snapshot -----------------------------------------------------

    def test_snapshot_run_writes_jsonl_under_kb(self):
        path = self.manager.snapshot_run("run-001", {"step": 11, "module": "mrp"})

        self.assertEqual(path, self.kb / "snapshots" / "run-001.jsonl")
        payload = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual(payload, {"step": 11, "module": "mrp"})

    def test_snapshot_rejects_empty_run_id(self):
        with self.assertRaises(ValueError):
            self.manager.snapshot_run("", {"step": 1})


class CliContractTest(unittest.TestCase):
    """技能通过 Skill(...) 以命令行 JSON 参数调用，stdout 必须是可解析的 JSON"""

    @classmethod
    def setUpClass(cls):
        cls.impl = _load_impl()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="ctm_cli_")
        self.workspace = Path(self._tmp.name) / "workspace"
        self.workspace.mkdir()
        self._cwd = Path.cwd()
        self._argv = sys.argv

    def tearDown(self):
        sys.argv = self._argv
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _run(self, payload, workspace=None):
        """以 CLI 方式调用 main()，返回 stdout 的 JSON 与退出码（本实现恒为 0）。"""
        sys.argv = ["main.py", json.dumps(payload)]
        env = {"CAPABILITY_TWIN_WORKSPACE": str(workspace or self.workspace)}
        original = os.environ.get("CAPABILITY_TWIN_WORKSPACE")
        os.environ["CAPABILITY_TWIN_WORKSPACE"] = env["CAPABILITY_TWIN_WORKSPACE"]
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                code = self.impl.main()
        finally:
            if original is None:
                os.environ.pop("CAPABILITY_TWIN_WORKSPACE", None)
            else:
                os.environ["CAPABILITY_TWIN_WORKSPACE"] = original
        text = buf.getvalue().strip()
        return (json.loads(text) if text else None), code

    def test_remember_then_recall_roundtrip(self):
        out, _ = self._run({"operation": "remember", "category": "fact",
                            "key": "mrp_posting", "value": "过账时校验库存",
                            "metadata": {"module": "mrp"}})
        self.assertEqual(out, {"status": "success", "operation": "remember"})

        out, _ = self._run({"operation": "recall", "category": "fact", "query": "mrp"})
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["data"]["mrp_posting"]["value"], "过账时校验库存")

    def test_cli_writes_into_workspace_not_cwd(self):
        """产物必须落在工作区：技能装在哪、进程 CWD 在哪都不影响"""
        elsewhere = Path(self._tmp.name) / "elsewhere"
        elsewhere.mkdir()
        os.chdir(elsewhere)

        self._run({"operation": "remember", "key": "k", "value": "v"})

        self.assertTrue((self.workspace / "kb" / "mem" / "long_term_facts.jsonl").is_file())
        self.assertFalse((elsewhere / "kb").exists())

    def test_cli_snapshot_operation(self):
        out, _ = self._run({"operation": "snapshot", "run_id": "run-xyz",
                            "context": {"step": 13}})
        self.assertEqual(out["status"], "success")
        snap = self.workspace / "kb" / "mem" / "snapshots" / "run-xyz.jsonl"
        self.assertTrue(snap.is_file())

    def test_cli_unknown_operation_reports_error(self):
        out, _ = self._run({"operation": "remeber", "key": "k"})
        self.assertEqual(out["status"], "error")
        self.assertIn("remeber", out["message"])

    def test_cli_invalid_json_arguments_reports_error(self):
        sys.argv = ["main.py", "{not json"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.impl.main()
        self.assertEqual(json.loads(buf.getvalue().strip())["status"], "error")

    def test_cli_without_arguments_is_silent(self):
        sys.argv = ["main.py"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.impl.main()
        self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
