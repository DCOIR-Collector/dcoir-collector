#!/usr/bin/env python3
"""Pareto routing and first-pass context wrapper for the hardened PR reviewer."""

from __future__ import annotations

import base64
import copy
import json
import os
import re
import signal
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import openrouter_pr_review_hardened as hardened


base = hardened.base
CONTEXT_REVIEW_MARKER = "Context mode:"


def optional_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value in ("", None):
        return None
    return float(value)


def load_pareto_context_config(path: str) -> Any:
    config = hardened.load_hardened_config(path)
    data = hardened.parse_yaml_like_data(path)
    config.pareto_min_coding_score = optional_float(data, "pareto_min_coding_score")
    config.first_pass_deep_review = hardened.bool_value(data, "first_pass_deep_review", True)
    config.deep_review_max_files = int(data.get("deep_review_max_files", min(getattr(config, "max_files", 30), 8)))
    config.deep_review_max_file_chars = int(data.get("deep_review_max_file_chars", 12000))
    config.deep_review_max_total_chars = int(data.get("deep_review_max_total_chars", 24000))
    hardened.ensure_free_models_are_opt_in(config)
    return config


_original_build_openrouter_payload = hardened.build_openrouter_payload


def build_openrouter_payload(
    prompt: str,
    schema: dict[str, Any],
    config: Any,
    ignored_providers: list[str],
    model: str,
) -> dict[str, Any]:
    payload = _original_build_openrouter_payload(prompt, schema, config, ignored_providers, model)
    if model.startswith("openrouter/pareto-code"):
        plugin: dict[str, Any] = {"id": "pareto-router"}
        min_coding_score = getattr(config, "pareto_min_coding_score", None)
        if min_coding_score is not None:
            plugin["min_coding_score"] = min_coding_score
        payload["plugins"] = [plugin]
    return payload


hardened.build_openrouter_payload = build_openrouter_payload


def command_option_tokens(body: str, command: str) -> set[str]:
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    if not first_line.startswith(command):
        return set()
    suffix = first_line[len(command) :].strip().lower()
    return {token for token in re.split(r"[\s,]+", suffix) if token}


def review_mode_for_command(body: str, command: str, config: Any, prior_successful_review: bool) -> str:
    tokens = command_option_tokens(body, command)
    if {"deep", "exhaustive"} & tokens:
        return "deep-forced"
    if "diff" in tokens:
        return "diff"
    if getattr(config, "first_pass_deep_review", True) and not prior_successful_review:
        return "first-pass-deep"
    return "diff"


def list_pr_reviews(gh: Any, pr_number: int) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh.request("GET", f"/repos/{gh.repo}/pulls/{pr_number}/reviews?per_page=100&page={page}")
        if not batch:
            break
        reviews.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return reviews


def has_prior_successful_context_review(gh: Any, pr_number: int) -> bool:
    for review in list_pr_reviews(gh, pr_number):
        body = str(review.get("body", ""))
        if base.MARKER in body and CONTEXT_REVIEW_MARKER in body:
            return True
    return False


def language_hint(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".bash": "bash",
        ".cjs": "javascript",
        ".js": "javascript",
        ".json": "json",
        ".md": "markdown",
        ".mjs": "javascript",
        ".ps1": "powershell",
        ".psd1": "powershell",
        ".psm1": "powershell",
        ".py": "python",
        ".sh": "bash",
        ".ts": "typescript",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def fetch_pr_file_text(gh: Any, path: str, ref: str) -> str:
    encoded_path = urllib.parse.quote(path, safe="/")
    encoded_ref = urllib.parse.quote(ref, safe="")
    payload = gh.request("GET", f"/repos/{gh.repo}/contents/{encoded_path}?ref={encoded_ref}")
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise RuntimeError("content API did not return a file")
    if payload.get("encoding") != "base64":
        raise RuntimeError("content API did not return base64 text")
    raw = base64.b64decode(str(payload.get("content", "")).replace("\n", ""))
    return raw.decode("utf-8")


def build_deep_context_block(gh: Any, pr: dict[str, Any], files: list[dict[str, Any]], config: Any, review_mode: str) -> tuple[str, str]:
    if review_mode == "diff":
        return "", "diff-focused review; no full changed-file context requested"
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return "", "deep context requested but PR head SHA was unavailable"

    max_files = max(0, int(getattr(config, "deep_review_max_files", 8)))
    max_file_chars = max(0, int(getattr(config, "deep_review_max_file_chars", 12000)))
    max_total_chars = max(0, int(getattr(config, "deep_review_max_total_chars", 24000)))
    lines = [
        "Deep changed-file context:",
        f"Mode: {review_mode}.",
        "Use this full changed-file context to reason about whole-file behavior and downstream effects, while anchoring actionable findings to changed lines when practical.",
    ]
    included: list[str] = []
    omitted: list[str] = []
    remaining = max_total_chars

    for item in files[:max_files]:
        path = str(item.get("filename", "")).strip()
        status = str(item.get("status", "")).strip()
        if not path:
            continue
        if status in {"removed", "deleted"}:
            omitted.append(f"{path} (deleted)")
            continue
        try:
            text = base.sanitize_text(fetch_pr_file_text(gh, path, head_sha), config)
        except UnicodeDecodeError:
            omitted.append(f"{path} (not utf-8 text)")
            continue
        except Exception as exc:
            omitted.append(f"{path} ({str(exc)[:120]})")
            continue
        truncated = len(text) > max_file_chars
        snippet = text[:max_file_chars]
        if truncated:
            snippet = f"{snippet}\n\n[full-file context truncated for this file]"
        block = f"### {path}\nStatus: {status}; head ref: {head_sha[:12]}\n~~~{language_hint(path)}\n{snippet}\n~~~"
        if len(block) > remaining:
            if not included and remaining > 400:
                block = block[: remaining - 35] + "\n\n[deep context budget exhausted]"
            else:
                omitted.append(f"{path} (deep context budget)")
                continue
        lines.append(block)
        included.append(f"{path}{' (truncated)' if truncated else ''}")
        remaining -= len(block)
        if remaining <= 400:
            break

    if not included:
        return "", f"{review_mode}; no changed-file context included; omitted: {', '.join(omitted) or 'none'}"
    summary = f"{review_mode}; included {len(included)} file context block(s): {', '.join(included[:6])}"
    if len(included) > 6:
        summary += f", and {len(included) - 6} more"
    if omitted:
        summary += f"; omitted {len(omitted)}: {', '.join(omitted[:4])}"
    return "\n\n".join(lines), summary


def build_prompt(
    pr: dict[str, Any],
    files: list[dict[str, Any]],
    diff: str,
    config: Any,
    risk_sentinels: list[hardened.RiskSentinel],
    deep_context_block: str,
    review_mode: str,
    context_summary: str,
) -> str:
    context = base.sanitize_text(deep_context_block.strip(), config)
    if context:
        budget = max(0, min(len(context), int(getattr(config, "deep_review_max_total_chars", 24000))))
        marker = "\n\n[deep context truncated by reviewer]"
        if len(context) > budget:
            context = f"{context[: max(0, budget - len(marker))]}{marker}"

    prompt_config = copy.copy(config)
    prompt_config.max_prompt_chars = max(0, config.max_prompt_chars - len(context) - 1000)
    prompt = hardened.build_prompt(pr, files, diff, prompt_config, risk_sentinels)
    mode_lines = [
        f"{CONTEXT_REVIEW_MARKER} {review_mode}",
        f"Context readback: {context_summary}",
        "When deep context is present, use it to reason about full changed-file behavior, but anchor actionable findings to changed lines when practical.",
    ]
    suffix = "\n\n".join(["\n".join(mode_lines), context]).strip()
    return hardened.append_with_budget(prompt, suffix, config.max_prompt_chars) if suffix else prompt


def append_context_to_review_body(body: str, review_mode: str, context_summary: str) -> str:
    return base.github_safe_body(f"{body}\n\n{CONTEXT_REVIEW_MARKER} `{review_mode}`\n\nContext readback: {context_summary}")


def main() -> None:
    repo = base.env_required("GITHUB_REPOSITORY")
    pr_number = int(base.env_required("PR_NUMBER"))
    token = base.env_required("GITHUB_TOKEN")
    trigger_comment_id = int(base.env_required("TRIGGER_COMMENT_ID"))
    comment_body = os.environ.get("TRIGGER_COMMENT_BODY", "")
    author = os.environ.get("TRIGGER_AUTHOR", "")
    config_path = os.environ.get("OPENROUTER_REVIEW_CONFIG", ".github/openrouter-pr-review-pareto.yml")
    config = load_pareto_context_config(config_path)

    if author in config.ignored_authors:
        print(f"Ignoring denied author {author}")
        return
    if config.allowed_authors and author not in config.allowed_authors:
        print(f"Ignoring unauthorized author {author}")
        return
    command = hardened.matching_command(comment_body, config.commands)
    if not command:
        print("Comment does not match configured review commands")
        return

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise hardened.ReviewTimeoutError(f"OpenRouter PR review exceeded script timeout of {config.script_timeout_seconds} seconds")

    schema = json.loads(base.read_text("schemas/openrouter-pr-review.schema.json"))
    gh = base.GitHubClient(token, repo)
    reporter = hardened.ProgressReporter(gh, pr_number, command, config)
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
        try:
            prior_successful_review = has_prior_successful_context_review(gh, pr_number)
            reporter.update("review-mode", f"prior context review found: {str(prior_successful_review).lower()}")
        except Exception as exc:
            prior_successful_review = False
            reporter.update("review-mode", f"prior context review readback failed; using first-pass posture: {str(exc)[:240]}")
        review_mode = review_mode_for_command(comment_body, command, config, prior_successful_review)
        deep_context_block, context_summary = build_deep_context_block(gh, pr, files, config, review_mode)
        reporter.update("context", context_summary)
        risk_sentinels = hardened.detect_risk_sentinels(diff, getattr(config, "risk_sentinel_max_anchors", 12))
        if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
            reporter.update("risk-sentinel", f"detected {len(risk_sentinels)} high-risk changed-line signals: {hardened.risk_sentinel_digest(risk_sentinels)}")
        reporter.update("prompt", f"building bounded prompt from {len(files)} changed files")
        prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        result, model_used, service_tier = hardened.openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels)
        reporter.update("normalize", "mapping model findings to changed diff lines")
        line_index = base.build_diff_line_index(diff)
        findings = hardened.normalize_findings(result, config, line_index)
        hardened.enforce_risk_sentinel_findings(findings, risk_sentinels, config)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        review_body = append_context_to_review_body(base.build_review_body(result, findings, model_used, config), review_mode, context_summary)
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments")
        gh.create_review(pr_number, review_body, event, comments, str(pr.get("head", {}).get("sha", "")))
        hardened.remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        tier_note = f"; service_tier={service_tier}" if service_tier else ""
        reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        reporter.complete(f"{model_used}{tier_note}", len(comments), event)
    except Exception as exc:
        hardened.remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        try:
            reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        except Exception as reporter_exc:
            print(f"WARN: unable to update reaction status: {reporter_exc}", file=sys.stderr, flush=True)
        reporter.fail(hardened.sanitize_github_output(str(exc), config))
        raise
    finally:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)


if __name__ == "__main__":
    main()
