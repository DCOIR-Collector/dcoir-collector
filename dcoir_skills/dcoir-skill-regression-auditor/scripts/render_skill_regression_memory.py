#!/usr/bin/env python3
"""Render a DCOIR skill-regression memory markdown file from JSON state."""
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


def fmt_item(item: dict[str, Any]) -> str:
    title = item.get("title", "untitled item")
    status = item.get("status", "open")
    parts = [f"- **{title}** (status: {status})"]
    for key in ["skill", "campaign_scope", "why", "buffer_state", "flush_trigger", "next_action"]:
        value = item.get(key, "")
        if value:
            parts.append(f"  - {key}: {value}")
    return "\n".join(parts)


def section(items: list[dict[str, Any]]) -> list[str]:
    return [fmt_item(item) for item in items] if items else ["- none"]


def bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- none"]


def build_markdown(state: dict[str, Any]) -> str:
    exported_at = state.get("exported_at_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    authority_basis = state.get("authority_basis", [])
    lines = [
        "---",
        "artifact_type: dcoir-skill-regression-memory",
        "schema_version: 2",
        f"project: {state.get('project', 'AFRICOM_SOC_IR / DCOIR')}",
        f"exported_at_utc: {exported_at}",
        "authority_basis:",
    ]
    lines.extend([f"  - {item}" for item in authority_basis] or ["  - none-recorded"])
    lines.extend([
        "---",
        "",
        "# DCOIR Skill Regression Memory",
        "",
        "## Current focus",
        state.get("current_focus", "not specified"),
        "",
        "## Tracked skills",
    ])
    lines.extend(section(state.get("tracked_skills", [])))
    lines.extend(["", "## Campaign coverage"])
    lines.extend(section(state.get("campaign_coverage", [])))
    lines.extend(["", "## Fixture baselines"])
    lines.extend(bullets(state.get("fixture_baselines", [])))
    lines.extend(["", "## Failure gates"])
    lines.extend(bullets(state.get("failure_gates", [])))
    lines.extend(["", "## Buffered state"])
    lines.extend(bullets(state.get("buffered_state", [])))
    lines.extend(["", "## Next actions"])
    lines.extend(bullets(state.get("next_actions", [])))
    lines.extend(["", "## Provenance notes"])
    lines.extend(bullets(state.get("provenance_notes", [])))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python render_skill_regression_memory.py state.json output.md")
        return 1
    state = load_state(Path(sys.argv[1]).resolve())
    output = Path(sys.argv[2]).resolve()
    output.write_text(build_markdown(state), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
