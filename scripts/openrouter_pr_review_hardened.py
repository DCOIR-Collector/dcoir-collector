#!/usr/bin/env python3
"""Hardened OpenRouter PR reviewer runner.

This wrapper reuses the existing OpenRouter reviewer safety helpers while
owning the governed routing payload and review-quality gates for issue #277.
"""

from __future__ import annotations

import copy
import json
import os
import re
import signal
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import openrouter_pr_review as base


OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"


class ReviewQualityError(RuntimeError):
    """Raised when the model output cannot support a useful PR review."""


class ReviewTimeoutError(TimeoutError):
    """Raised before the workflow timeout so cleanup can still run."""


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
        data.get("openrouter_session_id_prefix", "dcoir-openrouter-pr-review") or ""
    ).strip()
    config.smoke_test_free_model = bool_value(data, "smoke_test_free_model", False)
    config.fail_on_unanchored_findings = bool_value(data, "fail_on_unanchored_findings", True)
    config.fail_on_summary_only_problem = bool_value(data, "fail_on_summary_only_problem", True)
    config.script_timeout_seconds = int(data.get("script_timeout_seconds", getattr(config, "script_timeout_seconds", 1500)))
    config.post_progress_comment = bool_value(data, "post_progress_comment", getattr(config, "post_progress_comment", True))

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
        if getattr(self.config, "post_progress_comment", True):
            comment = self.gh.create_issue_comment(self.issue_number, self._body("running"))
            self.comment_id = int(comment.get("id", 0))

    def update(self, stage: str, message: str) -> None:
        self._record(stage, message)
        self._update_comment(self._body("running"))

    def complete(self, model_used: str, findings_count: int, review_event: str) -> None:
        plural = "finding" if findings_count == 1 else "findings"
        self._record("completed", f"posted GitHub review using {model_used}; {findings_count} inline {plural}; event={review_event}")
        self._update_comment(
            self._body(
                "completed",
                final_lines=[
                    f"- Result: GitHub review posted with `{findings_count}` inline {plural}.",
                    f"- Review event: `{review_event}`.",
                    f"- Model used: `{model_used}`.",
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
            print(f"[openrouter-pr-review] {stage}: {safe_message}", flush=True)

    def _body(self, state: str, final_lines: list[str] | None = None) -> str:
        lines = [
            base.MARKER,
            f"OpenRouter PR review {state}.",
            "",
            f"- Command: `{self.command}`.",
            f"- Model stack: `{model_stack_label(self.config)}`.",
            "- Branch changes: none; this workflow only posts review output.",
            "- Gate role: internal review-assist signal before any separately approved external review request.",
        ]
        if final_lines:
            lines.extend(["", *final_lines])
        lines.extend(["", "Progress:"])
        for stage, message in self.steps[-12:]:
            lines.append(f"- `{stage}`: {message}")
        return base.github_safe_body("\n".join(lines), limit=12000)

    def _update_comment(self, body: str, create_if_missing: bool = False) -> None:
        if not getattr(self.config, "post_progress_comment", True):
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


def build_prompt(pr: dict[str, Any], files: list[dict[str, Any]], diff: str, config: Any) -> str:
    hardening = """

Governed review hardening requirements:
- Do not hide actionable issues only in the summary. Every semantic, Markdown, governance, validation, or review-gate concern must be returned as a finding object.
- For Markdown and governed-source findings, anchor the finding to the nearest changed right-side line that introduced or materially preserves the risky wording.
- If a small suggestion block is not safe, leave suggested_replacement empty and put exact repair steps in the finding body.
- Each finding body must include observed behavior, impact, exact correction guidance, and validation or readback guidance.
""".strip()
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
        "X-OpenRouter-Title": "DCOIR OpenRouter PR Review",
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


def summary_suggests_problem(summary: str) -> bool:
    cleaned = re.sub(r"[^a-z0-9]+", " ", summary.lower()).strip()
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
    negated_problem_patterns = (
        r"\bno\b(?:\s+[a-z0-9]+){0,8}\s+(?:findings?|issues?|problems?|regressions?|risks?|failures?|bypasses?)\b"
        r"(?:\s+(?:were|was|are|is|found|identified|detected|observed|present|remaining|remain))*",
        r"\bnot\b(?:\s+[a-z0-9]+){0,5}\s+(?:found|identified|detected|observed)\b",
    )

    def clause_suggests_problem(clause: str) -> bool:
        stripped = clause
        for phrase in negative_phrases:
            stripped = stripped.replace(phrase, " ")
        for pattern in negated_problem_patterns:
            stripped = re.sub(pattern, " ", stripped)
        return any(re.search(rf"\b{re.escape(term)}s?\b", stripped) for term in positive_terms)

    clauses = re.split(r"\b(?:and|but|however|though|although|yet|except|nevertheless|still)\b", cleaned)
    return any(clause_suggests_problem(clause.strip()) for clause in clauses if clause.strip())


def normalize_findings(result: dict[str, Any], config: Any, line_index: dict[tuple[str, int], int]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    rejected: list[str] = []
    raw_findings = result.get("findings", [])
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
            rejected.append(f"{path or '<missing-path>'}:{line or '<missing-line>'} low confidence {confidence:.2f} ({title})")
            continue
        if (path, line) not in line_index:
            rejected.append(f"{path or '<missing-path>'}:{line or '<missing-line>'} not in changed diff ({title})")
            continue
        findings.append(item)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_order.get(str(f.get("severity", "low")), 9), -float(f.get("confidence", 0))))
    findings = findings[: config.max_inline_comments]
    if findings:
        return findings

    if raw_findings and getattr(config, "fail_on_unanchored_findings", True):
        details = "; ".join(rejected[:6]) if rejected else "no accepted findings"
        raise ReviewQualityError(
            "OpenRouter review quality failure: the model returned findings, but none became actionable inline comments. "
            f"Rejected findings: {details}."
        )

    summary = str(result.get("summary", "")).strip()
    if getattr(config, "fail_on_summary_only_problem", True) and summary_suggests_problem(summary):
        raise ReviewQualityError(
            "OpenRouter review quality failure: the model summary indicated a possible issue, but the structured findings "
            "array was empty. The review must produce actionable file/line findings or a clean summary."
        )

    return []


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

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise ReviewTimeoutError(f"OpenRouter PR review exceeded script timeout of {config.script_timeout_seconds} seconds")

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
        reporter.update("prompt", f"building bounded prompt from {len(files)} changed files")
        prompt = build_prompt(pr, files, diff, config)
        result, model_used, service_tier = openrouter_review(prompt, schema, config, reporter)
        reporter.update("normalize", "mapping model findings to changed diff lines")
        line_index = base.build_diff_line_index(diff)
        findings = normalize_findings(result, config, line_index)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        review_body = base.build_review_body(result, findings, model_used, config)
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments")
        gh.create_review(pr_number, review_body, event, comments, str(pr.get("head", {}).get("sha", "")))
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
