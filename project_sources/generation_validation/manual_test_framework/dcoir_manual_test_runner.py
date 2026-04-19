#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
CONTROL_PATH = BASE_DIR / "dcoir_manual_test_control.json"
TEST_OUTPUT_DIR = BASE_DIR / "_test_output"
WORK_ROOT = BASE_DIR / "_work"
RUNS_ROOT = BASE_DIR / "_runs"
HISTORY_ROOT = BASE_DIR / "_history"
DEFAULT_STATE_PATH = TEST_OUTPUT_DIR / "LATEST_runner_state.json"
DEFAULT_BOOTSTRAP_PATH = TEST_OUTPUT_DIR / "bootstrap_status.json"

STATUS_HELP = {
    "PENDING": "Waiting to run",
    "RUNNING": "Currently running",
    "FOUND": "Already installed or already available",
    "INSTALLED": "Installed successfully",
    "INSTALLING": "Installing now",
    "PASS": "Passed cleanly",
    "PARTIAL": "Worked, but has caveats",
    "FAIL": "Ran and failed the check",
    "ERROR": "The framework hit an execution error",
    "ACTION": "You need to do something",
    "LAUNCHING": "Opening the admin phase",
    "SKIPPED": "Not run",
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin-phase", action="store_true")
    ap.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    ap.add_argument("--bootstrap-status-path", default=str(DEFAULT_BOOTSTRAP_PATH))
    return ap.parse_args()


ARGS = parse_args()
STATE_PATH = Path(ARGS.state_path)
BOOTSTRAP_STATUS_PATH = Path(ARGS.bootstrap_status_path)


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def load_control() -> dict:
    if not CONTROL_PATH.exists():
        raise RuntimeError(f"Control file missing: {CONTROL_PATH}")
    return json.loads(CONTROL_PATH.read_text(encoding="utf-8"))


CONTROL = load_control()
STEP_ORDER: List[Tuple[str, str]] = [(row["id"], row["label"]) for row in CONTROL["steps"]]
REPO_URL = CONTROL["repo_url"]
LATEST_REPORT_PATH = TEST_OUTPUT_DIR / CONTROL["latest_report_name"]
LATEST_STATE_ARCHIVE = TEST_OUTPUT_DIR / CONTROL["latest_state_name"]
LATEST_SESSION_INFO_PATH = TEST_OUTPUT_DIR / "LATEST_session_info.json"


def ensure_base_dirs() -> None:
    for path in [TEST_OUTPUT_DIR, WORK_ROOT, RUNS_ROOT, HISTORY_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


ensure_base_dirs()


def load_bootstrap_statuses() -> Dict[str, Dict[str, str]]:
    if not BOOTSTRAP_STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(BOOTSTRAP_STATUS_PATH.read_text(encoding="utf-8"))
        return data.get("steps", {})
    except Exception:
        return {}


def blank_steps() -> Dict[str, Dict[str, str]]:
    steps = {}
    for step_id, label in STEP_ORDER:
        steps[step_id] = {"label": label, "status": "PENDING", "note": ""}
    return steps


def apply_bootstrap_statuses_into_state(state: Dict) -> None:
    for key, payload in load_bootstrap_statuses().items():
        if key in state["steps"]:
            current_status = state["steps"][key].get("status", "PENDING")
            current_note = state["steps"][key].get("note", "")
            if current_status == "PENDING" or not current_note:
                state["steps"][key]["status"] = payload.get("status", current_status)
                state["steps"][key]["note"] = payload.get("detail", current_note)


def new_session_id() -> str:
    return f"{CONTROL.get('session_prefix', 'DCOIR-MANUAL')}-{now_stamp()}"


def load_state() -> Dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if "steps" in data and "session_id" in data:
                return data
        except Exception:
            pass

    state = {
        "session_id": new_session_id(),
        "started_at": now_text(),
        "steps": blank_steps(),
        "context": {},
        "messages": [],
    }
    apply_bootstrap_statuses_into_state(state)
    return state


STATE = load_state()
SESSION_ID = STATE["session_id"]
SESSION_DIR = HISTORY_ROOT / SESSION_ID
SESSION_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = SESSION_DIR / f"{SESSION_ID}_DCOIR_Collector_Full_Signoff_Report.txt"
ARCHIVED_STATE_PATH = SESSION_DIR / f"{SESSION_ID}_runner_state.json"
MASTER_ZIP_PATH = SESSION_DIR / f"{SESSION_ID}_DCOIR_Collector_master.zip"


def active_session_root() -> Path:
    return WORK_ROOT / SESSION_ID


def repo_root() -> Path:
    return active_session_root() / "repo"


def stage_dir() -> Path:
    return active_session_root() / "stage"


def build_dir() -> Path:
    return active_session_root() / "build"


def live_runs_root() -> Path:
    return active_session_root() / "runs"


def collector_script_path() -> Path:
    return BASE_DIR / "DCOIR_Collector.ps1"


def live_zip_path() -> Path:
    return BASE_DIR / "DCOIR_Collector.zip"


def validate_script() -> Path:
    return repo_root() / "project_sources" / "validate_DCOIR_Run.ps1"


def harness_script() -> Path:
    return repo_root() / "project_sources" / "run_DCOIR_Tests.ps1"


def required_repo_paths() -> List[Path]:
    root = repo_root()
    return [
        root / "project_sources" / "DCOIR_Collector.ps1",
        root / "project_sources" / "collector_parts" / "DCOIR_Collector.05_Main_Entry.ps1",
        root / "project_sources" / "generation_validation" / "build_dcoir_collector_runtime_package.py",
        root / "project_sources" / "generation_validation" / "restore_dcoir_collector_runtime_zip.py",
        root / "supporting_assets" / "DCOIR_Collector.zip",
    ]


def sync_latest_report() -> None:
    if REPORT_PATH.exists():
        shutil.copy2(REPORT_PATH, LATEST_REPORT_PATH)


def write_session_info() -> None:
    info = {
        "session_id": SESSION_ID,
        "started_at": STATE.get("started_at"),
        "mode": "ADMIN" if ARGS.admin_phase else "NON-ADMIN",
        "base_dir": str(BASE_DIR),
        "report_path": str(REPORT_PATH),
        "latest_report_path": str(LATEST_REPORT_PATH),
        "state_path": str(STATE_PATH),
        "latest_state_path": str(LATEST_STATE_ARCHIVE),
        "session_archive_dir": str(SESSION_DIR),
        "active_session_root": str(active_session_root()),
        "repo_root": str(repo_root()),
        "is_admin_process": is_admin(),
    }
    LATEST_SESSION_INFO_PATH.write_text(json.dumps(info, indent=2), encoding="utf-8")


def save_state() -> None:
    apply_bootstrap_statuses_into_state(STATE)
    payload = json.dumps(STATE, indent=2)
    STATE_PATH.write_text(payload, encoding="utf-8")
    ARCHIVED_STATE_PATH.write_text(payload, encoding="utf-8")
    shutil.copy2(ARCHIVED_STATE_PATH, LATEST_STATE_ARCHIVE)
    write_session_info()


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def terminal_width(default: int = 120) -> int:
    try:
        return shutil.get_terminal_size((default, 40)).columns
    except Exception:
        return default


def wrap_text(text: str, width: int) -> List[str]:
    raw_lines: List[str] = []
    for chunk in str(text).splitlines() or [""]:
        wrapped = textwrap.wrap(chunk, width=width, replace_whitespace=False, drop_whitespace=False)
        raw_lines.extend(wrapped or [""])
    return raw_lines


def append_report(text: str) -> None:
    with REPORT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")
    sync_latest_report()


def init_report() -> None:
    if REPORT_PATH.exists() and ARGS.admin_phase:
        return
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"{CONTROL['framework_name']} Report",
                f"Started: {now_text()}",
                f"Framework mode: {'ADMIN' if ARGS.admin_phase else 'NON-ADMIN'}",
                f"Session ID: {SESSION_ID}",
                f"Base directory: {BASE_DIR}",
                f"Session archive directory: {SESSION_DIR}",
                "",
                "This report captures every command, exit code, stdout, stderr, traceback, and framework note.",
                "=" * 90,
                "",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    sync_latest_report()


def report_command_block(step_id: str, cmd: List[str], cwd: Path, rc: Optional[int], stdout: str, stderr: str, exc: str = "") -> None:
    lines = [
        "=" * 90,
        f"Timestamp: {now_text()}",
        f"Step: {step_id}",
        f"Working directory: {cwd}",
        "Command:",
        "  " + " ".join(f'"{part}"' if " " in str(part) else str(part) for part in cmd),
        f"Exit code: {rc if rc is not None else 'NO_EXIT_CODE'}",
        "",
        "STDOUT:",
        stdout.rstrip() or "<empty>",
        "",
        "STDERR:",
        stderr.rstrip() or "<empty>",
    ]
    if exc:
        lines += ["", "EXCEPTION:", exc.rstrip() or "<empty>"]
    append_report("\n".join(lines) + "\n")


def set_message(text: str) -> None:
    STATE["messages"].append({"timestamp": now_text(), "text": text})
    if len(STATE["messages"]) > 30:
        STATE["messages"] = STATE["messages"][-30:]
    render_dashboard(text)
    save_state()


def latest_message() -> str:
    if not STATE["messages"]:
        return "Framework loaded. Waiting for the next step."
    return STATE["messages"][-1]["text"]


def update_step(step_id: str, status: str, note: str = "") -> None:
    STATE["steps"][step_id]["status"] = status
    if note:
        STATE["steps"][step_id]["note"] = note
    save_state()
    render_dashboard(note or latest_message())


def draw_box(title: str, body: str, width: int) -> str:
    inner = max(30, width - 4)
    lines = wrap_text(body, inner - 2)
    top = "+" + "-" * inner + "+"
    title_line = f"| {title[: inner - 2].ljust(inner - 2)} |"
    content = [f"| {line.ljust(inner - 2)} |" for line in lines]
    return "\n".join([top, title_line, top] + content + [top])


def render_dashboard(message: str = "") -> None:
    clear_screen()
    width = max(100, min(terminal_width(), 160))
    status_w = 14
    name_w = width - status_w - 7
    top = "+" + "-" * (status_w + 2) + "+" + "-" * (name_w + 2) + "+"
    print(CONTROL["framework_name"])
    print(f"Mode: {'ADMIN' if ARGS.admin_phase else 'NON-ADMIN'}    Session: {SESSION_ID}")
    print(f"Latest report: {LATEST_REPORT_PATH}")
    print(f"Archived report: {REPORT_PATH}")
    print(f"Time: {now_text()}")
    print(top)
    print(f"| {'STATUS'.ljust(status_w)} | {'TEST'.ljust(name_w)} |")
    print(top)
    for step_id, _label in STEP_ORDER:
        status = STATE["steps"][step_id]["status"][:status_w]
        label = STATE["steps"][step_id]["label"][:name_w]
        print(f"| {status.ljust(status_w)} | {label.ljust(name_w)} |")
    print(top)
    print(draw_box("STATUS / NEXT ACTION", message or latest_message(), width))


def run_command(step_id: str, cmd: List[str], cwd: Path, note: str, allow_error: bool = False, timeout: Optional[int] = None) -> Dict[str, object]:
    update_step(step_id, "RUNNING", note)
    result = {"ok": False, "exit_code": None, "stdout": "", "stderr": ""}
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, shell=False)
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout or ""
        result["stderr"] = proc.stderr or ""
        report_command_block(step_id, cmd, cwd, proc.returncode, proc.stdout or "", proc.stderr or "")
        result["ok"] = (proc.returncode == 0) or allow_error
        return result
    except Exception:
        report_command_block(step_id, cmd, cwd, None, "", "", exc=traceback.format_exc())
        raise


def powershell_cmd(*args: str) -> List[str]:
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", *args]


def newest_delivery_zip() -> Path:
    zips = sorted(build_dir().glob("DCOIR_Collector_Delivery_Package_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        raise RuntimeError("No delivery package zip was produced.")
    return zips[0]


def newest_run_root(parent: Path, run_id: str = "") -> Path:
    candidates = [p for p in parent.glob("DCOIR_*") if p.is_dir()]
    if run_id:
        matches = [p for p in candidates if run_id in p.name]
        if matches:
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return matches[0]
    if not candidates:
        raise RuntimeError(f"No DCOIR run folders found under {parent}")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def parse_markers(text: str) -> Dict[str, str]:
    markers: Dict[str, str] = {}
    for line in (text or "").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            if key.isupper():
                markers[key] = value.strip()
    return markers


def test_output_has_all(text: str, tokens: List[str]) -> bool:
    hay = text or ""
    return all(token in hay for token in tokens)


def file_exists_or_raise(path: Path, friendly: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {friendly} -> {path}")


def remove_transient_root(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def remove_top_level_staged_runtime() -> None:
    for path in [collector_script_path(), live_zip_path(), BASE_DIR / "DCOIR_Collector_master.zip"]:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


def cleanup_previous_transients_for_new_run() -> None:
    if not CONTROL["cleanup"].get("remove_previous_transient_dirs_on_new_run", True):
        return
    for child in WORK_ROOT.iterdir():
        if child.is_dir() and child.name != SESSION_ID:
            remove_transient_root(child)
    remove_top_level_staged_runtime()


def cleanup_current_session_transients() -> None:
    if CONTROL["cleanup"].get("remove_current_transient_dirs_on_finish", True):
        remove_transient_root(active_session_root())
    if CONTROL["cleanup"].get("remove_top_level_staged_runtime_on_finish", True):
        remove_top_level_staged_runtime()


def summarize_git_failure(stderr: str) -> str:
    text = stderr or ""
    lower = text.lower()
    if "filename too long" in lower or "unable to create file" in lower:
        return (
            "Git hit a Windows path-length problem while checking out the repo. "
            "Use a short base folder like C:\\DCOIR, enable Windows long paths, enable Git long paths, restart the PC, and rerun the framework."
        )
    if "authentication failed" in lower or "repository not found" in lower or "could not read from remote repository" in lower:
        return "Git could not access the repo. Authenticate this machine to GitHub, then rerun the framework."
    return "Git could not fetch the repo. Read the report file for the exact git error, fix it, then rerun the framework."


def ensure_repo() -> None:
    root = repo_root()
    root.parent.mkdir(parents=True, exist_ok=True)
    git_exe = "git"

    if (root / ".git").exists():
        missing = [path for path in required_repo_paths() if not path.exists()]
        if not missing:
            update_step("repo_fetch", "PASS", "Reusing the existing repo copy for this session.")
            return
        remove_transient_root(root)
    elif root.exists():
        remove_transient_root(root)

    cmd = [git_exe, "-c", "core.longpaths=true", "clone", "--depth", "1", REPO_URL, str(root)]
    result = run_command("repo_fetch", cmd, BASE_DIR, "Cloning a fresh repo copy into the transient work area.")
    if result["exit_code"] != 0:
        note = summarize_git_failure(str(result["stderr"]))
        update_step("repo_fetch", "FAIL", note)
        raise RuntimeError(note)
    for path in required_repo_paths():
        file_exists_or_raise(path, path.name)
    update_step("repo_fetch", "PASS", "Repo fetched and required files are present.")


def validate_package(step_id: str = "package_validate") -> None:
    out = build_dir()
    remove_transient_root(out)
    out.mkdir(parents=True, exist_ok=True)
    script = repo_root() / "project_sources" / "generation_validation" / "validate_dcoir_collector_runtime_package.py"
    cmd = [sys.executable, str(script), "--source-dir", str(repo_root()), "--output-dir", str(out)]
    result = run_command(step_id, cmd, repo_root(), "Validating the current package rules.")
    if result["exit_code"] == 0:
        update_step(step_id, "PASS", "Package validation passed.")
    else:
        update_step(step_id, "FAIL", "Package validation failed. Open the report file and fix the reported package-rule problems.")
        raise RuntimeError("Package validation failed.")


def build_package(step_id: str = "package_build") -> None:
    out = build_dir()
    out.mkdir(parents=True, exist_ok=True)
    script = repo_root() / "project_sources" / "generation_validation" / "build_dcoir_collector_runtime_package.py"
    cmd = [sys.executable, str(script), "--source-dir", str(repo_root()), "--output-dir", str(out)]
    result = run_command(step_id, cmd, repo_root(), "Building the delivery package.")
    if result["exit_code"] == 0 and newest_delivery_zip().exists():
        update_step(step_id, "PASS", "Delivery package build passed.")
    else:
        update_step(step_id, "FAIL", "Delivery package build failed. Open the report file and fix the build issue before rerunning.")
        raise RuntimeError("Delivery package build failed.")


def restore_and_stage_runtime() -> None:
    sdir = stage_dir()
    remove_transient_root(sdir)
    sdir.mkdir(parents=True, exist_ok=True)

    restore_script = repo_root() / "project_sources" / "generation_validation" / "restore_dcoir_collector_runtime_zip.py"
    delivery_zip = newest_delivery_zip()
    base_runtime_zip = repo_root() / "supporting_assets" / "DCOIR_Collector.zip"
    restored_zip = sdir / "DCOIR_Collector_runtime_for_harness.zip"

    cmd = [
        sys.executable,
        str(restore_script),
        "--delivery-package-zip", str(delivery_zip),
        "--base-runtime-zip", str(base_runtime_zip),
        "--output-dir", str(sdir),
        "--output-name", restored_zip.name,
    ]
    result = run_command("runtime_restore", cmd, repo_root(), "Restoring the live-style runtime zip and extracting the combined collector.")
    if result["exit_code"] != 0:
        update_step("runtime_restore", "FAIL", "Runtime restore failed. Open the report file and fix the restore error.")
        raise RuntimeError("Runtime restore failed.")
    if not restored_zip.exists():
        update_step("runtime_restore", "FAIL", "Restore script finished but did not produce the runtime zip.")
        raise RuntimeError("Restore script did not produce the runtime zip.")

    if MASTER_ZIP_PATH.exists():
        MASTER_ZIP_PATH.unlink()
    shutil.copy2(restored_zip, MASTER_ZIP_PATH)

    extract_dir = sdir / "runtime_extract"
    remove_transient_root(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(restored_zip), str(extract_dir), "zip")

    combined = extract_dir / "DCOIR_Collector.ps1"
    file_exists_or_raise(combined, "Combined DCOIR_Collector.ps1")
    shutil.copy2(combined, collector_script_path())
    shutil.copy2(restored_zip, live_zip_path())
    shutil.copy2(MASTER_ZIP_PATH, BASE_DIR / "DCOIR_Collector_master.zip")

    update_step("runtime_restore", "PASS", "Staged DCOIR_Collector.ps1 and DCOIR_Collector.zip next to the framework for this run.")


def restage_live_zip() -> None:
    file_exists_or_raise(MASTER_ZIP_PATH, "Master runtime zip")
    if live_zip_path().exists():
        live_zip_path().unlink()
    shutil.copy2(MASTER_ZIP_PATH, live_zip_path())


def run_help_tests() -> None:
    cmd = powershell_cmd("-File", str(collector_script_path()), "-Help")
    result = run_command("help_top", cmd, BASE_DIR, "Running top-level help.")
    combined = f"{result['stdout']}\n{result['stderr']}"
    if test_output_has_all(combined, ["DCOIR Collector Help", "Quick usage:"]):
        update_step("help_top", "PASS", "Top-level help printed successfully.")
    else:
        update_step("help_top", "FAIL", "Top-level help did not print the expected help text.")
        raise RuntimeError("Top-level help test failed.")

    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "help")
    result = run_command("help_quick", cmd, BASE_DIR, "Running quick help.", allow_error=True)
    combined = f"{result['stdout']}\n{result['stderr']}"
    if test_output_has_all(combined, ["Quick command examples:", "collect-t1"]):
        status = "PARTIAL" if result["exit_code"] != 0 else "PASS"
        note = "Quick help printed the expected examples." if status == "PASS" else "Quick help printed, but it still returned a nonzero exit code."
        update_step("help_quick", status, note)
    else:
        update_step("help_quick", "FAIL", "Quick help did not print the expected examples.")
        raise RuntimeError("Quick help test failed.")

    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "bad-value")
    result = run_command("bad_quick", cmd, BASE_DIR, "Running a bad quick command to test the help fallback.", allow_error=True)
    combined = f"{result['stdout']}\n{result['stderr']}"
    if result["exit_code"] != 0 and test_output_has_all(combined, ["Unknown -Quick value", "DCOIR Collector Help"]):
        update_step("bad_quick", "PASS", "Bad quick command failed clearly and showed help text.")
    else:
        update_step("bad_quick", "FAIL", "Bad quick command did not fail clearly enough.")
        raise RuntimeError("Bad quick fallback test failed.")


def run_collect(step_id: str, out_root: Path, targeted: bool = False) -> Tuple[str, Dict[str, str], Path]:
    out_root.mkdir(parents=True, exist_ok=True)
    restage_live_zip()
    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "collect-t1", "-OutRoot", str(out_root))
    note = "Running a full non-targeted collect." if not targeted else "Running a targeted collect with an explicit time window."
    if targeted:
        cmd = powershell_cmd(
            "-File", str(collector_script_path()),
            "-Quick", "collect-targeted-popup",
            "-Target", "User reported popup around 2026-04-08T09:00Z",
            "-WindowStart", "2026-04-08T08:45:00Z",
            "-WindowEnd", "2026-04-08T09:15:00Z",
            "-OutRoot", str(out_root),
        )
    result = run_command(step_id, cmd, BASE_DIR, note)
    combined = f"{result['stdout']}\n{result['stderr']}"
    markers = parse_markers(combined)
    run_root = newest_run_root(out_root, markers.get("RUN_ID", ""))
    required = ["STATUS", "RUN_ID", "COLLECT_BUNDLE_PATH", "EXECUTION_CONTEXT_PATH", "SECURITY_AUDIT_POLICY_PATH", "ANALYST_OVERVIEW_PATH"]
    if all(markers.get(k) for k in required):
        state = markers.get("STATUS", "")
        grade = "PASS" if state == "SUCCESS" else "PARTIAL"
        note = "Collect completed and emitted the expected contract markers." if grade == "PASS" else "Collect completed with useful output but reported partial success."
        update_step(step_id, grade, note)
        return combined, markers, run_root
    update_step(step_id, "FAIL", "Collect did not emit the expected marker set.")
    raise RuntimeError(f"{step_id} failed.")


def run_validator(step_id: str, run_root: Path) -> Tuple[str, int]:
    cmd = powershell_cmd("-File", str(validate_script()), "-RunRoot", str(run_root))
    result = run_command(step_id, cmd, repo_root() / "project_sources", "Running the validate_DCOIR_Run checker.", allow_error=True)
    combined = f"{result['stdout']}\n{result['stderr']}"
    if "MODE=validate-on-run" in combined and "FAILURE_COUNT=" in combined:
        failure_count = 999
        for line in combined.splitlines():
            if line.startswith("FAILURE_COUNT="):
                try:
                    failure_count = int(line.split("=", 1)[1].strip())
                except Exception:
                    pass
        if result["exit_code"] == 0 and failure_count == 0:
            update_step(step_id, "PASS", "The validator passed cleanly.")
        else:
            update_step(step_id, "PARTIAL", "The validator ran and produced useful grading output, but it reported findings.")
        return combined, int(result["exit_code"])
    update_step(step_id, "FAIL", "The validator did not run in a usable way.")
    raise RuntimeError(f"{step_id} failed.")


def run_enrich_lifecycle(step_id: str, out_root: Path) -> Dict[str, Dict[str, str]]:
    restage_live_zip()
    out_root.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Dict[str, str]] = {}
    commands = [
        ("start", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-tcp", "-OutRoot", str(out_root))),
        ("add", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-add-logtext", "-Target", "Security", "-OutRoot", str(out_root))),
        ("finalize", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-finalize", "-OutRoot", str(out_root))),
    ]
    session_ids = []
    for name, cmd in commands:
        result = run_command(step_id, cmd, BASE_DIR, f"Running enrich lifecycle step: {name}.", allow_error=(name != "finalize"))
        combined = f"{result['stdout']}\n{result['stderr']}"
        markers = parse_markers(combined)
        results[name] = markers
        if markers.get("ENRICH_SESSION_ID"):
            session_ids.append(markers.get("ENRICH_SESSION_ID", ""))
    if (
        results.get("start", {}).get("ENRICH_SESSION_ID")
        and results.get("add", {}).get("ENRICH_SESSION_ID") == results.get("start", {}).get("ENRICH_SESSION_ID")
        and results.get("finalize", {}).get("ENRICH_BUNDLE_PATH")
    ):
        update_step(step_id, "PASS", "Enrich lifecycle created, reused, and finalized a session correctly.")
        return results
    update_step(step_id, "FAIL", "Enrich lifecycle did not behave correctly.")
    raise RuntimeError("Enrich lifecycle failed.")


def run_negative_cases(step_id: str, out_root: Path) -> None:
    restage_live_zip()
    out_root.mkdir(parents=True, exist_ok=True)
    cases = [
        ("invalid_mode", powershell_cmd("-File", str(collector_script_path()), "-Mode", "Bogus", "-OutRoot", str(out_root)), ["Mode", "Bogus"], True),
        ("bad_quick_pid", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-listdlls", "-Target", "abc", "-OutRoot", str(out_root)), ["requires a numeric -Target <pid>"], True),
        ("invalid_window", powershell_cmd("-File", str(collector_script_path()), "-Quick", "collect-targeted-popup", "-Target", "User reported popup around 2026-04-08T09:00Z", "-WindowStart", "not-a-date", "-WindowEnd", "2026-04-08T09:15:00Z", "-OutRoot", str(out_root)), ["Invalid WindowStart value"], False),
        ("missing_target", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-sigcheck", "-OutRoot", str(out_root)), ["requires -Target <path>"], True),
    ]
    pass_count = 0
    partial_count = 0
    for name, cmd, tokens, must_fail in cases:
        result = run_command(step_id, cmd, BASE_DIR, f"Running negative test: {name}.", allow_error=True)
        combined = f"{result['stdout']}\n{result['stderr']}"
        has_tokens = test_output_has_all(combined, tokens)
        if must_fail:
            if result["exit_code"] != 0 and has_tokens:
                pass_count += 1
        else:
            markers = parse_markers(combined)
            if has_tokens and markers.get("STATUS") in {"PARTIAL_SUCCESS", "SUCCESS"}:
                partial_count += 1
    if pass_count == 3 and partial_count == 1:
        update_step(step_id, "PASS", "Bad-input tests produced the expected clear failures and degraded behavior.")
    elif pass_count >= 2:
        update_step(step_id, "PARTIAL", "Some bad-input cases behaved correctly, but not all of them.")
    else:
        update_step(step_id, "FAIL", "Bad-input tests did not behave clearly enough.")
        raise RuntimeError("Negative test coverage failed.")


def launch_admin_phase() -> None:
    update_step("admin_launch", "LAUNCHING", "Opening the admin phase in a new elevated window.")
    save_state()
    params = f'"{__file__}" --admin-phase --state-path "{STATE_PATH}" --bootstrap-status-path "{BOOTSTRAP_STATUS_PATH}"'
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, str(BASE_DIR), 1)
    if int(rc) <= 32:
        update_step("admin_launch", "FAIL", "UAC elevation did not start. Accept the admin prompt or rerun the launcher as Administrator.")
        raise RuntimeError("Could not start the admin phase. Accept the UAC prompt or rerun the launcher as Administrator.")
    append_report(f"Admin phase launched at {now_text()}\n")


def monitor_admin_phase(timeout_seconds: int = 7200) -> None:
    set_message("Admin phase launched. Waiting for the elevated run to continue this same session.")
    deadline = dt.datetime.now() + dt.timedelta(seconds=timeout_seconds)
    last_mtime = STATE_PATH.stat().st_mtime if STATE_PATH.exists() else 0.0
    while dt.datetime.now() < deadline:
        time.sleep(2)
        if STATE_PATH.exists():
            current_mtime = STATE_PATH.stat().st_mtime
            if current_mtime != last_mtime:
                try:
                    fresh = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                    if "steps" in fresh:
                        STATE.clear()
                        STATE.update(fresh)
                        save_state()
                        render_dashboard(latest_message())
                except Exception:
                    pass
                last_mtime = current_mtime

        final_status = STATE["steps"]["final_signoff"]["status"]
        if final_status in {"PASS", "PARTIAL", "FAIL", "ERROR"}:
            return

        repo_status = STATE["steps"]["repo_fetch"]["status"]
        if repo_status in {"FAIL", "ERROR"} and ARGS.admin_phase is False:
            return

        admin_collect_status = STATE["steps"]["admin_collect"]["status"]
        if admin_collect_status in {"FAIL", "ERROR"}:
            return

    update_step("admin_launch", "PARTIAL", "Admin phase did not finish within the monitoring window. Read the latest report file for the current state.")


def compare_admin_nonadmin() -> None:
    nonadmin = STATE["context"].get("nonadmin_collect_markers", {})
    admin = STATE["context"].get("admin_collect_markers", {})
    if not nonadmin or not admin:
        update_step("admin_compare", "FAIL", "Could not compare admin and non-admin results because one side is missing.")
        raise RuntimeError("Missing comparison data.")
    if nonadmin.get("IS_ELEVATED") == "False" and admin.get("IS_ELEVATED") == "True":
        diff_keys = []
        for key in ["AUDIT_POLICY_ACCESS_STATUS", "NETSTAT_OWNER_AWARE_STATUS", "SECURITY_AUDIT_POLICY_PATH", "SECURITY_FILTERED_PATH"]:
            if nonadmin.get(key) != admin.get(key):
                diff_keys.append(key)
        if diff_keys:
            update_step("admin_compare", "PASS", "Admin and non-admin results were both captured, and the security/elevation differences are visible.")
        else:
            update_step("admin_compare", "PARTIAL", "Admin and non-admin runs were captured, but the practical differences were weaker than expected.")
    else:
        update_step("admin_compare", "FAIL", "The admin/non-admin comparison did not show the expected elevation markers.")
        raise RuntimeError("Admin/non-admin comparison failed.")


def run_full_regression() -> None:
    restage_live_zip()
    outroot = live_runs_root() / "harness_output"
    remove_transient_root(outroot)
    outroot.mkdir(parents=True, exist_ok=True)
    cmd = powershell_cmd(
        "-File", str(harness_script()),
        "-CollectorPath", str(collector_script_path()),
        "-Suite", "FullRegression",
        "-MasterZipPath", str(MASTER_ZIP_PATH),
        "-OutputRoot", str(outroot),
    )
    result = run_command("full_regression", cmd, repo_root() / "project_sources", "Running the full harness regression.")
    if result["exit_code"] == 0:
        update_step("full_regression", "PASS", "FullRegression completed successfully.")
    else:
        update_step("full_regression", "FAIL", "FullRegression failed. Open the report file and the harness output to see which suite broke.")
        raise RuntimeError("FullRegression failed.")


def recheck_package() -> None:
    validate_package(step_id="package_recheck")


def run_cleanup() -> None:
    update_step("cleanup", "RUNNING", "Running cleanup after evidence has already been saved.")
    okay = True
    for label, outroot in [("non-admin", live_runs_root() / "nonadmin"), ("admin", live_runs_root() / "admin")]:
        cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "cleanup", "-OutRoot", str(outroot))
        result = run_command("cleanup", cmd, BASE_DIR, f"Running cleanup for the {label} run.", allow_error=True)
        combined = f"{result['stdout']}\n{result['stderr']}"
        markers = parse_markers(combined)
        if markers.get("CLEANUP_STATUS") != "COMPLETE":
            okay = False
    cleanup_current_session_transients()
    if okay:
        update_step("cleanup", "PASS", "Cleanup completed after the evidence was saved, and transient artifacts were removed.")
    else:
        update_step("cleanup", "PARTIAL", "Cleanup ran, but at least one cleanup pass did not report COMPLETE cleanly. Transient artifacts were still removed.")


def final_signoff() -> None:
    counts: Dict[str, int] = {}
    for payload in STATE["steps"].values():
        counts[payload["status"]] = counts.get(payload["status"], 0) + 1
    failed = counts.get("FAIL", 0) + counts.get("ERROR", 0)
    partial = counts.get("PARTIAL", 0)
    if failed == 0 and partial == 0:
        verdict = "READY TO SIGN OFF"
        note = "Everything in this framework passed cleanly."
    elif failed == 0:
        verdict = "READY WITH RESERVATIONS"
        note = "Nothing hard-failed, but there are partial results that should be reviewed before final signoff."
    else:
        verdict = "NOT READY"
        note = "At least one test failed or errored. Review the report before signing off."
    append_report("\n" + "=" * 90 + "\n")
    append_report("FINAL SUMMARY")
    append_report(f"Finished: {now_text()}")
    append_report(f"Verdict: {verdict}")
    append_report(f"Note: {note}")
    append_report(f"Archived state file: {ARCHIVED_STATE_PATH}")
    append_report("Per-step results:")
    for step_id, _label in STEP_ORDER:
        payload = STATE["steps"][step_id]
        append_report(f"  - {payload['label']}: {payload['status']} :: {payload.get('note', '')}")
    update_step("final_signoff", "PASS" if failed == 0 else "PARTIAL", f"{verdict} - {note}")
    set_message(f"Framework finished. Verdict: {verdict}. Open the latest report at {LATEST_REPORT_PATH}")


def top_level_failure(exc: Exception) -> None:
    append_report("\n" + "=" * 90 + "\n")
    append_report("FRAMEWORK FATAL ERROR")
    append_report(f"Timestamp: {now_text()}")
    append_report(str(exc))
    append_report(traceback.format_exc())
    cleanup_current_session_transients()
    set_message(
        "Execution failed. Read the latest report file for the full command output and traceback. "
        "If the failure mentions path length, use a short folder like C:\\DCOIR and make sure Windows and Git long paths are enabled. "
        "If software was just installed, close this window, open a new PowerShell window, and rerun the launcher."
    )


def main() -> int:
    init_report()
    apply_bootstrap_statuses_into_state(STATE)
    render_dashboard("Framework loaded. Preparing to run.")
    save_state()
    try:
        if ARGS.admin_phase:
            update_step("admin_launch", "PASS", "Admin phase is now running.")
            ensure_repo()
            file_exists_or_raise(collector_script_path(), "Staged DCOIR_Collector.ps1")
            file_exists_or_raise(live_zip_path(), "Staged DCOIR_Collector.zip")
            file_exists_or_raise(MASTER_ZIP_PATH, "Session master runtime zip")
        else:
            cleanup_previous_transients_for_new_run()
            active_session_root().mkdir(parents=True, exist_ok=True)
            ensure_repo()
            validate_package()
            build_package()
            restore_and_stage_runtime()
            run_help_tests()

        if not ARGS.admin_phase:
            nonadmin_out = live_runs_root() / "nonadmin"
            nonadmin_collect_output, nonadmin_collect_markers, nonadmin_run_root = run_collect("nonadmin_collect", nonadmin_out, targeted=False)
            STATE["context"]["nonadmin_collect_output"] = nonadmin_collect_output
            STATE["context"]["nonadmin_collect_markers"] = nonadmin_collect_markers
            STATE["context"]["nonadmin_run_root"] = str(nonadmin_run_root)
            save_state()

            nonadmin_validator_output, nonadmin_validator_rc = run_validator("nonadmin_validate", nonadmin_run_root)
            STATE["context"]["nonadmin_validator_output"] = nonadmin_validator_output
            STATE["context"]["nonadmin_validator_rc"] = nonadmin_validator_rc
            save_state()

            targeted_out = live_runs_root() / "nonadmin_targeted"
            targeted_output, targeted_markers, targeted_run_root = run_collect("nonadmin_targeted", targeted_out, targeted=True)
            STATE["context"]["nonadmin_targeted_output"] = targeted_output
            STATE["context"]["nonadmin_targeted_markers"] = targeted_markers
            STATE["context"]["nonadmin_targeted_run_root"] = str(targeted_run_root)
            save_state()

            enrich_results = run_enrich_lifecycle("nonadmin_enrich", nonadmin_out)
            STATE["context"]["nonadmin_enrich_results"] = enrich_results
            save_state()

            run_negative_cases("nonadmin_negative", live_runs_root() / "nonadmin_negative")
            launch_admin_phase()
            monitor_admin_phase()
            return 0

        admin_out = live_runs_root() / "admin"
        admin_collect_output, admin_collect_markers, admin_run_root = run_collect("admin_collect", admin_out, targeted=False)
        STATE["context"]["admin_collect_output"] = admin_collect_output
        STATE["context"]["admin_collect_markers"] = admin_collect_markers
        STATE["context"]["admin_run_root"] = str(admin_run_root)
        save_state()

        admin_validator_output, admin_validator_rc = run_validator("admin_validate", admin_run_root)
        STATE["context"]["admin_validator_output"] = admin_validator_output
        STATE["context"]["admin_validator_rc"] = admin_validator_rc
        save_state()

        compare_admin_nonadmin()
        run_full_regression()
        recheck_package()
        run_cleanup()
        final_signoff()
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        for step_id, _label in STEP_ORDER:
            if STATE["steps"][step_id]["status"] == "RUNNING":
                update_step(step_id, "ERROR", str(exc))
                break
        top_level_failure(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
