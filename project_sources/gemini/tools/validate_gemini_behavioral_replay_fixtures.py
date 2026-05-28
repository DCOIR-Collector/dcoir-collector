#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from lib.gemini_behavioral_replay_schema import validate_fixture_shape


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    fixtures_root = Path(args.fixtures_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    index_path = fixtures_root / "index.json"
    index_payload = load_json(index_path)
    fixture_entries = index_payload.get("fixtures", [])

    report_rows: List[Dict[str, Any]] = []
    errors: List[str] = []

    for entry in fixture_entries:
        fixture_path = Path(entry["path"])
        if not fixture_path.is_absolute():
            fixture_path = (repo_root / fixture_path).resolve()
        fixture_payload = load_json(fixture_path)
        messages = validate_fixture_shape(fixture_payload)
        report_rows.append(
            {
                "fixture_id": fixture_payload.get("fixture_id", entry.get("fixture_id")),
                "path": str(fixture_path),
                "messages": [
                    {"level": message.level, "message": message.message}
                    for message in messages
                ],
                "success": not any(message.level == "error" for message in messages),
            }
        )
        for message in messages:
            if message.level == "error":
                errors.append(message.message)

    report = {
        "success": len(errors) == 0,
        "fixture_family": index_payload.get("fixture_family"),
        "fixture_count": len(fixture_entries),
        "model_split": index_payload.get("model_split", {}),
        "rows": report_rows,
        "errors": errors,
    }

    report_path = output_dir / "validate_gemini_behavioral_replay_fixtures_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
