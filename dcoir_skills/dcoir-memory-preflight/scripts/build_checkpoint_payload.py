#!/usr/bin/env python3
"""Build or validate a DCOIR Session Checkpoint payload.

Usage examples:
  python build_checkpoint_payload.py --current-focus "WBS09 planning gate" --active-plan PLAN-AIRTABLE-CLEANUP-RESTRUCTURE --active-work-item CLEANUP-WBS-09-01 --next-move "continue planning-gated WBS09 validation" --print-json
  python build_checkpoint_payload.py --input checkpoint.json --validate-only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_KEYS = [
    "checkpoint_id",
    "session_id",
    "session_mode",
    "current_focus",
    "active_plan",
    "active_work_item",
    "queue_branch",
    "execution_lane",
    "completed_work",
    "pending_work",
    "decisions_constraints",
    "blockers_conflicts",
    "artifacts_or_surfaces",
    "validation_evidence_status",
    "next_recommended_move",
    "resume_prompt",
    "checkpoint_at_utc",
    "trigger",
    "checkpoint_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"failed to read JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("checkpoint payload must be a JSON object")
    return data


def validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"missing required key: {key}")
    for list_key in ["completed_work", "pending_work", "blockers_conflicts", "artifacts_or_surfaces"]:
        if list_key in payload and not isinstance(payload[list_key], list):
            errors.append(f"{list_key} must be a list")
    for text_key in ["current_focus", "next_recommended_move", "trigger", "checkpoint_status"]:
        if text_key in payload and not str(payload[text_key]).strip():
            errors.append(f"{text_key} must not be blank")
    return errors


def split_items(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    ts = utc_now()
    checkpoint_id = args.checkpoint_id or f"CHK-DCOIR-CHECKPOINT-READY-{ts.replace('-', '').replace(':', '').replace('Z', 'Z')}"
    return {
        "checkpoint_id": checkpoint_id,
        "session_id": args.session_id or "session-current-chat",
        "session_mode": args.session_mode or "startup-reanchor-or-closeout",
        "current_focus": args.current_focus or "DCOIR session continuity",
        "active_plan": args.active_plan or "unknown",
        "active_work_item": args.active_work_item or "unknown",
        "queue_branch": args.queue_branch or "unknown",
        "execution_lane": args.execution_lane or "in-session Airtable-first planning",
        "completed_work": split_items(args.completed_work),
        "pending_work": split_items(args.pending_work),
        "decisions_constraints": args.decisions_constraints or "Airtable remains live authority; GitHub only when repo-source work requires it.",
        "blockers_conflicts": split_items(args.blockers_conflicts),
        "artifacts_or_surfaces": split_items(args.artifacts_or_surfaces),
        "validation_evidence_status": args.validation_evidence_status or "checkpoint-ready payload generated; live Airtable write/readback still required for durable checkpoint.",
        "next_recommended_move": args.next_move or "write or verify Session Checkpoint, then resume the active DCOIR branch.",
        "resume_prompt": args.resume_prompt or "Resume AFRICOM_SOC_IR / DCOIR from Airtable-first authority using this checkpoint payload.",
        "checkpoint_at_utc": ts,
        "trigger": args.trigger or "manual checkpoint payload generation",
        "checkpoint_status": args.checkpoint_status or "checkpoint-ready-non-durable",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint-id")
    parser.add_argument("--session-id")
    parser.add_argument("--session-mode")
    parser.add_argument("--current-focus")
    parser.add_argument("--active-plan")
    parser.add_argument("--active-work-item")
    parser.add_argument("--queue-branch")
    parser.add_argument("--execution-lane")
    parser.add_argument("--completed-work")
    parser.add_argument("--pending-work")
    parser.add_argument("--decisions-constraints")
    parser.add_argument("--blockers-conflicts")
    parser.add_argument("--artifacts-or-surfaces")
    parser.add_argument("--validation-evidence-status")
    parser.add_argument("--next-move")
    parser.add_argument("--resume-prompt")
    parser.add_argument("--trigger")
    parser.add_argument("--checkpoint-status")
    args = parser.parse_args()

    payload = load_json(args.input) if args.input else build_payload(args)
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("checkpoint payload valid")
        return 0

    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
        print(str(args.output))
    if args.print_json or not args.output:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
