#!/usr/bin/env python3
"""Governance A+ documentation guard.

Keeps the repository-level baseline source of truth consistent:
1. The baseline commit in docs/项目维护指南.md §1 is an ancestor of HEAD.
2. The passed count in §1 equals the count supplied by the current CI run.
3. No stale "pending CI" wording remains in tracked docs.
4. Other docs do not copy the full-suite passed count (single source of truth).
5. Package docs point to §1 instead of keeping their own baseline.

Local logic check:  python scripts/check_docs_baseline.py --self-test
CI gate check:      python scripts/check_docs_baseline.py --test-count "$TEST_COUNT"
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASELINE_DOC = Path("docs/项目维护指南.md")
PASS_RE = re.compile(r"(\d+)\s+passed")
COMMIT_ROW_RE = re.compile(r"^\|\s*基线提交\s*\|\s*`?([0-9a-f]{7,40})`?")
TEST_ROW_RE = re.compile(r"^\|\s*全量测试\s*\|(.*?)\|\s*$")
STALE_RE = re.compile(r"待\s*CI\s*(复核|验收)")
STALE_GAP_RE = re.compile(r"GAP-001.*幂等键未真正生效")
META_MARKERS = ("守卫", "禁止", "扫描", "规则", "过期时态", "过时")
POINTER_DOCS = (
    Path("skills/odoo-implementation/MAINTENANCE.md"),
    Path("skills/odoo-implementation/TODO.md"),
)
SKIP_DIRS = {"retired", ".git", ".workbuddy", "__pycache__", "node_modules"}


def markdown_files(repo: Path):
    for path in sorted(repo.rglob("*.md")):
        if SKIP_DIRS.intersection(path.parts):
            continue
        yield path


def parse_baseline(repo: Path):
    """Return (commit, passed_count) from the §1 baseline table."""
    commit = None
    count = None
    path = repo / BASELINE_DOC
    if not path.is_file():
        raise ValueError(f"missing baseline source of truth: {BASELINE_DOC}")
    for line in path.read_text(encoding="utf-8").splitlines():
        if commit is None:
            match = COMMIT_ROW_RE.match(line)
            if match:
                commit = match.group(1)
        match = TEST_ROW_RE.match(line)
        if match:
            passed = PASS_RE.search(match.group(1))
            if passed:
                count = int(passed.group(1))
    if not commit:
        raise ValueError(f"no baseline commit row in {BASELINE_DOC}")
    if count is None:
        raise ValueError(f"no 'N passed' value in {BASELINE_DOC} §1")
    return commit, count


def scan_stale(repo: Path):
    hits = []
    for path in markdown_files(repo):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            meta = any(marker in line for marker in META_MARKERS)
            if not meta and (STALE_RE.search(line) or STALE_GAP_RE.search(line)):
                hits.append(f"{path.relative_to(repo)}:{lineno}: stale wording: {line.strip()}")
    return hits


def scan_single_source(repo: Path):
    hits = []
    for path in markdown_files(repo):
        if path == repo / BASELINE_DOC:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "全量测试" in line and PASS_RE.search(line):
                hits.append(
                    f"{path.relative_to(repo)}:{lineno}: copied suite count; "
                    f"point to {BASELINE_DOC} §1 instead"
                )
    return hits


def scan_pointers(repo: Path):
    hits = []
    for rel in POINTER_DOCS:
        path = repo / rel
        if not path.is_file():
            hits.append(f"{rel}: missing pointer document")
            continue
        found = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "全量测试" in line:
                found = True
                if "项目维护指南.md" not in line or "§1" not in line:
                    hits.append(f"{rel}:{lineno}: must point to {BASELINE_DOC} §1")
        if not found:
            hits.append(f"{rel}: no '全量测试' row to validate")
    return hits


def is_ancestor(repo: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    # merge-base returns 1 when the commit is not an ancestor and 128 when the
    # object does not exist in this checkout; both are guard failures.
    return result.returncode == 0


def check(repo: Path, expected_count: int | None) -> list[str]:
    errors: list[str] = []
    commit, documented_count = parse_baseline(repo)
    if not is_ancestor(repo, commit):
        errors.append(f"baseline commit {commit} is not an ancestor of HEAD")
    if expected_count is not None and documented_count != expected_count:
        errors.append(
            f"suite count drift: documented={documented_count} ci={expected_count} "
            f"({BASELINE_DOC} §1)"
        )
    errors.extend(scan_stale(repo))
    errors.extend(scan_single_source(repo))
    errors.extend(scan_pointers(repo))
    return errors


def self_test() -> None:
    """Validate parsers and scanners without touching the real repository."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        doc_dir = repo / "docs"
        doc_dir.mkdir()
        (doc_dir / "项目维护指南.md").write_text(
            "| 基线提交 | `331257b`（验证） |\n"
            "| 全量测试 | `265 passed, 5 warnings, 4 subtests passed` |\n",
            encoding="utf-8",
        )
        assert parse_baseline(repo) == ("331257b", 265)
        (doc_dir / "stale.md").write_text("全量测试 待 CI 复核\n", encoding="utf-8")
        assert scan_stale(repo), "stale wording was not detected"
        (doc_dir / "stale.md").write_text(
            "守卫会扫描「待 CI 复核」等表述\n", encoding="utf-8"
        )
        assert not scan_stale(repo), "meta wording was falsely flagged"
        memory_dir = repo / ".workbuddy"
        memory_dir.mkdir()
        (memory_dir / "note.md").write_text("历史记录：待 CI 复核\n", encoding="utf-8")
        assert not scan_stale(repo), "workspace memory was falsely flagged"
        (doc_dir / "copy.md").write_text("| 全量测试 | 265 passed |\n", encoding="utf-8")
        assert scan_single_source(repo), "copied suite count was not detected"
        (doc_dir / "copy.md").unlink()
        pkg = repo / "skills/odoo-implementation"
        pkg.mkdir(parents=True)
        for name in ("MAINTENANCE.md", "TODO.md"):
            (pkg / name).write_text(
                "| 全量测试 | 见 `docs/项目维护指南.md` §1 |\n", encoding="utf-8"
            )
        assert not scan_pointers(repo), "valid pointers were falsely flagged"
        (pkg / "TODO.md").write_text("| 全量测试 | 本地基线 |\n", encoding="utf-8")
        assert scan_pointers(repo), "missing pointer was not detected"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--test-count", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("docs baseline self-test: PASS")
        if args.test_count is None:
            return 0
    repo = args.repo.resolve()
    errors = check(repo, args.test_count)
    if errors:
        print("docs baseline guard: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    commit, count = parse_baseline(repo)
    print(f"docs baseline guard: PASS (commit={commit}, passed={count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
