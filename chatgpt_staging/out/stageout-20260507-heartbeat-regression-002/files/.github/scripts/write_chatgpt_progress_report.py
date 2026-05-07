#!/usr/bin/env python3
"""Write a ChatGPT-readable progressive workflow report.

Each call appends one heartbeat to progress_history.jsonl and rewrites the
stable workflow_report.md. The sidecar survives tools that overwrite the report.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_segment(value: str, default: str = "unknown") -> str:
    text = str(value or default).strip() or default
    text = SAFE_SEGMENT_RE.sub("-", text).strip(".-_") or default
    return text[:120]


def read_history(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows[-100:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--result", default="running")
    parser.add_argument("--message", default="")
    parser.add_argument("--report-root", default="chatgpt_staging/status_reports")
    parser.add_argument("--request-path", default="")
    parser.add_argument("--artifact-name", default="")
    parser.add_argument("--exit-code", default="")
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    workflow = safe_segment(args.workflow)
    request_id = safe_segment(args.request_id)
    phase = safe_segment(args.phase)
    result = safe_segment(args.result)
    report_dir = Path(args.report_root) / workflow / request_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "workflow_report.md"
    history_path = report_dir / "progress_history.jsonl"

    ts = utc_now()
    entry = {
        "timestamp_utc": ts,
        "workflow": args.workflow,
        "request_id": args.request_id,
        "phase": phase,
        "result": result,
        "message": args.message,
        "request_path": args.request_path,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "unknown"),
        "github_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "github_ref": os.environ.get("GITHUB_REF", "unknown"),
        "artifact_name": args.artifact_name,
        "exit_code": args.exit_code,
        "extra": [x for x in args.extra if str(x).strip()],
    }
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")

    history = read_history(history_path)
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "unknown")
    sha = os.environ.get("GITHUB_SHA", "unknown")
    ref = os.environ.get("GITHUB_REF", "unknown")
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo != "unknown" and run_id != "unknown" else ""

    lines = [
        "# ChatGPT workflow report",
        "",
        "## Result",
        "",
        f"- workflow: {args.workflow}",
        "- report_scope: progressive-in-session",
        f"- result: {result}",
        f"- phase: {phase}",
        f"- request_id: {args.request_id}",
        f"- request_path: {args.request_path}",
        f"- github_run_id: {run_id}",
        f"- github_run_attempt: {run_attempt}",
        f"- github_sha: {sha}",
        f"- github_ref: {ref}",
        f"- workflow_run_url: {run_url}",
        f"- report_updated_utc: {ts}",
        f"- progress_history_path: {history_path.as_posix()}",
    ]
    if args.artifact_name:
        lines.append(f"- artifact_name: {args.artifact_name}")
    if args.exit_code:
        lines.append(f"- exit_code: {args.exit_code}")
    for item in args.extra:
        if item.strip():
            lines.append(f"- {item.strip()}")
    lines += ["", "## Current status", "", args.message or f"Workflow is in phase `{phase}`.", "", "## Phase history", ""]
    for item in history:
        lines.append(
            f"- {item.get('timestamp_utc','')} | phase={item.get('phase','')} | result={item.get('result','')} | {item.get('message','')}".rstrip()
        )
    lines += ["", "## Next ChatGPT action", "", "Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker."]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
