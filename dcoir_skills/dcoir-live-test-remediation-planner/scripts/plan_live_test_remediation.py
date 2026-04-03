#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
RULES_PATH = SKILL_ROOT / "references" / "remediation_rules.json"
OUTPUT_MD = "dcoir_live_test_remediation_report.md"
OUTPUT_JSON = "dcoir_live_test_remediation_report.json"


class RemediationError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_rules() -> Dict[str, Any]:
    return json.loads(read_text(RULES_PATH))


def resolve_control_files(source_dir: Path, roles: Dict[str, List[str]]) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    missing: List[str] = []
    for role, candidates in roles.items():
        hit = None
        for candidate in candidates:
            if (source_dir / candidate).exists():
                hit = candidate
                break
        if hit:
            resolved[role] = hit
        else:
            missing.append(role)
    if missing:
        raise RemediationError("remediation planning refused: missing required control-plane role(s): " + ", ".join(missing))
    return resolved


def match_rule(finding: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    text = finding.lower()
    for rule in rules:
        keywords = rule.get("keywords", [])
        if keywords and any(k.lower() in text for k in keywords):
            return rule
    for rule in rules:
        if rule["id"] == "fallback":
            return rule
    raise RemediationError("fallback remediation rule is missing")


def unique_preserve(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def packaging_rank(value: str) -> int:
    order = ["none", "targeted", "full_refresh"]
    return order.index(value) if value in order else -1


def build_plan(source_dir: Path, findings: List[str]) -> Dict[str, Any]:
    rules = load_rules()
    resolved = resolve_control_files(source_dir, rules["control_file_roles"])
    todo_text = read_text(source_dir / resolved["todo"])
    handoff_text = read_text(source_dir / resolved["handoff"])

    ranked_items: List[Dict[str, Any]] = []
    impacted: List[str] = []
    deep_regression: List[str] = []
    warnings: List[str] = []
    packaging = "none"

    for finding in findings:
        rule = match_rule(finding, rules["rules"])
        ranked_items.append({
            "finding": finding,
            "priority": rule["priority"],
            "remediation": rule["remediation"],
            "reason": rule["reason"]
        })
        impacted.extend(rule.get("impacted", []))
        deep_regression.extend(rule.get("deep_regression", []))
        if packaging_rank(rule.get("packaging", "none")) > packaging_rank(packaging):
            packaging = rule.get("packaging", "none")

    ranked_items.sort(key=lambda x: (x["priority"], x["finding"]))

    active_themes = []
    for needle in [
        "alert-triage-to-collector workflow",
        "operator workflow quality",
        "collector output interpretation",
        "large-file fallback",
        "bounded-confidence",
        "older per-file Knowledge-doc upload model"
    ]:
        if needle.lower().replace('-', ' ')[:12] in (todo_text + handoff_text).lower().replace('-', ' '):
            active_themes.append(needle)

    if any("manual classification required" in item for item in impacted):
        warnings.append("At least one finding did not match a known remediation class and needs explicit classification review.")

    stop_conditions = [
        "Stop if the manifest or change log cannot be resolved.",
        "Stop if the highest-priority finding indicates source-of-truth drift or packaging drift that changes the release set materially.",
        "Stop if the repaired path is not re-tested after the patch when the issue is testable.",
        "Stop if a helper-skill or bundle-generator remediation still fails deep regression after the patch."
    ]

    return {
        "remediation_status": "success",
        "resolved_control_files": resolved,
        "findings": findings,
        "active_themes": active_themes,
        "ranked_queue": ranked_items,
        "impacted": unique_preserve(impacted),
        "deep_regression": unique_preserve(deep_regression + ["re-test the repaired path before return to service"]),
        "packaging_recommendation": packaging,
        "warnings": unique_preserve(warnings),
        "stop_conditions": stop_conditions
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append('# DCOIR Live Test Remediation Report')
    lines.append('')
    lines.append(f"- Remediation status: {payload['remediation_status']}")
    lines.append(f"- Packaging recommendation: {payload['packaging_recommendation']}")
    lines.append('')
    lines.append('## Live-test finding summary')
    lines.append('')
    if payload.get('error'):
        lines.append(f"- Error: {payload['error']}")
    for finding in payload.get('findings', []):
        lines.append(f'- {finding}')
    lines.append('')
    lines.append('## Ranked remediation queue')
    lines.append('')
    for item in payload.get('ranked_queue', []):
        lines.append(f"- P{item['priority']}: {item['remediation']} — {item['finding']} ({item['reason']})")
    lines.append('')
    lines.append('## Impacted files and skills')
    lines.append('')
    for item in payload.get('impacted', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Deep-regression requirements')
    lines.append('')
    for item in payload.get('deep_regression', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Packaging recommendation')
    lines.append('')
    lines.append(f"- {payload.get('packaging_recommendation', 'none')}")
    lines.append('')
    lines.append('## Stop conditions and warnings')
    lines.append('')
    for item in payload.get('stop_conditions', []):
        lines.append(f'- {item}')
    for item in payload.get('warnings', []):
        lines.append(f'- Warning: {item}')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a DCOIR live-test remediation plan.')
    parser.add_argument('--source-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--finding', action='append', dest='findings', default=[])
    args = parser.parse_args()

    if not args.findings:
        raise SystemExit('At least one --finding is required')

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        payload = build_plan(source_dir, args.findings)
        status = 0
    except RemediationError as exc:
        payload = {
            'remediation_status': 'failure',
            'resolved_control_files': {},
            'findings': args.findings,
            'ranked_queue': [],
            'impacted': [],
            'deep_regression': [],
            'packaging_recommendation': 'none',
            'warnings': [],
            'stop_conditions': [],
            'error': str(exc)
        }
        status = 1

    (output_dir / OUTPUT_JSON).write_text(json.dumps(payload, indent=2), encoding='utf-8')
    (output_dir / OUTPUT_MD).write_text(render_markdown(payload), encoding='utf-8')
    print(render_markdown(payload))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
