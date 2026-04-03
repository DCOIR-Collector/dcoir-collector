#!/usr/bin/env python3
"""Render a DCOIR session-state markdown artifact from a JSON state file.

Usage:
    python render_session_state.py state.json output.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORDER = [
    "session_only",
    "candidate_log01",
    "candidate_log02",
    "candidate_log03",
    "durable_preference_candidate",
    "new_skill_idea",
    "follow_on_validation",
    "blocked_or_needs_authority",
]

TITLE = {
    "session_only": "session_only",
    "candidate_log01": "candidate_log01",
    "candidate_log02": "candidate_log02",
    "candidate_log03": "candidate_log03",
    "durable_preference_candidate": "durable_preference_candidate",
    "new_skill_idea": "new_skill_idea",
    "follow_on_validation": "follow_on_validation",
    "blocked_or_needs_authority": "blocked_or_needs_authority",
}


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("state file must contain a top-level JSON object")
    return data


def fmt_item(item: dict[str, Any]) -> str:
    item_id = item.get("id", "UNSPECIFIED")
    title = item.get("title", "untitled item")
    why = item.get("why", "")
    next_action = item.get("next_action", "")
    status = item.get("status", "open")
    provenance = item.get("provenance", "current_chat")

    parts = [f"- [{item_id}] {title} (status: {status}; provenance: {provenance})"]
    if why:
        parts.append(f"  - why: {why}")
    if next_action:
        parts.append(f"  - next_action: {next_action}")
    related = item.get("related", [])
    if related:
        parts.append(f"  - related: {', '.join(str(x) for x in related)}")
    return "\n".join(parts)


def section_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- none"]
    return [fmt_item(item) for item in items]


def build_markdown(state: dict[str, Any]) -> str:
    exported_at = state.get("exported_at_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    authority_basis = state.get("authority_basis", [])
    imports_merged = state.get("imports_merged", [])
    current_phase = state.get("current_phase", "not specified")
    best_next_move = state.get("best_next_move", "not specified")
    close_out_status = state.get("close_out_status", "not specified")
    durability_summary = state.get("durability_summary", {})
    open_items = state.get("open_items", {})
    completed = state.get("completed", [])
    promotion_ready = state.get("promotion_ready", {})
    starter_prompt = state.get("starter_prompt", "")
    closeout_verification = state.get("closeout_verification", [])
    provenance_notes = state.get("provenance_notes", [])

    lines: list[str] = [
        "---",
        "artifact_type: dcoir-session-state",
        "schema_version: 1",
        f"project: {state.get('project', 'AFRICOM_SOC_IR / DCOIR')}",
        f"exported_at_utc: {exported_at}",
        "authority_basis:",
    ]
    if authority_basis:
        lines.extend([f"  - {item}" for item in authority_basis])
    else:
        lines.append("  - none-recorded")
    lines.append(f"merge_mode: {state.get('merge_mode', 'merge')}")
    lines.append("imports_merged:")
    if imports_merged:
        lines.extend([f"  - {item}" for item in imports_merged])
    else:
        lines.append("  - none")
    lines.append("---")
    lines.append("")
    lines.append("# DCOIR Session State")
    lines.append("")
    lines.append("## Current phase")
    lines.append(current_phase)
    lines.append("")
    lines.append("## Best next move")
    lines.append(best_next_move)
    lines.append("")
    lines.append("## Close-out status")
    lines.append(close_out_status)
    lines.append("")
    lines.append("## Durability summary")
    lines.append(f"- governed_github: {durability_summary.get('governed_github', 'not specified')}")
    lines.append(f"- exported_handoff_only: {durability_summary.get('exported_handoff_only', 'not specified')}")
    lines.append(f"- buffered_session_only: {durability_summary.get('buffered_session_only', 'not specified')}")
    unresolved = durability_summary.get('unresolved_closeout_gap')
    if unresolved:
        lines.append(f"- unresolved_closeout_gap: {unresolved}")
    lines.append("")
    lines.append("## Open items")

    for key in ORDER:
        lines.append(f"### {TITLE[key]}")
        lines.extend(section_lines(open_items.get(key, [])))
        lines.append("")

    lines.append("## Completed or resolved this session")
    if completed:
        lines.extend(section_lines(completed))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Promotion-ready notes")
    for key in ["log01", "log02", "log03"]:
        lines.append(f"### {key.upper()} candidate text")
        block = promotion_ready.get(key, "")
        lines.append(block if block else "none")
        lines.append("")

    lines.append("## Starter prompt for next session")
    lines.append(starter_prompt if starter_prompt else "none")
    lines.append("")

    lines.append("## Close-out verification notes")
    if closeout_verification:
        lines.extend([f"- {note}" for note in closeout_verification])
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Provenance notes")
    if provenance_notes:
        lines.extend([f"- {note}" for note in provenance_notes])
    else:
        lines.append("- none")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python render_session_state.py state.json output.md")
        return 1

    state_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()

    state = load_state(state_path)
    output_path.write_text(build_markdown(state), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
