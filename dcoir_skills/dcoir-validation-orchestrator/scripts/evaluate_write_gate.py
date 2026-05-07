#!/usr/bin/env python3
"""Validation-only evaluator for DCOIR Write Gate proposed-action JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = [
    "target",
    "action_type",
    "authority_basis",
    "payload_or_record_identity",
    "schema_evidence",
    "duplicate_dependency_checks",
    "approval_scope",
    "execution_lane",
    "readback_plan",
    "evidence_destination",
    "failure_repair_plan",
]

HIGH_RISK_ACTIONS = {
    "process_delete_queue",
    "merge_records",
    "schema_change",
    "field_default_change",
    "repo_file_change",
    "skill_change",
    "workflow_or_tool_run",
    "automation_implementation",
}

SCHEMA_SENSITIVE_ACTIONS = {
    "create_record",
    "update_record",
    "retire_record",
    "queue_delete_request",
    "process_delete_queue",
    "merge_records",
    "schema_change",
    "field_default_change",
    "validation_evidence_write",
    "checkpoint_write",
    "lifecycle_ledger_write",
    "planning_note_write",
}


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def truthy_field(obj: Dict[str, Any], names: List[str]) -> bool:
    for name in names:
        if bool(obj.get(name)):
            return True
    return False


def evaluate(action: Dict[str, Any]) -> Dict[str, Any]:
    missing: List[str] = [field for field in REQUIRED_FIELDS if not is_present(action.get(field))]
    risks: List[str] = []
    conditions: List[str] = []
    repairs: List[str] = []

    action_type = str(action.get("action_type", "")).strip()
    hard_stops = action.get("hard_stop_conflicts") or []
    if isinstance(hard_stops, str):
        hard_stops = [hard_stops] if hard_stops.strip() else []

    approval = action.get("approval_scope") if isinstance(action.get("approval_scope"), dict) else {}
    schema = action.get("schema_evidence") if isinstance(action.get("schema_evidence"), dict) else {}
    dupdep = action.get("duplicate_dependency_checks") if isinstance(action.get("duplicate_dependency_checks"), dict) else {}
    lane = action.get("execution_lane") if isinstance(action.get("execution_lane"), dict) else {}
    target = action.get("target") if isinstance(action.get("target"), dict) else {}

    approval_required = bool(approval.get("required")) or action_type in HIGH_RISK_ACTIONS
    approval_present = bool(approval.get("present"))

    if hard_stops:
        risks.extend([f"hard stop: {item}" for item in hard_stops])

    if action.get("secret_exposure") is True:
        risks.append("secret exposure risk")

    if approval_required and not approval_present:
        if action_type in HIGH_RISK_ACTIONS:
            risks.append("high-risk action lacks explicit approval")
        else:
            conditions.append("approval must be captured before execution")

    if action_type in SCHEMA_SENSITIVE_ACTIONS:
        live_schema = truthy_field(schema, ["live_readback", "live_schema", "fresh_live_schema"])
        cache_only = bool(schema.get("cache_only"))
        if cache_only or not live_schema:
            risks.append("schema-sensitive action lacks fresh live schema evidence")

    if bool(schema.get("requires_refresh")):
        conditions.append("refresh live schema immediately before execution")

    dup_status = str(dupdep.get("duplicate_status", "")).lower()
    dep_status = str(dupdep.get("dependency_status", "")).lower()
    if dup_status in {"blocked", "duplicate", "unresolved", "unknown"}:
        risks.append(f"duplicate status unresolved: {dup_status}")
    if dep_status in {"blocked", "unresolved", "unknown"}:
        risks.append(f"dependency status unresolved: {dep_status}")

    if not truthy_field(lane, ["has_readback", "readback_supported"]):
        risks.append("execution lane does not show readback support")

    if not truthy_field(target, ["record_id", "canonical_key", "file_path", "table_id", "target_id"]):
        risks.append("target identity is not exact enough")

    if missing:
        repairs.append("provide missing required inputs: " + ", ".join(missing))
    if risks:
        repairs.append("resolve listed risks before execution")
    if conditions:
        repairs.append("satisfy named conditions before execution")

    if risks and any(r.startswith("hard stop") or "high-risk" in r or "secret" in r for r in risks):
        result = "STOP_ESCALATE"
    elif missing or risks:
        result = "FAIL"
    elif conditions:
        result = "CONDITIONAL_PASS"
    else:
        result = "PASS"

    return {
        "gate_result": result,
        "missing_required_inputs": missing,
        "risks": risks,
        "conditions": conditions,
        "repair_guidance": repairs or ["no repair required before the selected lane proceeds"],
        "smallest_next_safe_action": _next_action(result, repairs, conditions),
    }


def _next_action(result: str, repairs: List[str], conditions: List[str]) -> str:
    if result == "PASS":
        return "proceed only in the approved lane, then perform readback and evidence capture"
    if result == "CONDITIONAL_PASS":
        return conditions[0] if conditions else "satisfy the named condition, then re-run the gate"
    if result == "FAIL":
        return repairs[0] if repairs else "repair the failed evidence and re-run the gate"
    return "stop and obtain operator decision or authority/safety repair"


def main() -> int:
    parser = argparse.ArgumentParser(description="evaluate a DCOIR Write Gate proposed action")
    parser.add_argument("--input", required=True, help="path to proposed action JSON")
    parser.add_argument("--output", help="optional path for gate report JSON")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = evaluate(data)

    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
