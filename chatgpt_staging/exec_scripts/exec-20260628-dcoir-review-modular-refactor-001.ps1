$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'exec-20260628-dcoir-review-modular-refactor-001'
$BranchName = 'refactor/dcoir-review-modular-runtime-20260628'
$Repo = if ([string]::IsNullOrWhiteSpace($env:GITHUB_REPOSITORY)) { 'DCOIR-Collector/dcoir-collector' } else { $env:GITHUB_REPOSITORY }
$RepoRoot = if ([string]::IsNullOrWhiteSpace($env:GITHUB_WORKSPACE)) { (Get-Location).Path } else { $env:GITHUB_WORKSPACE }
$TempRoot = Join-Path $env:RUNNER_TEMP $RequestId
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
$TempSummary = Join-Path $TempRoot 'modular_refactor_summary.md'
$TempJson = Join-Path $TempRoot 'modular_refactor_summary.json'

function Add-SummaryLine {
  param([string]$Text = '')
  Add-Content -LiteralPath $TempSummary -Value $Text -Encoding UTF8
}

function Invoke-GitChecked {
  param([Parameter(Mandatory=$true)][string[]]$Arguments)
  & git @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
}

function Invoke-CommandChecked {
  param([Parameter(Mandatory=$true)][string]$Command)
  Add-SummaryLine "- `$Command`"
  cmd /c $Command
  if ($LASTEXITCODE -ne 0) {
    throw "validation command failed with exit code ${LASTEXITCODE}: $Command"
  }
}

Set-Location -LiteralPath $RepoRoot
Add-SummaryLine '# DCOIR Review modular refactor readback'
Add-SummaryLine ''
Add-SummaryLine "- request_id: $RequestId"
Add-SummaryLine "- branch: $BranchName"
Add-SummaryLine "- repository: $Repo"
Add-SummaryLine "- workflow_sha: $env:GITHUB_SHA"

Invoke-GitChecked @('config', 'user.name', 'DCOIR ChatGPT Exec')
Invoke-GitChecked @('config', 'user.email', 'dcoir-chatgpt-exec@users.noreply.github.com')
Invoke-GitChecked @('fetch', 'origin', 'main', '--prune')

$CleanBase = ''
try {
  $CleanBase = (& git rev-parse "$env:GITHUB_SHA~2").Trim()
} catch {
  $CleanBase = (& git rev-parse 'origin/main').Trim()
}
if ([string]::IsNullOrWhiteSpace($CleanBase)) { throw 'Unable to resolve clean base commit for refactor branch.' }
Add-SummaryLine "- clean_base: $CleanBase"

Invoke-GitChecked @('checkout', '-B', $BranchName, $CleanBase)

$Generator = @'
from __future__ import annotations

import ast
import json
import shutil
import textwrap
from pathlib import Path

ROOT = Path.cwd()
MAX_CONNECTOR_SAFE_LINES = 575
PKG = ROOT / "scripts" / "dcoir_review"

RUNTIME_LAYERS: dict[str, list[tuple[str, str | int, str | None]]] = {
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


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_marker_line(lines: list[str], marker: str) -> int:
    try:
        tree = ast.parse("\n".join(lines) + "\n")
    except SyntaxError as exc:
        raise RuntimeError(f"Unable to parse source while locating {marker}: {exc}") from exc
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == marker:
            return int(node.lineno)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_runtime_layer(layer: str, source_path: Path, specs: list[tuple[str, str | int, str | None]], manifest: list[dict[str, object]]) -> list[str]:
    lines = read_lines(source_path)
    rel_paths: list[str] = []
    for rel, start_marker, end_marker in specs:
        start = marker_to_start(lines, start_marker)
        end = marker_to_start(lines, end_marker) - 1 if end_marker is not None else len(lines)
        if start > end:
            raise RuntimeError(f"Invalid segment for {source_path}: {rel} start {start} end {end}")
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
        proposed_end = node_end
        if end and proposed_end - start + 1 > max_lines:
            chunks.append((start, end))
            start = node_start
        end = proposed_end
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
        for path in paths:
            lines.append(f"        {path!r},")
        lines.append("    ),")
    lines.append("}")
    return "\n".join(lines)


def write_wrappers(layer_paths: dict[str, list[str]]) -> None:
    loader = f'''from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import MutableMapping, Any\n\n{layer_mapping_literal(layer_paths)}\n\n\n@dataclass(frozen=True)\nclass RuntimeSegmentLoader:\n    layer: str\n    root: Path = Path(__file__).resolve().parent\n\n    def segment_paths(self) -> tuple[Path, ...]:\n        try:\n            relatives = LAYER_SEGMENTS[self.layer]\n        except KeyError as exc:\n            raise KeyError(f"unknown DCOIR Review runtime layer: {{self.layer}}") from exc\n        return tuple(self.root / relative for relative in relatives)\n\n    def load_into(self, namespace: MutableMapping[str, Any]) -> None:\n        for path in self.segment_paths():\n            source = path.read_text(encoding="utf-8")\n            exec(compile(source, str(path), "exec"), namespace)\n\n\ndef load_segments_into(namespace: MutableMapping[str, Any], layer: str) -> None:\n    RuntimeSegmentLoader(layer).load_into(namespace)\n'''
    write_text(PKG / "module_loader.py", loader)
    write_text(PKG / "__init__.py", '"""Connector-safe DCOIR Review runtime package."""\n')
    for directory in {Path(path).parent for paths in layer_paths.values() for path in paths}:
        if directory != Path('.'):
            write_text(PKG / directory / "__init__.py", '"""Generated DCOIR Review runtime segment package."""\n')

    for layer, target in WRAPPER_TARGETS.items():
        text = f'''#!/usr/bin/env python3\n"""Compatibility wrapper for the connector-safe DCOIR Review {layer} runtime layer."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport sys\n\n_SCRIPT_DIR = Path(__file__).resolve().parent\nif str(_SCRIPT_DIR) not in sys.path:\n    sys.path.insert(0, str(_SCRIPT_DIR))\n\nfrom dcoir_review.module_loader import load_segments_into\n\nload_segments_into(globals(), {layer!r})\n'''
        write_text(ROOT / target, text)

    for layer, target in SELFTEST_TARGETS.items():
        text = f'''#!/usr/bin/env python3\n"""Compatibility wrapper for the connector-safe DCOIR Review {layer} layer."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport sys\n\n_SCRIPT_DIR = Path(__file__).resolve().parent\nif str(_SCRIPT_DIR) not in sys.path:\n    sys.path.insert(0, str(_SCRIPT_DIR))\n\nfrom dcoir_review.module_loader import load_segments_into\n\nload_segments_into(globals(), {layer!r})\n'''
        write_text(ROOT / target, text)

    patch_items = "\n".join(f"        {name!r}," for name in PATCH_APPLY_ORDER)
    entrypoint = f'''from __future__ import annotations\n\nimport importlib\nfrom dataclasses import dataclass\nfrom types import ModuleType\nfrom typing import Iterable\n\n\n@dataclass(frozen=True)\nclass DcoirReviewEntrypoint:\n    review_module_name: str = "openrouter_pr_review_pareto_context"\n    patch_module_names: tuple[str, ...] = (\n{patch_items}\n    )\n\n    def import_module(self, module_name: str) -> ModuleType:\n        return importlib.import_module(module_name)\n\n    def apply_runtime_patches(self, review_module: ModuleType, patch_module_names: Iterable[str] | None = None) -> None:\n        for module_name in tuple(patch_module_names or self.patch_module_names):\n            patch_module = self.import_module(module_name)\n            apply_patch = getattr(patch_module, "apply_pareto_context_module", None)\n            if apply_patch is None:\n                raise RuntimeError(f"Runtime patch module {{module_name}} does not expose apply_pareto_context_module")\n            apply_patch(review_module)\n\n    def run(self) -> None:\n        review_module = self.import_module(self.review_module_name)\n        self.apply_runtime_patches(review_module)\n        review_module.main()\n\n\ndef main() -> None:\n    DcoirReviewEntrypoint().run()\n'''
    write_text(PKG / "entrypoint.py", entrypoint)
    write_text(ROOT / "scripts" / "openrouter_pr_review_entrypoint.py", '''#!/usr/bin/env python3\n"""Compatibility wrapper for the connector-safe DCOIR Review entrypoint."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport sys\n\n_SCRIPT_DIR = Path(__file__).resolve().parent\nif str(_SCRIPT_DIR) not in sys.path:\n    sys.path.insert(0, str(_SCRIPT_DIR))\n\nfrom dcoir_review.entrypoint import main\n\n\nif __name__ == "__main__":\n    main()\n''')


def split_workflow(manifest: list[dict[str, object]]) -> None:
    workflow = ROOT / ".github" / "workflows" / "openrouter-pr-review.yml"
    original = workflow.read_text(encoding="utf-8")
    marker = "\njobs:\n"
    if marker not in original:
        raise RuntimeError("openrouter-pr-review.yml does not contain a top-level jobs block")
    header, jobs_suffix = original.split(marker, 1)
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
    reusable_jobs = "\n".join(cleaned) + "\n"
    caller = header.rstrip() + "\n\njobs:\n  review:\n    name: DCOIR review\n    if: >-\n      ${{\n        github.event.issue.pull_request &&\n        github.event.comment.user.type != 'Bot' &&\n        github.event.comment.user.login == 'malwaredevil'\n      }}\n    uses: ./.github/workflows/reusable-openrouter-pr-review.yml\n    permissions:\n      actions: read\n      contents: read\n      issues: write\n      pull-requests: write\n    secrets:\n      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}\n"
    reusable = """# DCOIR REUSABLE WORKFLOW CONTRACT\n# Source entry workflow: openrouter-pr-review.yml\n# Purpose: reusable implementation module for operator-triggered DCOIR Review; entry workflow retains triggers, permissions, concurrency, and operator-visible contract notes.\nname: 99 Module - DCOIR Review\nrun-name: Module DCOIR Review | ${{ github.workflow }} | #${{ github.run_number }}\n\non:\n  workflow_call:\n    secrets:\n      OPENROUTER_API_KEY:\n        description: Explicit forwarded OpenRouter API key from the entry workflow.\n        required: true\n\npermissions:\n  actions: read\n  contents: read\n  issues: write\n  pull-requests: write\n\n""" + reusable_jobs
    write_text(workflow, caller)
    write_text(ROOT / ".github" / "workflows" / "reusable-openrouter-pr-review.yml", reusable)
    for path in (workflow, ROOT / ".github" / "workflows" / "reusable-openrouter-pr-review.yml"):
        manifest.append({"path": path.relative_to(ROOT).as_posix(), "line_count": len(path.read_text(encoding="utf-8").splitlines()), "layer": "workflow"})


def verify_connector_safe(manifest: list[dict[str, object]]) -> None:
    too_large = [item for item in manifest if int(item.get("line_count", 0)) > MAX_CONNECTOR_SAFE_LINES]
    if too_large:
        details = "; ".join(f"{item['path']}={item['line_count']}" for item in too_large)
        raise RuntimeError(f"Generated connector-safe file limit exceeded: {details}")


def main() -> None:
    if PKG.exists():
        shutil.rmtree(PKG)
    manifest: list[dict[str, object]] = []
    layer_paths: dict[str, list[str]] = {}
    for layer, target in WRAPPER_TARGETS.items():
        layer_paths[layer] = write_runtime_layer(layer, ROOT / target, RUNTIME_LAYERS[layer], manifest)
    for layer, target in SELFTEST_TARGETS.items():
        out_dir = Path("selftests") / layer
        layer_paths[layer] = split_top_level_source(layer, ROOT / target, out_dir, manifest)
    write_wrappers(layer_paths)
    split_workflow(manifest)
    wrapper_paths = list(WRAPPER_TARGETS.values()) + list(SELFTEST_TARGETS.values()) + ["scripts/openrouter_pr_review_entrypoint.py"]
    for rel in wrapper_paths:
        path = ROOT / rel
        manifest.append({"path": rel, "line_count": len(path.read_text(encoding="utf-8").splitlines()), "layer": "wrapper"})
    write_text(PKG / "modularization_manifest.json", json.dumps({"schema": "dcoir.review.modularization_manifest.v1", "max_connector_safe_lines": MAX_CONNECTOR_SAFE_LINES, "files": manifest}, indent=2) + "\n")
    manifest.append({"path": "scripts/dcoir_review/modularization_manifest.json", "line_count": len((PKG / "modularization_manifest.json").read_text(encoding="utf-8").splitlines()), "layer": "manifest"})
    verify_connector_safe(manifest)
    print(json.dumps({"max_connector_safe_lines": MAX_CONNECTOR_SAFE_LINES, "file_count": len(manifest), "max_lines": max(int(item.get("line_count", 0)) for item in manifest)}, indent=2))


if __name__ == "__main__":
    main()
'@

$GeneratorPath = Join-Path $TempRoot 'modularize_dcoir_review.py'
$Generator | Out-File -FilePath $GeneratorPath -Encoding utf8 -NoNewline
python $GeneratorPath
if ($LASTEXITCODE -ne 0) { throw "modularization generator failed with exit code $LASTEXITCODE" }

Add-SummaryLine ''
Add-SummaryLine '## Validation commands'
Invoke-CommandChecked 'python -m py_compile scripts/openrouter_pr_review.py scripts/openrouter_pr_review_hardened.py scripts/openrouter_pr_review_pareto_context.py scripts/openrouter_pr_review_entrypoint.py scripts/dcoir_review/module_loader.py scripts/dcoir_review/entrypoint.py'
Invoke-CommandChecked 'python -m py_compile scripts/dcoir_review/base/*.py scripts/dcoir_review/hardened/*.py scripts/dcoir_review/pareto_context/*.py scripts/dcoir_review/selftests/base_selftest/*.py scripts/dcoir_review/selftests/hardened_selftest/*.py scripts/dcoir_review/selftests/pareto_context_selftest/*.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_selftest.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_codex_regression_selftest.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_hardened_selftest.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_quality_recovery_selftest.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_pareto_context_regression_selftest.py'
Invoke-CommandChecked 'python scripts/openrouter_pr_review_pareto_context_selftest.py'

$Manifest = Get-Content -LiteralPath 'scripts/dcoir_review/modularization_manifest.json' -Raw | ConvertFrom-Json
$MaxLines = ($Manifest.files | Measure-Object -Property line_count -Maximum).Maximum
$FileCount = ($Manifest.files | Measure-Object).Count
Add-SummaryLine ''
Add-SummaryLine '## Modularization summary'
Add-SummaryLine "- generated_files_tracked_in_manifest: $FileCount"
Add-SummaryLine "- maximum_generated_file_lines: $MaxLines"
Add-SummaryLine "- connector_safe_limit: $($Manifest.max_connector_safe_lines)"
Add-SummaryLine '- compatibility wrappers preserved: openrouter_pr_review.py, openrouter_pr_review_hardened.py, openrouter_pr_review_pareto_context.py, openrouter_pr_review_entrypoint.py, and the three large selftest entrypoints.'
Add-SummaryLine '- workflow split: openrouter-pr-review.yml caller plus reusable-openrouter-pr-review.yml implementation module.'

$Tracked = @(
  '.github/workflows/openrouter-pr-review.yml',
  '.github/workflows/reusable-openrouter-pr-review.yml',
  'scripts/openrouter_pr_review.py',
  'scripts/openrouter_pr_review_hardened.py',
  'scripts/openrouter_pr_review_pareto_context.py',
  'scripts/openrouter_pr_review_entrypoint.py',
  'scripts/openrouter_pr_review_selftest.py',
  'scripts/openrouter_pr_review_hardened_selftest.py',
  'scripts/openrouter_pr_review_pareto_context_selftest.py',
  'scripts/dcoir_review'
)
Invoke-GitChecked @('add', '--')
foreach ($PathItem in $Tracked) { Invoke-GitChecked @('add', '--', $PathItem) }
$DiffStat = (& git diff --cached --stat) -join "`n"
Add-SummaryLine ''
Add-SummaryLine '## Git diff stat'
Add-SummaryLine '```text'
Add-SummaryLine $DiffStat
Add-SummaryLine '```'

Invoke-GitChecked @('commit', '-m', 'Refactor DCOIR Review runtime into connector-safe modules')
$HeadSha = (& git rev-parse 'HEAD').Trim()
Invoke-GitChecked @('push', '--force-with-lease', 'origin', "HEAD:refs/heads/$BranchName")
Add-SummaryLine "- head_sha: $HeadSha"

$Token = if (-not [string]::IsNullOrWhiteSpace($env:DCOIR_GITHUB_FG_TOKEN)) { $env:DCOIR_GITHUB_FG_TOKEN } elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) { $env:GITHUB_TOKEN } else { '' }
if ([string]::IsNullOrWhiteSpace($Token)) { throw 'No GitHub token available to create the draft PR.' }
$Headers = @{
  Authorization = "Bearer $Token"
  Accept = 'application/vnd.github+json'
  'X-GitHub-Api-Version' = '2022-11-28'
  'User-Agent' = 'dcoir-chatgpt-exec'
}
$PrBody = @"
Behavior-preserving connector-safe modularization of the DCOIR Review workflow/runtime.

What changed:
- Keeps the public script names as compatibility wrappers.
- Moves active DCOIR Review runtime layers into scripts/dcoir_review/ connector-safe package segments.
- Converts the patch-chain entrypoint into an object-oriented DcoirReviewEntrypoint class.
- Splits the operator-triggered workflow into a thin caller and reusable workflow module.
- Splits the largest selftest entrypoints into connector-safe package segments while preserving the old selftest command names.

Validation run by chatgpt-exec:
- py_compile for wrappers and generated package segments.
- openrouter_pr_review_selftest.py.
- openrouter_pr_review_codex_regression_selftest.py.
- openrouter_pr_review_hardened_selftest.py.
- openrouter_pr_review_quality_recovery_selftest.py.
- openrouter_pr_review_pareto_context_regression_selftest.py.
- openrouter_pr_review_pareto_context_selftest.py.

This PR is intentionally draft until the DCOIR Review test round and readback are graded.
"@
$Payload = @{
  title = '[refactor] Modularize DCOIR Review runtime'
  head = $BranchName
  base = 'main'
  body = $PrBody
  draft = $true
} | ConvertTo-Json -Depth 5
try {
  $Pr = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$Repo/pulls" -Headers $Headers -ContentType 'application/json' -Body $Payload
} catch {
  $Existing = Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$Repo/pulls?head=DCOIR-Collector:$BranchName&state=open" -Headers $Headers
  if ($Existing.Count -lt 1) { throw }
  $Pr = $Existing[0]
}
Add-SummaryLine ''
Add-SummaryLine '## Draft PR'
Add-SummaryLine "- pr_number: $($Pr.number)"
Add-SummaryLine "- pr_url: $($Pr.html_url)"
Add-SummaryLine "- pr_head_sha: $HeadSha"

[ordered]@{
  schema = 'dcoir.review.modular_refactor_readback.v1'
  request_id = $RequestId
  branch = $BranchName
  clean_base = $CleanBase
  head_sha = $HeadSha
  pr_number = $Pr.number
  pr_url = $Pr.html_url
  generated_file_count = $FileCount
  maximum_generated_file_lines = $MaxLines
  connector_safe_limit = $Manifest.max_connector_safe_lines
  validation = 'pass'
} | ConvertTo-Json -Depth 6 | Out-File -FilePath $TempJson -Encoding utf8

# Remove transient staging request/script from main before the workflow final report commit.
Invoke-GitChecked @('checkout', '-B', 'main', $env:GITHUB_SHA)
Remove-Item -LiteralPath "chatgpt_staging/exec_requests/$RequestId.json" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "chatgpt_staging/exec_scripts/$RequestId.ps1" -Force -ErrorAction SilentlyContinue
Invoke-GitChecked @('add', '-A', '--', "chatgpt_staging/exec_requests/$RequestId.json", "chatgpt_staging/exec_scripts/$RequestId.ps1")
$CleanupStatus = (& git status --short -- "chatgpt_staging/exec_requests/$RequestId.json" "chatgpt_staging/exec_scripts/$RequestId.ps1") -join "`n"
if (-not [string]::IsNullOrWhiteSpace($CleanupStatus)) {
  Invoke-GitChecked @('commit', '-m', "Clean up transient ChatGPT exec modular refactor request [skip ci]")
  Invoke-GitChecked @('push', 'origin', 'HEAD:main')
}

$ReportDir = Join-Path $RepoRoot "chatgpt_staging/status_reports/chatgpt-exec/$RequestId"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Copy-Item -LiteralPath $TempSummary -Destination (Join-Path $ReportDir 'modular_refactor_summary.md') -Force
Copy-Item -LiteralPath $TempJson -Destination (Join-Path $ReportDir 'modular_refactor_summary.json') -Force
