#!/usr/bin/env python3
"""Create standardized ChatGPT-readable GitHub workflow reports and retention cleanup plans.

This script has two modes:
- workflow-run: read a GitHub workflow_run event payload and write one workflow_report.md.
- cleanup: scan committed workflow_report.md files and create an age/status-based cleanup plan.

The script intentionally uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPORT_ROOT = Path("chatgpt_staging/status_reports")
SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_segment(value: object, default: str = "unknown") -> str:
    text = str(value or default).strip() or default
    text = SAFE_SEGMENT_RE.sub("-", text)
    text = text.strip(".-_") or default
    return text[:120]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def git_commit_epoch(path: Path) -> int | None:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    if not out:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def parse_report_result(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return "unknown"
    if "- result: failure" in text or "- conclusion: failure" in text:
        return "failure"
    if "- result: cancelled" in text or "- conclusion: cancelled" in text:
        return "failure"
    if "- result: timed_out" in text or "- conclusion: timed_out" in text:
        return "failure"
    if "- result: success" in text or "- conclusion: success" in text:
        return "success"
    if "chatgpt-report-retention-cleanup" in text or "retention-cleanup" in str(path):
        return "cleanup"
    return "unknown"


def report_age_days(path: Path, now: dt.datetime) -> float:
    epoch = git_commit_epoch(path)
    if epoch is None:
        return 0.0
    committed = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    return max(0.0, (now - committed).total_seconds() / 86400.0)


def newest_report_per_workflow(paths: Iterable[Path]) -> set[Path]:
    newest: dict[str, tuple[int, Path]] = {}
    for path in paths:
        parts = path.parts
        try:
            idx = parts.index("repo-workflows")
            workflow = parts[idx + 1]
        except Exception:
            workflow = str(path.parent)
        epoch = git_commit_epoch(path) or 0
        if workflow not in newest or epoch > newest[workflow][0]:
            newest[workflow] = (epoch, path)
    return {item[1] for item in newest.values()}


def make_workflow_report(args: argparse.Namespace) -> int:
    event_path = Path(args.event_json or os.environ.get("GITHUB_EVENT_PATH", ""))
    if not event_path.is_file():
        raise SystemExit(f"Missing GitHub event JSON: {event_path}")

    event = read_json(event_path)
    run = event.get("workflow_run") or {}
    workflow_name = run.get("name") or args.workflow_name or "unknown-workflow"
    workflow_safe = safe_segment(workflow_name)
    run_id = str(run.get("id") or args.run_id or os.environ.get("GITHUB_RUN_ID", "unknown-run"))
    run_safe = safe_segment(run_id)
    conclusion = str(run.get("conclusion") or "unknown")
    event_name = str(run.get("event") or "unknown")
    head_branch = str(run.get("head_branch") or "")
    head_sha = str(run.get("head_sha") or "")
    html_url = str(run.get("html_url") or "")
    actor = ((run.get("actor") or {}).get("login") or "unknown") if isinstance(run.get("actor"), dict) else "unknown"
    repository = ((run.get("repository") or {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY", "unknown")) if isinstance(run.get("repository"), dict) else os.environ.get("GITHUB_REPOSITORY", "unknown")

    out_dir = REPORT_ROOT / "repo-workflows" / workflow_safe / run_safe
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "workflow_report.md"

    result = "success" if conclusion == "success" else "failure" if conclusion in {"failure", "cancelled", "timed_out", "action_required", "startup_failure"} else conclusion
    action_hint = "No repair needed; review changed paths/artifacts if this workflow protects a code or docs surface." if result == "success" else "Inspect this report, then use the GitHub run URL/artifacts/logs to diagnose the failed workflow before asking the operator for screenshots or pasted logs."

    lines = [
        "# ChatGPT workflow report",
        "",
        "## Result",
        "",
        f"- workflow: {workflow_name}",
        f"- report_scope: repo-workflows",
        f"- result: {result}",
        f"- conclusion: {conclusion}",
        f"- source_event: {event_name}",
        f"- workflow_run_id: {run_id}",
        f"- workflow_run_url: {html_url}",
        f"- repository: {repository}",
        f"- head_branch: {head_branch}",
        f"- head_sha: {head_sha}",
        f"- actor: {actor}",
        f"- reporter_run_id: {os.environ.get('GITHUB_RUN_ID', 'unknown')}",
        f"- reporter_sha: {os.environ.get('GITHUB_SHA', 'unknown')}",
        f"- report_created_utc: {iso(utc_now())}",
        "",
        "## Troubleshooting context",
        "",
        "This report was generated by the central ChatGPT workflow-run reporter after the source workflow completed.",
        "Use the workflow_run_url for full GitHub Actions logs and artifacts when this summary is not enough.",
        "",
        "## Next ChatGPT action",
        "",
        action_hint,
        "",
        "## Cleanup guidance",
        "",
        "This report is managed by chatgpt-report-retention-cleanup. Success reports normally expire sooner than failure reports.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path)
    return 0


def make_cleanup_plan(args: argparse.Namespace) -> int:
    now = utc_now()
    root = REPORT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    reports = sorted(root.glob("**/workflow_report.md"))
    current_run = safe_segment(os.environ.get("GITHUB_RUN_ID", "manual"))
    report_id = safe_segment(args.report_id or f"retention-cleanup-{current_run}")
    cleanup_dir = root / "retention-cleanup" / report_id
    cleanup_report = cleanup_dir / "workflow_report.md"
    cleanup_dir.mkdir(parents=True, exist_ok=True)

    newest_keep = newest_report_per_workflow([p for p in reports if "repo-workflows" in p.parts]) if args.keep_latest else set()
    remove: list[tuple[Path, str, float, str]] = []
    keep: list[tuple[Path, str, float, str]] = []

    for path in reports:
        if path == cleanup_report or cleanup_dir in path.parents:
            keep.append((path, "cleanup", 0.0, "current cleanup report"))
            continue
        if any(part == ".gitkeep" for part in path.parts):
            keep.append((path, "scaffold", 0.0, "scaffold"))
            continue
        if args.workflow_filter and args.workflow_filter not in str(path):
            keep.append((path, "filtered", report_age_days(path, now), "workflow_filter did not match"))
            continue
        if path in newest_keep:
            keep.append((path, parse_report_result(path), report_age_days(path, now), "latest report for workflow"))
            continue
        result = parse_report_result(path)
        age = report_age_days(path, now)
        threshold = args.failure_days if result == "failure" else args.cleanup_days if "cleanup" in str(path) else args.success_days
        if age >= threshold:
            remove.append((path, result, age, f"age {age:.1f}d >= {threshold}d"))
        else:
            keep.append((path, result, age, f"age {age:.1f}d < {threshold}d"))

    removed_file = Path(args.removed_paths_file)
    removed_file.parent.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        removed_file.write_text("", encoding="utf-8")
    else:
        removed_file.write_text("\n".join(str(p) for p, _, _, _ in remove) + ("\n" if remove else ""), encoding="utf-8")

    lines = [
        "# ChatGPT workflow report",
        "",
        "## Result",
        "",
        "- workflow: chatgpt-report-retention-cleanup",
        "- report_scope: retention-cleanup",
        "- result: success",
        f"- mode: {'dry-run' if args.dry_run else 'delete'}",
        f"- success_retention_days: {args.success_days}",
        f"- failure_retention_days: {args.failure_days}",
        f"- cleanup_retention_days: {args.cleanup_days}",
        f"- keep_latest_per_workflow: {str(args.keep_latest).lower()}",
        f"- workflow_filter: {args.workflow_filter or ''}",
        f"- candidate_count: {len(remove)}",
        f"- retained_count: {len(keep)}",
        f"- github_run_id: {os.environ.get('GITHUB_RUN_ID', 'unknown')}",
        f"- github_sha: {os.environ.get('GITHUB_SHA', 'unknown')}",
        f"- report_created_utc: {iso(now)}",
        "",
        "## Reports selected for cleanup" if not args.dry_run else "## Reports that would be cleaned",
    ]
    if remove:
        for path, result, age, reason in remove:
            lines.append(f"- `{path}` | result={result} | age_days={age:.1f} | reason={reason}")
    else:
        lines.append("- none")
    lines += ["", "## Reports retained or skipped"]
    if keep:
        for path, result, age, reason in keep[:200]:
            lines.append(f"- `{path}` | result={result} | age_days={age:.1f} | reason={reason}")
        if len(keep) > 200:
            lines.append(f"- ... {len(keep) - 200} additional retained reports omitted from summary")
    else:
        lines.append("- none")
    lines += [
        "",
        "## Next ChatGPT action",
        "",
        "Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.",
    ]
    cleanup_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(cleanup_report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    wr = sub.add_parser("workflow-run")
    wr.add_argument("--event-json")
    wr.add_argument("--workflow-name")
    wr.add_argument("--run-id")
    wr.set_defaults(func=make_workflow_report)

    cl = sub.add_parser("cleanup")
    cl.add_argument("--success-days", type=int, default=7)
    cl.add_argument("--failure-days", type=int, default=30)
    cl.add_argument("--cleanup-days", type=int, default=7)
    cl.add_argument("--workflow-filter", default="")
    cl.add_argument("--report-id", default="")
    cl.add_argument("--removed-paths-file", default=".github/tmp/chatgpt_report_cleanup_removed.txt")
    cl.add_argument("--dry-run", action="store_true")
    cl.add_argument("--keep-latest", action="store_true", default=True)
    cl.set_defaults(func=make_cleanup_plan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
