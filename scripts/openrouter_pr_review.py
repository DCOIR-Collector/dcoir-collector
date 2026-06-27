#!/usr/bin/env python3
"""Summoned DCOIR PR reviewer for GitHub Actions.

This script is intentionally dependency-free. It reads a PR diff through the
GitHub API, asks OpenRouter for structured findings, and posts a GitHub PR
review with inline suggestion blocks when safe. It never pushes commits and it
never checks out or executes untrusted PR code.
"""

from __future__ import annotations

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

GITHUB_API = "https://api.github.com"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
MARKER = "<!-- dcoir-review -->"
LEGACY_MARKERS = ("<!-- openrouter-pr-review -->",)
REVIEW_DISPLAY_NAME = "DCOIR Review"
DEBUG_ARTIFACT_DIR_ENV = "DCOIR_REVIEW_DEBUG_ARTIFACT_DIR"
DEBUG_ARTIFACT_DEFAULT_DIR = "dcoir-review-debug"
DEBUG_ARTIFACT_MAX_CHARS = 250_000
DEBUG_ARTIFACT_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.\-/]+$")
PUBLIC_IDENTITY_REPLACEMENTS = (
    ("OPENROUTER_API_KEY", "REVIEW_PROVIDER_API_KEY"),
    ("OPENROUTER_REVIEW_CONFIG", "REVIEW_PROVIDER_CONFIG"),
    ("OPENROUTER_", "REVIEW_PROVIDER_"),
    ("OpenRouter PR Review", REVIEW_DISPLAY_NAME),
    ("OpenRouter PR review", REVIEW_DISPLAY_NAME),
    ("OpenRouter Review", REVIEW_DISPLAY_NAME),
    ("OpenRouter review", REVIEW_DISPLAY_NAME),
    ("OpenRouter", "review provider"),
    ("openrouter_key", "review_provider_key"),
    ("openrouter-pr-review", "dcoir-review"),
    ("openrouter-review", "dcoir-review"),
    ("openrouter/", "provider/"),
    ("openrouter:", "provider:"),
    ("openrouter-", "provider-"),
    ("openrouter_", "provider_"),
    ("openrouter", "provider"),
)
REDACTION = "[redacted-secret]"
GITHUB_MENTION = re.compile(
    r"(?<![A-Za-z0-9_.+-])@(?P<mention>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?(?:/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?)?)(?=$|[^A-Za-z0-9_/-])"
)
CODEX_TRIGGER_MENTION = re.compile(
    r"(?<![A-Za-z0-9_.+-])@(?P<mention>codex|chatgpt-codex-connector)(?=$|[^A-Za-z0-9_-])", re.IGNORECASE
)


@dataclass
class Config:
    commands: list[str]
    model: str
    model_stack: list[str]
    max_prompt_chars: int
    max_files: int
    max_inline_comments: int
    request_changes_on_findings: bool
    minimum_confidence: float
    validation_commands: list[str]
    guidance_files: list[str]
    ignored_authors: list[str]
    allowed_authors: list[str]
    post_summary_when_findings: bool
    include_confidence: bool
    redact_secret_literals: bool
    openrouter_max_attempts: int
    openrouter_retry_max_seconds: int
    ignored_providers: list[str]
    script_timeout_seconds: int
    post_progress_comment: bool
    debug: bool


def read_text(path: str, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def workflow_run_id() -> str:
    return os.environ.get("GITHUB_RUN_ID", "").strip()


def workflow_run_url() -> str:
    run_id = workflow_run_id()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").strip() or "https://github.com"
    if not run_id or not repo:
        return ""
    return f"{server.rstrip('/')}/{repo}/actions/runs/{run_id}"


def workflow_run_status_lines(config: Config) -> list[str]:
    run_id = sanitize_github_output(workflow_run_id(), config)
    if not run_id:
        return []
    url = sanitize_github_output(workflow_run_url(), config)
    if url:
        return [f"- Workflow run: [`{run_id}`]({url})."]
    return [f"- Workflow run id: `{run_id}`."]


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_yaml_like_config(path: str) -> Config:
    """Parse the tiny YAML subset used by .github/openrouter-pr-review.yml."""

    raw = read_text(path)
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            data[key] = [] if value == "" else parse_scalar(value)
        elif current_key and stripped.startswith("-"):
            item = stripped[1:].strip()
            data.setdefault(current_key, []).append(parse_scalar(item))

    model = str(data.get("model", "openrouter/free"))
    raw_stack = data.get("model_stack", [])
    model_stack = [str(item) for item in raw_stack] if isinstance(raw_stack, list) else []
    if not model_stack:
        model_stack = [model]

    return Config(
        commands=list(data.get("commands", ["/or-review", "/openrouter-review", "/dcoir-review"])),
        model=model,
        model_stack=model_stack,
        max_prompt_chars=int(data.get("max_prompt_chars", 60000)),
        max_files=int(data.get("max_files", 30)),
        max_inline_comments=int(data.get("max_inline_comments", 12)),
        request_changes_on_findings=bool(data.get("request_changes_on_findings", False)),
        minimum_confidence=float(data.get("minimum_confidence", 0.70)),
        validation_commands=list(data.get("validation_commands", [])),
        guidance_files=list(data.get("guidance_files", [])),
        ignored_authors=list(data.get("ignored_authors", [])),
        allowed_authors=list(data.get("allowed_authors", [])),
        post_summary_when_findings=bool(data.get("post_summary_when_findings", False)),
        include_confidence=bool(data.get("include_confidence", False)),
        redact_secret_literals=bool(data.get("redact_secret_literals", True)),
        openrouter_max_attempts=int(data.get("openrouter_max_attempts", 4)),
        openrouter_retry_max_seconds=int(data.get("openrouter_retry_max_seconds", 45)),
        ignored_providers=list(data.get("ignored_providers", [])),
        script_timeout_seconds=int(data.get("script_timeout_seconds", 1500)),
        post_progress_comment=bool(data.get("post_progress_comment", False)),
        debug=bool(data.get("debug", False)),
    )


def env_required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"missing required environment variable {name}")
    return value


class ReviewTimeoutError(TimeoutError):
    """Raised by the script-level timeout before the workflow job timeout."""


class GitHubClient:
    def __init__(self, token: str, repo: str) -> None:
        self.token = token
        self.repo = repo

    def request(
        self,
        method: str,
        path: str,
        body: Any | None = None,
        accept: str = "application/vnd.github+json",
    ) -> Any:
        url = f"{GITHUB_API}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": accept,
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "dcoir-review",
        }
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = response.read()
                if accept.endswith(".diff") or accept == "application/vnd.github.v3.diff":
                    return payload.decode("utf-8", errors="replace")
                if not payload:
                    return {}
                return json.loads(payload.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc

    def get_pr(self, number: int) -> dict[str, Any]:
        return self.request("GET", f"/repos/{self.repo}/pulls/{number}")

    def get_pr_diff(self, number: int) -> str:
        return self.request("GET", f"/repos/{self.repo}/pulls/{number}", accept="application/vnd.github.v3.diff")

    def list_files(self, number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.request("GET", f"/repos/{self.repo}/pulls/{number}/files?per_page=100&page={page}")
            if not batch:
                break
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return files

    def create_issue_comment(self, number: int, body: str) -> dict[str, Any]:
        return self.request("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": body})

    def update_issue_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        return self.request("PATCH", f"/repos/{self.repo}/issues/comments/{comment_id}", {"body": body})

    def create_issue_comment_reaction(self, comment_id: int, content: str) -> dict[str, Any]:
        return self.request("POST", f"/repos/{self.repo}/issues/comments/{comment_id}/reactions", {"content": content})

    def delete_issue_comment_reaction(self, comment_id: int, reaction_id: int) -> dict[str, Any]:
        return self.request("DELETE", f"/repos/{self.repo}/issues/comments/{comment_id}/reactions/{reaction_id}")

    def create_review(self, number: int, body: str, event: str, comments: list[dict[str, Any]], commit_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {"event": event, "comments": comments, "commit_id": commit_id}
        if body.strip():
            payload["body"] = body
        return self.request("POST", f"/repos/{self.repo}/pulls/{number}/reviews", payload)


def github_safe_body(text: str, limit: int = 65000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 200] + f"\n\n[truncated by {REVIEW_DISPLAY_NAME}]"


def actions_notice_escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def append_step_summary(stage: str, message: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not summary_path:
        return
    try:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(f"- **{stage}:** {message}\n")
    except OSError as exc:
        print(f"WARN: unable to write step summary: {exc}", file=sys.stderr, flush=True)


def emit_status(stage: str, message: str) -> None:
    print(f"[dcoir-review] {stage}: {message}", flush=True)
    print(f"::notice title={REVIEW_DISPLAY_NAME}::{actions_notice_escape(stage + ': ' + message)}", flush=True)
    append_step_summary(stage, message)


def matching_command(body: str, commands: list[str]) -> str | None:
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    for command in commands:
        if re.fullmatch(rf"{re.escape(command)}(?:\s+.*)?", first_line):
            return command
    return None


def command_arguments(body: str, command: str) -> str:
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    match = re.fullmatch(rf"{re.escape(command)}(?:\s+(?P<args>.*))?", first_line)
    return (match.group("args") or "").strip() if match else ""


def command_requests_debug(body: str, command: str) -> bool:
    args = command_arguments(body, command).lower()
    if not args:
        return False
    if re.search(r"(?:^|[\s,])(?:--)?debug\s*[:=]?\s*(?:false|0|no|off)\b", args):
        return False
    if re.search(r"(?:^|[\s,])(?:--)?debug(?:\s*[:=]\s*|\s+)(?:true|1|yes|on)\b", args):
        return True
    tokens = re.split(r"[\s,]+", args)
    truthy = {"debug", "--debug", "debug=true", "debug:true", "debug=1", "debug:1", "verbose", "verbose=true"}
    falsy = {"debug=false", "debug:false", "debug=0", "debug:0", "nodebug", "no-debug", "--no-debug"}
    if any(token in falsy for token in tokens):
        return False
    return any(token in truthy for token in tokens)


def apply_debug_flag(config: Config, body: str, command: str) -> None:
    if config.debug or command_requests_debug(body, command):
        config.debug = True
        config.post_progress_comment = True


def command_matches(body: str, commands: list[str]) -> bool:
    return matching_command(body, commands) is not None


def provider_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", name.strip().lower()).strip("-")


def model_stack_label(config: Config) -> str:
    return ", ".join(config.model_stack)


def neutralize_github_mentions(text: str) -> str:
    return GITHUB_MENTION.sub(lambda match: f"@<!-- -->{match.group('mention')}", text)


def neutralize_codex_trigger_mentions(text: str) -> str:
    return CODEX_TRIGGER_MENTION.sub(lambda match: f"@<!-- -->{match.group('mention')}", text)


def sanitize_public_identity(text: str) -> str:
    cleaned = text
    for old, new in PUBLIC_IDENTITY_REPLACEMENTS:
        cleaned = cleaned.replace(old, new)
    return cleaned


class ProgressReporter:
    def __init__(self, gh: GitHubClient, issue_number: int, command: str, config: Config) -> None:
        self.gh = gh
        self.issue_number = issue_number
        self.command = command
        self.config = config
        self.comment_id = 0
        self.steps: list[tuple[str, str]] = []

    def start(self) -> None:
        self._record("started", "accepted operator review command and initialized progress reporting")
        if not self.config.post_progress_comment:
            return
        try:
            comment = self.gh.create_issue_comment(self.issue_number, self._body("running"))
            self.comment_id = int(comment.get("id", 0))
        except Exception as exc:
            print(f"WARN: unable to create progress comment: {exc}", file=sys.stderr, flush=True)

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
        emit_status(stage, safe_message)

    def _body(self, state: str, final_lines: list[str] | None = None) -> str:
        lines = [
            MARKER,
            f"{REVIEW_DISPLAY_NAME} {state}.",
            "",
            f"- Command: `{self.command}`.",
            f"- Debug progress: `{str(getattr(self.config, 'debug', False)).lower()}`.",
            *workflow_run_status_lines(self.config),
            "- Branch changes: none; this workflow only posts review output.",
            "- Gate role: internal review-assist signal before any separately approved external review request.",
        ]
        if final_lines:
            lines.extend(["", *final_lines])
        lines.extend(["", "Progress:"])
        for stage, message in self.steps[-12:]:
            lines.append(f"- `{sanitize_public_identity(stage)}`: {message}")
        return github_safe_body("\n".join(lines), limit=12000)

    def _update_comment(self, body: str, create_if_missing: bool = False) -> None:
        if not self.config.post_progress_comment:
            return
        try:
            if self.comment_id:
                self.gh.update_issue_comment(self.comment_id, body)
            elif create_if_missing:
                comment = self.gh.create_issue_comment(self.issue_number, body)
                self.comment_id = int(comment.get("id", 0))
        except Exception as exc:
            print(f"WARN: unable to update progress comment: {exc}", file=sys.stderr, flush=True)


def build_diff_line_index(diff: str) -> dict[tuple[str, int], int]:
    mapping: dict[tuple[str, int], int] = {}
    current_path: str | None = None
    position = 0
    right_line: int | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current_path = None
            position = 0
            right_line = None
            continue
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if line.startswith("@@"):
            position += 1
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            right_line = int(match.group(1)) if match else None
            continue
        if current_path is None or right_line is None:
            continue
        position += 1
        if line.startswith("-") and not line.startswith("---"):
            continue
        mapping[(current_path, right_line)] = position
        right_line += 1
    return mapping


def extract_relevant_file_patches(diff: str, max_files: int) -> str:
    chunks = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    selected = [chunk for chunk in chunks if chunk.strip()]
    return "\n".join(selected[:max_files])


def load_guidance(config: Config) -> str:
    parts = []
    for path in config.guidance_files:
        text = read_text(path)
        if text:
            parts.append(f"## {path}\n\n{text}")
    return "\n\n".join(parts)


PRIVATE_KEY_BLOCK = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE | re.DOTALL)
SECRET_VALUE_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9_])sk-(?:or|proj|live|test)?-?[A-Za-z0-9][A-Za-z0-9_\-]{8,}", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])sk_[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
URL_PASSWORD_CREDENTIAL = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)([^/\s:@?#]*):([^@\s/]+)@")
URL_TOKEN_CREDENTIAL = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://)((?:gh[pousr]_|github_pat_|sk-(?:or|proj|live|test)?-?)[^@\s/]+)@"
)
SIGNED_URL_QUERY_CREDENTIAL = re.compile(
    r"(?i)([?&](?:x-amz-signature|x-amz-credential|x-amz-security-token|awsaccesskeyid|signature|sig|sas|se|sp|sv|sr|spr|st|skoid|sktid|skt|ske|sks|skv|token|access_token|refresh_token|sessiontoken|session_token)=)([^&#\s\"']+)"
)
HEADER_CREDENTIAL = re.compile(
    r"""(?ix)(?<![A-Z0-9_\-])(?P<name_quote>[\"']?)(?P<name>(?:proxy-)?authorization|x-api-key|api-key|x-auth-token|x-access-token)(?P=name_quote)(?P<sep>\s*[:=]\s*)(?P<quote>[\"']?)(?:(?P<scheme>bearer|basic|token)\s+)?(?P<value>(?![$`])[^\"'\s,;)}\r\n]+)(?P=quote)(?=$|[\s\r\n\"',;)}])"""
)
HEADER_FIELD_CREDENTIAL_START = re.compile(
    r"""(?ix)(?<![A-Z0-9_\-])(?P<name_quote>[\"']?)(?P<name>(?:proxy-)?authorization|x-api-key|api-key|x-auth-token|x-access-token|cookie|set-cookie)(?P=name_quote)(?P<sep>\s*[:=]\s*)(?P<value_prefix>[rubf]{0,2})(?P<value_quote>[\"'])"""
)

UNQUOTED_HEADER_CREDENTIAL_START = re.compile(
    r"""(?ix)(?<![A-Z0-9_\-])(?P<name_quote>[\"']?)(?P<name>(?:proxy-)?authorization|x-api-key|api-key|x-auth-token|x-access-token)(?P=name_quote)(?P<sep>\s*[:=]\s*)(?!\s*[\"'])"""
)

COOKIE_UNQUOTED_FIELD_START = re.compile(
    r"""(?ix)(?<![A-Z0-9_\-])(?P<name_quote>[\"']?)(?P<name>cookie|set-cookie)(?P=name_quote)(?P<sep>\s*[:=]\s*)(?!\s*[\"'])"""
)
# Cookie pairs use name=value, so only colon-delimited object fields end inline cookies.
OBJECT_FIELD_AFTER_COMMA = re.compile(r"""(?ix)^\s*[\"']?[A-Z0-9_\-]+[\"']?\s*:""")
HEADER_VALUE_SCHEME = re.compile(r"(?is)^(?P<prefix>\s*(?:bearer|basic|token)\s+)(?P<secret>.+)$")
CURL_USER_OPTION = re.compile(r"""(?ix)(?P<prefix>(?<!\S)(?:--(?:proxy-)?user(?:\s+|=)|-u\s*))""")
NETRC_PASSWORD_CREDENTIAL = re.compile(r"(?i)\b(machine\s+\S+\s+login\s+\S+\s+password\s+)(\S{4,})")
SECRET_QUOTED_ASSIGNMENT_START = re.compile(
    r"""(?ix)(?<![A-Z0-9_\-])(?P<key_quote>[\"']?)(?P<key>[A-Z0-9_\-]*(?:TOKEN|SECRET|PASSWORD|API[_-]?KEY)[A-Z0-9_\-]*)(?P=key_quote)(?P<sep>\s*[:=]\s*)(?P<value_prefix>[rubf]{0,2})(?P<value_quote>[\"'])"""
)
SECRET_UNQUOTED_ASSIGNMENT = re.compile(
    r"""(?ix)
    (?P<prefix>(?<![A-Z0-9_\-])(?P<key_quote>[\"']?)(?P<key>[A-Z0-9_\-]*(?:TOKEN|SECRET|PASSWORD|API[_-]?KEY)[A-Z0-9_\-]*)(?P=key_quote)(?P<sep>\s*[:=]\s*))
    (?P<value>
        \$\{\{[^\r\n]*\}\}
        | os\.getenv\([^\r\n]*?\)[^\r\n]*
        | os\.environ\.get\([^\r\n]*?\)[^\r\n]*
        | os\.environ\[[^\r\n]*?\][^\r\n]*
        | os\.environ\b[^\r\n]*
        | env\.get\([^\r\n]*?\)[^\r\n]*
        | getenv\([^\r\n]*?\)[^\r\n]*
        | process\.env[^\r\n]*
        | import\.meta\.env[^\r\n]*
        | secrets\.get\([^\r\n]*?\)[^\r\n]*
        | [^\s\"']{8,}
    )"""
)
SAFE_REFERENCE = re.compile(
    r"""(?ix)^(?:
    os\.getenv\(\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*(?:,\s*(?:""|''|None)\s*)?\)
    | os\.environ(?:\.get\(\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*(?:,\s*(?:""|''|None)\s*)?\)|\[\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*\])
    | env\.get\(\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*(?:,\s*(?:""|''|None)\s*)?\)
    | getenv\(\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*(?:,\s*(?:""|''|None)\s*)?\)
    | process\.env(?:\.[A-Z_][A-Z0-9_]*|\[\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*\])
    | import\.meta\.env(?:\.[A-Z_][A-Z0-9_]*|\[\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*\])
    | secrets\.get\(\s*[\"'][A-Z_][A-Z0-9_]*[\"']\s*\)
    | \$\{\{\s*(?:secrets|env|vars)\.[A-Z_][A-Z0-9_]*\s*\}\}
)$"""
)
ENV_REFERENCE = re.compile(r"^(?:\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\})$")


def is_safe_reference(value: str) -> bool:
    stripped = value.strip()
    return bool(SAFE_REFERENCE.fullmatch(stripped) or ENV_REFERENCE.fullmatch(stripped))


def is_safe_unquoted_reference(value: str) -> bool:
    return is_safe_reference(value)


def is_safe_quoted_reference(value: str) -> bool:
    return is_safe_reference(value)


def find_quoted_value_end(text: str, start: int, quote: str) -> int:
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == quote:
            return index
        if char in {"\r", "\n"}:
            return -1
    return -1


def find_curl_quoted_value_end(text: str, start: int, quote: str) -> int:
    escaped = False
    line_start = start
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"\r", "\n"}:
            line_start = index + 1
            continue
        if char == quote:
            if line_start > start and CURL_USER_OPTION.search(text[line_start:index]):
                return -1
            return index
    return -1


def redact_private_key_blocks(text: str) -> str:
    return PRIVATE_KEY_BLOCK.sub(REDACTION, text)


def redact_url_credentials(text: str) -> str:
    cleaned = URL_PASSWORD_CREDENTIAL.sub(lambda match: f"{match.group(1)}{match.group(2)}:{REDACTION}@", text)
    cleaned = URL_TOKEN_CREDENTIAL.sub(lambda match: f"{match.group(1)}{REDACTION}@", cleaned)
    return SIGNED_URL_QUERY_CREDENTIAL.sub(lambda match: f"{match.group(1)}{REDACTION}", cleaned)


def redact_header_credential(match: re.Match[str]) -> str:
    value = match.group("value").strip()
    if not value or is_safe_header_secret_value(value):
        return match.group(0)
    scheme = match.group("scheme")
    tail = match.string[match.end():].lstrip()
    if scheme is None and value.lower() in {"bearer", "basic", "token"}:
        if tail[:1] in {'"', "'"}:
            return match.group(0)
    if scheme is not None and value == "\\" and tail[:1] in {'"', "'"}:
        return match.group(0)
    scheme_prefix = f"{scheme} " if scheme else ""
    return f"{match.group('name_quote')}{match.group('name')}{match.group('name_quote')}{match.group('sep')}{match.group('quote')}{scheme_prefix}{REDACTION}{match.group('quote')}"

def is_inline_object_cookie_context(text: str, field_start: int) -> bool:
    line_start = text.rfind("\n", 0, field_start) + 1
    last_open = max(text.rfind("{", line_start, field_start), text.rfind("[", line_start, field_start))
    if last_open < 0:
        return False
    last_close = max(text.rfind("}", line_start, field_start), text.rfind("]", line_start, field_start))
    return last_close < last_open


def find_unquoted_cookie_value_end(text: str, start: int, inline_object: bool) -> int:
    interpolation_depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "$" and index + 1 < len(text) and text[index + 1] == "{":
            if index + 2 < len(text) and text[index + 2] == "{":
                interpolation_depth += 2
                index += 3
            else:
                interpolation_depth += 1
                index += 2
            continue
        if char == "}" and interpolation_depth:
            interpolation_depth -= 1
            index += 1
            continue
        if char in {"\r", "\n"}:
            return index
        if inline_object and char in {"}", "]"}:
            return index
        if inline_object and char == "," and OBJECT_FIELD_AFTER_COMMA.match(text[index + 1 :]):
            return index
        index += 1
    return len(text)


def redact_unquoted_cookie_credentials(text: str) -> str:
    result: list[str] = []
    cursor = 0
    for match in COOKIE_UNQUOTED_FIELD_START.finditer(text):
        if match.start() < cursor:
            continue
        value_start = match.end()
        inline_object = is_inline_object_cookie_context(text, match.start())
        value_end = find_unquoted_cookie_value_end(text, value_start, inline_object)
        value = text[value_start:value_end].strip()
        if not value or value == REDACTION or is_safe_reference(value):
            continue
        result.append(text[cursor:value_start])
        result.append(REDACTION)
        cursor = value_end
    if not result:
        return text
    result.append(text[cursor:])
    return "".join(result)


def skip_line_continuation_whitespace(text: str, start: int) -> int:
    index = start
    while index < len(text):
        if text[index] != "\\":
            return index
        if index + 2 < len(text) and text[index + 1] == "\r" and text[index + 2] == "\n":
            index += 3
        elif index + 1 < len(text) and text[index + 1] in {"\r", "\n"}:
            index += 2
        else:
            return index
        while index < len(text) and text[index] in {" ", "\t"}:
            index += 1
    return index


def find_escaped_quoted_value_end(text: str, start: int, quote: str) -> int:
    index = start
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            if text[index + 1] == quote:
                return index + 2
            index += 2
            continue
        if text[index] in {"\r", "\n"}:
            return -1
        index += 1
    return -1

def find_unquoted_header_credential_end(text: str, start: int) -> int:
    index = start
    consumed_plain = False
    while index < len(text):
        continuation_index = skip_line_continuation_whitespace(text, index)
        if continuation_index != index:
            index = continuation_index
            continue
        if text.startswith("${{", index):
            expression_end = find_github_expression_end(text, index + 3)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end
            consumed_plain = True
            continue
        if text.startswith("${", index):
            expression_end = text.find("}", index + 2)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            consumed_plain = True
            continue
        if text.startswith("$(", index):
            expression_end = find_command_substitution_end(text, index + 2)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            consumed_plain = True
            continue
        if text[index] == "$" and index + 1 < len(text) and text[index + 1] in {'"', "'"}:
            expression_end = find_curl_quoted_value_end(text, index + 2, text[index + 1])
            if expression_end < 0:
                return len(text)
            index = expression_end + 1
            consumed_plain = True
            continue
        if text[index] == "`":
            expression_end = find_backtick_substitution_end(text, index + 1)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            consumed_plain = True
            continue
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1] in {'"', "'"}:
            expression_end = find_escaped_quoted_value_end(text, index + 2, text[index + 1])
            if consumed_plain:
                next_delimiter = len(text)
                for delimiter in ("\r", "\n", "\t", " ", ",", ";", ")", "}", "]"):
                    delimiter_position = text.find(delimiter, index + 2)
                    if delimiter_position >= 0:
                        next_delimiter = min(next_delimiter, delimiter_position)
                if expression_end < 0 or expression_end > next_delimiter:
                    return index
            if expression_end < 0:
                return len(text)
            index = expression_end
            consumed_plain = True
            continue
        if text[index] in {'"', "'"}:
            expression_end = find_curl_quoted_value_end(text, index + 1, text[index])
            if consumed_plain:
                next_delimiter = len(text)
                for delimiter in ("\r", "\n", "\t", " ", ",", ";", ")", "}", "]"):
                    delimiter_position = text.find(delimiter, index + 1)
                    if delimiter_position >= 0:
                        next_delimiter = min(next_delimiter, delimiter_position)
                if expression_end < 0 or expression_end > next_delimiter:
                    return index
            if expression_end < 0:
                return len(text)
            index = expression_end + 1
            consumed_plain = True
            continue
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            consumed_plain = True
            continue
        if text[index] in {"\r", "\n", "\t", " ", ",", ";", ")", "}", "]"}:
            return index
        consumed_plain = True
        index += 1
    return index

def find_unquoted_header_value_end(text: str, start: int) -> int:
    probe = start
    while probe < len(text) and text[probe] in {" ", "\t"}:
        probe += 1
    for scheme in ("bearer", "basic", "token"):
        scheme_end = probe + len(scheme)
        if text[probe:scheme_end].lower() == scheme and scheme_end < len(text) and text[scheme_end] in {" ", "\t"}:
            secret_start = scheme_end
            while secret_start < len(text) and text[secret_start] in {" ", "\t"}:
                secret_start += 1
            return find_unquoted_header_credential_end(text, secret_start)
    return find_unquoted_header_credential_end(text, start)


def is_safe_header_secret_value(value: str) -> bool:
    stripped = value.strip()
    if is_safe_reference(stripped):
        return True
    if len(stripped) >= 2 and stripped[0] in {'"', "'"} and stripped[-1] == stripped[0]:
        return is_safe_reference(stripped[1:-1].strip())
    if len(stripped) >= 3 and stripped[0] == "$" and stripped[1] in {'"', "'"} and stripped[-1] == stripped[1]:
        return is_safe_reference(stripped[2:-1].strip())
    if len(stripped) >= 4 and stripped[0] == "\\" and stripped[1] in {'"', "'"} and stripped[-2:] == f"\\{stripped[1]}":
        return is_safe_reference(stripped[2:-2].strip())
    return False

def redact_unquoted_header_credentials(text: str) -> str:
    result: list[str] = []
    cursor = 0
    for match in UNQUOTED_HEADER_CREDENTIAL_START.finditer(text):
        if match.start() < cursor:
            continue
        value_start = match.end()
        value_end = find_unquoted_header_value_end(text, value_start)
        value = text[value_start:value_end]
        stripped_value = value.strip()
        if not stripped_value or stripped_value == REDACTION:
            continue
        scheme_match = HEADER_VALUE_SCHEME.fullmatch(value)
        secret_value = scheme_match.group("secret").strip() if scheme_match else stripped_value
        if is_safe_header_secret_value(stripped_value) or (scheme_match and is_safe_header_secret_value(secret_value)):
            continue
        result.append(text[cursor:value_start])
        if scheme_match:
            result.append(f"{scheme_match.group('prefix')}{REDACTION}")
        else:
            leading = value[: len(value) - len(value.lstrip())]
            result.append(f"{leading}{REDACTION}")
        cursor = value_end
    if not result:
        return text
    result.append(text[cursor:])
    return "".join(result)

def redact_header_field_credentials(text: str) -> str:
    result: list[str] = []
    cursor = 0
    for match in HEADER_FIELD_CREDENTIAL_START.finditer(text):
        if match.start() < cursor:
            continue
        value_start = match.end()
        value_end = find_quoted_value_end(text, value_start, match.group("value_quote"))
        if value_end < 0:
            continue
        value = text[value_start:value_end]
        scheme_match = HEADER_VALUE_SCHEME.fullmatch(value)
        if is_safe_header_secret_value(value.strip()) or (scheme_match and is_safe_header_secret_value(scheme_match.group("secret").strip())):
            continue
        result.append(text[cursor:value_start])
        if scheme_match:
            result.append(f"{scheme_match.group('prefix')}{REDACTION}")
        else:
            result.append(REDACTION)
        cursor = value_end
    if not result:
        return text
    result.append(text[cursor:])
    return "".join(result)

def find_curl_credential_line_end(text: str, start: int) -> int:
    line_end = len(text)
    for newline in ("\r", "\n"):
        position = text.find(newline, start)
        if position >= 0:
            line_end = min(line_end, position)
    return line_end


def find_github_expression_end(text: str, start: int) -> int:
    quote = ""
    escaped = False
    index = start
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote:
            if char == "\\":
                escaped = True
            elif quote == "'" and char == "'" and index + 1 < len(text) and text[index + 1] == "'":
                index += 2
                continue
            elif char == quote:
                quote = ""
            elif char in {"\r", "\n"}:
                return -1
            index += 1
            continue
        if char in {"\"", "'"}:
            quote = char
            index += 1
            continue
        if text.startswith("}}", index):
            return index + 2
        if char in {"\r", "\n"}:
            return -1
        index += 1
    return -1


def find_unquoted_curl_credential_end(text: str, start: int) -> int:
    index = start
    while index < len(text):
        if text.startswith("${{", index):
            expression_end = find_github_expression_end(text, index + 3)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end
            continue
        if text.startswith("${", index):
            expression_end = text.find("}", index + 2)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            continue
        if text.startswith("$(", index):
            expression_end = find_command_substitution_end(text, index + 2)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            continue
        if text[index] == "$" and index + 1 < len(text) and text[index + 1] in {'"', "'"}:
            expression_end = find_curl_quoted_value_end(text, index + 2, text[index + 1])
            if expression_end < 0:
                return len(text)
            index = expression_end + 1
            continue
        if text[index] == "`":
            expression_end = find_backtick_substitution_end(text, index + 1)
            if expression_end < 0:
                return find_curl_credential_line_end(text, index)
            index = expression_end + 1
            continue
        if text[index] == "\\":
            continuation_index = skip_line_continuation_whitespace(text, index)
            if continuation_index != index:
                index = continuation_index
                continue
            if index + 1 < len(text):
                index += 2
                continue
        if text[index] in {'"', "'"}:
            expression_end = find_curl_quoted_value_end(text, index + 1, text[index])
            if expression_end < 0:
                return len(text)
            index = expression_end + 1
            continue
        if text[index] in {"\r", "\n", "\t", " ", '"', "'"}:
            return index
        index += 1
    return index

def find_command_substitution_end(text: str, start: int) -> int:
    depth = 1
    quote = ""
    escaped = False
    index = start
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote:
            if char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in {"\"", "'"}:
            quote = char
            index += 1
            continue
        if text.startswith("$(", index):
            depth += 1
            index += 2
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def find_backtick_substitution_end(text: str, start: int) -> int:
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "`":
            return index
    return -1


def skip_curl_line_continuation_whitespace(text: str, start: int) -> int:
    return skip_line_continuation_whitespace(text, start)

def redact_curl_user_credentials(text: str) -> str:
    result: list[str] = []
    cursor = 0
    for match in CURL_USER_OPTION.finditer(text):
        if match.start() < cursor:
            continue
        value_start = skip_curl_line_continuation_whitespace(text, match.end())
        if value_start >= len(text):
            continue
        quote_prefix_length = 0
        if text[value_start] == "$" and value_start + 1 < len(text) and text[value_start + 1] in {"\"", "'"}:
            quote_prefix_length = 1
            quote = text[value_start + 1]
        else:
            quote = text[value_start] if text[value_start] in {"\"", "'"} else ""
        if quote:
            credential_start = value_start + quote_prefix_length + 1
            credential_end = find_curl_quoted_value_end(text, credential_start, quote)
            if credential_end < 0:
                credential_end = len(text)
            credential = text[credential_start:credential_end]
        else:
            credential_start = value_start
            credential_end = find_unquoted_curl_credential_end(text, credential_start)
            credential = text[credential_start:credential_end]
        colon_index = credential.find(":")
        if colon_index < 0 or len(credential[colon_index + 1 :].strip()) < 4:
            continue
        password_start = credential_start + colon_index + 1
        result.append(text[cursor:password_start])
        result.append(REDACTION)
        cursor = credential_end
    if not result:
        return text
    result.append(text[cursor:])
    return "".join(result)


def redact_quoted_assignments(text: str) -> str:
    result: list[str] = []
    cursor = 0
    for match in SECRET_QUOTED_ASSIGNMENT_START.finditer(text):
        if match.start() < cursor:
            continue
        value_start = match.end()
        value_end = find_quoted_value_end(text, value_start, match.group("value_quote"))
        if value_end < 0 or value_end - value_start < 8:
            continue
        value = text[value_start:value_end]
        result.append(text[cursor:value_start])
        result.append(value if is_safe_quoted_reference(value) else REDACTION)
        cursor = value_end
    if not result:
        return text
    result.append(text[cursor:])
    return "".join(result)


def redact_unquoted_assignment(match: re.Match[str]) -> str:
    value = match.group("value")
    if is_safe_unquoted_reference(value):
        return match.group(0)
    stripped = value.rstrip()
    trailing_whitespace = value[len(stripped) :]
    if stripped.endswith(","):
        candidate = stripped[:-1].rstrip()
        candidate_trailing = stripped[len(candidate) :]
        if is_safe_unquoted_reference(candidate):
            return f"{match.group('prefix')}{candidate}{candidate_trailing}{trailing_whitespace}"
    return f"{match.group('prefix')}{REDACTION}"


def sanitize_text(text: str, config: Config) -> str:
    if not config.redact_secret_literals:
        return text
    cleaned = text
    cleaned = redact_private_key_blocks(cleaned)
    cleaned = redact_url_credentials(cleaned)
    cleaned = redact_header_field_credentials(cleaned)
    cleaned = redact_unquoted_cookie_credentials(cleaned)
    cleaned = redact_unquoted_header_credentials(cleaned)
    cleaned = HEADER_CREDENTIAL.sub(redact_header_credential, cleaned)
    cleaned = redact_curl_user_credentials(cleaned)
    cleaned = NETRC_PASSWORD_CREDENTIAL.sub(lambda match: f"{match.group(1)}{REDACTION}", cleaned)
    cleaned = redact_quoted_assignments(cleaned)
    cleaned = SECRET_UNQUOTED_ASSIGNMENT.sub(redact_unquoted_assignment, cleaned)
    for pattern in SECRET_VALUE_PATTERNS:
        cleaned = pattern.sub(REDACTION, cleaned)
    return cleaned


def sanitize_github_output(text: str, config: Config, neutralize_mentions: bool = True) -> str:
    cleaned = sanitize_public_identity(sanitize_text(text, config))
    if neutralize_mentions:
        return neutralize_github_mentions(cleaned)
    return neutralize_codex_trigger_mentions(cleaned)


def debug_artifact_root(config: Config) -> Path | None:
    if not getattr(config, "debug", False):
        return None
    raw_path = os.environ.get(DEBUG_ARTIFACT_DIR_ENV, "").strip() or DEBUG_ARTIFACT_DEFAULT_DIR
    root = Path(raw_path)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve(strict=False)


def debug_artifact_path(config: Config, name: str) -> Path | None:
    root = debug_artifact_root(config)
    if root is None:
        return None
    if not DEBUG_ARTIFACT_SAFE_NAME.fullmatch(name) or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"unsafe debug artifact name: {name}")
    path = (root / name).resolve(strict=False)
    if path != root and root not in path.parents:
        raise ValueError(f"debug artifact path escapes root: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def bounded_debug_artifact_text(text: str, max_chars: int = DEBUG_ARTIFACT_MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    marker = "\n\n[debug artifact truncated by DCOIR Review]\n"
    return text[: max(0, max_chars - len(marker))].rstrip() + marker


def sanitize_debug_json_value(value: Any, config: Config) -> Any:
    if isinstance(value, str):
        return sanitize_github_output(value, config)
    if isinstance(value, dict):
        return {
            sanitize_github_output(str(key), config): sanitize_debug_json_value(item, config)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_debug_json_value(item, config) for item in value]
    if isinstance(value, tuple):
        return [sanitize_debug_json_value(item, config) for item in value]
    return value


def write_debug_text_artifact(config: Config, name: str, text: str, max_chars: int = DEBUG_ARTIFACT_MAX_CHARS) -> Path | None:
    path = debug_artifact_path(config, name)
    if path is None:
        return None
    safe_text = sanitize_github_output(str(text), config)
    path.write_text(bounded_debug_artifact_text(safe_text, max_chars), encoding="utf-8")
    return path


def write_debug_json_artifact(config: Config, name: str, data: Any, max_chars: int = DEBUG_ARTIFACT_MAX_CHARS) -> Path | None:
    path = debug_artifact_path(config, name)
    if path is None:
        return None
    safe_data = sanitize_debug_json_value(data, config)
    text = json.dumps(safe_data, indent=2, sort_keys=True, default=str)
    path.write_text(bounded_debug_artifact_text(text, max_chars) + "\n", encoding="utf-8")
    return path


def sanitized_prompt_value(value: Any, config: Config) -> str:
    return sanitize_text(str(value or ""), config)


def build_prompt(pr: dict[str, Any], files: list[dict[str, Any]], diff: str, config: Config) -> str:
    guidance = sanitize_text(load_guidance(config), config)
    changed_files = []
    for item in files[: config.max_files]:
        changed_files.append(
            {
                "filename": sanitized_prompt_value(item.get("filename"), config),
                "status": sanitized_prompt_value(item.get("status"), config),
                "additions": item.get("additions"),
                "deletions": item.get("deletions"),
                "changes": item.get("changes"),
                "patch": sanitized_prompt_value(item.get("patch", ""), config),
            }
        )
    content = f"""
Repository: {sanitize_text(os.environ.get('GITHUB_REPOSITORY', ''), config)}
PR number: {pr.get('number')}
PR title: {sanitized_prompt_value(pr.get('title'), config)}
PR body:
{sanitized_prompt_value(pr.get('body'), config)}

Trusted repository guidance:
{guidance}

Preferred validation commands:
{json.dumps([sanitize_text(str(command), config) for command in config.validation_commands], indent=2)}

Changed file summary:
{json.dumps(changed_files, indent=2)}

Unified diff:
{sanitize_text(extract_relevant_file_patches(diff, config.max_files), config)}

Review task:
Find only high-signal issues in the PR diff. For each finding, give the exact changed file path and right-side line number. Provide a suggested_replacement only when a small GitHub suggestion block would be safe and likely to apply cleanly. Include validation commands that should pass after the fix.
""".strip()
    content = sanitize_text(content, config)
    if len(content) > config.max_prompt_chars:
        content = content[: config.max_prompt_chars] + "\n\n[context truncated by reviewer]"
    return content


def parse_openrouter_error(detail: str) -> dict[str, Any]:
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return {"message": detail.strip()[:1000]}
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    metadata = error.get("metadata", {}) if isinstance(error, dict) else {}
    message = str(error.get("message", "OpenRouter request failed")) if isinstance(error, dict) else "OpenRouter request failed"
    provider = str(metadata.get("provider_name", "")).strip() if isinstance(metadata, dict) else ""
    retry_after = metadata.get("retry_after_seconds") if isinstance(metadata, dict) else None
    if retry_after is None and isinstance(metadata, dict):
        retry_after = metadata.get("retry_after_seconds_raw")
    return {"message": message, "provider": provider, "retry_after": retry_after}


def build_openrouter_payload(prompt: str, schema: dict[str, Any], config: Config, ignored_providers: list[str], model: str) -> dict[str, Any]:
    provider: dict[str, Any] = {"allow_fallbacks": True, "require_parameters": True}
    clean_ignored = [item for item in ignored_providers if item]
    if clean_ignored:
        provider["ignore"] = clean_ignored
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": read_text("prompts/openrouter-pr-review-system.md")},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "openrouter_pr_review", "strict": True, "schema": schema},
        },
        "provider": provider,
        "temperature": 0.2,
    }


def openrouter_request_once(prompt: str, schema: dict[str, Any], config: Config, ignored_providers: list[str], model: str) -> tuple[dict[str, Any], str]:
    api_key = env_required("OPENROUTER_API_KEY")
    payload = build_openrouter_payload(prompt, schema, config, ignored_providers, model)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DCOIR-Collector/dcoir-collector",
        "X-OpenRouter-Title": REVIEW_DISPLAY_NAME,
    }
    req = urllib.request.Request(OPENROUTER_API, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    model_used = str(data.get("model", model))
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
    return parsed, model_used


def openrouter_review(prompt: str, schema: dict[str, Any], config: Config, reporter: ProgressReporter | None = None) -> tuple[dict[str, Any], str]:
    attempts = max(1, config.openrouter_max_attempts)
    retry_cap = max(1, config.openrouter_retry_max_seconds)
    last_error = "OpenRouter request failed"

    for model_index, model in enumerate(config.model_stack, start=1):
        ignored_providers = [provider_slug(item) for item in config.ignored_providers]
        if reporter:
            reporter.update("openrouter", f"calling model {model_index}/{len(config.model_stack)}: {model}")
        for attempt in range(1, attempts + 1):
            try:
                if reporter:
                    reporter.update("openrouter-attempt", f"model={model}; attempt={attempt}/{attempts}")
                return openrouter_request_once(prompt, schema, config, ignored_providers, model)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                parsed_error = parse_openrouter_error(detail)
                provider = provider_slug(str(parsed_error.get("provider", "")))
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


def normalize_findings(result: dict[str, Any], config: Config, line_index: dict[tuple[str, int], int]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in result.get("findings", []):
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", ""))
        except (TypeError, ValueError):
            continue
        if confidence < config.minimum_confidence:
            continue
        if (path, line) not in line_index:
            continue
        findings.append(item)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_order.get(str(f.get("severity", "low")), 9), -float(f.get("confidence", 0))))
    return findings[: config.max_inline_comments]


def is_safe_suggestion(suggestion: str) -> bool:
    text = suggestion.strip()
    if not text:
        return False
    prose_prefixes = ("use ", "replace ", "remove ", "avoid ", "store ", "validate ", "sanitize ", "consider ", "e.g.", "for example")
    lowered = text.lower()
    if lowered.startswith(prose_prefixes):
        return False
    if " should " in lowered or " you should " in lowered:
        return False
    code_signals = ("=", "(", ")", "{", "}", "[", "]", ":", ";", "return ", "throw ", "raise ", "if ", "for ", "while ")
    return any(signal_text in text for signal_text in code_signals)


VALIDATION_COMMAND_PREFIXES = (
    "bandit ",
    "bash ",
    "git ",
    "Invoke-ScriptAnalyzer ",
    "node ",
    "npm ",
    "npx ",
    "pwsh ",
    "powershell ",
    "python ",
    "python3 ",
    "pytest ",
    "ruff ",
    "sh ",
)


def has_balanced_command_quotes(text: str) -> bool:
    quote = ""
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"\"", "'"}:
            quote = char
    return not quote


def is_validation_command(text: str) -> bool:
    stripped = text.strip()
    return has_balanced_command_quotes(stripped) and any(stripped.startswith(prefix) for prefix in VALIDATION_COMMAND_PREFIXES)


def powershell_double_quoted(value: str) -> str:
    escaped = value.replace("`", "``").replace('"', '`"').replace("$", "`$")
    return f'"{escaped}"'


def extract_validation_commands(validation: str) -> list[str]:
    commands: list[str] = []
    for line in validation.splitlines():
        cleaned = line.strip().strip("-*").strip()
        if cleaned.startswith("```") or not cleaned:
            continue
        if is_validation_command(cleaned):
            commands.append(cleaned)
    for match in re.finditer(r"`([^`\n]+)`", validation):
        candidate = match.group(1).strip()
        if is_validation_command(candidate):
            commands.append(candidate)
    return commands


def default_validation_commands_for_path(path: str) -> list[str]:
    if not path:
        return []
    lower_path = path.lower()
    quoted = shlex.quote(path)
    if lower_path.endswith(".py"):
        return [
            f"python3 -m py_compile {quoted}",
            f"bandit -r {quoted}",
        ]
    if lower_path.endswith((".ps1", ".psm1", ".psd1")):
        ps_path = powershell_double_quoted(path)
        return [
            f"pwsh -NoProfile -Command '$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath {ps_path}), [ref]$errors) | Out-Null; if ($errors) {{ throw ($errors | Out-String) }}'",
            f"pwsh -NoProfile -Command 'Invoke-ScriptAnalyzer -Path {ps_path}'",
        ]
    if lower_path.endswith(".json"):
        return [f"python3 -m json.tool {quoted}"]
    return []


def validation_text_for_finding(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "")).strip()
    commands = extract_validation_commands(str(finding.get("validation", "")).strip())
    defaults = default_validation_commands_for_path(path)
    combined: list[str] = []
    seen: set[str] = set()
    for command in [*commands, *defaults]:
        if command and command not in seen:
            combined.append(command)
            seen.add(command)
    return "\n".join(combined)


def strip_markdown_fence_lines(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith(("```", "~~~")):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def fix_guidance_value_text(value: Any, config: Config, *, neutralize_mentions: bool = False) -> str:
    return strip_markdown_fence_lines(
        sanitize_github_output(str(value or "").strip(), config, neutralize_mentions=neutralize_mentions)
    )


def markdown_emphasis_safe_text(value: str) -> str:
    text = " ".join(str(value or "").strip().splitlines())
    return re.sub(r"([*_`])", lambda match: "\\" + match.group(1), text)


def build_inline_comment(finding: dict[str, Any], model_used: str, config: Config) -> str:
    title = markdown_emphasis_safe_text(sanitize_github_output(str(finding.get("title", "Finding")).strip(), config))
    severity = markdown_emphasis_safe_text(str(finding.get("severity", "medium")).upper())
    confidence = float(finding.get("confidence", 0))
    body = sanitize_github_output(str(finding.get("body", "")).strip(), config)
    validation = sanitize_github_output(validation_text_for_finding(finding), config)
    suggestion = sanitize_github_output(str(finding.get("suggested_replacement", "")).rstrip(), config, neutralize_mentions=False)
    fix_guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    parts = [f"**{severity}: {title}**", "", body]
    if config.include_confidence:
        parts.extend(["", f"Confidence: `{confidence:.2f}`"])
    if suggestion:
        if is_safe_suggestion(suggestion):
            parts.extend(["", "Suggested fix:", "", "```suggestion", suggestion, "```"])
        else:
            parts.extend(["", "Suggested fix guidance:", "", "```text", suggestion, "```"])
    if fix_guidance:
        parts.extend(["", "Suggested repair:"])
        for label, key in (("Remove", "remove"), ("Replace", "replace"), ("Add", "add")):
            value = fix_guidance_value_text(fix_guidance.get(key, ""), config, neutralize_mentions=False)
            if value:
                parts.extend(["", f"{label}:", "", "```text", value, "```"])
        notes = fix_guidance_value_text(fix_guidance.get("notes", ""), config)
        if notes:
            parts.extend(["", "Notes:", "", "```text", notes, "```"])
    if validation:
        parts.extend(["", "Validation expected after fix:", "", "```text", validation, "```"])
    parts.extend(["", f"<sub>{REVIEW_DISPLAY_NAME}</sub>"])
    return github_safe_body("\n".join(parts), limit=12000)


def short_commit(commit_sha: str) -> str:
    return commit_sha[:12] if commit_sha else "unavailable"


def build_review_body(
    result: dict[str, Any],
    findings: list[dict[str, Any]],
    model_used: str,
    config: Config,
    reviewed_commit: str = "",
) -> str:
    summary = sanitize_github_output(str(result.get("summary", f"{REVIEW_DISPLAY_NAME} completed.")).strip(), config)
    event_text = "Review posted with inline findings." if findings else "No high-confidence inline findings were found in the changed diff."
    lines = [
        MARKER,
        f"💡 {REVIEW_DISPLAY_NAME}",
        "Here are some review suggestions for this pull request." if findings else "No high-confidence inline review suggestions were found for this pull request.",
        "",
        f"Reviewed commit: `{short_commit(reviewed_commit)}`",
    ]
    if summary and (not findings or config.post_summary_when_findings):
        lines.extend(["", summary])
    lines.extend(["", f"Result: {event_text}"])
    return github_safe_body(
        "\n".join(lines).strip()
    )


def main() -> None:
    repo = env_required("GITHUB_REPOSITORY")
    pr_number = int(env_required("PR_NUMBER"))
    token = env_required("GITHUB_TOKEN")
    trigger_comment_id = int(env_required("TRIGGER_COMMENT_ID"))
    comment_body = os.environ.get("TRIGGER_COMMENT_BODY", "")
    author = os.environ.get("TRIGGER_AUTHOR", "")
    config_path = os.environ.get("OPENROUTER_REVIEW_CONFIG", ".github/openrouter-pr-review.yml")
    config = load_yaml_like_config(config_path)

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
    apply_debug_flag(config, comment_body, command)

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise ReviewTimeoutError(f"{REVIEW_DISPLAY_NAME} exceeded script timeout of {config.script_timeout_seconds} seconds")

    schema = json.loads(read_text("schemas/openrouter-pr-review.schema.json"))
    gh = GitHubClient(token, repo)
    reporter = ProgressReporter(gh, pr_number, command, config)
    eyes_reaction_id = 0

    try:
        reaction = gh.create_issue_comment_reaction(trigger_comment_id, "eyes")
        eyes_reaction_id = int(reaction.get("id", 0))
    except Exception as exc:
        print(f"WARN: unable to add eyes reaction: {exc}", file=sys.stderr, flush=True)

    try:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.script_timeout_seconds)
        env_required("OPENROUTER_API_KEY")
        reporter.start()
        reporter.update("github", "fetching PR metadata")
        pr = gh.get_pr(pr_number)
        reporter.update("github", "fetching PR diff")
        diff = gh.get_pr_diff(pr_number)
        reporter.update("github", "fetching changed file list")
        files = gh.list_files(pr_number)
        reporter.update("prompt", f"building bounded prompt from {len(files)} changed files")
        prompt = build_prompt(pr, files, diff, config)
        result, model_used = openrouter_review(prompt, schema, config, reporter)
        reporter.update("normalize", "mapping model findings to changed diff lines")
        line_index = build_diff_line_index(diff)
        findings = normalize_findings(result, config, line_index)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        reviewed_commit = str(pr.get("head", {}).get("sha", "") or "")
        review_body = build_review_body(result, findings, model_used, config, reviewed_commit)
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments")
        gh.create_review(pr_number, review_body, event, comments, reviewed_commit)
        reporter.complete(model_used, len(comments), event)
    except Exception as exc:
        safe_error = sanitize_github_output(str(exc), config)
        reporter.fail(safe_error)
        if not config.post_progress_comment:
            error_body = f"""{MARKER}
{REVIEW_DISPLAY_NAME} failed.

```text
{safe_error[:4000]}
```
""".strip()
            try:
                gh.create_issue_comment(pr_number, error_body)
            except Exception as comment_exc:
                print(f"WARN: unable to post failure comment: {comment_exc}", file=sys.stderr, flush=True)
        raise
    finally:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        if eyes_reaction_id:
            try:
                gh.delete_issue_comment_reaction(trigger_comment_id, eyes_reaction_id)
            except Exception as exc:
                print(f"WARN: unable to remove eyes reaction: {exc}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
