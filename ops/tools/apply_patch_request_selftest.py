#!/usr/bin/env python3
"""Self-tests for the governed ops apply-patch request tool."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from collections.abc import Mapping


TOOL = pathlib.Path(__file__).with_name("apply_patch_request.py").resolve()


def run(
    cmd: list[str],
    cwd: pathlib.Path,
    *,
    check: bool = True,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=merged_env)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_repo(repo: pathlib.Path) -> None:
    run(["git", "init", "-b", "main"], repo)
    run(["git", "config", "user.email", "dcoir-selftest@example.invalid"], repo)
    run(["git", "config", "user.name", "DCOIR Selftest"], repo)
    write(repo / "project_sources/large.txt", "alpha\nbeta\n")
    write(repo / "project_sources/other.txt", "one\n")
    run(["git", "add", "project_sources"], repo)
    run(["git", "commit", "-m", "seed"], repo)
    run(["git", "checkout", "-b", "feature/apply-patch-target"], repo)
    run(["git", "checkout", "main"], repo)
    run(["git", "config", "--unset", "user.name"], repo, check=False)
    run(["git", "config", "--unset", "user.email"], repo, check=False)


def make_patch(repo: pathlib.Path, new_text: str, patch_path: pathlib.Path) -> None:
    target = repo / "project_sources/large.txt"
    original = target.read_text(encoding="utf-8")
    target.write_text(new_text, encoding="utf-8")
    patch = run(["git", "diff", "--", "project_sources/large.txt"], repo).stdout
    target.write_text(original, encoding="utf-8")
    write(patch_path, patch)


def request_body(repo: pathlib.Path, request_id: str, patch_rel: str, patch_file: pathlib.Path, *, target_branch: str = "feature/apply-patch-target") -> dict[str, object]:
    blob = run(["git", "ls-files", "-s", "--", "project_sources/large.txt"], repo).stdout.split()[1]
    return {
        "schema": "dcoir.ops.apply_patch_request.v1",
        "request_id": request_id,
        "mode": "apply",
        "target_branch": target_branch,
        "target_path": "project_sources/large.txt",
        "allowed_roots": ["project_sources"],
        "patch_path": patch_rel,
        "expected_patch_sha256": sha256(patch_file),
        "expected_target_blob_sha": blob,
        "expected_current_sha256": sha256(repo / "project_sources/large.txt"),
        "expected_new_sha256": hashlib.sha256(b"alpha\nBETA\n").hexdigest(),
        "commit_message": f"Apply selftest patch {request_id}",
    }


def test_happy_path(repo: pathlib.Path) -> None:
    no_global_git_identity = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    request_id = "selftest-good"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    make_patch(repo, "alpha\nBETA\n", patch_file)
    write(request_dir / "request.json", json.dumps(request_body(repo, request_id, patch_rel, patch_file), indent=2) + "\n")

    run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo)
    report_dir = repo / "out/report"
    run(
        [
            sys.executable,
            str(TOOL),
            "apply",
            "--repo",
            str(repo),
            "--request",
            str(request_dir / "request.json"),
            "--local-only",
            "--no-push",
            "--report-dir",
            str(report_dir),
        ],
        repo,
        env=no_global_git_identity,
    )
    assert (repo / "project_sources/large.txt").read_text(encoding="utf-8") == "alpha\nBETA\n"
    assert json.loads((report_dir / "result.json").read_text(encoding="utf-8"))["result"] == "success"
    assert run(["git", "config", "--local", "--get", "user.name"], repo).stdout.strip() == "github-actions[bot]"
    assert run(["git", "config", "--local", "--get", "user.email"], repo).stdout.strip() == "41898282+github-actions[bot]@users.noreply.github.com"


def test_rejects_default_branch(repo: pathlib.Path) -> None:
    request_id = "selftest-main"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    run(["git", "checkout", "main"], repo)
    make_patch(repo, "alpha\nBETA\n", patch_file)
    body = request_body(repo, request_id, patch_rel, patch_file, target_branch="main")
    write(request_dir / "request.json", json.dumps(body, indent=2) + "\n")
    proc = run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo, check=False)
    assert proc.returncode != 0
    assert "default branch" in proc.stderr


def test_rejects_multifile_patch(repo: pathlib.Path) -> None:
    request_id = "selftest-multifile"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    run(["git", "checkout", "main"], repo)
    write(repo / "project_sources/large.txt", "alpha\nBETA\n")
    write(repo / "project_sources/other.txt", "two\n")
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(run(["git", "diff", "--", "project_sources"], repo).stdout, encoding="utf-8")
    run(["git", "checkout", "--", "project_sources"], repo)
    body = request_body(repo, request_id, patch_rel, patch_file)
    body["expected_new_sha256"] = hashlib.sha256(b"alpha\nBETA\n").hexdigest()
    write(request_dir / "request.json", json.dumps(body, indent=2) + "\n")
    proc = run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo, check=False)
    assert proc.returncode != 0
    assert "patch must touch only target_path" in proc.stderr


def test_rejects_plain_delete_patch(repo: pathlib.Path) -> None:
    request_id = "selftest-delete"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    run(["git", "checkout", "main"], repo)
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(
        "diff --git a/project_sources/large.txt b/project_sources/large.txt\n"
        "--- a/project_sources/large.txt\n"
        "+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n"
        "-alpha\n"
        "-beta\n",
        encoding="utf-8",
    )
    body = request_body(repo, request_id, patch_rel, patch_file)
    body.pop("expected_new_sha256", None)
    write(request_dir / "request.json", json.dumps(body, indent=2) + "\n")
    proc = run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo, check=False)
    assert proc.returncode != 0
    assert "must not create or delete" in proc.stderr


def test_rejects_non_string_digest(repo: pathlib.Path) -> None:
    request_id = "selftest-nonstring-digest"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    run(["git", "checkout", "main"], repo)
    make_patch(repo, "alpha\nBETA\n", patch_file)
    body = request_body(repo, request_id, patch_rel, patch_file)
    body["expected_target_blob_sha"] = 12345
    write(request_dir / "request.json", json.dumps(body, indent=2) + "\n")
    proc = run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo, check=False)
    assert proc.returncode != 0
    assert "expected_target_blob_sha must be a string" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_rejects_string_boolean_override(repo: pathlib.Path) -> None:
    request_id = "selftest-string-bool"
    request_dir = repo / "ops/requests/apply_patch" / request_id
    patch_rel = f"ops/requests/apply_patch/{request_id}/change.patch"
    patch_file = repo / patch_rel
    run(["git", "checkout", "main"], repo)
    make_patch(repo, "alpha\nBETA\n", patch_file)
    body = request_body(repo, request_id, patch_rel, patch_file, target_branch="main")
    body["allow_default_branch"] = "false"
    body["default_branch_reason"] = "string booleans must not unlock this gate"
    write(request_dir / "request.json", json.dumps(body, indent=2) + "\n")
    proc = run([sys.executable, str(TOOL), "validate", "--repo", str(repo), "--request", str(request_dir / "request.json")], repo, check=False)
    assert proc.returncode != 0
    assert "allow_default_branch must be a boolean" in proc.stderr


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dcoir-ops-patch-") as tmp:
        repo = pathlib.Path(tmp)
        init_repo(repo)
        test_happy_path(repo)
        test_rejects_default_branch(repo)
        test_rejects_multifile_patch(repo)
        test_rejects_plain_delete_patch(repo)
        test_rejects_non_string_digest(repo)
        test_rejects_string_boolean_override(repo)
    print("apply_patch_request selftests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
