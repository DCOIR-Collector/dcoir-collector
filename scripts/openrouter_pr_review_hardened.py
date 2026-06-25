#!/usr/bin/env python3
"""Hardened DCOIR Review runner.

This wrapper reuses the existing reviewer safety helpers while
owning the governed routing payload and review-quality gates for issue #277.
"""

from __future__ import annotations

import copy
import json
import os
import re
import shlex
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import openrouter_pr_review as base


OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"


class ReviewQualityError(RuntimeError):
    """Raised when the model output cannot support a useful PR review."""


class ReviewTimeoutError(TimeoutError):
    """Raised before the workflow timeout so cleanup can still run."""


@dataclass(frozen=True)
class ChangedLine:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class RiskSentinel:
    path: str
    line: int
    label: str
    detail: str
    text: str


RISK_SENTINEL_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "unsafe deserialization primitive",
        "deserialization of operator or request-controlled bytes can execute code or construct unsafe objects",
        re.compile(r"\b(?:pickle\.loads|pickle\.load|yaml\.load|marshal\.loads|ObjectInputStream|BinaryFormatter)\b", re.IGNORECASE),
    ),
    (
        "PowerShell Invoke-Expression",
        "Invoke-Expression executes constructed text as code; verify no operator/comment input reaches it",
        re.compile(r"\bInvoke-Expression\b", re.IGNORECASE),
    ),
    (
        "PowerShell process launch",
        "Start-Process can execute request-controlled tools or arguments unless command and arguments are allowlisted",
        re.compile(r"\bStart-Process\b[^\n]*(?:\$Request\.|\$Input|\$args\b)", re.IGNORECASE),
    ),
    (
        "PowerShell unsafe archive extraction",
        "archive extraction needs destination containment and entry traversal checks before expanding untrusted archives",
        re.compile(r"\bExpand-Archive\b[^\n]*(?:\$Request\.|\$Input|\$args\b)", re.IGNORECASE),
    ),
    (
        "PowerShell outbound request or download",
        "web requests and downloads can create SSRF or exfiltration paths when URI, headers, or output path are request controlled",
        re.compile(r"\b(?:Invoke-WebRequest|Invoke-RestMethod|iwr)\b[^\n]*(?:\$Request\.|\$Input|\$args\b|Authorization|Bearer)", re.IGNORECASE),
    ),
    (
        "PowerShell broad ACL grant",
        "broad ACL grants such as Everyone FullControl can expose collector evidence or execution surfaces",
        re.compile(r"\b(?:FileSystemAccessRule|Set-Acl)\b[^\n]*(?:Everyone|FullControl|Allow|\$Request\.)", re.IGNORECASE),
    ),
    (
        "Node.js command execution",
        "child-process execution can turn request-controlled strings into command execution unless command and arguments are bounded",
        re.compile(r"\b(?:exec|execSync|spawn|spawnSync|execFile|execFileSync)\s*\([^\n]*(?:request\.|req\.|input|params\.|body\.|\$\{)", re.IGNORECASE),
    ),
    (
        "dynamic code evaluation",
        "eval-style APIs execute constructed text as code and require complete elimination or strict allowlisting",
        re.compile(r"\b(?:eval|Function)\s*\([^\n]*(?:request\.|req\.|input|params\.|body\.|\$Request\.|\$\{)", re.IGNORECASE),
    ),
    (
        "TypeScript/JavaScript unsafe path construction",
        "request-controlled path segments need normalization and root containment before file writes, reads, uploads, or staging",
        re.compile(r"\b(?:path\.)?(?:join|resolve)\s*\([^\n]*(?:request\.|req\.|input|params\.|body\.)", re.IGNORECASE),
    ),
    (
        "TypeScript/JavaScript unsafe file write",
        "file writes need root containment when the destination path can be request, operator, or PR controlled",
        re.compile(r"\b(?:writeFileSync|writeFile|appendFileSync|appendFile|createWriteStream)\s*\([^\n]*(?:request\.|req\.|input|params\.|body\.|destination|target|path)", re.IGNORECASE),
    ),
    (
        "raw SQL/query string interpolation",
        "raw variables are interpolated into a query-like string; verify escaping, parameterization, and evidence scope",
        re.compile(
            r"(?:\bSELECT\b|\bFROM\b|\bWHERE\b(?!-Object)|(?<!-)\bLIKE\b).*(?:\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*)",
            re.IGNORECASE,
        ),
    ),
    (
        "shell=True subprocess invocation",
        "shell execution can turn path or identifier input into command execution and can hide failures when check is false",
        re.compile(r"\bsubprocess\.\w+\([^#\n]*\bshell\s*=\s*True\b"),
    ),
    (
        "Python unsafe archive extraction",
        "archive extraction needs destination containment and member traversal checks before unpacking untrusted archives",
        re.compile(r"\b(?:extractall|shutil\.unpack_archive|tarfile\.open|zipfile\.ZipFile|subprocess\.\w+\([^\n]*(?:tar|unzip))\b", re.IGNORECASE),
    ),
    (
        "outbound request or SSRF primitive",
        "request-controlled URLs can create SSRF or exfiltration paths unless scheme, host, redirect, and destination policy are bounded",
        re.compile(r"\b(?:fetch|requests\.(?:get|post|put|request)|urllib\.request\.urlopen|httpx\.(?:get|post|request))\s*\([^\n]*(?:request|req|input|params|body|callback|url)", re.IGNORECASE),
    ),
    (
        "CI token exfiltration primitive",
        "CI or environment secret material appears in a sink that may persist or send secrets outside the trusted workflow boundary",
        re.compile(r"(?:GITHUB_TOKEN|secrets\.[A-Za-z0-9_]+|process\.env\.[A-Za-z0-9_]*(?:TOKEN|KEY|SECRET)|os\.environ\.get\([^\n]*(?:TOKEN|KEY|SECRET))", re.IGNORECASE),
    ),
    (
        "GitHub Actions privileged PR context",
        "pull_request_target or privileged checkout patterns can execute untrusted PR content with repository write tokens",
        re.compile(r"\bpull_request_target\b|github\.event\.pull_request\.head\.(?:ref|sha)", re.IGNORECASE),
    ),
    (
        "GitHub Actions untrusted metadata shell execution",
        "PR title, body, branch, or other event metadata must not be written into a shell script or executed in a privileged workflow",
        re.compile(r"github\.event\.pull_request\.(?:title|body|head\.ref|head\.sha)", re.IGNORECASE),
    ),
    (
        "Kubernetes privileged container setting",
        "privileged, root, host-network, or privilege-escalation settings expand container breakout and node compromise risk",
        re.compile(r"\b(?:privileged|allowPrivilegeEscalation|hostNetwork)\s*:\s*true\b|\brunAsUser\s*:\s*0\b", re.IGNORECASE),
    ),
    (
        "Kubernetes host filesystem exposure",
        "hostPath mounts can expose node filesystems and credentials to containers unless narrowly scoped and read-only",
        re.compile(r"\bhostPath\s*:\s*$|\bmountPath\s*:\s*/host\b", re.IGNORECASE),
    ),
    (
        "truthy literal branch condition",
        "a literal string after or/-or is always truthy and can bypass intended severity or confidence checks",
        re.compile(r"(?:\bor\b|\b-or\b)\s+['\"][^'\"]+['\"]", re.IGNORECASE),
    ),
    (
        "recursive delete primitive",
        "recursive deletion needs path root constraints, fail-closed behavior, and visible errors",
        re.compile(r"\bshutil\.rmtree\b|\bRemove-Item\b[^\n]*\s-Recurse\b", re.IGNORECASE),
    ),
    (
        "PowerShell unsafe file-write path",
        "PowerShell file writes need root containment when the destination path can be request or operator controlled",
        re.compile(
            r"\b(?:Set-Content|Add-Content|Out-File|Export-Clixml|Export-Csv|Copy-Item|Move-Item|New-Item)\b"
            r"[^\n]*\s-(?:Path|LiteralPath|FilePath|Destination)\s+\$Request\.",
            re.IGNORECASE,
        ),
    ),
    (
        "environment dump or exfiltration primitive",
        "full environment enumeration can leak CI or collector secrets into reports, logs, or webhooks",
        re.compile(r"\bos\.environ(?:\.items\(\)|\b)|\bGet-ChildItem\s+Env:", re.IGNORECASE),
    ),
)

RISK_SENTINEL_EXTENSIONS = {
    ".bash",
    ".cjs",
    ".js",
    ".json",
    ".mjs",
    ".ps1",
    ".psd1",
    ".psm1",
    ".py",
    ".sh",
    ".ts",
    ".yaml",
    ".yml",
}

RISK_SENTINEL_COVERAGE_LINE_WINDOW = 4

RISK_SENTINEL_FINDING_TERMS: dict[str, tuple[str, ...]] = {
    "PowerShell Invoke-Expression": (
        "invoke-expression",
        "constructed text",
        "command injection",
        "code execution",
    ),
    "PowerShell process launch": (
        "start-process",
        "process",
        "command execution",
        "allowlist",
    ),
    "PowerShell unsafe archive extraction": (
        "expand-archive",
        "archive",
        "extraction",
        "path traversal",
        "containment",
    ),
    "PowerShell outbound request or download": (
        "invoke-webrequest",
        "web request",
        "ssrf",
        "exfiltration",
        "outbound",
    ),
    "PowerShell broad ACL grant": (
        "acl",
        "set-acl",
        "everyone",
        "fullcontrol",
        "permission",
    ),
    "Node.js command execution": (
        "exec",
        "spawn",
        "child process",
        "command injection",
    ),
    "dynamic code evaluation": (
        "eval",
        "function",
        "dynamic code",
        "code execution",
    ),
    "TypeScript/JavaScript unsafe path construction": (
        "path traversal",
        "path construction",
        "root containment",
        "file write",
    ),
    "TypeScript/JavaScript unsafe file write": (
        "writefile",
        "file write",
        "root containment",
        "path traversal",
    ),
    "raw SQL/query string interpolation": (
        "sql",
        "query",
        "interpolation",
        "parameter",
    ),
    "shell=True subprocess invocation": (
        "shell=true",
        "shell true",
        "shell execution",
        "subprocess",
        "command injection",
    ),
    "Python unsafe archive extraction": (
        "archive",
        "tar",
        "unpack",
        "extract",
        "path traversal",
    ),
    "outbound request or SSRF primitive": (
        "ssrf",
        "outbound",
        "url",
        "request",
        "exfiltration",
    ),
    "CI token exfiltration primitive": (
        "token",
        "secret",
        "authorization",
        "exfiltration",
    ),
    "GitHub Actions privileged PR context": (
        "pull_request_target",
        "privileged",
        "untrusted",
        "write token",
        "checkout",
    ),
    "GitHub Actions untrusted metadata shell execution": (
        "pull request title",
        "pull request body",
        "shell",
        "untrusted metadata",
    ),
    "Kubernetes privileged container setting": (
        "kubernetes",
        "privileged",
        "runasuser",
        "hostnetwork",
        "allowprivilegeescalation",
    ),
    "Kubernetes host filesystem exposure": (
        "hostpath",
        "host filesystem",
        "mount",
        "node",
    ),
    "unsafe deserialization primitive": (
        "deserialization",
        "pickle",
        "yaml.load",
        "code execution",
    ),
    "truthy literal branch condition": (
        "truthy",
        "always true",
        "literal branch",
        "bypass",
    ),
    "recursive delete primitive": (
        "recursive delete",
        "remove-item",
        "rmtree",
        "deletion",
        "path root",
    ),
    "PowerShell unsafe file-write path": (
        "powershell",
        "file write",
        "set-content",
        "out-file",
        "root containment",
        "request",
        "path",
    ),
    "environment dump or exfiltration primitive": (
        "environment",
        "os.environ",
        "get-childitem env",
        "secret",
        "exfiltration",
    ),
    "unsafe file-write path construction": (
        "path traversal",
        "file write",
        "arbitrary overwrite",
        "root containment",
        "dynamic path",
    ),
}

RISK_SENTINEL_HIGH_SEVERITY_LABELS = {
    "unsafe deserialization primitive",
    "PowerShell Invoke-Expression",
    "PowerShell process launch",
    "PowerShell unsafe archive extraction",
    "PowerShell outbound request or download",
    "PowerShell broad ACL grant",
    "Node.js command execution",
    "dynamic code evaluation",
    "TypeScript/JavaScript unsafe path construction",
    "TypeScript/JavaScript unsafe file write",
    "raw SQL/query string interpolation",
    "shell=True subprocess invocation",
    "Python unsafe archive extraction",
    "outbound request or SSRF primitive",
    "CI token exfiltration primitive",
    "GitHub Actions privileged PR context",
    "GitHub Actions untrusted metadata shell execution",
    "Kubernetes privileged container setting",
    "Kubernetes host filesystem exposure",
    "environment dump or exfiltration primitive",
    "PowerShell unsafe file-write path",
    "unsafe file-write path construction",
}

RISK_SENTINEL_LABEL_PRIORITY = {
    label: index
    for index, label in enumerate(
        (
            "unsafe deserialization primitive",
            "PowerShell Invoke-Expression",
            "PowerShell process launch",
            "PowerShell unsafe archive extraction",
            "PowerShell outbound request or download",
            "PowerShell broad ACL grant",
            "Node.js command execution",
            "TypeScript/JavaScript unsafe path construction",
            "TypeScript/JavaScript unsafe file write",
            "shell=True subprocess invocation",
            "dynamic code evaluation",
            "raw SQL/query string interpolation",
            "GitHub Actions privileged PR context",
            "CI token exfiltration primitive",
            "GitHub Actions untrusted metadata shell execution",
            "unsafe file-write path construction",
            "PowerShell unsafe file-write path",
            "Python unsafe archive extraction",
            "outbound request or SSRF primitive",
            "Kubernetes privileged container setting",
            "Kubernetes host filesystem exposure",
            "environment dump or exfiltration primitive",
            "recursive delete primitive",
            "truthy literal branch condition",
        )
    )
}


OPTIONAL_RISK_SENTINEL_LABEL_PREFIXES = (
    "TypeScript/JavaScript ",
    "Kubernetes ",
)
OPTIONAL_RISK_SENTINEL_LABELS = {
    "Node.js command execution",
}
YAML_REQUIRED_RISK_SENTINEL_LABEL_PREFIXES = (
    "GitHub Actions ",
)
YAML_REQUIRED_RISK_SENTINEL_LABELS = {
    "CI token exfiltration primitive",
}
PROJECT_TARGET_RISK_SENTINEL_EXTENSIONS = {
    ".ps1",
    ".psd1",
    ".psm1",
    ".py",
}


POWERSHELL_REQUEST_PATH_ASSIGNMENT = re.compile(
    r"^\s*\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"(?P<value>.*(?:\bJoin-Path\b[^\n]*\$Request\.|\$Request\.(?:Path|RelativePath|FilePath|OutputPath|Destination)\b).*)$",
    re.IGNORECASE,
)
POWERSHELL_WRITE_PATH_VARIABLE = re.compile(
    r"\b(?:Set-Content|Add-Content|Out-File|Export-Clixml|Export-Csv|Copy-Item|Move-Item|New-Item)\b"
    r"[^\n]*\s-(?:Path|LiteralPath|FilePath|Destination)\s+\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
    re.IGNORECASE,
)


NON_ACTIONABLE_FINDING_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b(?:downgrades?|downgraded)\b.{0,120}\binformational\b", re.IGNORECASE | re.DOTALL),
        "finding downgrades itself to informational",
    ),
    (
        re.compile(r"\binformational\b.{0,120}\b(?:note|signal|finding|only)\b", re.IGNORECASE | re.DOTALL),
        "finding describes itself as informational",
    ),
    (
        re.compile(
            r"\b(?:risk|signal|finding)\b.{0,120}\b(?:not realized|is not realized|was not realized)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "finding says the risk is not realized",
    ),
    (
        re.compile(
            r"\bdoes not(?: itself)?\s+(?:introduce|create|pose|add)\b.{0,120}"
            r"\b(?:risk|issue|problem|defect|vulnerability|injection path)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "finding says the changed code does not introduce the risk",
    ),
    (
        re.compile(r"\bno\b.{0,80}\b(?:input|data|value|text)\b.{0,80}\breaches\b", re.IGNORECASE | re.DOTALL),
        "finding says no input reaches the risky path",
    ),
    (
        re.compile(r"\bno\b.{0,80}\b(?:execution|injection|exploit|vulnerability)\b.{0,80}\b(?:path|risk)\b", re.IGNORECASE | re.DOTALL),
        "finding says no execution or injection path exists",
    ),
    (
        re.compile(r"\b(?:out of scope|outside (?:the )?PR scope|no action is required)\b", re.IGNORECASE | re.DOTALL),
        "finding describes itself as out of scope",
    ),
)



def sanitize_github_output(text: str, config: Any, neutralize_mentions: bool = True) -> str:
    if hasattr(base, "sanitize_github_output"):
        return base.sanitize_github_output(text, config, neutralize_mentions=neutralize_mentions)
    cleaned = base.sanitize_text(text, config)
    if neutralize_mentions and hasattr(base, "neutralize_github_mentions"):
        return base.neutralize_github_mentions(cleaned)
    return cleaned


def parse_yaml_like_data(path: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    raw = Path(path).read_text(encoding="utf-8")
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            data[current_key] = [] if value == "" else base.parse_scalar(value)
            continue
        if current_key and stripped.startswith("-"):
            data.setdefault(current_key, []).append(base.parse_scalar(stripped[1:].strip()))
    return data


def list_value(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in ("", None):
        return []
    return [str(value)]


def bool_value(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "on", "1"}:
        return True
    if lowered in {"false", "no", "off", "0", "none", "null", ""}:
        return False
    return bool(value)


def optional_int(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value in ("", None):
        return None
    return int(value)


def is_free_model(model: str) -> bool:
    lowered = model.strip().lower()
    return lowered == "openrouter/free" or lowered.endswith(":free")


def ensure_free_models_are_opt_in(config: Any) -> None:
    models = [config.model, *getattr(config, "model_stack", []), *getattr(config, "fallback_models", [])]
    if any(is_free_model(model) for model in models) and not getattr(config, "smoke_test_free_model", False):
        raise RuntimeError(
            "OpenRouter free-router models are smoke-test only. Set smoke_test_free_model: true "
            "only for explicit non-governed smoke runs."
        )


def load_hardened_config(path: str) -> Any:
    config = base.load_yaml_like_config(path)
    data = parse_yaml_like_data(path)

    config.model = str(data.get("model", getattr(config, "model", "openrouter/auto")))
    model_stack = list_value(data, "model_stack")
    config.model_stack = model_stack or [config.model]
    config.fallback_models = list_value(data, "fallback_models")
    config.auto_allowed_models = list_value(data, "auto_allowed_models")
    config.auto_cost_quality_tradeoff = optional_int(data, "auto_cost_quality_tradeoff")
    config.openrouter_route = str(data.get("openrouter_route", "") or "").strip()
    config.openrouter_service_tier = str(data.get("openrouter_service_tier", "") or "").strip()
    config.openrouter_session_id_prefix = str(
        data.get("openrouter_session_id_prefix", "dcoir-review") or ""
    ).strip()
    config.smoke_test_free_model = bool_value(data, "smoke_test_free_model", False)
    config.fail_on_unanchored_findings = bool_value(data, "fail_on_unanchored_findings", True)
    config.fail_on_summary_only_problem = bool_value(data, "fail_on_summary_only_problem", True)
    config.review_quality_retry_on_rejected_output = bool_value(data, "review_quality_retry_on_rejected_output", True)
    config.risk_sentinel_quality_gate = bool_value(data, "risk_sentinel_quality_gate", True)
    config.risk_sentinel_retry_on_empty = bool_value(data, "risk_sentinel_retry_on_empty", True)
    config.risk_sentinel_max_anchors = int(data.get("risk_sentinel_max_anchors", 12))
    config.script_timeout_seconds = int(data.get("script_timeout_seconds", getattr(config, "script_timeout_seconds", 1500)))
    config.debug = bool_value(data, "debug", getattr(config, "debug", False))
    config.post_progress_comment = bool_value(data, "post_progress_comment", getattr(config, "post_progress_comment", False))

    ensure_free_models_are_opt_in(config)
    return config


def model_stack_label(config: Any) -> str:
    primary = ", ".join(getattr(config, "model_stack", [config.model]))
    fallbacks = getattr(config, "fallback_models", [])
    if fallbacks:
        return f"{primary}; native fallbacks: {', '.join(fallbacks)}"
    return primary


class SimpleProgressReporter:
    def __init__(self, gh: Any, issue_number: int, command: str, config: Any) -> None:
        self.gh = gh
        self.issue_number = issue_number
        self.command = command
        self.config = config
        self.comment_id = 0
        self.steps: list[tuple[str, str]] = []

    def start(self) -> None:
        self._record("started", "accepted operator review command and initialized progress reporting")
        if getattr(self.config, "post_progress_comment", False):
            comment = self.gh.create_issue_comment(self.issue_number, self._body("running"))
            self.comment_id = int(comment.get("id", 0))

    def update(self, stage: str, message: str) -> None:
        self._record(stage, message)
        self._update_comment(self._body("running"))

    def complete(self, model_used: str, findings_count: int, review_event: str) -> None:
        plural = "finding" if findings_count == 1 else "findings"
        self._record("completed", f"posted GitHub review; {findings_count} inline {plural}; event={review_event}")
        self._update_comment(
            self._body(
                "completed",
                final_lines=[
                    f"- Result: GitHub review posted with `{findings_count}` inline {plural}.",
                    f"- Review event: `{review_event}`.",
                ],
            )
        )

    def fail(self, message: str) -> None:
        safe_message = sanitize_github_output(message, self.config)
        self._record("failed", safe_message[:500])
        self._update_comment(
            self._body(
                "failed",
                final_lines=[
                    "- Result: review failed before a usable PR review could be posted.",
                    "",
                    "```text",
                    safe_message[:4000],
                    "```",
                ],
            ),
            create_if_missing=True,
        )

    def _record(self, stage: str, message: str) -> None:
        safe_message = sanitize_github_output(message, self.config)
        self.steps.append((stage, safe_message))
        if hasattr(base, "emit_status"):
            base.emit_status(stage, safe_message)
        else:
            print(f"[dcoir-review] {stage}: {safe_message}", flush=True)

    def _body(self, state: str, final_lines: list[str] | None = None) -> str:
        lines = [
            base.MARKER,
            f"{base.REVIEW_DISPLAY_NAME} {state}.",
            "",
            f"- Command: `{self.command}`.",
            f"- Debug progress: `{str(getattr(self.config, 'debug', False)).lower()}`.",
            *(
                base.workflow_run_status_lines(self.config)
                if hasattr(base, "workflow_run_status_lines")
                else []
            ),
            "- Branch changes: none; this workflow only posts review output.",
            "- Gate role: internal review-assist signal before any separately approved external review request.",
        ]
        if final_lines:
            lines.extend(["", *final_lines])
        lines.extend(["", "Progress:"])
        for stage, message in self.steps[-12:]:
            public_stage = base.sanitize_public_identity(stage) if hasattr(base, "sanitize_public_identity") else stage
            lines.append(f"- `{public_stage}`: {message}")
        return base.github_safe_body("\n".join(lines), limit=12000)

    def _update_comment(self, body: str, create_if_missing: bool = False) -> None:
        if not getattr(self.config, "post_progress_comment", False):
            return
        if self.comment_id:
            self.gh.update_issue_comment(self.comment_id, body)
        elif create_if_missing:
            comment = self.gh.create_issue_comment(self.issue_number, body)
            self.comment_id = int(comment.get("id", 0))


ProgressReporter = getattr(base, "ProgressReporter", SimpleProgressReporter)


def matching_command(body: str, commands: list[str]) -> str | None:
    if hasattr(base, "matching_command"):
        return base.matching_command(body, commands)
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    for command in commands:
        if re.fullmatch(rf"{re.escape(command)}(?:\s+.*)?", first_line):
            return command
    return None


def session_id(config: Any) -> str:
    prefix = getattr(config, "openrouter_session_id_prefix", "")
    if not prefix:
        return ""
    raw = f"{prefix}:{os.environ.get('GITHUB_REPOSITORY', 'repo')}:pr-{os.environ.get('PR_NUMBER', 'unknown')}"
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw)[:256]


def iter_added_diff_lines(diff: str) -> list[ChangedLine]:
    lines: list[ChangedLine] = []
    current_path: str | None = None
    right_line: int | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current_path = None
            right_line = None
            continue
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,\d+)?", line)
            right_line = int(match.group(1)) if match else None
            continue
        if current_path is None or right_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(ChangedLine(current_path, right_line, line[1:]))
            right_line += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            continue
        right_line += 1
    return lines


def build_added_line_index(diff: str) -> dict[tuple[str, int], int]:
    right_line_index = base.build_diff_line_index(diff)
    added_line_index: dict[tuple[str, int], int] = {}
    for changed_line in iter_added_diff_lines(diff):
        key = (changed_line.path, changed_line.line)
        if key in right_line_index:
            added_line_index[key] = right_line_index[key]
    return added_line_index


def is_comment_only_added_line(path: str, text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    suffix = Path(path).suffix.lower()
    if suffix in {".py", ".sh", ".bash", ".yaml", ".yml"}:
        return stripped.startswith("#")
    if suffix in {".ps1", ".psd1", ".psm1"}:
        return stripped.startswith(("#", "<#", "#>"))
    if suffix in {".js", ".cjs", ".mjs", ".ts"}:
        return stripped.startswith(("//", "/*", "*", "*/"))
    return False


def append_risk_sentinel(
    sentinels: list[RiskSentinel],
    seen: set[tuple[str, int, str]],
    changed_line: ChangedLine,
    label: str,
    detail: str,
) -> None:
    key = (changed_line.path, changed_line.line, label)
    if key in seen:
        return
    seen.add(key)
    sentinels.append(
        RiskSentinel(
            path=changed_line.path,
            line=changed_line.line,
            label=label,
            detail=detail,
            text=changed_line.text,
        )
    )


def select_risk_sentinels(sentinels: list[RiskSentinel], max_anchors: int | None) -> list[RiskSentinel]:
    if max_anchors is None or len(sentinels) <= max_anchors:
        return sentinels
    if max_anchors <= 0:
        return []

    indexed = list(enumerate(sentinels))
    by_path: dict[str, list[tuple[int, RiskSentinel]]] = {}
    for index, sentinel in indexed:
        by_path.setdefault(sentinel.path, []).append((index, sentinel))

    def sort_key(item: tuple[int, RiskSentinel]) -> tuple[int, int]:
        index, sentinel = item
        return (RISK_SENTINEL_LABEL_PRIORITY.get(sentinel.label, 1000), index)

    for items in by_path.values():
        items.sort(key=sort_key)

    path_order = sorted(
        by_path,
        key=lambda path: (
            RISK_SENTINEL_LABEL_PRIORITY.get(by_path[path][0][1].label, 1000),
            by_path[path][0][0],
        ),
    )
    selected: list[RiskSentinel] = []
    selected_indexes: set[int] = set()
    selected_labels_by_path: dict[str, set[str]] = {path: set() for path in path_order}
    while len(selected) < max_anchors:
        made_progress = False
        for path in path_order:
            candidates = [item for item in by_path[path] if item[0] not in selected_indexes]
            next_item = next(
                (item for item in candidates if item[1].label not in selected_labels_by_path[path]),
                candidates[0] if candidates else None,
            )
            if next_item is None:
                continue
            index, sentinel = next_item
            selected_indexes.add(index)
            selected_labels_by_path[path].add(sentinel.label)
            selected.append(sentinel)
            made_progress = True
            if len(selected) >= max_anchors:
                break
        if not made_progress:
            break
    return selected


def detect_risk_sentinels(diff: str, max_anchors: int | None = None) -> list[RiskSentinel]:
    sentinels: list[RiskSentinel] = []
    seen: set[tuple[str, int, str]] = set()
    active_python_subprocess_call: str | None = None
    current_path = ""
    powershell_request_path_vars: set[str] = set()
    shell_subprocess_detail = next(
        detail for label, detail, _pattern in RISK_SENTINEL_RULES if label == "shell=True subprocess invocation"
    )
    powershell_file_write_detail = next(
        detail for label, detail, _pattern in RISK_SENTINEL_RULES if label == "PowerShell unsafe file-write path"
    )
    for changed_line in iter_added_diff_lines(diff):
        if changed_line.path != current_path:
            current_path = changed_line.path
            powershell_request_path_vars = set()
        suffix = Path(changed_line.path).suffix.lower()
        if suffix not in RISK_SENTINEL_EXTENSIONS:
            active_python_subprocess_call = None
            powershell_request_path_vars = set()
            continue
        if is_comment_only_added_line(changed_line.path, changed_line.text):
            continue

        if suffix == ".py":
            if active_python_subprocess_call == changed_line.path and re.search(r"\bshell\s*=\s*True\b", changed_line.text):
                append_risk_sentinel(
                    sentinels,
                    seen,
                    changed_line,
                    "shell=True subprocess invocation",
                    shell_subprocess_detail,
                )
            open_call = re.search(r"\bsubprocess\.\w+\(", changed_line.text)
            if open_call and ")" not in changed_line.text[open_call.end() :]:
                active_python_subprocess_call = changed_line.path
            elif active_python_subprocess_call == changed_line.path and ")" in changed_line.text:
                active_python_subprocess_call = None
        else:
            active_python_subprocess_call = None

        if suffix in {".ps1", ".psd1", ".psm1"}:
            assignment_match = POWERSHELL_REQUEST_PATH_ASSIGNMENT.search(changed_line.text)
            if assignment_match:
                powershell_request_path_vars.add(assignment_match.group("name").lower())
            write_match = POWERSHELL_WRITE_PATH_VARIABLE.search(changed_line.text)
            if write_match and write_match.group("name").lower() in powershell_request_path_vars:
                append_risk_sentinel(
                    sentinels,
                    seen,
                    changed_line,
                    "PowerShell unsafe file-write path",
                    powershell_file_write_detail,
                )

        for label, detail, pattern in RISK_SENTINEL_RULES:
            if pattern.search(changed_line.text):
                append_risk_sentinel(sentinels, seen, changed_line, label, detail)
                break
    return select_risk_sentinels(sentinels, max_anchors)


def risk_sentinel_digest(sentinels: list[RiskSentinel]) -> str:
    return "; ".join(f"{item.path}:{item.line} {item.label}" for item in sentinels[:6])


def risk_sentinel_block(sentinels: list[RiskSentinel], config: Any) -> str:
    lines = [
        "Changed-code risk signals detected before model review:",
        "Any non-empty findings response must cover these anchors by path, nearby line, and risk class. Unrelated findings do not satisfy this gate.",
    ]
    for item in sentinels[: getattr(config, "risk_sentinel_max_anchors", 12)]:
        snippet = item.text.strip().replace("`", "'")
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        lines.append(f"- {item.path}:{item.line} [{item.label}] {item.detail}. Changed code: `{snippet}`")
    return base.sanitize_text("\n".join(lines), config)


def normalized_quality_text(text: str) -> str:
    return re.sub(r"[^a-z0-9_.:=/-]+", " ", text.lower()).strip()


def risk_sentinel_terms(sentinel: RiskSentinel) -> tuple[str, ...]:
    terms = RISK_SENTINEL_FINDING_TERMS.get(sentinel.label, ())
    if terms:
        return terms
    label_terms = tuple(part for part in normalized_quality_text(sentinel.label).split() if len(part) >= 4)
    return label_terms or (normalized_quality_text(sentinel.label),)


def finding_covers_risk_sentinel(finding: dict[str, Any], sentinel: RiskSentinel) -> bool:
    try:
        finding_line = int(finding.get("line", 0))
    except (TypeError, ValueError):
        return False
    finding_path = str(finding.get("path", "")).strip()
    if finding_path != sentinel.path:
        return False
    if abs(finding_line - sentinel.line) > RISK_SENTINEL_COVERAGE_LINE_WINDOW:
        return False
    finding_text = normalized_quality_text(
        "\n".join(
            [
                str(finding.get("title", "") or ""),
                str(finding.get("body", "") or ""),
                str(finding.get("validation", "") or ""),
            ]
        )
    )
    if not finding_text:
        return False
    return any(normalized_quality_text(term) in finding_text for term in risk_sentinel_terms(sentinel))


def is_required_risk_sentinel(sentinel: RiskSentinel) -> bool:
    label = sentinel.label
    if label in OPTIONAL_RISK_SENTINEL_LABELS or any(
        label.startswith(prefix) for prefix in OPTIONAL_RISK_SENTINEL_LABEL_PREFIXES
    ):
        return False
    suffix = Path(sentinel.path).suffix.lower()
    if suffix in PROJECT_TARGET_RISK_SENTINEL_EXTENSIONS:
        return True
    if suffix in {".yml", ".yaml"}:
        return label in YAML_REQUIRED_RISK_SENTINEL_LABELS or any(
            label.startswith(prefix) for prefix in YAML_REQUIRED_RISK_SENTINEL_LABEL_PREFIXES
        )
    return False


def required_risk_sentinels(sentinels: list[RiskSentinel]) -> list[RiskSentinel]:
    return [sentinel for sentinel in sentinels if is_required_risk_sentinel(sentinel)]


def uncovered_risk_sentinels(
    findings: list[dict[str, Any]],
    risk_sentinels: list[RiskSentinel],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[RiskSentinel]:
    if not risk_sentinels or not getattr(config, "risk_sentinel_quality_gate", True):
        return []
    candidate_findings = [*findings, *(unanchored_findings or [])]
    return [
        sentinel
        for sentinel in required_risk_sentinels(risk_sentinels)
        if not any(finding_covers_risk_sentinel(finding, sentinel) for finding in candidate_findings)
    ]


def risk_sentinel_coverage_digest(sentinels: list[RiskSentinel]) -> str:
    return "; ".join(f"{item.path}:{item.line} {item.label}" for item in sentinels[:8])


def primary_validation_command(config: Any) -> str:
    commands = getattr(config, "validation_commands", [])
    if isinstance(commands, list) and commands:
        return str(commands[0])
    return "Run the relevant dcoir-review selftests and workflow validation."


def risk_sentinel_fallback_finding(sentinel: RiskSentinel, config: Any) -> dict[str, Any]:
    severity = "high" if sentinel.label in RISK_SENTINEL_HIGH_SEVERITY_LABELS else "medium"
    return {
        "title": f"Deterministic risk sentinel: {sentinel.label}",
        "severity": severity,
        "confidence": 0.99,
        "path": sentinel.path,
        "line": sentinel.line,
        "body": (
            f"This changed line matched dcoir-review's deterministic `{sentinel.label}` sentinel. "
            f"{sentinel.detail}. Treat this as actionable unless the code constrains the input and side effect "
            "before this line; otherwise replace the primitive with a bounded, validated implementation and add "
            "readback validation for the narrowed behavior."
        ),
        "suggested_replacement": "",
        "validation": primary_validation_command(config),
    }


def add_risk_sentinel_fallback_findings(
    findings: list[dict[str, Any]],
    risk_sentinels: list[RiskSentinel],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    uncovered = uncovered_risk_sentinels(findings, risk_sentinels, config, unanchored_findings)
    if not uncovered:
        return findings
    inline_limit = int(getattr(config, "max_inline_comments", 12))
    if inline_limit <= 0:
        return findings
    required_uncovered = required_risk_sentinels(uncovered)
    fallback_source = required_uncovered if required_uncovered else uncovered
    fallback_findings = [risk_sentinel_fallback_finding(sentinel, config) for sentinel in fallback_source[:inline_limit]]
    if len(findings) + len(fallback_findings) <= inline_limit:
        augmented = [*findings, *fallback_findings]
    else:
        existing_budget = max(0, inline_limit - len(fallback_findings))
        existing_findings = select_findings_for_inline(findings, existing_budget)
        augmented = [*existing_findings, *fallback_findings]
    return select_findings_for_inline(augmented, inline_limit)


def append_with_budget(prefix: str, suffix: str, max_chars: int) -> str:
    separator = "\n\n"
    if len(prefix) + len(separator) + len(suffix) <= max_chars:
        return f"{prefix}{separator}{suffix}"
    truncation_marker = "\n\n[context truncated by reviewer]"
    if len(suffix) + len(truncation_marker) >= max_chars:
        retained_suffix = max(0, max_chars - len(truncation_marker))
        return f"{suffix[:retained_suffix]}{truncation_marker}"
    retained = max(0, max_chars - len(separator) - len(suffix) - len(truncation_marker))
    return f"{prefix[:retained]}{truncation_marker}{separator}{suffix}"


def powershell_double_quoted(value: str) -> str:
    escaped = value.replace("`", "``").replace('"', '`"').replace("$", "`$")
    return f'"{escaped}"'


def validation_hint_for_path(path: str) -> str:
    quoted = shlex.quote(path)
    ps_path = powershell_double_quoted(path)
    lower_path = path.lower()
    if lower_path.endswith(".py"):
        return (
            f"- `{path}`: validate with `python3 -m py_compile {quoted}` plus the nearest Python selftest or unit test "
            "that imports or exercises the changed function."
        )
    if lower_path.endswith(".ps1") or lower_path.endswith(".psm1") or lower_path.endswith(".psd1"):
        return (
            f"- `{path}`: validate with `pwsh -NoProfile -Command '$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath {ps_path}), [ref]$errors) | Out-Null; if ($errors) {{ throw ($errors | Out-String) }}'` "
            "plus the collector PowerShell validation script when collector behavior is touched."
        )
    if lower_path.endswith((".yml", ".yaml")):
        return (
            f"- `{path}`: validate YAML parsing and the affected workflow check; for GitHub Actions changes include "
            "`python3 project_sources/github_actions/tools/build_workflow_inventory.py --check` after regenerating inventory if workflow metadata changed."
        )
    if lower_path.endswith(".json"):
        return f"- `{path}`: validate with `python3 -m json.tool {quoted}` plus the nearest schema or report validator."
    if lower_path.endswith(".md"):
        return f"- `{path}`: validate the rendered Markdown and read back the exact changed section from the PR diff."
    return f"- `{path}`: choose a syntax/static check and a focused behavior check for the changed file, not a generic full-run command."


def validation_hint_block(files: list[dict[str, Any]], max_files: int = 12) -> str:
    paths = []
    seen: set[str] = set()
    for item in files:
        path = str(item.get("filename", "")).strip()
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
        if len(paths) >= max_files:
            break
    if not paths:
        return ""
    hints = "\n".join(validation_hint_for_path(path) for path in paths)
    return f"Changed-file validation hints:\n{hints}"


def build_prompt(
    pr: dict[str, Any],
    files: list[dict[str, Any]],
    diff: str,
    config: Any,
    risk_sentinels: list[RiskSentinel] | None = None,
) -> str:
    hardening = """
Governed review hardening requirements:
- Do not hide actionable issues only in the summary. Every semantic, Markdown, governance, validation, or review-gate concern must be returned as a finding object.
- For Markdown and governed-source findings, anchor the finding to the nearest changed right-side line that introduced or materially preserves the risky wording.
- If a small suggestion block is not safe, leave suggested_replacement empty and put exact repair steps in the finding body.
- Each finding body must include observed behavior, impact, exact correction guidance, and validation or readback guidance.
- Validation guidance must be specific to the changed file and finding. Prefer syntax/static/security checks or focused tests that exercise the affected file or behavior; do not recommend reviewer-runner selftests unless the changed code is the reviewer runner itself.
- Do not return informational or advisory findings that say the risk is not realized, the changed code does not introduce the risk, or no input reaches the risky path. Put that in a clean summary instead.
- Treat changed tests, fixtures, validation probes, examples, workflow snippets, infrastructure config, and generated-looking files as review targets when they contain executable behavior, security policy, credential handling, or operator guidance. Do not dismiss a finding merely because the file appears non-production.
- Review across languages and file types for command/process execution, dynamic code evaluation, request-controlled path reads/writes/extraction, raw query construction, unsafe deserialization, outbound requests or SSRF, token/secret persistence or forwarding, CI/CD privilege boundaries, broad ACL or permission grants, and container/orchestration privilege escalation.
- Project emphasis: pay extra attention to PowerShell collectors, Python tooling, and GitHub Actions/YAML. For PowerShell inspect Invoke-Expression, Start-Process, Invoke-WebRequest/Invoke-RestMethod, Expand-Archive, Set-Content/Out-File/Copy-Item, Remove-Item, and Set-Acl. For Python inspect subprocess shell usage, unsafe deserialization, archive extraction, request-controlled paths, raw query construction, and secret/env persistence. For GitHub Actions/YAML inspect privileged PR triggers, checkout of untrusted refs, secret/token forwarding, broad permissions, and untrusted event metadata in shell commands.
""".strip()
    validation_hints = validation_hint_block(files)
    if validation_hints:
        hardening = f"{hardening}\n\n{validation_hints}"
    if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
        hardening = f"{hardening}\n\n{risk_sentinel_block(risk_sentinels, config)}"
    separator = "\n\n"
    truncation_marker = "\n\n[context truncated by reviewer]"
    prompt_budget = max(0, config.max_prompt_chars - len(hardening) - len(separator))
    base_budget = max(0, prompt_budget - len(truncation_marker))
    prompt_config = copy.copy(config)
    prompt_config.max_prompt_chars = base_budget
    prompt = base.build_prompt(pr, files, diff, prompt_config)
    combined = f"{hardening}{separator}{prompt}"
    if len(combined) > config.max_prompt_chars:
        retained_chars = max(0, config.max_prompt_chars - len(truncation_marker))
        combined = combined[:retained_chars] + truncation_marker
    return base.sanitize_text(combined, config)


def raw_findings_digest(result: dict[str, Any]) -> str:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return "findings field was not a list"
    details: list[str] = []
    for item in raw_findings[:6]:
        if not isinstance(item, dict):
            details.append("invalid finding shape")
            continue
        raw_path = item.get("path")
        raw_line = item.get("line")
        raw_title = item.get("title")
        path = str(raw_path).strip() if raw_path else "<missing-path>"
        line = str(raw_line).strip() if raw_line else "<missing-line>"
        title = (str(raw_title).strip() if raw_title else "untitled")[:80]
        try:
            confidence = float(item.get("confidence", 0))
            confidence_text = f"{confidence:.2f}"
        except (TypeError, ValueError):
            confidence_text = "invalid"
        details.append(f"{path}:{line} confidence {confidence_text} ({title})")
    return "; ".join(details) if details else "no structured findings"


def finding_text_for_quality(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title", "") or ""),
        str(item.get("body", "") or ""),
        str(item.get("validation", "") or ""),
    ]
    return re.sub(r"\s+", " ", "\n".join(parts)).strip()


def non_actionable_finding_reason(item: dict[str, Any]) -> str:
    text = finding_text_for_quality(item)
    if not text:
        return ""
    for pattern, reason in NON_ACTIONABLE_FINDING_PATTERNS:
        if pattern.search(text):
            return reason
    return ""


def non_actionable_findings_digest(result: dict[str, Any], config: Any) -> str:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return ""
    details: list[str] = []
    for item in raw_findings[:6]:
        if not isinstance(item, dict):
            continue
        reason = non_actionable_finding_reason(item)
        if not reason:
            continue
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < config.minimum_confidence:
            continue
        raw_path = item.get("path")
        raw_line = item.get("line")
        raw_title = item.get("title")
        path = str(raw_path).strip() if raw_path else "<missing-path>"
        line = str(raw_line).strip() if raw_line else "<missing-line>"
        title = (str(raw_title).strip() if raw_title else "untitled")[:80]
        details.append(f"{path}:{line} {reason} ({title})")
    return "; ".join(details)



def has_minimum_confidence_finding(result: dict[str, Any], config: Any) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        try:
            if float(item.get("confidence", 0)) >= config.minimum_confidence:
                return True
        except (TypeError, ValueError):
            continue
    return False



def has_actionable_minimum_confidence_finding(result: dict[str, Any], config: Any) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict) or non_actionable_finding_reason(item):
            continue
        try:
            if float(item.get("confidence", 0)) >= config.minimum_confidence:
                return True
        except (TypeError, ValueError):
            continue
    return False

def has_actionable_changed_line_finding(
    result: dict[str, Any],
    config: Any,
    line_index: dict[tuple[str, int], int],
) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict) or non_actionable_finding_reason(item):
            continue
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", "")).strip()
        except (TypeError, ValueError):
            continue
        if confidence >= config.minimum_confidence and (path, line) in line_index:
            return True
    return False


def review_quality_retry_reason(
    result: dict[str, Any],
    config: Any,
    risk_sentinels: list[RiskSentinel],
    line_index: dict[tuple[str, int], int] | None = None,
) -> str:
    gated_sentinels = required_risk_sentinels(risk_sentinels)
    if (
        gated_sentinels
        and getattr(config, "risk_sentinel_quality_gate", True)
        and getattr(config, "risk_sentinel_retry_on_empty", True)
        and has_no_structured_findings(result)
    ):
        return "model returned zero findings despite high-risk changed-line signals"

    if not getattr(config, "review_quality_retry_on_rejected_output", True):
        return ""

    summary = str(result.get("summary", "")).strip()
    if has_no_structured_findings(result):
        if getattr(config, "fail_on_summary_only_problem", True) and summary_suggests_problem(summary):
            return "model summary indicated a possible issue while the structured findings array was empty"
        return ""

    raw_findings = result.get("findings", [])
    if raw_findings and getattr(config, "fail_on_unanchored_findings", True):
        non_actionable_details = non_actionable_findings_digest(result, config)
        if non_actionable_details and not has_actionable_minimum_confidence_finding(result, config):
            return (
                "model returned only self-described non-actionable or informational findings: "
                f"{non_actionable_details}"
            )
        if not has_minimum_confidence_finding(result, config):
            return (
                "model returned structured findings, but none met the configured minimum confidence "
                f"{config.minimum_confidence:.2f}: {raw_findings_digest(result)}"
            )
        if line_index is not None and not has_actionable_changed_line_finding(result, config, line_index):
            return (
                "model returned high-confidence structured findings, but none were anchored to changed diff lines: "
                f"{raw_findings_digest(result)}"
            )
        if (
            gated_sentinels
            and line_index is not None
            and getattr(config, "risk_sentinel_quality_gate", True)
        ):
            try:
                findings, unanchored_findings = split_findings(result, config, line_index)
            except ReviewQualityError:
                findings, unanchored_findings = [], []
            uncovered = uncovered_risk_sentinels(findings, gated_sentinels, config, unanchored_findings)
            if uncovered:
                return (
                    "model returned actionable findings, but they did not cover high-risk changed-line signals: "
                    f"{risk_sentinel_coverage_digest(uncovered)}"
                )

    return ""


def build_quality_retry_prompt(
    prompt: str,
    previous_result: dict[str, Any],
    risk_sentinels: list[RiskSentinel],
    config: Any,
    quality_issue: str | None = None,
) -> str:
    previous_summary = str(previous_result.get("summary", "")).strip() or "No previous summary returned."
    raw_findings = previous_result.get("findings", [])
    try:
        previous_findings = json.dumps(raw_findings[:6] if isinstance(raw_findings, list) else raw_findings, ensure_ascii=False, indent=2)
    except TypeError:
        previous_findings = str(raw_findings)
    if len(previous_findings) > 1800:
        previous_findings = f"{previous_findings[:1770]}... [truncated]"
    issue_line = quality_issue or "the previous response did not clear review-quality checks"
    anchor_block = risk_sentinel_block(risk_sentinels, config) if risk_sentinels else "No high-risk changed-line anchors were detected."
    retry_guidance = f"""
Review quality retry:
The previous response failed review-quality checks: {issue_line}.
Re-review the changed diff and return one of two valid outputs:
- Actionable findings anchored to changed right-side file/line entries with confidence at or above {config.minimum_confidence:.2f}, covering every high-risk anchor by path, nearby line, and risk class; or
- An empty findings array with a clean summary that does not imply a remaining issue.
Return the full corrected finding set. Preserve previous real actionable findings while adding or repairing missing anchor coverage; do not narrow the retry response to only the uncovered anchor.
Do not place actionable concerns only in the summary. Do not return low-confidence, unanchored, or speculative findings.
Do not return informational/advisory findings that explain there is no realized risk; use a clean summary for those.
Do not satisfy a high-risk anchor with an unrelated finding on another risk class.
If a previous finding was real but poorly anchored or below confidence threshold, convert it into a valid finding with exact file, changed line, observed behavior, impact, correction guidance, and validation/readback guidance.

{anchor_block}

Previous summary:
{previous_summary}

Previous structured findings:
{previous_findings}
""".strip()
    return append_with_budget(prompt, base.sanitize_text(retry_guidance, config), config.max_prompt_chars)


def has_no_structured_findings(result: dict[str, Any]) -> bool:
    findings = result.get("findings", [])
    return not isinstance(findings, list) or len(findings) == 0


def build_openrouter_payload(prompt: str, schema: dict[str, Any], config: Any, ignored_providers: list[str], model: str) -> dict[str, Any]:
    provider: dict[str, Any] = {"allow_fallbacks": True, "require_parameters": True}
    clean_ignored = [item for item in ignored_providers if item]
    if clean_ignored:
        provider["ignore"] = clean_ignored

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": base.read_text("prompts/openrouter-pr-review-system.md")},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "openrouter_pr_review", "strict": True, "schema": schema},
        },
        "provider": provider,
        "temperature": 0.2,
    }

    fallbacks = getattr(config, "fallback_models", [])
    if fallbacks:
        payload["models"] = [model, *fallbacks]
    route = getattr(config, "openrouter_route", "")
    if route:
        payload["route"] = route
    service_tier = getattr(config, "openrouter_service_tier", "")
    if service_tier:
        payload["service_tier"] = service_tier
    sticky_session = session_id(config)
    if sticky_session:
        payload["session_id"] = sticky_session

    if model == "openrouter/auto":
        plugin: dict[str, Any] = {"id": "auto-router"}
        allowed_models = getattr(config, "auto_allowed_models", [])
        if allowed_models:
            plugin["allowed_models"] = allowed_models
        tradeoff = getattr(config, "auto_cost_quality_tradeoff", None)
        if tradeoff is not None:
            plugin["cost_quality_tradeoff"] = tradeoff
        payload["plugins"] = [plugin]

    return payload


def openrouter_request_once(
    prompt: str,
    schema: dict[str, Any],
    config: Any,
    ignored_providers: list[str],
    model: str,
) -> tuple[dict[str, Any], str, str]:
    api_key = base.env_required("OPENROUTER_API_KEY")
    payload = build_openrouter_payload(prompt, schema, config, ignored_providers, model)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DCOIR-Collector/dcoir-collector",
        "X-OpenRouter-Title": base.REVIEW_DISPLAY_NAME,
    }
    sticky_session = session_id(config)
    if sticky_session:
        headers["X-Session-Id"] = sticky_session

    req = urllib.request.Request(OPENROUTER_API, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    model_used = str(data.get("model", model))
    service_tier = str(data.get("service_tier", "") or "")
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("OpenRouter returned an empty response")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(1))
    return parsed, model_used, service_tier


def openrouter_review(prompt: str, schema: dict[str, Any], config: Any, reporter: Any | None = None) -> tuple[dict[str, Any], str, str]:
    attempts = max(1, config.openrouter_max_attempts)
    retry_cap = max(1, config.openrouter_retry_max_seconds)
    last_error = "OpenRouter request failed"

    for model_index, model in enumerate(config.model_stack, start=1):
        ignored_providers = [base.provider_slug(item) for item in config.ignored_providers]
        if reporter:
            fallback_note = f"; native fallbacks={len(getattr(config, 'fallback_models', []))}"
            reporter.update("openrouter", f"calling model {model_index}/{len(config.model_stack)}: {model}{fallback_note}")
        for attempt in range(1, attempts + 1):
            try:
                if reporter:
                    reporter.update("openrouter-attempt", f"model={model}; attempt={attempt}/{attempts}")
                result, model_used, service_tier = openrouter_request_once(prompt, schema, config, ignored_providers, model)
                if reporter:
                    tier_note = f"; service_tier={service_tier}" if service_tier else ""
                    reporter.update("openrouter-result", f"served model={model_used}{tier_note}")
                return result, model_used, service_tier
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                parsed_error = base.parse_openrouter_error(detail)
                provider = base.provider_slug(str(parsed_error.get("provider", "")))
                if provider and provider not in ignored_providers:
                    ignored_providers.append(provider)
                retry_after = parsed_error.get("retry_after")
                try:
                    delay = float(retry_after) if retry_after is not None else float(exc.headers.get("Retry-After", ""))
                except (TypeError, ValueError):
                    delay = min(2**attempt, retry_cap)
                delay = min(max(delay, 1.0), float(retry_cap))
                last_error = f"OpenRouter API failed with HTTP {exc.code}: {parsed_error.get('message', 'request failed')}"
                if provider:
                    last_error += f" Provider skipped for retry: {provider}."
                retryable = exc.code in {408, 409, 425, 429, 500, 502, 503, 504}
                if retryable and attempt < attempts:
                    if reporter:
                        reporter.update("openrouter-retry", f"{last_error} retrying in {delay:.0f}s")
                    time.sleep(delay)
                    continue
                break
            except RuntimeError as exc:
                last_error = str(exc)
                if "empty response" in last_error.lower() and attempt < attempts:
                    delay = min(2**attempt, retry_cap)
                    if reporter:
                        reporter.update("openrouter-retry", f"{last_error}; retrying in {delay:.0f}s")
                    time.sleep(delay)
                    continue
                break
            except json.JSONDecodeError:
                last_error = "OpenRouter returned invalid JSON"
                if attempt < attempts:
                    delay = min(2**attempt, retry_cap)
                    if reporter:
                        reporter.update("openrouter-retry", f"{last_error}; retrying in {delay:.0f}s")
                    time.sleep(delay)
                    continue
                break
        if model_index < len(config.model_stack) and reporter:
            reporter.update("openrouter-fallback", f"model {model} failed; trying next configured model")

    raise RuntimeError(last_error)


def write_debug_text_artifact_safely(config: Any, name: str, text: str) -> None:
    writer = getattr(base, "write_debug_text_artifact", None)
    if writer is None:
        return
    try:
        writer(config, name, text)
    except Exception as exc:
        print(f"WARN: unable to write debug text artifact {name}: {exc}", file=sys.stderr, flush=True)


def write_debug_json_artifact_safely(config: Any, name: str, data: Any) -> None:
    writer = getattr(base, "write_debug_json_artifact", None)
    if writer is None:
        return
    try:
        writer(config, name, data)
    except Exception as exc:
        print(f"WARN: unable to write debug JSON artifact {name}: {exc}", file=sys.stderr, flush=True)


def finding_merge_bucket(finding: dict[str, Any]) -> str:
    text = normalized_quality_text(
        "\n".join(
            [
                str(finding.get("title", "") or ""),
                str(finding.get("body", "") or ""),
                str(finding.get("validation", "") or ""),
            ]
        )
    )
    buckets: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("deserialization", ("pickle", "deserial", "yaml.load", "objectinputstream", "binaryformatter")),
        ("command-execution", ("command injection", "command execution", "shell", "subprocess", "exec", "spawn", "start-process")),
        ("dynamic-code", ("eval", "new function", "dynamic code", "invoke-expression")),
        ("sql", ("sql", "query", "interpolation", "parameter")),
        ("path-write", ("path traversal", "file write", "writefile", "root containment", "arbitrary overwrite")),
        ("archive-extract", ("archive", "extract", "tar", "unpack", "zip slip")),
        ("ssrf-outbound", ("ssrf", "outbound", "callback", "webhook", "urlopen", "invoke-webrequest", "fetch")),
        ("secret-token", ("secret", "token", "authorization", "credential", "exfil")),
        ("workflow-privilege", ("pull_request_target", "workflow", "privileged", "untrusted", "github token")),
        ("acl-permission", ("acl", "permission", "everyone", "fullcontrol")),
        ("kubernetes-privilege", ("kubernetes", "privileged", "hostpath", "hostnetwork", "runasuser")),
        ("delete", ("recursive delete", "rmtree", "remove-item", "deletion")),
        ("logic", ("truthy", "always true", "bypass")),
    )
    for bucket, terms in buckets:
        if any(term in text for term in terms):
            return bucket
    title = normalized_quality_text(str(finding.get("title", "") or ""))
    return title[:80] or "unknown"


def finding_merge_key(finding: dict[str, Any]) -> tuple[str, int, str]:
    path = str(finding.get("path", "") or "").strip()
    try:
        line = int(finding.get("line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    return (path, line, finding_merge_bucket(finding))


def severity_rank(severity: Any) -> int:
    return {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }.get(str(severity or "").strip().lower(), 0)


def finding_quality_score(finding: dict[str, Any]) -> tuple[int, float, int]:
    try:
        confidence = float(finding.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    body_length = len(str(finding.get("body", "") or ""))
    validation_length = len(str(finding.get("validation", "") or ""))
    return (severity_rank(finding.get("severity")), confidence, body_length + validation_length)


def result_findings(result: dict[str, Any]) -> list[dict[str, Any]]:
    raw_findings = result.get("findings", []) if isinstance(result, dict) else []
    if not isinstance(raw_findings, list):
        return []
    return [dict(item) for item in raw_findings if isinstance(item, dict)]


def merge_review_results(initial_result: dict[str, Any], retry_result: dict[str, Any]) -> dict[str, Any]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str, int, str], int] = {}
    for source_result in (initial_result, retry_result):
        for finding in result_findings(source_result):
            key = finding_merge_key(finding)
            if key in index_by_key:
                existing_index = index_by_key[key]
                if finding_quality_score(finding) >= finding_quality_score(merged[existing_index]):
                    merged[existing_index] = finding
                continue
            index_by_key[key] = len(merged)
            merged.append(finding)

    retry_summary = str(retry_result.get("summary", "") if isinstance(retry_result, dict) else "").strip()
    initial_summary = str(initial_result.get("summary", "") if isinstance(initial_result, dict) else "").strip()
    summary = retry_summary or initial_summary
    if initial_summary and retry_summary and normalized_quality_text(initial_summary) != normalized_quality_text(retry_summary):
        summary = (
            f"{retry_summary}\n\n"
            "The review result also preserves distinct actionable findings returned by the first pass when they "
            "remain anchored to changed code."
        )
    return {"summary": summary, "findings": merged}


def openrouter_review_with_quality_retry(
    prompt: str,
    schema: dict[str, Any],
    config: Any,
    reporter: Any | None,
    risk_sentinels: list[RiskSentinel],
    line_index: dict[tuple[str, int], int] | None = None,
) -> tuple[dict[str, Any], str, str]:
    write_debug_text_artifact_safely(config, "prompts/01-initial-prompt.txt", prompt)
    write_debug_json_artifact_safely(
        config,
        "metadata/01-initial-request.json",
        {
            "prompt_chars": len(prompt),
            "risk_sentinel_count": len(risk_sentinels),
            "risk_sentinel_digest": risk_sentinel_digest(risk_sentinels) if risk_sentinels else "",
            "line_index_entries": len(line_index or {}),
        },
    )
    result, model_used, service_tier = openrouter_review(prompt, schema, config, reporter)
    write_debug_json_artifact_safely(
        config,
        "responses/01-initial-result.json",
        {"model_used": model_used, "service_tier": service_tier, "result": result},
    )
    initial_result = result
    retry_reason = review_quality_retry_reason(result, config, risk_sentinels, line_index)
    if retry_reason:
        if reporter:
            safe_reason = sanitize_github_output(retry_reason, config)
            reporter.update("quality-retry", f"{safe_reason}; retrying with stricter actionable-output guidance")
        retry_sentinels = required_risk_sentinels(risk_sentinels) or risk_sentinels
        retry_prompt = build_quality_retry_prompt(prompt, result, retry_sentinels, config, retry_reason)
        write_debug_text_artifact_safely(config, "prompts/02-quality-retry-prompt.txt", retry_prompt)
        write_debug_json_artifact_safely(
            config,
            "metadata/02-quality-retry-request.json",
            {
                "retry_reason": retry_reason,
                "prompt_chars": len(retry_prompt),
                "risk_sentinel_count": len(retry_sentinels),
                "risk_sentinel_digest": risk_sentinel_digest(retry_sentinels) if retry_sentinels else "",
            },
        )
        result, model_used, service_tier = openrouter_review(retry_prompt, schema, config, reporter)
        write_debug_json_artifact_safely(
            config,
            "responses/02-quality-retry-result.json",
            {"model_used": model_used, "service_tier": service_tier, "result": result},
        )
        merged_result = merge_review_results(initial_result=initial_result, retry_result=result)
        write_debug_json_artifact_safely(
            config,
            "responses/03-quality-retry-merged-result.json",
            {
                "model_used": model_used,
                "service_tier": service_tier,
                "initial_finding_count": len(result_findings(initial_result)),
                "retry_finding_count": len(result_findings(result)),
                "merged_finding_count": len(result_findings(merged_result)),
                "result": merged_result,
            },
        )
        result = merged_result
    return result, model_used, service_tier


def summary_suggests_problem(summary: str) -> bool:
    positive_terms = (
        "finding",
        "issue",
        "problem",
        "regression",
        "risk",
        "bypass",
        "unsafe",
        "missing",
        "misleading",
        "failure",
        "should",
        "must",
        "breaks",
    )
    negative_phrases = (
        "nothing actionable",
        "no high confidence inline findings were found",
        "no high confidence findings were found",
        "no high confidence inline findings",
        "no high confidence findings",
        "no high signal findings",
        "no high confidence",
        "no high signal",
        "no actionable",
        "no findings",
        "no problems",
        "no issues",
        "no issue",
        "looks good",
        "clean review",
    )
    problem_noun_pattern = r"(?:findings?|issues?|problems?|regressions?|risks?|failures?|bypasses?)"
    remaining_problem_noun_pattern = r"(?:issues?|problems?|regressions?|risks?|failures?|bypasses?)"
    modified_problem_noun_pattern = rf"(?:[a-z0-9-]+\s+){{0,4}}{problem_noun_pattern}"
    clean_two_item_problem_noun_pattern = (
        rf"(?!(?:a|an|the|this|that|these|those)\b)"
        rf"(?:[a-z0-9-]+\s+){{0,4}}{problem_noun_pattern}"
    )
    clean_two_item_remaining_noun_pattern = (
        rf"(?!(?:a|an|the|this|that|these|those)\b)"
        rf"(?:[a-z0-9-]+\s+){{1,4}}{remaining_problem_noun_pattern}"
    )
    clean_two_item_following_remaining_noun_pattern = (
        rf"(?!(?:a|an|the|this|that|these|those)\b)"
        rf"(?:[a-z0-9-]+\s+){{0,4}}{remaining_problem_noun_pattern}"
    )
    clean_two_item_result_verb_pattern = r"(?:(?:were|was|are|is)\s+)?(?:found|identified|detected|observed)"
    negated_list_patterns = (
        rf"\bno\b\s+{clean_two_item_problem_noun_pattern}"
        rf"\s+(?:and|or)\s+{clean_two_item_problem_noun_pattern}"
        rf"\s+{clean_two_item_result_verb_pattern}",
        rf"\bno\b\s+{clean_two_item_problem_noun_pattern}"
        rf"\s+or\s+{clean_two_item_problem_noun_pattern}"
        r"\s+(?:present|remaining|remain)",
        rf"\bno\b\s+{clean_two_item_remaining_noun_pattern}"
        rf"\s+and\s+{clean_two_item_following_remaining_noun_pattern}"
        r"\s+(?:present|remaining|remain)",
        rf"\bno\b\s+{modified_problem_noun_pattern}"
        rf"(?:,\s*(?!\b(?:and|or)\b){modified_problem_noun_pattern})+"
        rf"(?:,\s*|\s+)(?:and|or)\s+{modified_problem_noun_pattern}"
        r"(?:\s+(?:were|was|are|is|found|identified|detected|observed|present|remaining|remain))*",
        rf"\bno\b\s+{modified_problem_noun_pattern}"
        rf"(?:,\s*(?!\b(?:and|or)\b){modified_problem_noun_pattern})*"
        rf",\s*(?:and|or)\s+{modified_problem_noun_pattern}"
        r"(?:\s+(?:were|was|are|is|found|identified|detected|observed|present|remaining|remain))*",
    )
    negated_problem_patterns = (
        *negated_list_patterns,
        r"\bno\b(?:\s+[a-z0-9]+){0,8}\s+(?:findings?|issues?|problems?|regressions?|risks?|failures?|bypasses?)\b"
        r"(?:\s+(?:were|was|are|is|found|identified|detected|observed|present|remaining|remain))*",
        r"\bnot\b(?:\s+[a-z0-9]+){0,5}\s+(?:found|identified|detected|observed)\b",
    )

    def clause_suggests_problem(clause: str) -> bool:
        stripped = re.sub(r"[^a-z0-9]+", " ", clause.lower()).strip()
        for pattern in negated_problem_patterns:
            stripped = re.sub(pattern, " ", stripped)
        for phrase in negative_phrases:
            stripped = stripped.replace(phrase, " ")
        return any(re.search(rf"\b{re.escape(term)}s?\b", stripped) for term in positive_terms)

    cleaned_summary = summary.lower()
    for pattern in negated_list_patterns:
        cleaned_summary = re.sub(pattern, " ", cleaned_summary)
    clauses = re.split(r"(?:[.;:!?]+|,\s+|\b(?:and|but|however|though|although|yet|except|nevertheless|still)\b)", cleaned_summary)
    return any(clause_suggests_problem(clause.strip()) for clause in clauses if clause.strip())


def finding_location_text(path: str, line: int) -> str:
    path_text = path if path else "<missing-path>"
    line_text = str(line) if line else "<missing-line>"
    return f"{path_text}:{line_text}"


def normalize_findings(result: dict[str, Any], config: Any, line_index: dict[tuple[str, int], int]) -> list[dict[str, Any]]:
    findings, _unanchored_findings = split_findings(result, config, line_index)
    return findings


def severity_sort_key(finding: dict[str, Any]) -> tuple[int, float]:
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    try:
        confidence = float(finding.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0
    return severity_order.get(str(finding.get("severity", "low")).lower(), 9), -confidence


def is_github_actions_yaml_path(path: str) -> bool:
    lower_path = path.lower()
    suffix = Path(lower_path).suffix
    if suffix not in {".yml", ".yaml"}:
        return False
    name = Path(lower_path).name
    return (
        lower_path.startswith(".github/workflows/")
        or "workflow" in name
        or "github" in lower_path
        or "actions" in lower_path
    )


def is_required_review_target_path(path: str) -> bool:
    suffix = Path(path.lower()).suffix
    if suffix in PROJECT_TARGET_RISK_SENTINEL_EXTENSIONS:
        return True
    return is_github_actions_yaml_path(path)


def is_required_review_target_finding(finding: dict[str, Any]) -> bool:
    path = str(finding.get("path", "") or "").strip()
    if is_required_review_target_path(path):
        return True
    text = normalized_quality_text(
        "\n".join(
            [
                str(finding.get("title", "") or ""),
                str(finding.get("body", "") or ""),
                str(finding.get("validation", "") or ""),
            ]
        )
    )
    required_terms = (
        "powershell",
        "python",
        "github actions",
        "pull_request_target",
        "github.event.pull_request",
        "github_token",
        "ci token",
    )
    return any(term in text for term in required_terms)


def select_findings_for_inline(findings: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    required = [finding for finding in findings if is_required_review_target_finding(finding)]
    optional = [finding for finding in findings if not is_required_review_target_finding(finding)]
    required.sort(key=severity_sort_key)
    optional.sort(key=severity_sort_key)
    return [*required, *optional][:limit]


def split_findings(
    result: dict[str, Any],
    config: Any,
    line_index: dict[tuple[str, int], int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    unanchored_findings: list[dict[str, Any]] = []
    rejected: list[str] = []
    raw_findings = result.get("findings", [])
    changed_paths = {path for path, _line in line_index}
    for item in raw_findings:
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", "")).strip()
        except (AttributeError, TypeError, ValueError):
            rejected.append("invalid finding shape")
            continue
        title = str(item.get("title", "untitled")).strip()[:80]
        if confidence < config.minimum_confidence:
            location_text = finding_location_text(path, line)
            rejected.append(f"{location_text} low confidence {confidence:.2f} ({title})")
            continue
        non_actionable_reason = non_actionable_finding_reason(item)
        if non_actionable_reason:
            location_text = finding_location_text(path, line)
            rejected.append(f"{location_text} non-actionable ({non_actionable_reason}; {title})")
            continue
        if (path, line) not in line_index:
            if path and path in changed_paths:
                unanchored = dict(item)
                unanchored["_unanchored_reason"] = f"{path}:{line} is in a changed file but not an added changed line"
                unanchored_findings.append(unanchored)
                continue
            location_text = finding_location_text(path, line)
            rejected.append(f"{location_text} not in changed diff ({title})")
            continue
        findings.append(item)

    findings = select_findings_for_inline(findings, int(config.max_inline_comments))
    unanchored_findings = select_findings_for_inline(unanchored_findings, int(config.max_inline_comments))
    if findings or unanchored_findings:
        return findings, unanchored_findings

    if raw_findings and getattr(config, "fail_on_unanchored_findings", True):
        details = "; ".join(rejected[:6]) if rejected else "no accepted findings"
        raise ReviewQualityError(
            f"{base.REVIEW_DISPLAY_NAME} quality failure: the model returned findings, but none became actionable inline comments. "
            f"Rejected findings: {details}."
        )

    summary = str(result.get("summary", "")).strip()
    if getattr(config, "fail_on_summary_only_problem", True) and summary_suggests_problem(summary):
        raise ReviewQualityError(
            f"{base.REVIEW_DISPLAY_NAME} quality failure: the model summary indicated a possible issue, but the structured findings "
            "array was empty. The review must produce actionable file/line findings or a clean summary."
        )

    return [], []


def enforce_risk_sentinel_findings(
    findings: list[dict[str, Any]],
    risk_sentinels: list[RiskSentinel],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> None:
    if not risk_sentinels or not getattr(config, "risk_sentinel_quality_gate", True):
        return
    uncovered = uncovered_risk_sentinels(findings, risk_sentinels, config, unanchored_findings)
    if not uncovered:
        return
    raise ReviewQualityError(
        f"{base.REVIEW_DISPLAY_NAME} quality failure: the changed diff contained high-risk changed-line signals, but the model "
        "did not produce actionable findings covering those signals after quality retry. Uncovered signals: "
        f"{risk_sentinel_coverage_digest(uncovered)}."
    )


def format_unanchored_finding(finding: dict[str, Any], model_used: str, config: Any) -> str:
    title = sanitize_github_output(str(finding.get("title", "Finding")).strip(), config)
    severity = str(finding.get("severity", "medium")).upper()
    path = sanitize_github_output(str(finding.get("path", "<missing-path>")).strip(), config)
    line = sanitize_github_output(str(finding.get("line", "<missing-line>")).strip(), config)
    body = sanitize_github_output(str(finding.get("body", "")).strip(), config)
    validation = sanitize_github_output(base.validation_text_for_finding(finding), config)
    reason = sanitize_github_output(str(finding.get("_unanchored_reason", "not anchored to an added changed line")), config)
    try:
        confidence = float(finding.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0
    parts = [
        f"**{severity}: {title}**",
        f"- Location: `{path}:{line}`.",
        f"- Inline anchor: {reason}.",
        f"- Confidence: `{confidence:.2f}`.",
    ]
    if body:
        parts.extend(["", body])
    if validation:
        parts.extend(["", "Validation expected after fix:", "", "```text", validation, "```"])
    parts.extend(["", f"<sub>{base.REVIEW_DISPLAY_NAME}</sub>"])
    return "\n".join(parts)


def build_review_body_with_unanchored(
    result: dict[str, Any],
    findings: list[dict[str, Any]],
    unanchored_findings: list[dict[str, Any]],
    model_used: str,
    config: Any,
    reviewed_commit: str = "",
) -> str:
    if not unanchored_findings:
        return base.build_review_body(result, findings, model_used, config, reviewed_commit)
    summary = sanitize_github_output(str(result.get("summary", f"{base.REVIEW_DISPLAY_NAME} completed.")).strip(), config)
    inline_plural = "finding" if len(findings) == 1 else "findings"
    body_plural = "finding" if len(unanchored_findings) == 1 else "findings"
    formatted_unanchored = "\n\n".join(
        format_unanchored_finding(finding, model_used, config) for finding in unanchored_findings
    )
    result_line = (
        f"Review posted with `{len(findings)}` inline {inline_plural} and "
        f"`{len(unanchored_findings)}` unanchored review-body {body_plural}."
    )
    lines = [
        base.MARKER,
        f"💡 {base.REVIEW_DISPLAY_NAME}",
        "Here are some review suggestions for this pull request.",
        "",
        f"Reviewed commit: `{base.short_commit(reviewed_commit)}`",
    ]
    if summary and getattr(config, "post_summary_when_findings", False):
        lines.extend(["", summary])
    lines.extend(
        [
            "",
            f"Result: {result_line}",
            "",
            "Unanchored findings:",
            "",
            formatted_unanchored,
        ]
    )
    return base.github_safe_body(
        "\n".join(lines).strip(),
        limit=12000,
    )


def remove_eyes_reaction(gh: Any, trigger_comment_id: int, reaction_id: int, status: dict[str, str]) -> None:
    if not reaction_id:
        status["removed"] = "not attempted; no eyes reaction id was recorded"
        return
    try:
        gh.delete_issue_comment_reaction(trigger_comment_id, reaction_id)
        status["removed"] = "success"
    except Exception as exc:
        status["removed"] = f"failed: {str(exc)[:500]}"


def main() -> None:
    repo = base.env_required("GITHUB_REPOSITORY")
    pr_number = int(base.env_required("PR_NUMBER"))
    token = base.env_required("GITHUB_TOKEN")
    trigger_comment_id = int(base.env_required("TRIGGER_COMMENT_ID"))
    comment_body = os.environ.get("TRIGGER_COMMENT_BODY", "")
    author = os.environ.get("TRIGGER_AUTHOR", "")
    config_path = os.environ.get("OPENROUTER_REVIEW_CONFIG", ".github/openrouter-pr-review-governed.yml")
    config = load_hardened_config(config_path)

    if author in config.ignored_authors:
        print(f"Ignoring denied author {author}")
        return
    if config.allowed_authors and author not in config.allowed_authors:
        print(f"Ignoring unauthorized author {author}")
        return
    command = matching_command(comment_body, config.commands)
    if not command:
        print("Comment does not match configured review commands")
        return
    if hasattr(base, "apply_debug_flag"):
        base.apply_debug_flag(config, comment_body, command)

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise ReviewTimeoutError(f"{base.REVIEW_DISPLAY_NAME} exceeded script timeout of {config.script_timeout_seconds} seconds")

    schema = json.loads(base.read_text("schemas/openrouter-pr-review.schema.json"))
    gh = base.GitHubClient(token, repo)
    reporter = ProgressReporter(gh, pr_number, command, config)
    reaction_id = 0
    reaction_status = {"added": "not attempted", "removed": "not attempted"}

    try:
        reaction = gh.create_issue_comment_reaction(trigger_comment_id, "eyes")
        reaction_id = int(reaction.get("id", 0))
        reaction_status["added"] = f"success id={reaction_id}" if reaction_id else "success without returned id"
    except Exception as exc:
        reaction_status["added"] = f"failed: {str(exc)[:500]}"
        print(f"WARN: unable to add eyes reaction: {exc}", file=sys.stderr, flush=True)

    try:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.script_timeout_seconds)
        base.env_required("OPENROUTER_API_KEY")
        reporter.start()
        reporter.update("reaction", f"eyes add: {reaction_status['added']}")
        reporter.update("github", "fetching PR metadata")
        pr = gh.get_pr(pr_number)
        reporter.update("github", "fetching PR diff")
        diff = gh.get_pr_diff(pr_number)
        reporter.update("github", "fetching changed file list")
        files = gh.list_files(pr_number)
        risk_sentinels = detect_risk_sentinels(diff, getattr(config, "risk_sentinel_max_anchors", 12))
        if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
            reporter.update("risk-sentinel", f"detected {len(risk_sentinels)} high-risk changed-line signals: {risk_sentinel_digest(risk_sentinels)}")
        reporter.update("prompt", f"building bounded prompt from {len(files)} changed files")
        prompt = build_prompt(pr, files, diff, config, risk_sentinels)
        line_index = build_added_line_index(diff)
        result, model_used, service_tier = openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels, line_index)
        reporter.update("normalize", "mapping model findings to changed diff lines")
        findings, unanchored_findings = split_findings(result, config, line_index)
        findings = add_risk_sentinel_fallback_findings(findings, risk_sentinels, config, unanchored_findings)
        enforce_risk_sentinel_findings(findings, risk_sentinels, config, unanchored_findings)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        reviewed_commit = str(pr.get("head", {}).get("sha", "") or "")
        review_body = build_review_body_with_unanchored(result, findings, unanchored_findings, model_used, config, reviewed_commit)
        unanchored_note = f" and {len(unanchored_findings)} unanchored review-body findings" if unanchored_findings else ""
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments{unanchored_note}")
        gh.create_review(pr_number, review_body, event, comments, reviewed_commit)
        remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        tier_note = f"; service_tier={service_tier}" if service_tier else ""
        reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        reporter.complete(f"{model_used}{tier_note}", len(comments), event)
    except Exception as exc:
        remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        try:
            reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        except Exception as reporter_exc:
            print(f"WARN: unable to update reaction status: {reporter_exc}", file=sys.stderr, flush=True)
        safe_error = sanitize_github_output(str(exc), config)
        reporter.fail(safe_error)
        raise
    finally:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)


if __name__ == "__main__":
    main()
