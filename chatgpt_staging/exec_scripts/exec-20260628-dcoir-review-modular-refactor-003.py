#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REQUEST_ID = "exec-20260628-dcoir-review-modular-refactor-003"
BRANCH_NAME = "refactor/dcoir-review-modular-runtime-20260628"
CLEAN_BASE_SEED_COMMIT = "5adae509c99a0b6246c523c7290fd83e558e5ab5"
MAX_CONNECTOR_SAFE_LINES = 575
ROOT = Path.cwd()
PKG = ROOT / "scripts" / "dcoir_review"
REPORT_DIR = ROOT / "chatgpt_staging" / "status_reports" / "chatgpt-exec" / REQUEST_ID
SUMMARY_MD = REPORT_DIR / "modular_refactor_summary.md"
SUMMARY_JSON = REPORT_DIR / "modular_refactor_summary.json"

RUNTIME_LAYERS = {
    "base": [
        ("base/part_01_core_config_github.py", 1, "PRIVATE_KEY_BLOCK"),
        ("base/part_02_redaction_core.py", "PRIVATE_KEY_BLOCK", "skip_line_continuation_whitespace"),
        ("base/part_03_redaction_shell.py", "skip_line_continuation_whitespace", "debug_artifact_root"),
        ("base/part_04_debug_artifacts.py", "debug_artifact_root", "build_prompt"),
        ("base/part_05_prompt_provider.py", "build_prompt", "normalize_findings"),
        ("base/part_06_findings_comments.py", "normalize_findings", "main"),
        ("base/part_07_main.py", "main", None),
    ],
    "hardened": [
        ("hardened/part_01_rules.py", 1, "sanitize_github_output"),
        ("hardened/part_02_config_progress.py", "sanitize_github_output", "iter_added_diff_lines"),
        ("hardened/part_03_sentinels_prompt.py", "iter_added_diff_lines", "raw_findings_digest"),
        ("hardened/part_04_quality_provider.py", "raw_findings_digest", "write_debug_text_artifact_safely"),
        ("hardened/part_05_debug_and_merge.py", "write_debug_text_artifact_safely", "summary_suggests_problem"),
        ("hardened/part_06_normalize_select.py", "summary_suggests_problem", "format_unanchored_finding"),
        ("hardened/part_07_review_body_main.py", "format_unanchored_finding", None),
    ],
    "pareto_context": [
        ("pareto_context/part_01_config_payload.py", 1, "python_path_assignment_start"),
        ("pareto_context/part_02_python_path_helpers.py", "python_path_assignment_start", "detect_python_dynamic_exec_sentinels"),
        ("pareto_context/part_03_python_diff_scope.py", "detect_python_dynamic_exec_sentinels", "detect_python_file_write_path_sentinels"),
        ("pareto_context/part_04_sentinels_modes_context.py", "detect_python_file_write_path_sentinels", "rank_findings_for_required_budget"),
        ("pareto_context/part_05_ranking_per_file_review.py", "rank_findings_for_required_budget", "file_line_text"),
        ("pareto_context/part_06_fix_synthesis.py", "file_line_text", "build_python_path_alias_context"),
        ("pareto_context/part_07_deep_context_main.py", "build_python_path_alias_context", None),
    ],
}
WRAPPER_TARGETS = {
    "base": "scripts/openrouter_pr_review.py",
    "hardened": "scripts/openrouter_pr_review_hardened.py",
    "pareto_context": "scripts/openrouter_pr_review_pareto_context.py",
}
SELFTEST_TARGETS = {
    "base_selftest": "scripts/openrouter_pr_review_selftest.py",
    "hardened_selftest": "scripts/openrouter_pr_review_hardened_selftest.py",
    "pareto_context_selftest": "scripts/openrouter_pr_review_pareto_context_selftest.py",
}
PATCH_APPLY_ORDER = (
    "dcoir_review_runtime_patches",
    "dcoir_review_strict_runtime_patches",
    "dcoir_review_required_runtime_patches",
    "dcoir_review_required_runtime_patch_v2",
    "dcoir_review_required_runtime_patch_v3",
    "dcoir_review_required_runtime_patch_v4_apply",
    "dcoir_review_required_runtime_patch_v5_apply",
    "dcoir_review_required_runtime_patch_v6",
    "dcoir_review_required_runtime_patch_v7",
    "dcoir_review_required_runtime_patch_v8",
    "dcoir_review_required_runtime_patch_v9",
    "dcoir_review_required_runtime_patch_v10",
    "dcoir_review_required_runtime_patch_v11",
    "dcoir_review_required_runtime_patch_v12",
    "dcoir_review_required_runtime_patch_v13",
    "dcoir_review_required_runtime_patch_v15",
    "dcoir_review_required_runtime_patch_v14",
    "dcoir_review_required_runtime_patch_v15",
    "dcoir_review_required_runtime_patch_v16",
    "dcoir_review_required_runtime_patch_v17",
    "dcoir_review_required_runtime_patch_v18",
)


def run(args: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=capture)


def sh(command: str) -> None:
    print("+", command, flush=True)
    subprocess.run(command, cwd=ROOT, shell=True, check=True)


def summary(line: str = "") -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with SUMMARY_MD.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_marker_line(lines: list[str], marker: str) -> int:
    tree = ast.parse("\n".join(lines) + "\n")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == marker:
            return int(node.lineno)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == marker:
                    return int(node.lineno)
    for index, line in enumerate(lines, start=1):
        if line.startswith(marker):
            return index
    raise KeyError(f"marker not found: {marker}")


def marker_to_start(lines: list[str], marker: str | int | None) -> int:
    if marker is None:
        return len(lines) + 1
    if isinstance(marker, int):
        return marker
    return find_marker_line(lines, marker)


def write_runtime_layer(layer: str, source_path: Path, specs: list[tuple[str, str | int, str | None]], manifest: list[dict[str, object]]) -> list[str]:
    lines = read_lines(source_path)
    rel_paths: list[str] = []
    for rel, start_marker, end_marker in specs:
        start = marker_to_start(lines, start_marker)
        end = marker_to_start(lines, end_marker) - 1 if end_marker is not None else len(lines)
        text = "\n".join(lines[start - 1 : end]) + "\n"
        out_path = PKG / rel
        write_text(out_path, text)
        line_count = len(text.splitlines())
        manifest.append({"path": out_path.relative_to(ROOT).as_posix(), "source": source_path.relative_to(ROOT).as_posix(), "start_line": start, "end_line": end, "line_count": line_count, "layer": layer})
        rel_paths.append(rel)
    return rel_paths


def split_top_level_source(layer: str, source_path: Path, out_dir: Path, manifest: list[dict[str, object]], max_lines: int = 420) -> list[str]:
    lines = read_lines(source_path)
    tree = ast.parse("\n".join(lines) + "\n")
    nodes = [node for node in tree.body if hasattr(node, "lineno") and hasattr(node, "end_lineno")]
    chunks: list[tuple[int, int]] = []
    start = 1
    end = 0
    for node in nodes:
        node_start = int(node.lineno)
        node_end = int(node.end_lineno or node.lineno)
        if end and node_end - start + 1 > max_lines:
            chunks.append((start, end))
            start = node_start
        end = node_end
    if end:
        chunks.append((start, len(lines)))
    rel_paths: list[str] = []
    for index, (start_line, end_line) in enumerate(chunks, start=1):
        rel = f"{out_dir.as_posix()}/part_{index:02d}.py"
        text = "\n".join(lines[start_line - 1 : end_line]) + "\n"
        out_path = PKG / rel
        write_text(out_path, text)
        line_count = len(text.splitlines())
        manifest.append({"path": out_path.relative_to(ROOT).as_posix(), "source": source_path.relative_to(ROOT).as_posix(), "start_line": start_line, "end_line": end_line, "line_count": line_count, "layer": layer})
        rel_paths.append(rel)
    return rel_paths


def layer_mapping_literal(layer_paths: dict[str, list[str]]) -> str:
    lines = ["LAYER_SEGMENTS: dict[str, tuple[str, ...]] = {"]
    for layer, paths in layer_paths.items():
        lines.append(f"    {layer!r}: (")
        lines.extend(f"        {path!r}," for path in paths)
        lines.append("    ),")
    lines.append("}")
    return "\n".join(lines)


def write_wrappers(layer_paths: dict[str, list[str]]) -> None:
    loader = f'''from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Any, MutableMapping\n\n{layer_mapping_literal(layer_paths)}\n\n\n@dataclass(frozen=True)\nclass RuntimeSegmentLoader:\n    layer: str\n    root: Path = Path(__file__).resolve().parent\n\n    def segment_paths(self) -> tuple[Path, ...]:\n        try:\n            relatives = LAYER_SEGMENTS[self.layer]\n        except KeyError as exc:\n            raise KeyError(f"unknown DCOIR Review runtime layer: {{self.layer}}") from exc\n        return tuple(self.root / relative for relative in relatives)\n\n    def load_into(self, namespace: MutableMapping[str, Any]) -> None:\n        for path in self.segment_paths():\n            source = path.read_text(encoding="utf-8")\n            exec(compile(source, str(path), "exec"), namespace)\n\n\ndef load_segments_into(namespace: MutableMapping[str, Any], layer: str) -> None:\n    RuntimeSegmentLoader(layer).load_into(namespace)\n'''
    write_text(PKG / "module_loader.py", loader)
    write_text(PKG / "__init__.py", '"""Connector-safe DCOIR Review runtime package."""\n')
    for directory in {Path(path).parent for paths in layer_paths.values() for path in paths}:
        if directory != Path("."):
            write_text(PKG / directory / "__init__.py", '"""Generated DCOIR Review runtime segment package."""\n')
    for layer, target in {**WRAPPER_TARGETS, **SELFTEST_TARGETS}.items():
        text = f'''#!/usr/bin/env python3\n"""Compatibility wrapper for connector-safe DCOIR Review layer {layer}."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport sys\n\n_SCRIPT_DIR = Path(__file__).resolve().parent\nif str(_SCRIPT_DIR) not in sys.path:\n    sys.path.insert(0, str(_SCRIPT_DIR))\n\nfrom dcoir_review.module_loader import load_segments_into\n\nload_segments_into(globals(), {layer!r})\n'''
        write_text(ROOT / target, text)
    patch_items = "\n".join(f"        {name!r}," for name in PATCH_APPLY_ORDER)
    entrypoint = f'''from __future__ import annotations\n\nimport importlib\nfrom dataclasses import dataclass\nfrom types import ModuleType\nfrom typing import Iterable\n\n\n@dataclass(frozen=True)\nclass DcoirReviewEntrypoint:\n    review_module_name: str = "openrouter_pr_review_pareto_context"\n    patch_module_names: tuple[str, ...] = (\n{patch_items}\n    )\n\n    def import_module(self, module_name: str) -> ModuleType:\n        return importlib.import_module(module_name)\n\n    def apply_runtime_patches(self, review_module: ModuleType, patch_module_names: Iterable[str] | None = None) -> None:\n        for module_name in tuple(patch_module_names or self.patch_module_names):\n            patch_module = self.import_module(module_name)\n            apply_patch = getattr(patch_module, "apply_pareto_context_module", None)\n            if apply_patch is None:\n                raise RuntimeError(f"Runtime patch module {{module_name}} does not expose apply_pareto_context_module")\n            apply_patch(review_module)\n\n    def run(self) -> None:\n        review_module = self.import_module(self.review_module_name)\n        self.apply_runtime_patches(review_module)\n        review_module.main()\n\n\ndef main() -> None:\n    DcoirReviewEntrypoint().run()\n'''
    write_text(PKG / "entrypoint.py", entrypoint)
    write_text(ROOT / "scripts" / "openrouter_pr_review_entrypoint.py", '''#!/usr/bin/env python3\n"""Compatibility wrapper for the connector-safe DCOIR Review entrypoint."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport sys\n\n_SCRIPT_DIR = Path(__file__).resolve().parent\nif str(_SCRIPT_DIR) not in sys.path:\n    sys.path.insert(0, str(_SCRIPT_DIR))\n\nfrom dcoir_review.entrypoint import main\n\n\nif __name__ == "__main__":\n    main()\n''')


def split_workflow(manifest: list[dict[str, object]]) -> None:
    workflow = ROOT / ".github" / "workflows" / "openrouter-pr-review.yml"
    original = workflow.read_text(encoding="utf-8")
    header, jobs_suffix = original.split("\njobs:\n", 1)
    reusable_jobs = "jobs:\n" + jobs_suffix
    reusable_lines = reusable_jobs.splitlines()
    cleaned: list[str] = []
    index = 0
    while index < len(reusable_lines):
        line = reusable_lines[index]
        if line == "    if: >-":
            while index < len(reusable_lines) and not reusable_lines[index].startswith("    runs-on:"):
                index += 1
            continue
        cleaned.append(line)
        index += 1
    caller = header.rstrip() + """

jobs:
  review:
    name: DCOIR review
    if: >-
      ${{
        github.event.issue.pull_request &&
        github.event.comment.user.type != 'Bot' &&
        github.event.comment.user.login == 'malwaredevil'
      }}
    uses: ./.github/workflows/reusable-openrouter-pr-review.yml
    permissions:
      actions: read
      contents: read
      issues: write
      pull-requests: write
    secrets:
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
"""
    reusable = """# DCOIR REUSABLE WORKFLOW CONTRACT
# Source entry workflow: openrouter-pr-review.yml
# Purpose: reusable implementation module for operator-triggered DCOIR Review; entry workflow retains triggers, permissions, concurrency, and operator-visible contract notes.
name: 99 Module - DCOIR Review
run-name: Module DCOIR Review | ${{ github.workflow }} | #${{ github.run_number }}

on:
  workflow_call:
    secrets:
      OPENROUTER_API_KEY:
        description: Explicit forwarded OpenRouter API key from the entry workflow.
        required: true

permissions:
  actions: read
  contents: read
  issues: write
  pull-requests: write

""" + "\n".join(cleaned) + "\n"
    write_text(workflow, caller)
    reusable_path = ROOT / ".github" / "workflows" / "reusable-openrouter-pr-review.yml"
    write_text(reusable_path, reusable)
    for path in (workflow, reusable_path):
        manifest.append({"path": path.relative_to(ROOT).as_posix(), "line_count": len(path.read_text(encoding="utf-8").splitlines()), "layer": "workflow"})


def generate_modular_sources() -> list[dict[str, object]]:
    if PKG.exists():
        shutil.rmtree(PKG)
    manifest: list[dict[str, object]] = []
    layer_paths: dict[str, list[str]] = {}
    for layer, target in WRAPPER_TARGETS.items():
        layer_paths[layer] = write_runtime_layer(layer, ROOT / target, RUNTIME_LAYERS[layer], manifest)
    for layer, target in SELFTEST_TARGETS.items():
        layer_paths[layer] = split_top_level_source(layer, ROOT / target, Path("selftests") / layer, manifest)
    write_wrappers(layer_paths)
    split_workflow(manifest)
    for rel in list(WRAPPER_TARGETS.values()) + list(SELFTEST_TARGETS.values()) + ["scripts/openrouter_pr_review_entrypoint.py"]:
        path = ROOT / rel
        manifest.append({"path": rel, "line_count": len(path.read_text(encoding="utf-8").splitlines()), "layer": "wrapper"})
    manifest_data = {"schema": "dcoir.review.modularization_manifest.v1", "max_connector_safe_lines": MAX_CONNECTOR_SAFE_LINES, "files": manifest}
    write_text(PKG / "modularization_manifest.json", json.dumps(manifest_data, indent=2) + "\n")
    manifest.append({"path": "scripts/dcoir_review/modularization_manifest.json", "line_count": len((PKG / "modularization_manifest.json").read_text(encoding="utf-8").splitlines()), "layer": "manifest"})
    oversized = [item for item in manifest if int(item.get("line_count", 0)) > MAX_CONNECTOR_SAFE_LINES]
    if oversized:
        raise RuntimeError("connector-safe limit exceeded: " + "; ".join(f"{item['path']}={item['line_count']}" for item in oversized))
    for path in list((ROOT / "scripts").glob("openrouter_pr_review*.py")) + list(PKG.rglob("*.py")) + [ROOT / ".github" / "workflows" / "openrouter-pr-review.yml", ROOT / ".github" / "workflows" / "reusable-openrouter-pr-review.yml"]:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_CONNECTOR_SAFE_LINES:
            raise RuntimeError(f"post-generation connector-safe check failed: {path.relative_to(ROOT).as_posix()}={line_count}")
    return manifest


def validate() -> None:
    commands = [
        "python -m py_compile scripts/openrouter_pr_review.py scripts/openrouter_pr_review_hardened.py scripts/openrouter_pr_review_pareto_context.py scripts/openrouter_pr_review_entrypoint.py scripts/dcoir_review/module_loader.py scripts/dcoir_review/entrypoint.py",
        "python -m py_compile scripts/dcoir_review/base/*.py scripts/dcoir_review/hardened/*.py scripts/dcoir_review/pareto_context/*.py scripts/dcoir_review/selftests/base_selftest/*.py scripts/dcoir_review/selftests/hardened_selftest/*.py scripts/dcoir_review/selftests/pareto_context_selftest/*.py",
        "python scripts/openrouter_pr_review_selftest.py",
        "python scripts/openrouter_pr_review_codex_regression_selftest.py",
        "python scripts/openrouter_pr_review_hardened_selftest.py",
        "python scripts/openrouter_pr_review_quality_recovery_selftest.py",
        "python scripts/openrouter_pr_review_pareto_context_regression_selftest.py",
        "python scripts/openrouter_pr_review_pareto_context_selftest.py",
    ]
    summary("## Validation commands")
    for command in commands:
        summary(f"- `{command}`")
        sh(command)


def create_or_get_pr(head_sha: str) -> dict[str, object]:
    repo = os.environ.get("GITHUB_REPOSITORY", "DCOIR-Collector/dcoir-collector")
    token = os.environ.get("DCOIR_GITHUB_FG_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("No GitHub token available for PR creation")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "dcoir-chatgpt-exec",
    }
    body = {
        "title": "[refactor] Modularize DCOIR Review runtime",
        "head": BRANCH_NAME,
        "base": "main",
        "draft": True,
        "body": "\n".join([
            "Behavior-preserving connector-safe modularization of the DCOIR Review workflow/runtime.",
            "",
            "What changed:",
            "- Keeps public script names as compatibility wrappers.",
            "- Moves active DCOIR Review runtime layers into scripts/dcoir_review/ connector-safe package segments.",
            "- Converts the patch-chain entrypoint into an object-oriented DcoirReviewEntrypoint class.",
            "- Splits openrouter-pr-review.yml into a thin caller plus reusable workflow module.",
            "- Splits the largest selftest entrypoints into connector-safe package segments while preserving old command names.",
            "",
            "Validation run by chatgpt-exec:",
            "- py_compile for wrappers and generated package segments.",
            "- openrouter_pr_review_selftest.py.",
            "- openrouter_pr_review_codex_regression_selftest.py.",
            "- openrouter_pr_review_hardened_selftest.py.",
            "- openrouter_pr_review_quality_recovery_selftest.py.",
            "- openrouter_pr_review_pareto_context_regression_selftest.py.",
            "- openrouter_pr_review_pareto_context_selftest.py.",
            "",
            f"Refactor head SHA: {head_sha}",
            "",
            "This PR is intentionally draft until DCOIR Review and operator grading are complete.",
        ]),
    }
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(f"https://api.github.com/repos/{repo}/pulls", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise
        query = urllib.parse.urlencode({"head": f"DCOIR-Collector:{BRANCH_NAME}", "state": "open"})
        existing_request = urllib.request.Request(f"https://api.github.com/repos/{repo}/pulls?{query}", headers=headers, method="GET")
        with urllib.request.urlopen(existing_request, timeout=60) as response:
            existing = json.loads(response.read().decode("utf-8"))
        if not existing:
            raise
        return existing[0]


def cleanup_transient_main_files() -> None:
    run(["git", "checkout", "-B", "main", os.environ.get("GITHUB_SHA", "HEAD")])
    transient = [
        "chatgpt_staging/exec_scripts/exec-20260628-dcoir-review-modular-refactor-001.ps1",
        "chatgpt_staging/exec_scripts/exec-20260628-dcoir-review-modular-refactor-002.ps1",
        "chatgpt_staging/exec_scripts/exec-20260628-dcoir-review-modular-refactor-003.py",
        "chatgpt_staging/exec_requests/exec-20260628-dcoir-review-modular-refactor-003.json",
    ]
    for rel in transient:
        path = ROOT / rel
        if path.exists():
            path.unlink()
    run(["git", "add", "-A", "--", *transient])
    status = run(["git", "status", "--short", "--", *transient], capture=True).stdout.strip()
    if status:
        run(["git", "commit", "-m", "Clean up transient ChatGPT exec modular refactor files [skip ci]"])
        run(["git", "push", "origin", "HEAD:main"])


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text("# DCOIR Review modular refactor readback\n\n", encoding="utf-8", newline="\n")
    summary(f"- request_id: {REQUEST_ID}")
    summary(f"- branch: {BRANCH_NAME}")
    run(["git", "config", "user.name", "DCOIR ChatGPT Exec"])
    run(["git", "config", "user.email", "dcoir-chatgpt-exec@users.noreply.github.com"])
    run(["git", "fetch", "origin", "main", "--prune"])
    clean_base = run(["git", "rev-parse", f"{CLEAN_BASE_SEED_COMMIT}^"], capture=True).stdout.strip()
    summary(f"- clean_base: {clean_base}")
    run(["git", "checkout", "-B", BRANCH_NAME, clean_base])
    manifest = generate_modular_sources()
    validate()
    tracked = [
        ".github/workflows/openrouter-pr-review.yml",
        ".github/workflows/reusable-openrouter-pr-review.yml",
        "scripts/openrouter_pr_review.py",
        "scripts/openrouter_pr_review_hardened.py",
        "scripts/openrouter_pr_review_pareto_context.py",
        "scripts/openrouter_pr_review_entrypoint.py",
        "scripts/openrouter_pr_review_selftest.py",
        "scripts/openrouter_pr_review_hardened_selftest.py",
        "scripts/openrouter_pr_review_pareto_context_selftest.py",
        "scripts/dcoir_review",
    ]
    run(["git", "add", "--", *tracked])
    stat = run(["git", "diff", "--cached", "--stat"], capture=True).stdout.strip()
    summary("\n## Git diff stat")
    summary("```text")
    summary(stat)
    summary("```")
    run(["git", "commit", "-m", "Refactor DCOIR Review runtime into connector-safe modules"])
    head_sha = run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    run(["git", "push", "--force-with-lease", "origin", f"HEAD:refs/heads/{BRANCH_NAME}"])
    pr = create_or_get_pr(head_sha)
    max_lines = max(int(item.get("line_count", 0)) for item in manifest)
    summary("\n## Draft PR")
    summary(f"- pr_number: {pr.get('number')}")
    summary(f"- pr_url: {pr.get('html_url')}")
    summary(f"- pr_head_sha: {head_sha}")
    summary(f"- generated_file_count: {len(manifest)}")
    summary(f"- maximum_generated_file_lines: {max_lines}")
    result = {
        "schema": "dcoir.review.modular_refactor_readback.v1",
        "request_id": REQUEST_ID,
        "branch": BRANCH_NAME,
        "clean_base": clean_base,
        "head_sha": head_sha,
        "pr_number": pr.get("number"),
        "pr_url": pr.get("html_url"),
        "generated_file_count": len(manifest),
        "maximum_generated_file_lines": max_lines,
        "connector_safe_limit": MAX_CONNECTOR_SAFE_LINES,
        "validation": "pass",
    }
    SUMMARY_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    cleanup_transient_main_files()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "modular_refactor_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        raise
