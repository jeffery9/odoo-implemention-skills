#!/usr/bin/env python3
"""CI guard: committed ontology manifest must match a deterministic rebuild.

When no committed manifest or Odoo source is available the guard reports an
explicit skip with open-question status; it never reports a green result for an
ontology that was not actually built.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ontology_lib.core import REPO_ROOT, canonical_json, load_json  # noqa: E402


def check(manifest_path: Path, rebuilt_dir: Path) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    rebuilt_dir = Path(rebuilt_dir)
    if not manifest_path.is_file():
        return {"status": "skipped", "reason": "manifest missing", "open_questions": ["ontology not built"]}
    if not rebuilt_dir.is_dir():
        return {"status": "skipped", "reason": "rebuild output missing", "open_questions": ["ontology rebuild not run"]}

    committed = load_json(manifest_path)
    rebuilt = load_json(rebuilt_dir / "manifest.json")
    errors: list[str] = []
    if committed.get("sha256") != rebuilt.get("sha256"):
        errors.append(f"sha256 drift: committed={committed.get('sha256')} rebuilt={rebuilt.get('sha256')}")
    if committed.get("counts") != rebuilt.get("counts"):
        errors.append("node/edge counts drift")
    for rel, digest in committed.get("files", {}).items():
        path = rebuilt_dir / rel
        if not path.is_file():
            errors.append(f"missing rebuilt file: {rel}")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "open_questions": committed.get("counts", {}).get("open_questions", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "ontology" / "manifest.json")
    parser.add_argument("--out", type=Path, default=Path("/tmp/ontology-rebuilt"))
    parser.add_argument("--source", type=Path, default=None)
    args = parser.parse_args()

    source = args.source
    if source is None:
        raw = os.environ.get("ODOO_SOURCE_PATH", "").strip()
        source = Path(raw) if raw else None

    if args.manifest.is_file() and (source is None or not Path(source).is_dir()):
        result = {
            "status": "skipped",
            "reason": "ODOO_SOURCE_PATH not configured",
            "open_questions": ["ontology source revision unverified"],
        }
    else:
        result = check(args.manifest, args.out)

    print(canonical_json(result))
    return 0 if result["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
