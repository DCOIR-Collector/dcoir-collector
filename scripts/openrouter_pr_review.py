#!/usr/bin/env python3
"""Summoned OpenRouter PR reviewer for GitHub Actions.

This script is intentionally dependency-free. It reads a PR diff through the
GitHub API, asks OpenRouter for structured findings, and posts a GitHub PR
review with inline suggestion blocks when safe. It never pushes commits and it
never checks out or executes untrusted PR code.
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GITHUB_API = "https://api.github.com"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
MARKER = "<!-- openrouter-pr-review -->"


@dataclass
class Config:
    commands: list[str]
    model: str
    max_prompt_chars: int
    max_files: int
    max_inline_comments: int
    request_changes_on_findings: bool
    minimum_confidence: float
    validation_commands: list[str]
    guidance_files: list[str]
    ignored_authors: list[str]
    allowed_authors: list[str]


def die(message: str, exit_code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(exit_code)


def read_text(path: str, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def load_yaml_like_config(path: str) -> Config:
    """Parse the tiny YAML subset used by .github/openrouter-pr-review.yml.

    The parser supports top-level scalars and lists. Avoiding PyYAML keeps the
    action dependency-free and faster to bootstrap on GitHub-hosted runners.
    """
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
            if value == "":
                data[key] = []
            else:
                data[key] = parse_scalar(value)
        elif current_key and stripped.startswith("-"):
            item = stripped[1:].strip()
            data.setdefault(current_key, []).append(parse_scalar(item))
    return Config(
        commands=list(data.get("commands", ["/or-review", "/openrouter-review"])),
        model=str(data.get("model", "openrouter/free")),
        max_prompt_chars=int(data.get("max_prompt_chars", 60000)),
        max_files=int(data.get("max_files", 30)),
        max_inline_comments=int(data.get("max_inline_comments", 12)),
        request_changes_on_findings=bool(data.get("request_changes_on_findings", False)),
        minimum_confidence=float(data.get("minimum_confidence", 0.70)),
        validation_commands=list(data.get("validation_commands", [])),
        guidance_files=list(data.get("guidance_files", [])),
        ignored_authors=list(data.get("ignored_authors", [])),
        allowed_authors=list(data.get("allowed_authors", [])),
    )


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


def env_required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        die(f"missing required environment variable {name}")
    return value


class GitHubClient:
    def __init__(self, token: str, repo: str) -> None:
        self.token = token
        self.repo = repo
        self.owner, self.name = repo.split("/", 1)

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
            "User-Agent": "dcoir-openrouter-pr-review",
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
        payload: dict[str, Any] = {"body": body, "event": event, "comments": comments, "commit_id": commit_id}
        return self.request("POST", f"/repos/{self.repo}/pulls/{number}/reviews", payload)


def github_safe_body(text: str, limit: int = 65000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 200] + "\n\n[truncated by OpenRouter PR Review]"


def command_matches(body: str, commands: list[str]) -> bool:
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    return any(first_line == cmd or first_line.startswith(cmd + " ") for cmd in commands)


def build_diff_line_index(diff: str) -> dict[tuple[str, int], int]:
    """Map (path, right-side line) to GitHub legacy diff position."""
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
        if line.startswith("+") and not line.startswith("+++"):
            mapping[(current_path, right_line)] = position
            right_line += 1
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


def build_prompt(pr: dict[str, Any], files: list[dict[str, Any]], diff: str, config: Config) -> str:
    guidance = load_guidance(config)
    changed_files = []
    for item in files[: config.max_files]:
        changed_files.append(
            {
                "filename": item.get("filename"),
                "status": item.get("status"),
                "additions": item.get("additions"),
                "deletions": item.get("deletions"),
                "changes": item.get("changes"),
                "patch": item.get("patch", ""),
            }
        )
    content = f"""
Repository: {os.environ.get('GITHUB_REPOSITORY', '')}
PR number: {pr.get('number')}
PR title: {pr.get('title')}
PR body:
{pr.get('body') or ''}

Trusted repository guidance:
{guidance}

Preferred validation commands:
{json.dumps(config.validation_commands, indent=2)}

Changed file summary:
{json.dumps(changed_files, indent=2)}

Unified diff:
{extract_relevant_file_patches(diff, config.max_files)}

Review task:
Find only high-signal issues in the PR diff. For each finding, give the exact changed file path and right-side line number. Provide a suggested_replacement only when a small GitHub suggestion block would be safe and likely to apply cleanly. Include validation commands that should pass after the fix.
""".strip()
    if len(content) > config.max_prompt_chars:
        content = content[: config.max_prompt_chars] + "\n\n[context truncated by reviewer]"
    return content


def openrouter_review(prompt: str, schema: dict[str, Any], config: Config) -> tuple[dict[str, Any], str]:
    api_key = env_required("OPENROUTER_API_KEY")
    system_prompt = read_text("prompts/openrouter-pr-review-system.md")
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "openrouter_pr_review",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DCOIR-Collector/dcoir-collector",
        "X-OpenRouter-Title": "DCOIR OpenRouter PR Review",
    }
    req = urllib.request.Request(OPENROUTER_API, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter API failed: {exc.code} {detail}") from exc
    data = json.loads(raw)
    model_used = str(data.get("model", config.model))
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("OpenRouter returned an empty response")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Some free models may wrap JSON in a fenced block. Try one conservative recovery.
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(1))
    return parsed, model_used


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


def build_inline_comment(finding: dict[str, Any]) -> str:
    title = str(finding.get("title", "Finding")).strip()
    severity = str(finding.get("severity", "medium")).upper()
    confidence = float(finding.get("confidence", 0))
    body = str(finding.get("body", "")).strip()
    validation = str(finding.get("validation", "")).strip()
    suggestion = str(finding.get("suggested_replacement", "")).rstrip()
    parts = [
        f"**{severity}: {title}**",
        "",
        body,
        "",
        f"Confidence: `{confidence:.2f}`",
    ]
    if suggestion:
        parts.extend(["", "Suggested fix:", "", "```suggestion", suggestion, "```"])
    if validation:
        parts.extend(["", "Validation expected after fix:", "", "```text", validation, "```"])
    return github_safe_body("\n".join(parts), limit=12000)


def build_review_body(result: dict[str, Any], findings: list[dict[str, Any]], model_used: str, config: Config) -> str:
    summary = str(result.get("summary", "OpenRouter review completed.")).strip()
    if findings:
        event_text = "Review posted with inline findings."
    else:
        event_text = "No high-confidence inline findings were found in the changed diff."
    commands = "\n".join(f"- `{cmd}`" for cmd in config.validation_commands) or "- No validation commands configured."
    return github_safe_body(
        f"""{MARKER}
### OpenRouter PR review

{summary}

Result: {event_text}

Model used: `{model_used}`

Validation guidance:
{commands}

Notes:
- This bot does not push commits or auto-fix branches.
- Inline suggestions are proposed patches for a human reviewer to apply.
- The job reads PR diffs through the GitHub API and checks out only the trusted default branch.
""".strip()
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
    if not command_matches(comment_body, config.commands):
        print("Comment does not match configured review commands")
        return

    schema = json.loads(read_text("schemas/openrouter-pr-review.schema.json"))
    gh = GitHubClient(token, repo)
    eyes_reaction_id = 0
    status_comment_id = 0

    try:
        reaction = gh.create_issue_comment_reaction(trigger_comment_id, "eyes")
        eyes_reaction_id = int(reaction.get("id", 0))
    except Exception as exc:
        print(f"WARN: unable to add eyes reaction: {exc}", file=sys.stderr)

    status_comment = gh.create_issue_comment(
        pr_number,
        f"{MARKER}\nPreparing OpenRouter PR review for `{repo}` PR #{pr_number}...",
    )
    status_comment_id = int(status_comment.get("id", 0))

    try:
        pr = gh.get_pr(pr_number)
        diff = gh.get_pr_diff(pr_number)
        files = gh.list_files(pr_number)
        prompt = build_prompt(pr, files, diff, config)
        result, model_used = openrouter_review(prompt, schema, config)
        line_index = build_diff_line_index(diff)
        findings = normalize_findings(result, config, line_index)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append(
                {
                    "path": path,
                    "position": line_index[(path, line)],
                    "body": build_inline_comment(finding),
                }
            )

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        review_body = build_review_body(result, findings, model_used, config)
        gh.create_review(pr_number, review_body, event, comments, str(pr.get("head", {}).get("sha", "")))

        final = f"""{MARKER}
OpenRouter PR review completed.

- Model used: `{model_used}`
- Inline findings posted: `{len(comments)}`
- Event: `{event}`
- Auto-fix: `disabled`
""".strip()
        if status_comment_id:
            gh.update_issue_comment(status_comment_id, final)
    except Exception as exc:
        error_body = f"""{MARKER}
OpenRouter PR review failed.

```text
{str(exc)[:4000]}
```
""".strip()
        if status_comment_id:
            gh.update_issue_comment(status_comment_id, error_body)
        raise
    finally:
        if eyes_reaction_id:
            try:
                gh.delete_issue_comment_reaction(trigger_comment_id, eyes_reaction_id)
            except Exception as exc:
                print(f"WARN: unable to remove eyes reaction: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
