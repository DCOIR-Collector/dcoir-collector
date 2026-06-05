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
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "_test_output"
WORK_DIR = BASE_DIR / "_work"
RUNS_DIR = BASE_DIR / "_runs"
RUNTIME_DIR = OUTPUT_DIR / "live_runtime"
STATE_DEFAULT = OUTPUT_DIR / "_runner_state.json"
REPORT_PATH = OUTPUT_DIR / "DCOIR_Collector_Full_Signoff_Report.txt"
SESSION_INFO_PATH = OUTPUT_DIR / "_session_info.json"
BOOTSTRAP_DEFAULT = OUTPUT_DIR / "bootstrap_status.json"
MASTER_ZIP_PATH = OUTPUT_DIR / "DCOIR_Collector_master.zip"

REPO_URL = "https://github.com/malwaredevil/dcoir-collector.git"

STEP_ORDER = [
    ("git_check", "Git prerequisite"),
    ("python_check", "Python prerequisite"),
    ("repo_fetch", "Fetch or update repo"),
    ("package_validate", "Validate package rules"),
    ("package_build", "Build delivery package"),
    ("runtime_restore", "Restore and stage live runtime"),
    ("help_top", "Top-level help"),
    ("help_quick", "Quick help"),
    ("help_contextual", "Contextual help"),
    ("bad_quick", "Bad command help fallback"),
    ("nonadmin_collect", "Non-admin collect"),
    ("nonadmin_validate", "Non-admin validator check"),
    ("review_surfaces", "Review-surface tuning"),
    ("nonadmin_targeted", "Non-admin targeted collect"),
    ("nonadmin_enrich", "Non-admin enrich lifecycle"),
    ("nonadmin_negative", "Non-admin bad input cases"),
    ("admin_launch", "Launch admin phase"),
    ("admin_collect", "Admin collect"),
    ("admin_validate", "Admin validator check"),
    ("admin_compare", "Admin vs non-admin compare"),
    ("t2_pathway_note", "T2 pathway mapping note"),
    ("full_regression", "FullRegression harness"),
    ("package_recheck", "Package build parity recheck"),
    ("cleanup", "Cleanup and evidence closeout"),
    ("final_signoff", "Final signoff summary"),
]

TERMINAL_STATUSES = {
    "PENDING": "Waiting",
    "RUNNING": "Running",
    "FOUND": "Ready",
    "INSTALLED": "Ready",
    "INSTALLING": "Installing",
    "PASS": "Pass",
    "PARTIAL": "Partial",
    "FAIL": "Fail",
    "ERROR": "Error",
    "ACTION": "Action",
    "LAUNCHING": "Launching",
    "SKIPPED": "Skipped",
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin-phase", action="store_true")
    ap.add_argument("--state-path", default=str(STATE_DEFAULT))
    ap.add_argument("--bootstrap-status-path", default=str(BOOTSTRAP_DEFAULT))
    return ap.parse_args()


ARGS = parse_args()
STATE_PATH = Path(ARGS.state_path)
BOOTSTRAP_STATUS_PATH = Path(ARGS.bootstrap_status_path)


def ensure_dirs() -> None:
    for path in [OUTPUT_DIR, WORK_DIR, RUNS_DIR, RUNTIME_DIR]:
        path.mkdir(parents=True, exist_ok=True)


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


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_bootstrap_statuses() -> Dict[str, Dict[str, str]]:
    if not BOOTSTRAP_STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(BOOTSTRAP_STATUS_PATH.read_text(encoding="utf-8"))
        return data.get("steps", {})
    except Exception:
        return {}


def normalize_bootstrap_status(status: str) -> str:
    mapping = {
        "FOUND": "PASS",
        "INSTALLED": "PASS",
        "INSTALLING": "INSTALLING",
        "ACTION_REQUIRED": "ACTION",
        "FAIL": "FAIL",
        "ERROR": "ERROR",
        "PASS": "PASS",
    }
    return mapping.get((status or "").upper(), status or "PENDING")


def blank_steps() -> Dict[str, Dict[str, str]]:
    return {
        step_id: {"label": label, "status": "PENDING", "note": ""}
        for step_id, label in STEP_ORDER
    }


def sync_bootstrap_into_state(data: Dict) -> Dict:
    steps = data.setdefault("steps", blank_steps())
    for key, payload in load_bootstrap_statuses().items():
        if key in steps:
            steps[key]["status"] = normalize_bootstrap_status(payload.get("status", "PENDING"))
            steps[key]["note"] = payload.get("detail", "")
    return data


def load_state() -> Dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if "steps" in data:
                return sync_bootstrap_into_state(data)
        except Exception:
            pass
    data = {"steps": blank_steps(), "context": {}, "messages": []}
    return sync_bootstrap_into_state(data)


STATE = load_state()


def save_state() -> None:
    STATE_PATH.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
    SESSION_INFO_PATH.write_text(
        json.dumps(
            {
                "started_at": STATE.get("context", {}).get("framework_started_at", now_text()),
                "mode": "ADMIN" if ARGS.admin_phase else "NON-ADMIN",
                "base_dir": str(BASE_DIR),
                "report_path": str(REPORT_PATH),
                "state_path": str(STATE_PATH),
                "repo_root": str(repo_root()),
                "runtime_dir": str(RUNTIME_DIR),
                "is_admin_process": is_admin(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def init_report() -> None:
    if REPORT_PATH.exists() and ARGS.admin_phase:
        return
    REPORT_PATH.write_text(
        "\n".join(
            [
                "DCOIR Collector Manual Test Framework Report",
                f"Started: {now_text()}",
                f"Framework mode: {'ADMIN' if ARGS.admin_phase else 'NON-ADMIN'}",
                f"Base directory: {BASE_DIR}",
                "",
                "This report captures every command, exit code, stdout, stderr, and framework note.",
                "=" * 90,
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def append_report(text: str) -> None:
    with REPORT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")


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
    STATE.setdefault("messages", []).append({"timestamp": now_text(), "text": text})
    if len(STATE["messages"]) > 20:
        STATE["messages"] = STATE["messages"][-20:]
    render_dashboard(text)
    save_state()


def latest_message() -> str:
    if not STATE.get("messages"):
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
    print("DCOIR Manual Test Framework")
    print(f"Mode: {'ADMIN' if ARGS.admin_phase else 'NON-ADMIN'}    Report: {REPORT_PATH}")
    print(f"Time: {now_text()}")
    print(top)
    print(f"| {'STATUS'.ljust(status_w)} | {'TEST'.ljust(name_w)} |")
    print(top)
    for step_id, _label in STEP_ORDER:
        raw_status = STATE["steps"][step_id]["status"]
        status = TERMINAL_STATUSES.get(raw_status, raw_status)[:status_w]
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


def repo_root() -> Path:
    return WORK_DIR / "dcoir-collector"


def stage_dir() -> Path:
    return OUTPUT_DIR / "staging"


def build_dir() -> Path:
    return WORK_DIR / "out_build"


def validate_script() -> Path:
    return repo_root() / "project_sources" / "collector" / "harness" / "validate_DCOIR_Run.ps1"


def harness_script() -> Path:
    return repo_root() / "project_sources" / "collector" / "harness" / "run_DCOIR_Tests.ps1"


def collector_script_path() -> Path:
    return RUNTIME_DIR / "DCOIR_Collector.ps1"


def live_zip_path() -> Path:
    return RUNTIME_DIR / "DCOIR_Collector.zip"


def required_repo_paths() -> List[Path]:
    root = repo_root()
    return [
        root / "project_sources" / "collector" / "source" / "DCOIR_Collector.ps1",
        root / "project_sources" / "collector" / "source" / "parts" / "DCOIR_Collector.05_Main_Entry.ps1",
        root / "project_sources" / "collector" / "tools" / "build_dcoir_collector_runtime_package.py",
        root / "project_sources" / "collector" / "tools" / "restore_dcoir_collector_runtime_zip.py",
        root / "supporting_assets" / "DCOIR_Collector.zip",
    ]


def file_exists_or_raise(path: Path, friendly: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {friendly} -> {path}")


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


def best_effort_cleanup_paths() -> None:
    for path in [stage_dir(), build_dir(), OUTPUT_DIR / "harness_output_temp"]:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def ensure_repo() -> None:
    root = repo_root()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    if (root / ".git").exists():
        cmd = ["git", "-C", str(root), "pull", "--ff-only"]
        result = run_command("repo_fetch", cmd, BASE_DIR, "Updating the local repo copy.")
        if result["exit_code"] != 0:
            update_step("repo_fetch", "FAIL", "Git pull failed. Authenticate Git to GitHub if needed, then rerun the framework.")
            raise RuntimeError("Git pull failed. If the repository is private, make sure this machine is authenticated to GitHub.")
    else:
        cmd = ["git", "clone", REPO_URL, str(root)]
        result = run_command("repo_fetch", cmd, BASE_DIR, "Cloning the repo into the local work folder.")
        if result["exit_code"] != 0:
            update_step("repo_fetch", "FAIL", "Git clone failed. If this repo is private, sign in to Git on this machine and rerun the framework.")
            raise RuntimeError("Git clone failed. If the repository is private, authenticate this machine to GitHub and rerun the framework.")

    for path in required_repo_paths():
        file_exists_or_raise(path, path.name)
    update_step("repo_fetch", "PASS", "Repo fetched and required files are present.")


def validate_package(step_id: str = "package_validate") -> None:
    out = build_dir()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    script = repo_root() / "project_sources" / "collector" / "tools" / "validate_dcoir_collector_runtime_package.py"
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
    script = repo_root() / "project_sources" / "collector" / "tools" / "build_dcoir_collector_runtime_package.py"
    cmd = [sys.executable, str(script), "--source-dir", str(repo_root()), "--output-dir", str(out)]
    result = run_command(step_id, cmd, repo_root(), "Building the delivery package.")
    if result["exit_code"] == 0 and newest_delivery_zip().exists():
        update_step(step_id, "PASS", "Delivery package build passed.")
    else:
        update_step(step_id, "FAIL", "Delivery package build failed. Open the report file and fix the build issue before rerunning.")
        raise RuntimeError("Delivery package build failed.")


def ensure_runtime_available() -> None:
    if collector_script_path().exists() and live_zip_path().exists():
        return
    file_exists_or_raise(MASTER_ZIP_PATH, "Master runtime zip")
    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASTER_ZIP_PATH, live_zip_path())
    extract_dir = stage_dir() / "master_runtime_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir, ignore_errors=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(MASTER_ZIP_PATH), str(extract_dir), "zip")
    combined = extract_dir / "DCOIR_Collector.ps1"
    file_exists_or_raise(combined, "Combined DCOIR_Collector.ps1")
    shutil.copy2(combined, collector_script_path())


def restore_and_stage_runtime() -> None:
    sdir = stage_dir()
    if sdir.exists():
        shutil.rmtree(sdir)
    sdir.mkdir(parents=True, exist_ok=True)

    restore_script = repo_root() / "project_sources" / "collector" / "tools" / "restore_dcoir_collector_runtime_zip.py"
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

    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    extract_dir = sdir / "runtime_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(restored_zip), str(extract_dir), "zip")

    combined = extract_dir / "DCOIR_Collector.ps1"
    file_exists_or_raise(combined, "Combined DCOIR_Collector.ps1")
    shutil.copy2(combined, collector_script_path())
    shutil.copy2(restored_zip, live_zip_path())

    update_step("runtime_restore", "PASS", f"Staged DCOIR_Collector.ps1 and DCOIR_Collector.zip in {RUNTIME_DIR}.")


def run_help_tests() -> None:
    ensure_runtime_available()
    cmd = powershell_cmd("-File", str(collector_script_path()), "-Help")
    result = run_command("help_top", cmd, BASE_DIR, "Running top-level help.")
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    if test_output_has_all(combined, ["DCOIR Collector Help", "Quick usage:"]):
        update_step("help_top", "PASS", "Top-level help printed successfully.")
    else:
        update_step("help_top", "FAIL", "Top-level help did not print the expected help text.")
        raise RuntimeError("Top-level help test failed.")

    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "help")
    result = run_command("help_quick", cmd, BASE_DIR, "Running quick help.", allow_error=True)
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    if result["exit_code"] == 0 and test_output_has_all(combined, ["Quick command examples:", "collect-t1"]):
        update_step("help_quick", "PASS", "Quick help printed the expected examples and returned cleanly.")
    else:
        update_step("help_quick", "FAIL", "Quick help did not print the expected examples cleanly.")
        raise RuntimeError("Quick help test failed.")

    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "help-collect")
    result = run_command("help_contextual", cmd, BASE_DIR, "Running contextual collect help.", allow_error=True)
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    if result["exit_code"] == 0 and test_output_has_all(combined, ["DCOIR Collector Contextual Help - Collect", "collect-t1"]):
        update_step("help_contextual", "PASS", "Contextual help printed collect-specific guidance and returned cleanly.")
    else:
        update_step("help_contextual", "FAIL", "Contextual help did not print the expected collect-specific guidance.")
        raise RuntimeError("Contextual help test failed.")

    cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "bad-value")
    result = run_command("bad_quick", cmd, BASE_DIR, "Running a bad quick command to test the help fallback.", allow_error=True)
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    if result["exit_code"] != 0 and test_output_has_all(combined, ["Unknown -Quick value", "DCOIR Collector Help"]):
        update_step("bad_quick", "PASS", "Bad quick command failed clearly and showed help text.")
    else:
        update_step("bad_quick", "FAIL", "Bad quick command did not fail in a clear helpful way.")
        raise RuntimeError("Bad quick fallback test failed.")

def classify_collect_note(markers: Dict[str, str], targeted: bool = False) -> str:
    expected_nonadmin = markers.get("AUDIT_POLICY_ACCESS_STATUS") == "PRIVILEGE_REQUIRED_NON_ELEVATED"
    if markers.get("STATUS") == "PARTIAL_SUCCESS" and expected_nonadmin:
        return (
            "Targeted collect produced the expected targeted output files and expected non-elevated limitations were recorded honestly."
            if targeted
            else "Collect completed and produced the expected live-style output markers; expected non-elevated limitations were recorded honestly."
        )
    return (
        "Targeted collect produced the expected targeted output files."
        if targeted
        else "Collect completed and produced the expected live-style output markers."
    )


def run_collect(step_id: str, outroot: Path, targeted: bool = False) -> Tuple[str, Dict[str, str], Path]:
    if outroot.exists():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)
    ensure_runtime_available()

    if targeted:
        cmd = powershell_cmd(
            "-File", str(collector_script_path()),
            "-Quick", "collect-targeted-popup",
            "-Target", "User reported popup around 2026-04-08T09:00Z",
            "-WindowStart", "2026-04-08T08:45:00Z",
            "-WindowEnd", "2026-04-08T09:15:00Z",
            "-OutRoot", str(outroot),
        )
        note = "Running a targeted collect in the same local style a user would."
    else:
        cmd = powershell_cmd(
            "-File", str(collector_script_path()),
            "-Quick", "collect-t1",
            "-OutRoot", str(outroot),
        )
        note = "Running a full collect in the same local style a user would."

    result = run_command(step_id, cmd, BASE_DIR, note)
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    markers = parse_markers(combined)
    run_id = markers.get("RUN_ID", "")
    run_root = newest_run_root(outroot, run_id=run_id)

    if targeted:
        ok = result["exit_code"] == 0 and "COLLECTION_SCOPE_PATH" in markers and "TARGETED_COLLECTION_PLAN_PATH" in markers
        if ok:
            update_step(step_id, "PASS", classify_collect_note(markers, targeted=True))
        else:
            update_step(step_id, "FAIL", "Targeted collect did not produce the expected targeted outputs.")
            raise RuntimeError("Targeted collect test failed.")
    else:
        ok = result["exit_code"] == 0 and "COLLECT_BUNDLE_PATH" in markers and "RUN_ID" in markers and "STATUS" in markers
        if ok:
            update_step(step_id, "PASS", classify_collect_note(markers, targeted=False))
        else:
            update_step(step_id, "FAIL", "Collect did not produce the expected live-style output markers.")
            raise RuntimeError("Collect test failed.")

    return combined, markers, run_root


def run_validator(step_id: str, run_root: Path) -> Tuple[str, int]:
    cmd = powershell_cmd("-File", str(validate_script()), "-RunRoot", str(run_root))
    result = run_command(step_id, cmd, repo_root(), "Running the standalone validator against the collected run.", allow_error=True)
    combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
    if result["exit_code"] == 0:
        update_step(step_id, "PASS", "Validator passed.")
    else:
        update_step(step_id, "FAIL", "Validator failed. Open the report file to see the exact failing checks.")
    return combined, int(result["exit_code"] or 0)


def run_enrich_lifecycle(step_id: str, outroot: Path) -> Dict[str, Dict[str, str]]:
    ensure_runtime_available()
    results: Dict[str, Dict[str, str]] = {}
    commands = [
        ("start", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-tcp", "-OutRoot", str(outroot))),
        ("add", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-add-logtext", "-Target", "Security", "-OutRoot", str(outroot))),
        ("finalize", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-finalize", "-OutRoot", str(outroot))),
    ]
    update_step(step_id, "RUNNING", "Running the enrich lifecycle with live-style commands.")
    session_id = None
    okay = True
    for subname, cmd in commands:
        result = run_command(step_id, cmd, BASE_DIR, f"Running enrich lifecycle step: {subname}.", allow_error=True)
        combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
        markers = parse_markers(combined)
        results[subname] = markers
        if subname in ("start", "add"):
            if "ENRICH_SESSION_ID" not in markers:
                okay = False
            elif session_id is None:
                session_id = markers["ENRICH_SESSION_ID"]
            elif markers["ENRICH_SESSION_ID"] != session_id:
                okay = False
        if subname == "finalize" and "ENRICH_BUNDLE_PATH" not in markers:
            okay = False

    if okay:
        update_step(step_id, "PASS", "Enrich start, add, and finalize behaved correctly.")
    else:
        update_step(step_id, "FAIL", "Enrich lifecycle did not behave as expected.")
        raise RuntimeError("Enrich lifecycle test failed.")
    return results


def find_first_glob(root: Path, pattern: str) -> Optional[Path]:
    matches = sorted(root.glob(pattern))
    return matches[0] if matches else None


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def run_review_surfaces(run_root: Path) -> None:
    update_step("review_surfaces", "RUNNING", "Inspecting tuned first-review collector surfaces.")
    follow_up = find_first_glob(run_root, "final_artifacts/35_ANALYST_FOLLOW_UP_QUEUE_*.txt")
    high_signal = find_first_glob(run_root, "final_artifacts/25A_EVENT_TIMELINE_TEXT_security_high_signal_summary.txt")
    overview = find_first_glob(run_root, "DCOIR_ANALYST_OVERVIEW_*.txt")
    missing = []
    if not follow_up:
        missing.append("analyst follow-up queue")
    if not high_signal:
        missing.append("security high-signal summary")
    if not overview:
        missing.append("analyst overview")
    if missing:
        update_step("review_surfaces", "FAIL", "Missing required review-surface files: " + ", ".join(missing) + ".")
        raise RuntimeError("Review-surface files missing.")

    follow_up_text = safe_read_text(follow_up)
    high_signal_text = safe_read_text(high_signal)
    overview_text = safe_read_text(overview)

    noisy_follow_up_hits = []
    if "DlpUserAgent.exe" in follow_up_text:
        noisy_follow_up_hits.append("DlpUserAgent.exe")
    if "-Quick collect-t1" in follow_up_text or "DCOIR_Collector.ps1" in follow_up_text and "collect-t1" in follow_up_text:
        noisy_follow_up_hits.append("collector self-run command")

    process_review_lines = [line for line in follow_up_text.splitlines() if "Process review candidate PID" in line]
    process_review_missing_parent = [line for line in process_review_lines if " parent=" not in line]

    noisy_task_hits = []
    for task_name in [r"\UptimeCheck", r"\UptimePopup", r"\Deploy_Sysmon_Production", r"\Cleanup Old PS Transcripts"]:
        if task_name in high_signal_text:
            noisy_task_hits.append(task_name)

    missing_overview_fields = [token for token in ["CollectTier=", "CollectorObservedErrorCount=", "RunHealth="] if token not in overview_text]

    problems = []
    if noisy_follow_up_hits:
        problems.append("follow-up queue still surfaced known benign items: " + ", ".join(noisy_follow_up_hits))
    if process_review_missing_parent:
        problems.append("process review candidates are missing parent context")
    if noisy_task_hits:
        problems.append("high-signal summary still surfaced suppressed scheduled tasks: " + ", ".join(noisy_task_hits))
    if missing_overview_fields:
        problems.append("analyst overview missing fields: " + ", ".join(missing_overview_fields))

    if problems:
        update_step("review_surfaces", "FAIL", "; ".join(problems))
        raise RuntimeError("Review-surface tuning check failed.")

    update_step("review_surfaces", "PASS", "Review surfaces reflect tuned suppression, process parent context, and overview fields.")


def record_t2_pathway_note() -> None:
    note = (
        "Framework recorded the bounded follow-on only. Use Airtable test case COL-T2-PATH-001 to compare T2-first, T2-after-T1, and any other bounded live pathway scenarios outside this automated framework."
    )
    append_report("\n" + "=" * 90 + "\n")
    append_report("T2 PATHWAY FOLLOW-ON NOTE")
    append_report(note)
    update_step("t2_pathway_note", "ACTION", note)


def run_negative_cases(step_id: str, outroot: Path) -> None:
    ensure_runtime_available()
    cases = [
        ("invalid_quick", powershell_cmd("-File", str(collector_script_path()), "-Quick", "unknown-value", "-OutRoot", str(outroot)), ["Unknown -Quick value", "DCOIR Collector Help"], True),
        ("missing_target", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-sigcheck", "-OutRoot", str(outroot)), ["requires -Target <path>"], True),
        ("bad_pid", powershell_cmd("-File", str(collector_script_path()), "-Quick", "enrich-start-listdlls", "-Target", "abc", "-OutRoot", str(outroot)), ["requires a numeric -Target <pid>"], True),
        ("bad_window", powershell_cmd("-File", str(collector_script_path()), "-Quick", "collect-targeted-popup", "-Target", "User reported popup", "-WindowStart", "not-a-date", "-WindowEnd", "2026-04-08T09:15:00Z", "-OutRoot", str(outroot)), ["Invalid WindowStart value"], False),
    ]
    update_step(step_id, "RUNNING", "Running bad-input tests.")
    pass_count = 0
    partial_count = 0
    for name, cmd, tokens, must_fail in cases:
        result = run_command(step_id, cmd, BASE_DIR, f"Running negative test: {name}.", allow_error=True)
        combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
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
    update_step("admin_launch", "LAUNCHING", "Opening the admin phase in a new elevated PowerShell window.")
    save_state()
    launcher = BASE_DIR / "run_dcoir_manual_tests.ps1"
    file_exists_or_raise(launcher, "run_dcoir_manual_tests.ps1")
    args = (
        f'-NoProfile -ExecutionPolicy Bypass -File "{launcher}" '
        f'-AdminPhase -StatePath "{STATE_PATH}" -BootstrapStatusPath "{BOOTSTRAP_STATUS_PATH}"'
    )
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", args, str(BASE_DIR), 1)
    if int(rc) <= 32:
        update_step("admin_launch", "FAIL", "UAC elevation did not start. Accept the admin prompt or rerun the launcher as Administrator.")
        raise RuntimeError("Could not start the admin phase. Accept the UAC prompt or rerun the launcher as Administrator.")
    update_step("admin_launch", "PASS", "Admin phase is now running.")
    append_report(f"Admin phase launched at {now_text()}\n")
    set_message("Admin phase launched. The elevated window should continue this same session with the same dashboard style.")
    sys.exit(0)


def compare_admin_nonadmin() -> None:
    nonadmin = STATE.get("context", {}).get("nonadmin_collect_markers", {})
    admin = STATE.get("context", {}).get("admin_collect_markers", {})
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
    ensure_runtime_available()
    outroot = OUTPUT_DIR / "harness_output"
    if outroot.exists():
        shutil.rmtree(outroot)
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


def cleanup_transient_framework_artifacts() -> None:
    for path in [collector_script_path(), live_zip_path()]:
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
    for path in [stage_dir(), build_dir()]:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def run_cleanup() -> None:
    ensure_runtime_available()
    update_step("cleanup", "RUNNING", "Running cleanup after evidence has already been saved.")
    okay = True
    for label, outroot in [("non-admin", RUNS_DIR / "nonadmin"), ("admin", RUNS_DIR / "admin")]:
        cmd = powershell_cmd("-File", str(collector_script_path()), "-Quick", "cleanup", "-OutRoot", str(outroot))
        result = run_command("cleanup", cmd, BASE_DIR, f"Running cleanup for the {label} run.", allow_error=True)
        combined = (result["stdout"] or "") + "\n" + (result["stderr"] or "")
        markers = parse_markers(combined)
        if markers.get("CLEANUP_STATUS") != "COMPLETE":
            okay = False
    cleanup_transient_framework_artifacts()
    if okay:
        update_step("cleanup", "PASS", "Cleanup completed after the evidence was saved, and transient staged runtime files were removed.")
    else:
        update_step("cleanup", "PARTIAL", "Cleanup ran, but at least one cleanup pass did not report COMPLETE cleanly.")


def final_signoff() -> None:
    steps = STATE["steps"]
    counts: Dict[str, int] = {}
    for payload in steps.values():
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
    append_report("Per-step results:")
    for step_id, _label in STEP_ORDER:
        payload = STATE["steps"][step_id]
        append_report(f"  - {payload['label']}: {payload['status']} :: {payload.get('note', '')}")
    update_step("final_signoff", "PASS" if failed == 0 else "PARTIAL", f"{verdict} - {note}")
    set_message(f"Framework finished. Verdict: {verdict}. Open the report at {REPORT_PATH}")


def top_level_failure(exc: Exception) -> None:
    append_report("\n" + "=" * 90 + "\n")
    append_report("FRAMEWORK FATAL ERROR")
    append_report(f"Timestamp: {now_text()}")
    append_report(str(exc))
    append_report(traceback.format_exc())
    access_denied = "denied" in str(exc).lower() or "access is denied" in str(exc).lower()
    if access_denied:
        set_message(
            "Execution failed because a file or folder was locked or denied. Close any leftover PowerShell or Python windows, let antivirus finish, then rerun the launcher."
        )
    else:
        set_message(
            "Execution failed. Read the report file for the full command output and traceback. If this happened during repo access, authenticate Git and rerun. If it happened right after an install, close this window, open a new PowerShell window, and rerun the launcher."
        )
    cleanup_transient_framework_artifacts()


def main() -> int:
    ensure_dirs()
    STATE.setdefault("context", {})["framework_started_at"] = STATE.get("context", {}).get("framework_started_at", now_text())
    init_report()
    render_dashboard("Framework loaded. Preparing to run.")
    save_state()

    try:
        sync_bootstrap_into_state(STATE)
        save_state()
        if ARGS.admin_phase:
            update_step("admin_launch", "PASS", "Admin phase is now running.")

        ensure_repo()
        validate_package()
        build_package()
        restore_and_stage_runtime()
        run_help_tests()

        if not ARGS.admin_phase:
            nonadmin_out = RUNS_DIR / "nonadmin"
            nonadmin_collect_output, nonadmin_collect_markers, nonadmin_run_root = run_collect("nonadmin_collect", nonadmin_out, targeted=False)
            STATE["context"]["nonadmin_collect_output"] = nonadmin_collect_output
            STATE["context"]["nonadmin_collect_markers"] = nonadmin_collect_markers
            STATE["context"]["nonadmin_run_root"] = str(nonadmin_run_root)
            save_state()

            nonadmin_validator_output, nonadmin_validator_rc = run_validator("nonadmin_validate", nonadmin_run_root)
            STATE["context"]["nonadmin_validator_output"] = nonadmin_validator_output
            STATE["context"]["nonadmin_validator_rc"] = nonadmin_validator_rc
            save_state()

            run_review_surfaces(nonadmin_run_root)

            targeted_out = RUNS_DIR / "nonadmin_targeted"
            targeted_output, targeted_markers, targeted_run_root = run_collect("nonadmin_targeted", targeted_out, targeted=True)
            STATE["context"]["nonadmin_targeted_output"] = targeted_output
            STATE["context"]["nonadmin_targeted_markers"] = targeted_markers
            STATE["context"]["nonadmin_targeted_run_root"] = str(targeted_run_root)
            save_state()

            enrich_results = run_enrich_lifecycle("nonadmin_enrich", nonadmin_out)
            STATE["context"]["nonadmin_enrich_results"] = enrich_results
            save_state()

            run_negative_cases("nonadmin_negative", RUNS_DIR / "nonadmin_negative")
            launch_admin_phase()
            return 0

        admin_out = RUNS_DIR / "admin"
        ensure_runtime_available()
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
        record_t2_pathway_note()
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
