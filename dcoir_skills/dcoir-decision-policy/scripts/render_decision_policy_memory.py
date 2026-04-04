#!/usr/bin/env python3
"""Render a DCOIR decision-policy memory markdown file from JSON state."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("state file must contain a top-level JSON object")
    return data


def fmt_rule(item: dict[str, Any]) -> str:
    title = item.get("title", "untitled rule")
    status = item.get("status", "open")
    source = item.get("source", "current_chat")
    parts = [f"- **{title}** (status: {status}; source: {source})"]
    for key in [
        "observed_statement",
        "interpreted_rule",
        "class",
        "persistence_target",
        "current_task_effect",
        "buffer_state",
        "flush_trigger",
        "campaign_scope",
        "deferred_review_countdown",
        "rule",
        "why",
        "next_action",
    ]:
        value = item.get(key, "")
        if value:
            parts.append(f"  - {key}: {value}")
    return "
".join(parts)


def bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- none"]


def rule_section(items: list[dict[str, Any]]) -> list[str]:
    return [fmt_rule(item) for item in items] if items else ["- none"]


def build_markdown(state: dict[str, Any]) -> str:
    exported_at = state.get("exported_at_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    authority_basis = state.get("authority_basis", [])
    lines = [
        "---",
        "artifact_type: dcoir-decision-policy-memory",
        "schema_version: 2",
        f"project: {state.get('project', 'AFRICOM_SOC_IR / DCOIR')}",
        f"exported_at_utc: {exported_at}",
        "authority_basis:",
    ]
    lines.extend([f"  - {item}" for item in authority_basis] or ["  - none-recorded"])
    lines.extend([
        "---",
        "",
        "# DCOIR Decision Policy Memory",
        "",
        "## Current focus",
        state.get("current_focus", "not specified"),
        "",
        "## Approved overlay snapshot",
    ])
    lines.extend(rule_section(state.get("approved_overlays", [])))
    lines.extend(["", "## Pending or situational learning"])
    lines.extend(rule_section(state.get("pending_candidates", [])))
    lines.extend(["", "## Delivery and update preferences"])
    lines.extend(bullet_list(state.get("delivery_preferences", [])))
    lines.extend(["", "## Buffered or deferred state"])
    lines.extend(bullet_list(state.get("buffered_state", [])))
    lines.extend(["", "## Deferred review counters"])
    lines.extend(bullet_list(state.get("deferred_review_counters", [])))
    lines.extend(["", "## Next actions"])
    lines.extend(bullet_list(state.get("next_actions", [])))
    lines.extend(["", "## Provenance notes"])
    lines.extend(bullet_list(state.get("provenance_notes", [])))
    lines.append("")
    return "
".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python render_decision_policy_memory.py state.json output.md")
        return 1
    state = load_state(Path(sys.argv[1]).resolve())
    output = Path(sys.argv[2]).resolve()
    output.write_text(build_markdown(state), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
