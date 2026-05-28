from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def render_markdown_report(results: List[Dict[str, Any]]) -> str:
    lines = [
        "# Gemini Behavioral Replay Report",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result['fixture_id']}",
                "",
                f"- mode: `{result.get('mode', 'unknown')}`",
                f"- model: `{result.get('model_name', 'unknown')}`",
                f"- success: `{str(result['success']).lower()}`",
                f"- turns passed: `{result['turn_success_count']}/{result['turn_count']}`",
                f"- required marker ratio: `{result['overall_required_marker_ratio']}`",
                f"- anomaly count: `{result['anomaly_count']}`",
                "",
            ]
        )
        if result.get("missing_turns"):
            lines.append(f"- missing turns: `{', '.join(result['missing_turns'])}`")
            lines.append("")
        lines.append("### Per-turn findings")
        lines.append("")
        for turn in result.get("per_turn", []):
            lines.append(f"- `{turn['turn_id']}` success=`{str(turn['success']).lower()}`")
            lines.append(f"  required matched: {', '.join(turn['required_markers']['matched']) or 'none'}")
            lines.append(f"  forbidden hits: {', '.join(turn['forbidden_markers']['hits']) or 'none'}")
            anomaly_details = ", ".join(f"{row['type']}: {row['detail']}" for row in turn.get("anomalies", []))
            lines.append(f"  anomalies: {anomaly_details or 'none'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_reports(output_dir: Path, report_name: str, results: List[Dict[str, Any]]) -> Dict[str, str]:
    ensure_dir(output_dir)
    json_path = output_dir / f"{report_name}.json"
    markdown_path = output_dir / f"{report_name}.md"
    write_json(json_path, {"results": results})
    markdown_path.write_text(render_markdown_report(results), encoding="utf-8")
    return {
        "json_report": str(json_path),
        "markdown_report": str(markdown_path),
    }
