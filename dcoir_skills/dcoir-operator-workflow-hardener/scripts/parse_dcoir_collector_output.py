#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

KEY_RE = re.compile(r'^(?P<key>[A-Z0-9_]+)=(?P<value>.*)$')


def classify_phase(markers: Dict[str, str], lines: List[str]) -> str:
    text = "\n".join(lines)
    if markers.get("CLEANUP_STATUS") == "COMPLETE":
        return "cleanup_complete"
    if "ENRICH_BUNDLE_PATH" in markers or "Retrieve DCOIR enrich bundle" in text:
        return "enrich_bundle_ready"
    if "COLLECT_BUNDLE_PATH" in markers or "Retrieve DCOIR collect bundle" in text:
        return "collect_bundle_ready"
    if "enrich" in text.lower() and ("current DCOIR session" in text or "enrich session" in text.lower()):
        return "enrich_session_active"
    if "ANALYST_INTERPRETATION_GUIDE" in text or "review" in text.lower():
        return "interpretation_guidance"
    return "unknown"


def parse_lines(lines: List[str]) -> Dict[str, object]:
    markers: Dict[str, str] = {}
    quick_steps: List[str] = []
    for raw in lines:
        line = raw.strip()
        m = KEY_RE.match(line)
        if m:
            markers[m.group("key")] = m.group("value")
        elif re.match(r'^\d+\.\s+', line):
            quick_steps.append(line)
    phase = classify_phase(markers, lines)
    return {
        "phase": phase,
        "markers": markers,
        "has_next_get_file": "NEXT_GET_FILE" in markers,
        "has_cleanup_command": "CLEANUP_COMMAND" in markers,
        "has_delete_script_command": "DELETE_SCRIPT_COMMAND" in markers,
        "quick_steps": quick_steps,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize DCOIR collector output into a small JSON summary.")
    ap.add_argument("--input-file", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_json)
    lines = input_path.read_text(encoding="utf-8").splitlines()
    summary = parse_lines(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
