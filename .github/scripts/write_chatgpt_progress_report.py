#!/usr/bin/env python3
"""Write a ChatGPT-readable progressive workflow report.

This is for in-session workflows where ChatGPT polls one stable
workflow_report.md path while a GitHub Actions job is still running.
Each call rewrites the same report and preserves prior phase bullets when
possible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path

SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
HISTORY_MARKER = "## Phase history"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_segment(value: str, default: str = "unknown") -> str:
    text = str(value or default).strip() or default
    text = SAFE_SEGMENT_RE.sub("-", text).strip(".-_") or default
    return text[:120]


def read_existing_history(path: Path) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if HISTORY_MARKER not in text:
        return []
    tail = text.split(HISTORY_MARKER, 1)[1]
    lines: list[str] = []
    for line in tail.splitlines()[1:]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            lines.append(line)
    return lines[-50:]


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
    report_path = Path(args.report_root) / workflow / request_id / "workflow_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    ts = utc_now()
    history = read_existing_history(report_path)
    history.append(f"- {ts} | phase={phase} | result={result} | {args.message}".rstrip())
    history = history[-50:]

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
    ]
    if args.artifact_name:
        lines.append(f"- artifact_name: {args.artifact_name}")
    if args.exit_code:
        lines.append(f"- exit_code: {args.exit_code}")
    for item in args.extra:
        if item.strip():
            lines.append(f"- {item.strip()}")
    lines += [
        "",
        "## Current status",
        "",
        args.message or f"Workflow is in phase `{phase}`.",
        "",
        HISTORY_MARKER,
        "",
        *history,
        "",
        "## Next ChatGPT action",
        "",
        "Poll this same report path until result is success or failure. If result is running, use the phase and phase history to decide whether to wait, inspect the GitHub run URL, or report a blocker.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
