#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from lib.gemini_behavioral_replay_reporting import write_reports
from lib.gemini_behavioral_replay_runner import load_fixtures, load_response_pack
from lib.gemini_behavioral_replay_schema import validate_response_pack_shape
from lib.gemini_behavioral_replay_scoring import score_response_pack


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-root", required=True)
    parser.add_argument("--response-pack", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fixture-id")
    args = parser.parse_args()

    fixtures_root = Path(args.fixtures_root).resolve()
    response_pack = load_response_pack(Path(args.response_pack).resolve())
    output_dir = Path(args.output_dir).resolve()

    fixtures = load_fixtures(fixtures_root, Path(__file__), args.fixture_id)
    if not fixtures:
        raise SystemExit(f"No fixtures matched fixture_id={args.fixture_id!r}")

    results: List[Dict[str, Any]] = []
    target_fixture_id = response_pack.get("fixture_id")
    validation_messages: List[Dict[str, str]] = []

    for row in fixtures:
        fixture = row["fixture"]
        if target_fixture_id and fixture.get("fixture_id") != target_fixture_id:
            continue
        response_messages = validate_response_pack_shape(response_pack, fixture)
        validation_messages.extend(
            {"level": message.level, "message": message.message}
            for message in response_messages
        )
        if any(message.level == "error" for message in response_messages):
            continue
        results.append(score_response_pack(fixture, response_pack))

    if not results and not validation_messages:
        raise SystemExit("Response pack fixture_id did not match any selected fixture.")

    report_paths = write_reports(output_dir, "gemini_behavioral_replay_run_report", results)
    summary = {
        "success": bool(results) and all(result["success"] for result in results) and not any(
            message["level"] == "error" for message in validation_messages
        ),
        "result_count": len(results),
        "validation_messages": validation_messages,
        "report_paths": report_paths,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
