#!/usr/bin/env python3
"""Build a report-only collector PowerShell function reachability report.

This #306 report is intentionally conservative. It checks only the
manifest-declared collector runtime source, records literal function references,
and reports dynamic invocation uncertainty without making deletion-readiness
claims. When PowerShell is available, it uses the PowerShell parser AST for
function and command discovery. Otherwise it falls back to a deterministic
Python lexical pass that masks comments, strings, and here-strings before
looking for definitions and literal references.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from powershell_analyzer_contract import AnalyzerContractError, repo_relative_input_path, sha256_file

SCHEMA_VERSION = "dcoir_powershell_function_reachability_report_v1"
ISSUE_NUMBER = 306
PARENT_ISSUE_NUMBER = 260
DEFAULT_MANIFEST = Path("project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_function_reachability_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_function_reachability_report.md")

CLASSIFICATIONS = (
    "entrypoint",
    "literal_referenced",
    "dynamic_invocation_uncertain",
    "static_unreferenced",
)

NON_CLAIMS = [
    "This report is not whole-program dead-code proof.",
    "This report does not claim any function is safe to delete.",
    "This report only covers manifest-declared collector runtime source.",
    "Runtime-lane coverage is not collected unless explicit suite evidence is supplied by a later lane.",
    "Static absence is reported as bounded evidence, not as proof of operator or dynamic invocation absence.",
]

POWERSHELL_AST_SCRIPT = r"""
param(
  [Parameter(Mandatory = $true)][string]$InputJson,
  [Parameter(Mandatory = $true)][string]$OutputJson
)

$ErrorActionPreference = 'Stop'
$payload = Get-Content -LiteralPath $InputJson -Raw -Encoding UTF8 | ConvertFrom-Json
$items = New-Object System.Collections.Generic.List[object]

foreach ($source in $payload.sources) {
  $path = [string]$source.path
  $repo_path = [string]$source.repo_path
  $load_order = [int]$source.load_order
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  $tokens = $null
  $parseErrors = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$tokens, [ref]$parseErrors)
  $errors = @()
  if ($parseErrors) {
    foreach ($err in $parseErrors) {
      $errors += [ordered]@{
        line = $err.Extent.StartLineNumber
        column = $err.Extent.StartColumnNumber
        message = $err.Message
      }
    }
  }

  $defs = @()
  foreach ($fn in $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    $parent = $fn.Parent
    $nested = $false
    while ($null -ne $parent) {
      if ($parent -is [System.Management.Automation.Language.FunctionDefinitionAst]) {
        $nested = $true
        break
      }
      $parent = $parent.Parent
    }
    $defs += [ordered]@{
      name = $fn.Name
      source_path = $repo_path
      line = $fn.Extent.StartLineNumber
      column = $fn.Extent.StartColumnNumber
      end_line = $fn.Extent.EndLineNumber
      definition_kind = $(if ($nested) { 'nested' } else { 'top_level' })
      load_order = $load_order
    }
  }

  $commands = @()
  foreach ($cmd in $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true)) {
    $name = $cmd.GetCommandName()
    $commands += [ordered]@{
      name = $name
      source_path = $repo_path
      line = $cmd.Extent.StartLineNumber
      column = $cmd.Extent.StartColumnNumber
      invocation_operator = [string]$cmd.InvocationOperator
      text = $cmd.Extent.Text
    }
  }

  $items.Add([ordered]@{
    repo_path = $repo_path
    load_order = $load_order
    parse_errors = $errors
    definitions = $defs
    commands = $commands
  })
}

$items | ConvertTo-Json -Depth 10 | Out-File -LiteralPath $OutputJson -Encoding UTF8
"""


class ReachabilityError(RuntimeError):
    """Raised for fail-closed reachability report errors."""


@dataclass(frozen=True)
class SourceFile:
    repo_path: str
    path: Path
    load_order: int


@dataclass(frozen=True)
class Definition:
    name: str
    source_path: str
    line: int
    column: int | None
    end_line: int | None
    definition_kind: str
    load_order: int

    @property
    def key(self) -> str:
        return self.name.casefold()


@dataclass(frozen=True)
class Reference:
    name: str
    source_path: str
    line: int
    column: int | None
    invocation_kind: str
    parser: str

    @property
    def key(self) -> str:
        return self.name.casefold()


def scalar(value: Any) -> str:
    return "" if value is None else str(value)


def ast_definition_kind(value: Any) -> str:
    definition_kind = scalar(value).strip()
    if not definition_kind:
        return "top_level"
    return definition_kind


def ast_invocation_kind(value: Any) -> str:
    invocation_kind = scalar(value).strip()
    if not invocation_kind:
        return "not_extracted"
    return invocation_kind


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReachabilityError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReachabilityError(f"{label} is invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ReachabilityError(f"{label} could not be read: {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def line_column(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    line_start = text.rfind("\n", 0, index)
    return line, index + 1 if line_start < 0 else index - line_start


def context_line(text: str, line: int) -> str:
    lines = normalize_newlines(text).splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def safe_output_path(repo_root: Path, value: str | Path, label: str, suffix: str) -> tuple[Path, str]:
    try:
        path = repo_relative_input_path(repo_root, value, label)
    except AnalyzerContractError as exc:
        raise ReachabilityError(str(exc)) from exc
    try:
        repo_path = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ReachabilityError(f"{label} must resolve inside the repository root") from exc
    if not repo_path.startswith("project_sources/collector/"):
        raise ReachabilityError(f"{label} must stay under project_sources/collector/: {repo_path}")
    if path.suffix != suffix:
        raise ReachabilityError(f"{label} must use {suffix} suffix: {repo_path}")
    return path, repo_path


def resolve_sources(repo_root: Path, manifest_path: Path) -> tuple[dict[str, Any], list[SourceFile], list[str]]:
    manifest = read_json(manifest_path, "collector runtime manifest")
    if not isinstance(manifest, dict):
        raise ReachabilityError("collector runtime manifest must be a JSON object")
    errors: list[str] = []
    source_values: list[str] = []
    wrapper = manifest.get("collector_wrapper_source")
    if not isinstance(wrapper, str) or not wrapper.strip():
        errors.append("collector manifest: collector_wrapper_source must be a non-empty string")
    else:
        source_values.append(wrapper)
    part_files = manifest.get("collector_part_files")
    if not isinstance(part_files, list) or not part_files:
        errors.append("collector manifest: collector_part_files must be a non-empty list")
    else:
        for index, item in enumerate(part_files, start=1):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"collector manifest: collector_part_files[{index}] must be a non-empty string")
            else:
                source_values.append(item)
    sources: list[SourceFile] = []
    for load_order, raw in enumerate(source_values):
        try:
            path = repo_relative_input_path(repo_root, raw, "collector runtime source")
        except AnalyzerContractError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"collector runtime source is missing: {raw}")
            continue
        sources.append(SourceFile(repo_path=path.resolve().relative_to(repo_root.resolve()).as_posix(), path=path, load_order=load_order))
    return manifest, sources, errors


def mask_powershell_non_code(text: str) -> str:
    """Mask comments and string bodies while preserving line/column layout."""
    chars = list(normalize_newlines(text))
    i = 0
    state = "code"
    quote = ""
    here_end = ""
    while i < len(chars):
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if state == "code":
            if ch == "<" and nxt == "#":
                chars[i] = chars[i + 1] = " "
                i += 2
                state = "block_comment"
                continue
            if ch == "#":
                while i < len(chars) and chars[i] != "\n":
                    chars[i] = " "
                    i += 1
                continue
            if ch == "@" and nxt in {"'", '"'}:
                quote = nxt
                here_end = nxt + "@"
                chars[i] = chars[i + 1] = " "
                i += 2
                state = "here_string"
                continue
            if ch in {"'", '"'}:
                quote = ch
                chars[i] = " "
                i += 1
                state = "string"
                continue
            i += 1
            continue
        if state == "block_comment":
            if ch == "#" and nxt == ">":
                chars[i] = chars[i + 1] = " "
                i += 2
                state = "code"
                continue
            if ch != "\n":
                chars[i] = " "
            i += 1
            continue
        if state == "string":
            if ch == "`":
                chars[i] = " "
                if i + 1 < len(chars) and chars[i + 1] != "\n":
                    chars[i + 1] = " "
                    i += 2
                else:
                    i += 1
                continue
            if ch == quote:
                if quote == "'" and nxt == "'":
                    chars[i] = chars[i + 1] = " "
                    i += 2
                    continue
                chars[i] = " "
                i += 1
                state = "code"
                continue
            if ch != "\n":
                chars[i] = " "
            i += 1
            continue
        if state == "here_string":
            at_line_start = i == 0 or chars[i - 1] == "\n"
            if at_line_start:
                probe_end = i + len(here_end)
                if "".join(chars[i:probe_end]) == here_end:
                    for j in range(i, probe_end):
                        chars[j] = " "
                    i = probe_end
                    state = "code"
                    continue
            if ch != "\n":
                chars[i] = " "
            i += 1
            continue
    return "".join(chars)


def brace_depths(masked: str) -> list[int]:
    depths: list[int] = [0] * (len(masked) + 1)
    depth = 0
    for i, ch in enumerate(masked):
        depths[i] = depth
        if ch == "{":
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
    depths[len(masked)] = depth
    return depths


def powershell_backtick_tolerant_literal(value: str) -> str:
    return "".join(r"`?" + re.escape(character) for character in value)


FUNCTION_RE = re.compile(r"(?i)(?<![-\w])function\s+([A-Za-z_][A-Za-z0-9_-]*)")
TOKEN_RE = re.compile(r"(?<![-\w])([A-Za-z_][A-Za-z0-9_-]*)(?![-\w])")
INVOKE_EXPRESSION_RE = re.compile(
    rf"(?i)(?<![-\w]){powershell_backtick_tolerant_literal('Invoke-Expression')}(?!`?[-\w])"
)
AST_DYNAMIC_TEXT_RE = re.compile(r"(?i)(^|\s)(&\s*\$|\.\s*\$|\[ScriptBlock\]::Create)")
DYNAMIC_PATTERNS = (
    ("call_operator_variable", re.compile(r"&[ \t]*\$[A-Za-z_][A-Za-z0-9_]*", re.IGNORECASE)),
    ("dot_source_variable", re.compile(r"\.[ \t]*\$[A-Za-z_][A-Za-z0-9_]*", re.IGNORECASE)),
    ("invoke_expression", INVOKE_EXPRESSION_RE),
    ("scriptblock_create", re.compile(r"\[ScriptBlock\]::Create", re.IGNORECASE)),
)


def has_dynamic_command_text(text: str) -> bool:
    return bool(INVOKE_EXPRESSION_RE.search(text) or AST_DYNAMIC_TEXT_RE.search(text))


def fallback_function_keys(sources: list[SourceFile]) -> set[str]:
    keys: set[str] = set()
    for source in sources:
        text = normalize_newlines(source.path.read_text(encoding="utf-8", errors="ignore"))
        masked = mask_powershell_non_code(text)
        keys.update(match.group(1).casefold() for match in FUNCTION_RE.finditer(masked))
    return keys


def fallback_parse_source(
    source: SourceFile,
    all_function_keys: set[str] | None = None,
) -> tuple[list[Definition], list[Reference], list[dict[str, Any]], list[dict[str, Any]]]:
    text = normalize_newlines(source.path.read_text(encoding="utf-8", errors="ignore"))
    masked = mask_powershell_non_code(text)
    depths = brace_depths(masked)
    definitions: list[Definition] = []
    definition_spans: list[tuple[int, int]] = []
    for match in FUNCTION_RE.finditer(masked):
        name = match.group(1)
        name_start, name_end = match.span(1)
        line, column = line_column(masked, name_start)
        definition_spans.append((name_start, name_end))
        definitions.append(
            Definition(
                name=name,
                source_path=source.repo_path,
                line=line,
                column=column,
                end_line=None,
                definition_kind="nested" if depths[match.start()] > 0 else "top_level",
                load_order=source.load_order,
            )
        )
    definition_name_spans = set(definition_spans)
    function_keys = all_function_keys if all_function_keys is not None else {definition.name.casefold() for definition in definitions}
    references: list[Reference] = []
    for match in TOKEN_RE.finditer(masked):
        name = match.group(1)
        if name.casefold() not in function_keys:
            continue
        if match.span(1) in definition_name_spans:
            continue
        prefix = masked[max(0, match.start() - 10) : match.start()]
        if re.search(r"(?i)\bfunction\s+$", prefix):
            continue
        previous = masked[match.start() - 1] if match.start() > 0 else ""
        if previous in {"$", "-", "."}:
            continue
        line, column = line_column(masked, match.start(1))
        references.append(
            Reference(
                name=name,
                source_path=source.repo_path,
                line=line,
                column=column,
                invocation_kind="literal_token",
                parser="python_lexical_fallback",
            )
        )
    dynamic_sites: list[dict[str, Any]] = []
    for kind, pattern in DYNAMIC_PATTERNS:
        for match in pattern.finditer(masked):
            line, column = line_column(masked, match.start())
            dynamic_sites.append(
                {
                    "kind": kind,
                    "source_path": source.repo_path,
                    "line": line,
                    "column": column,
                    "context": context_line(text, line),
                    "claim": "dynamic invocation site creates bounded static-analysis uncertainty",
                }
            )
    return definitions, references, dynamic_sites, []


def powershell_executable() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def parse_with_powershell_ast(sources: list[SourceFile]) -> tuple[list[Definition], list[Reference], list[dict[str, Any]], list[dict[str, Any]], str]:
    exe = powershell_executable()
    if not exe:
        return [], [], [], [{"message": "PowerShell parser executable not found; used Python lexical fallback."}], "python_lexical_fallback"
    payload = {
        "sources": [
            {
                "path": source.path.as_posix(),
                "repo_path": source.repo_path,
                "load_order": source.load_order,
            }
            for source in sources
        ]
    }
    with tempfile.TemporaryDirectory(prefix="dcoir-reachability-") as temp:
        temp_dir = Path(temp)
        input_json = temp_dir / "input.json"
        output_json = temp_dir / "output.json"
        script_path = temp_dir / "parse.ps1"
        input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        script_path.write_text(POWERSHELL_AST_SCRIPT, encoding="utf-8")
        proc = subprocess.run(
            [exe, "-NoProfile", "-File", str(script_path), str(input_json), str(output_json)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0 or not output_json.exists():
            warning = {
                "message": "PowerShell AST parse failed; used Python lexical fallback.",
                "stdout": proc.stdout[-1000:],
                "stderr": proc.stderr[-1000:],
            }
            return [], [], [], [warning], "python_lexical_fallback"
        raw = json.loads(output_json.read_text(encoding="utf-8-sig"))
    if isinstance(raw, dict):
        raw_items = [raw]
    else:
        raw_items = raw if isinstance(raw, list) else []
    definitions: list[Definition] = []
    references: list[Reference] = []
    dynamic_sites: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    function_names: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        for error in item.get("parse_errors", []):
            if isinstance(error, dict):
                parse_errors.append({"source_path": item.get("repo_path"), **error})
        for raw_def in item.get("definitions", []):
            if not isinstance(raw_def, dict):
                continue
            name = scalar(raw_def.get("name")).strip()
            if not name:
                continue
            function_names.add(name.casefold())
            definitions.append(
                Definition(
                    name=name,
                    source_path=scalar(raw_def.get("source_path")).strip(),
                    line=int(raw_def.get("line") or 0),
                    column=int(raw_def.get("column") or 0) or None,
                    end_line=int(raw_def.get("end_line") or 0) or None,
                    definition_kind=ast_definition_kind(raw_def.get("definition_kind")),
                    load_order=int(raw_def.get("load_order") or 0),
                )
            )
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        for raw_cmd in item.get("commands", []):
            if not isinstance(raw_cmd, dict):
                continue
            name = scalar(raw_cmd.get("name")).strip()
            text = scalar(raw_cmd.get("text")).strip()
            source_path = scalar(raw_cmd.get("source_path")).strip()
            line = int(raw_cmd.get("line") or 0)
            column = int(raw_cmd.get("column") or 0) or None
            invocation = ast_invocation_kind(raw_cmd.get("invocation_operator"))
            if name and name.casefold() in function_names:
                references.append(
                    Reference(
                        name=name,
                        source_path=source_path,
                        line=line,
                        column=column,
                        invocation_kind=invocation,
                        parser="powershell_ast",
                    )
                )
            if not name or has_dynamic_command_text(text):
                dynamic_sites.append(
                    {
                        "kind": "ast_dynamic_or_expression_command",
                        "source_path": source_path,
                        "line": line,
                        "column": column,
                        "context": text[:240],
                        "claim": "PowerShell AST could not resolve this command to a literal local function name.",
                    }
                )
    return definitions, references, dynamic_sites, parse_errors, "powershell_ast"


def parse_sources(sources: list[SourceFile], parser_mode: str) -> tuple[list[Definition], list[Reference], list[dict[str, Any]], list[dict[str, Any]], str]:
    if parser_mode in {"auto", "powershell_ast"}:
        definitions, references, dynamic_sites, warnings, mode = parse_with_powershell_ast(sources)
        if mode == "powershell_ast" or parser_mode == "powershell_ast":
            return definitions, references, dynamic_sites, warnings, mode
    definitions: list[Definition] = []
    references: list[Reference] = []
    dynamic_sites: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    all_function_keys = fallback_function_keys(sources)
    for source in sources:
        defs, refs, dynamic, parse_warnings = fallback_parse_source(source, all_function_keys)
        definitions.extend(defs)
        references.extend(refs)
        dynamic_sites.extend(dynamic)
        warnings.extend(parse_warnings)
    return definitions, references, dynamic_sites, warnings, "python_lexical_fallback"


def reference_entry(reference: Reference) -> dict[str, Any]:
    return {
        "source_path": reference.source_path,
        "line": reference.line,
        "column": reference.column,
        "invocation_kind": reference.invocation_kind,
        "parser": reference.parser,
    }


def classify_functions(
    definitions: list[Definition],
    references: list[Reference],
    dynamic_sites: list[dict[str, Any]],
    entrypoints: set[str],
) -> list[dict[str, Any]]:
    refs_by_key: dict[str, list[Reference]] = defaultdict(list)
    for ref in references:
        refs_by_key[ref.key].append(ref)
    has_dynamic_uncertainty = bool(dynamic_sites)
    records: list[dict[str, Any]] = []
    for definition in sorted(definitions, key=lambda item: (item.load_order, item.line, item.name.casefold())):
        refs = refs_by_key.get(definition.key, [])
        if definition.key in entrypoints:
            classification = "entrypoint"
        elif refs:
            classification = "literal_referenced"
        elif has_dynamic_uncertainty:
            classification = "dynamic_invocation_uncertain"
        else:
            classification = "static_unreferenced"
        records.append(
            {
                "name": definition.name,
                "normalized_name": definition.key,
                "classification": classification,
                "source_path": definition.source_path,
                "line": definition.line,
                "column": definition.column,
                "end_line": definition.end_line,
                "definition_kind": definition.definition_kind,
                "static_reference_status": "literal_reference_found" if refs else "no_literal_reference_found",
                "dynamic_uncertainty_status": "dynamic_invocation_sites_present" if has_dynamic_uncertainty else "no_dynamic_invocation_sites_detected",
                "reference_count": len(refs),
                "references": [reference_entry(ref) for ref in refs[:20]],
                "truncated_reference_count": max(0, len(refs) - 20),
                "coverage_status": "not_observed_in_suite",
                "coverage_lanes": [],
                "claim": "classification is report-only and not deletion proof",
            }
        )
    return records


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# PowerShell Function Reachability Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: #{report['issue']}",
        f"- Parent issue: #{report['parent_issue']}",
        f"- Parser mode: `{summary['parser_mode']}`",
        f"- Validation: `{'pass' if report['validation']['success'] else 'fail'}`",
        f"- Functions: `{summary['function_count']}`",
        "",
        "## Classification Summary",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]
    for classification in CLASSIFICATIONS:
        lines.append(f"| `{classification}` | {summary['classification_counts'].get(classification, 0)} |")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            f"- Manifest: `{report['analysis_scope']['manifest_path']}`",
            "- Runtime-lane coverage: `not_collected`",
            "- Covered source files:",
        ]
    )
    lines.extend(f"  - `{item['path']}`" for item in report["analysis_scope"]["source_files"])
    lines.extend(["", "## Potential Follow-Up Functions", "", "| Function | Classification | Source | Line | References |", "| --- | --- | --- | ---: | ---: |"])
    for item in report["functions"]:
        if item["classification"] in {"static_unreferenced", "dynamic_invocation_uncertain", "entrypoint"}:
            lines.append(
                f"| `{item['name']}` | `{item['classification']}` | `{item['source_path']}` | {item['line']} | {item['reference_count']} |"
            )
    if not any(item["classification"] in {"static_unreferenced", "dynamic_invocation_uncertain", "entrypoint"} for item in report["functions"]):
        lines.append("| none | `none` | none |  |  |")
    lines.extend(["", "## Dynamic Invocation Sites", "", "| Kind | Source | Line | Context |", "| --- | --- | ---: | --- |"])
    for site in report["dynamic_invocation_sites"][:50]:
        context = scalar(site.get("context")).replace("|", "\\|")
        lines.append(f"| `{site.get('kind')}` | `{site.get('source_path')}` | {site.get('line')} | `{context}` |")
    if not report["dynamic_invocation_sites"]:
        lines.append("| none | none |  | none detected |")
    lines.extend(["", "## Non-Claims", ""])
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    if report["validation"]["errors"]:
        lines.extend(["", "## Validation Errors", ""])
        lines.extend(f"- {error}" for error in report["validation"]["errors"])
    if report["validation"]["warnings"]:
        lines.extend(["", "## Validation Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["validation"]["warnings"])
    return "\n".join(lines) + "\n"


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    functions = report.get("functions")
    if not isinstance(functions, list) or not functions:
        errors.append("report must contain at least one function record")
        return errors
    classifications = Counter(scalar(item.get("classification")) for item in functions if isinstance(item, dict))
    for classification in classifications:
        if classification not in CLASSIFICATIONS:
            errors.append(f"unknown function classification: {classification}")
    if sum(classifications.values()) != report["summary"].get("function_count"):
        errors.append("classification counts do not sum to function_count")
    markdown = render_markdown(report)
    for fragment in (
        "This report does not claim any function is safe to delete.",
        "Runtime-lane coverage: `not_collected`",
        "Classification Summary",
    ):
        if fragment not in markdown:
            errors.append(f"Markdown parity missing fragment: {fragment}")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest_path = repo_relative_input_path(repo_root, args.manifest, "collector runtime manifest")
    except AnalyzerContractError as exc:
        raise ReachabilityError(str(exc)) from exc
    manifest, sources, source_errors = resolve_sources(repo_root, manifest_path)
    errors.extend(source_errors)
    definitions: list[Definition] = []
    references: list[Reference] = []
    dynamic_sites: list[dict[str, Any]] = []
    parser_warnings: list[dict[str, Any]] = []
    parser_mode = "python_lexical_fallback" if getattr(args, "no_powershell", False) else args.parser_mode
    if not errors:
        definitions, references, dynamic_sites, parser_warnings, parser_mode = parse_sources(sources, parser_mode)
        warnings.extend(scalar(item.get("message")) for item in parser_warnings if isinstance(item, dict) and item.get("message"))
    seen_defs: set[tuple[str, str, int]] = set()
    for definition in definitions:
        key = (definition.key, definition.source_path, definition.line)
        if key in seen_defs:
            errors.append(f"duplicate function definition record: {definition.name} {definition.source_path}:{definition.line}")
        seen_defs.add(key)
    entrypoints = {item.casefold() for item in args.entrypoint}
    function_records = classify_functions(definitions, references, dynamic_sites, entrypoints)
    classification_counts = Counter(item["classification"] for item in function_records)
    source_files = [
        {
            "path": source.repo_path,
            "load_order": source.load_order,
            "sha256": sha256_file(source.path),
            "size_bytes": source.path.stat().st_size,
        }
        for source in sources
    ]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": PARENT_ISSUE_NUMBER,
        "generated_from": {
            "tool": "project_sources/collector/tools/run_powershell_function_reachability_report.py",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "parser_mode": parser_mode,
        },
        "analysis_scope": {
            "scope": "manifest_declared_collector_runtime_source",
            "manifest_path": manifest_path.resolve().relative_to(repo_root).as_posix(),
            "collector_wrapper_source": manifest.get("collector_wrapper_source"),
            "collector_part_files": manifest.get("collector_part_files", []),
            "source_files": source_files,
            "excluded_surfaces": [
                "workflow-embedded PowerShell",
                "fixtures",
                "harness-only code",
                "operator tooling",
                "staging artifacts",
            ],
        },
        "summary": {
            "parser_mode": parser_mode,
            "source_file_count": len(sources),
            "function_count": len(function_records),
            "nested_function_count": len([item for item in function_records if item["definition_kind"] == "nested"]),
            "reference_count": len(references),
            "dynamic_invocation_site_count": len(dynamic_sites),
            "classification_counts": dict(sorted(classification_counts.items())),
            "coverage_state": "not_collected",
            "validation_success": False,
        },
        "entrypoint_names": sorted(args.entrypoint, key=str.casefold),
        "functions": function_records,
        "dynamic_invocation_sites": dynamic_sites,
        "runtime_lane_coverage": {
            "state": "not_collected",
            "observed_lanes": [],
            "claim": "Runtime absence is not claimed; no suite trace evidence was supplied to this report.",
        },
        "non_claims": list(NON_CLAIMS),
        "outputs": {
            "json": DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown": DEFAULT_MARKDOWN_OUTPUT.as_posix(),
        },
        "validation": {
            "success": False,
            "errors": errors,
            "warnings": warnings,
        },
    }
    if not errors:
        errors.extend(validate_report(report))
    report["validation"]["errors"] = errors
    report["validation"]["success"] = not errors
    report["summary"]["validation_success"] = report["validation"]["success"]
    return report


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_path, json_repo_path = safe_output_path(repo_root, json_output, "function reachability JSON output", ".json")
    markdown_path, markdown_repo_path = safe_output_path(repo_root, markdown_output, "function reachability Markdown output", ".md")
    if json_path.resolve() == markdown_path.resolve():
        raise ReachabilityError("function reachability JSON and Markdown output paths must be different")
    report["outputs"]["json"] = json_repo_path
    report["outputs"]["markdown"] = markdown_repo_path
    write_json(json_path, report)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST.as_posix(), help="Collector runtime manifest")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Output JSON report path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Output Markdown report path")
    parser.add_argument("--parser-mode", choices=("auto", "powershell_ast", "python_lexical_fallback"), default="auto")
    parser.add_argument("--no-powershell", action="store_true", help="Force the deterministic Python lexical fallback and never invoke PowerShell.")
    parser.add_argument("--entrypoint", action="append", default=[], help="Known entrypoint function name; repeatable")
    parser.add_argument("--no-write", action="store_true", help="Build report without writing output files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        report = build_report(args)
        repo_root = Path(args.repo_root).resolve()
        if not args.no_write:
            write_outputs(repo_root, report, Path(args.json_output), Path(args.markdown_output))
    except ReachabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if report["validation"]["success"]:
        return 0
    for error in report["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
