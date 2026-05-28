#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.gemini_behavioral_replay_reporting import render_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-json", required=True)
    parser.add_argument("--output-path", required=True)
    args = parser.parse_args()

    results_json = Path(args.results_json).resolve()
    output_path = Path(args.output_path).resolve()

    payload = json.loads(results_json.read_text(encoding="utf-8"))
    results = payload.get("results", [])
    markdown = render_markdown_report(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    summary = {
        "success": True,
        "result_count": len(results),
        "output_path": str(output_path),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
