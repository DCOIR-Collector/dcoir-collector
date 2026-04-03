#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fenced(text: str) -> str:
    return f"```powershell\n{text}\n```"


def bullet_list(items: List[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def status_list(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "- none"
    lines = []
    for item in items:
        lines.append(f"- **{item.get('name','unnamed')}**: {item.get('status','unknown')} — {item.get('details','')}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a DCOIR collector QA markdown report.")
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--manual-json")
    parser.add_argument("--repair-plan-json")
    parser.add_argument("--md-out", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    audit = load_json(Path(args.audit_json))
    manual = load_json(Path(args.manual_json)) if args.manual_json else {}
    repair_plan = load_json(Path(args.repair_plan_json)) if args.repair_plan_json else {}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_posture = manual.get("run_posture", "hybrid")
    executed_checks = manual.get("executed_checks", [])
    findings = list(audit.get("findings", [])) + list(manual.get("findings", []))
    fixes = manual.get("recommended_fixes", [])
    known_lane = manual.get("known_failure_lane", audit.get("known_failure_lane", {}))

    source_inventory = []
    for key, record in audit.get("sources", {}).items():
        if not record:
            continue
        source_inventory.append(f"- **{key}**: `{record['filename']}` ({record['bytes']} bytes)")

    static_results = []
    alias = audit.get("runtime_alias", {})
    static_results.append(
        f"- runtime alias support: manifest/layout={alias.get('manifest_and_layout_support_alias')} ; harness-targeting={alias.get('harness_targets_runtime_alias')}"
    )
    harness = audit.get("harness", {})
    static_results.append(f"- harness suites discovered: {', '.join(harness.get('suite_names', [])) or 'none'}")
    output_markers = audit.get("output_contract", {}).get("marker_status", {})
    static_results.append(
        "- output-contract markers: " + ", ".join(f"{k}={v}" for k, v in output_markers.items())
    )

    doc = audit.get("documentation_health", {})
    doc_results = [
        f"- file-level comment-based help present: {doc.get('file_comment_help_present')}",
        f"- function count: {doc.get('function_count')}",
        f"- documented function count: {doc.get('documented_function_count')}",
        f"- undocumented function count: {doc.get('undocumented_function_count')}",
    ]
    undocumented = doc.get("undocumented_functions_sample", [])
    if undocumented:
        doc_results.append("- undocumented function sample: " + ", ".join(undocumented[:10]))

    blocked = []
    if not executed_checks:
        blocked.append({
            "name": "local-or-in-chat execution lanes",
            "status": "planned-not-executed",
            "details": "No manual execution evidence was supplied to the report renderer.",
        })

    code_blocks = audit.get("maintenance_code_blocks", {})
    code_sections = []
    for name, command in code_blocks.items():
        code_sections.append(f"### {name}\n\n{fenced(command)}")

    repair_candidates = audit.get("repair_candidates", [])
    repair_lines = []
    for item in repair_candidates:
        repair_lines.append(f"- **{item.get('type','unknown')}** — {item.get('target','unknown target')}: {item.get('reason','')}" )
    if not repair_lines:
        repair_lines.append("- none")

    repair_plan_text = "- none"
    if repair_plan:
        repair_plan_text = "\n".join([
            f"- requested mode: {repair_plan.get('requested_mode','repair')}",
            f"- defect summary: {repair_plan.get('defect_summary','')}",
            f"- changed targets: {', '.join(repair_plan.get('changed_targets', [])) or 'none'}",
            f"- documentation actions: {', '.join(repair_plan.get('documentation_actions', [])) or 'none'}",
            f"- validation lanes: {', '.join(repair_plan.get('validation_lanes', [])) or 'none'}",
        ])

    report = f"""# DCOIR Collector QA Report

Generated: {timestamp}

## Scope
Static and hybrid QA review of the current DCOIR collector readable source, harness mirrors, runtime alias rules, documentation health, and preserved known-failure lane.

## Authoritative basis
- `project_sources/DCOIR_Collector.ps1`
- `project_sources/run_DCOIR_Tests.ps1`
- `project_sources/RB-01_DCOIR_Collector_refinement_2_1_3.txt` when present for rollback comparison
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt`
- `project_sources/LOG-01_DCOIR_Todo_Log.txt`, `project_sources/LOG-01_DCOIR_Todo_Index.txt`, and `project_sources/todo/*.txt` when the active work-line split matters to current QA follow-through

## Run posture
- {run_posture}

## Current source inventory
{chr(10).join(source_inventory) if source_inventory else '- none'}

## Static-audit results
{chr(10).join(static_results)}

## Documentation-health results
{chr(10).join(doc_results)}

## Executed checks
{status_list(executed_checks)}

## Blocked or planned-not-executed checks
{status_list(blocked)}

## Known-failure regression lane
- **{known_lane.get('name','gemini-collector-transcript-error')}**: {known_lane.get('status','unknown')}
- {known_lane.get('details','')}

## Maintenance code blocks
{chr(10).join(code_sections) if code_sections else '- none'}

## Repair and documentation candidates
{chr(10).join(repair_lines)}

## Repair-plan summary
{repair_plan_text}

## Findings
{bullet_list(findings)}

## Recommended fixes
{bullet_list(fixes)}

## Next actions
- Recover or paste the exact Gemini collector error excerpt to upgrade the placeholder regression lane into a concrete replay fixture.
- Run representative local or in-chat harness checks when the environment supports them.
- In repair mode, keep changed targets bounded, refresh targeted in-code documentation where it materially improves maintenance, and rerun the motivating regression lane plus at least one known-good control lane before calling the patch validated.
"""

    Path(args.md_out).write_text(report, encoding="utf-8")
    if args.json_out:
        combined = {
            "generated_at": timestamp,
            "audit": audit,
            "manual": manual,
            "repair_plan": repair_plan,
            "report_path": str(Path(args.md_out).resolve()),
        }
        Path(args.json_out).write_text(json.dumps(combined, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
