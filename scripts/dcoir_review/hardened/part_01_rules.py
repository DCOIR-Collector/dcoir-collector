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



