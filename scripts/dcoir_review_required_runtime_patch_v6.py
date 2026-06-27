"""Sixth required-coverage layer for DCOIR Review.

This layer adds a guarded OpenRouter Auto prompt-review pass before Pareto
model calls, while fixing the PR #329 deterministic failures around helper
compatibility, env-token redaction provenance, YAML metadata-shell semantics,
and required-coverage debug readback.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v2 as v2
import dcoir_review_required_runtime_patch_v3 as v3
import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5

PROMPT_REVIEW_MODEL = "openrouter/auto"
PROMPT_REVIEW_MAX_ADDENDUM_CHARS = 1800
PROMPT_REVIEW_MAX_INPUT_CHARS = 90000
PROMPT_REVIEW_SECTION_TITLE = "Prompt-review supplemental guidance"

ENV_PROVENANCE_LINE_RE = re.compile(
    r"(?m)^.*(?:os\.environ(?:\.get)?|os\.getenv|\$env:|process\.env\.|Environment::GetEnvironmentVariable)[^\n]*$"
)
SAFE_BEARER_EXPR_RE = re.compile(
    r"(?P<prefix>[fFrRbBuU]*)(?P<quote>[\"'])(?P<body>Bearer\s+(?:\{[^}\n]+\}|\$env:[A-Za-z_][A-Za-z0-9_]*|\$\{[^}\n]+\}|\$[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*%))(?P=quote)"
)
SENTINEL_ANCHOR_RE = re.compile(r"(?m)^- (?P<anchor>[^:\n]+:\d+ \[[^\]\n]+\])")
ENV_PROVENANCE_TOKEN_RE = re.compile(
    r"os\.environ(?:\.get)?\([^\n)]*\)|os\.environ\[[^\n\]]+\]|os\.getenv\([^\n)]*\)|\$env:[A-Za-z_][A-Za-z0-9_]*|process\.env\.[A-Za-z_][A-Za-z0-9_]*|Environment::GetEnvironmentVariable\([^\n)]*\)"
)
FORBIDDEN_ADDENDUM_RE = re.compile(
    r"```|\b(?:remove|delete|omit|ignore|weaken|downgrade)\b[^.\n]{0,80}\b(?:sentinel|anchor|finding|schema|changed line|diff|code block)\b|\bsummary-only\b|\bredacted-secret\b",
    re.IGNORECASE,
)

PROMPT_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["use_original", "supplemental_instructions", "risk_notes", "preserved_constraints", "rejected_changes"],
    "properties": {
        "use_original": {"type": "boolean"},
        "supplemental_instructions": {"type": "string"},
        "risk_notes": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "preserved_constraints": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
        "rejected_changes": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
    },
}

_prompt_review_lock = threading.Lock()
_prompt_review_counter = 0
_prompt_review_cache: dict[str, tuple[str, dict[str, Any]]] = {}


def _next_prompt_review_id() -> int:
    global _prompt_review_counter
    with _prompt_review_lock:
        _prompt_review_counter += 1
        return _prompt_review_counter


def _sha12(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def _prompt_kind(prompt: str) -> str:
    lower = prompt.lower()
    if "per-file detector pass" in lower:
        return "per-file-detector"
    if "review quality retry" in lower:
        return "quality-retry"
    if "fix synthesis" in lower or "structured repair data" in lower:
        return "fix-synthesis"
    if "context mode:" in lower:
        return "whole-pr-detector"
    return "model-prompt"


def _protect_env_provenance(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def stash(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"__DCOIR_ENV_PROVENANCE_{len(protected) - 1}__"

    result = ENV_PROVENANCE_LINE_RE.sub(stash, text)
    result = SAFE_BEARER_EXPR_RE.sub(stash, result)
    return result, protected


def _restore_env_provenance(text: str, protected: list[str]) -> str:
    result = text
    for index, value in enumerate(protected):
        result = result.replace(f"__DCOIR_ENV_PROVENANCE_{index}__", value)
    return result


def _extract_sentinel_anchors(prompt: str) -> list[str]:
    return [match.group("anchor") for match in SENTINEL_ANCHOR_RE.finditer(prompt)]


def _extract_env_provenance(prompt: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for match in ENV_PROVENANCE_TOKEN_RE.finditer(prompt):
        value = match.group(0)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _review_enabled(config: Any) -> bool:
    env_value = os.environ.get("DCOIR_PROMPT_REVIEW", "").strip().lower()
    if env_value in {"0", "false", "no", "off", "disabled"}:
        return False
    return bool(getattr(config, "prompt_review_enabled", True))


def _should_review_model(model: str, config: Any) -> bool:
    if str(model or "") == PROMPT_REVIEW_MODEL:
        return False
    if not _review_enabled(config):
        return False
    if bool(getattr(config, "prompt_review_all_models", False)):
        return True
    return "pareto" in str(model or "").lower()


def _prompt_review_prompt(original_prompt: str, prompt_kind: str) -> str:
    clipped = original_prompt
    if len(clipped) > PROMPT_REVIEW_MAX_INPUT_CHARS:
        clipped = clipped[:PROMPT_REVIEW_MAX_INPUT_CHARS] + "\n\n[prompt clipped for prompt-review preflight]"
    return f"""
You are reviewing a DCOIR Review prompt before it is sent to a coding review model.
Your task is prompt engineering only.

Return structured JSON only. Do not rewrite the full prompt. Provide at most one supplemental instruction block that can be appended after the original prompt.

Hard constraints:
- Do not alter file paths, line numbers, changed code, diffs, code fences, full-file context, right-side changed-line maps, required risk-sentinel anchors, JSON schema rules, validation commands, repository guidance, PR metadata, or redaction placeholders.
- Do not weaken required coverage, deterministic fallback, env-token wording, or the requirement to return finding objects rather than summary-only concerns.
- If the original prompt is malformed, describe the problem in risk_notes and supplemental_instructions, but do not invent replacement source code.
- Keep supplemental_instructions concise, imperative, and directly useful to the next model.
- If no safe improvement is needed, set use_original to true and leave supplemental_instructions empty.

Prompt kind: {prompt_kind}

Original prompt:
<<<DCOIR_ORIGINAL_PROMPT
{clipped}
DCOIR_ORIGINAL_PROMPT
""".strip()


def _request_prompt_review(original_prompt: str, prompt_kind: str, config: Any, hardened: Any, base: Any) -> tuple[dict[str, Any], str, str]:
    api_key = base.env_required("OPENROUTER_API_KEY")
    payload: dict[str, Any] = {
        "model": PROMPT_REVIEW_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a prompt-engineering reviewer. Return only JSON that matches the requested schema.",
            },
            {"role": "user", "content": _prompt_review_prompt(original_prompt, prompt_kind)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "dcoir_prompt_review", "strict": True, "schema": PROMPT_REVIEW_SCHEMA},
        },
        "provider": {"allow_fallbacks": True, "require_parameters": True},
        "plugins": [{"id": "auto-router"}, {"id": "response-healing"}],
        "temperature": 0.1,
    }
    sticky_session = getattr(hardened, "session_id", lambda _config: "")(config)
    if sticky_session:
        payload["session_id"] = sticky_session
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DCOIR-Collector/dcoir-collector",
        "X-OpenRouter-Title": base.REVIEW_DISPLAY_NAME,
    }
    if sticky_session:
        headers["X-Session-Id"] = sticky_session
    req = urllib.request.Request(hardened.OPENROUTER_API, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    model_used = str(data.get("model", PROMPT_REVIEW_MODEL))
    service_tier = str(data.get("service_tier", "") or "")
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("prompt review returned empty response")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(1))
    return parsed, model_used, service_tier


def _clean_addendum(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > PROMPT_REVIEW_MAX_ADDENDUM_CHARS:
        text = text[:PROMPT_REVIEW_MAX_ADDENDUM_CHARS].rstrip() + "\n[prompt-review addendum truncated]"
    return text


def _candidate_with_addendum(original_prompt: str, addendum: str, config: Any) -> str:
    addendum = _clean_addendum(addendum)
    if not addendum:
        return original_prompt
    block = f"{PROMPT_REVIEW_SECTION_TITLE}:\n{addendum}"
    separator = "\n\n"
    max_chars = int(getattr(config, "max_prompt_chars", len(original_prompt) + len(block) + 2) or 0)
    if max_chars and len(original_prompt) + len(separator) + len(block) > max_chars:
        available = max_chars - len(original_prompt) - len(separator) - len(f"{PROMPT_REVIEW_SECTION_TITLE}:\n")
        if available < 160:
            return original_prompt
        addendum = addendum[:available].rstrip() + "\n[prompt-review addendum truncated]"
        block = f"{PROMPT_REVIEW_SECTION_TITLE}:\n{addendum}"
    return f"{original_prompt}{separator}{block}"


def _validate_reviewed_prompt(original_prompt: str, candidate: str, addendum: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if candidate == original_prompt:
        return True, reasons
    if not candidate.startswith(original_prompt):
        reasons.append("reviewed prompt did not preserve the original prompt as an immutable prefix")
    if FORBIDDEN_ADDENDUM_RE.search(addendum):
        reasons.append("supplemental instructions attempted to alter protected evidence or constraints")
    for anchor in _extract_sentinel_anchors(original_prompt):
        if anchor not in candidate:
            reasons.append(f"missing required sentinel anchor: {anchor}")
    for provenance in _extract_env_provenance(original_prompt):
        if provenance not in candidate:
            reasons.append(f"missing env-token provenance: {provenance}")
    if "findings" in original_prompt and "findings" not in candidate:
        reasons.append("structured findings contract was not preserved")
    return not reasons, reasons


def _write_prompt_review_debug(
    hardened: Any,
    config: Any,
    prompt_kind: str,
    original_prompt: str,
    candidate_prompt: str,
    metadata: dict[str, Any],
) -> None:
    sequence = _next_prompt_review_id()
    digest = _sha12(original_prompt)
    safe_kind = re.sub(r"[^A-Za-z0-9_.-]+", "-", prompt_kind)[:40] or "prompt"
    stem = f"prompt-review/{sequence:02d}-{safe_kind}-{digest}"
    hardened.write_debug_text_artifact_safely(config, f"prompts/{stem}-original.txt", original_prompt)
    if candidate_prompt != original_prompt:
        hardened.write_debug_text_artifact_safely(config, f"prompts/{stem}-reviewed.txt", candidate_prompt)
    hardened.write_debug_json_artifact_safely(config, f"metadata/{stem}.json", metadata)


def _review_prompt_once(original_prompt: str, config: Any, hardened: Any, base: Any) -> str:
    prompt_kind = _prompt_kind(original_prompt)
    cache_key = f"{prompt_kind}:{_sha12(original_prompt)}"
    if cache_key in _prompt_review_cache:
        return _prompt_review_cache[cache_key][0]
    metadata: dict[str, Any] = {
        "prompt_kind": prompt_kind,
        "original_chars": len(original_prompt),
        "model": PROMPT_REVIEW_MODEL,
        "accepted": False,
        "fallback_to_original": True,
        "validation_reasons": [],
    }
    candidate = original_prompt
    try:
        review, model_used, service_tier = _request_prompt_review(original_prompt, prompt_kind, config, hardened, base)
        metadata["model_used"] = model_used
        metadata["service_tier"] = service_tier
        metadata["use_original"] = bool(review.get("use_original", False))
        metadata["risk_notes"] = review.get("risk_notes", [])
        metadata["preserved_constraints"] = review.get("preserved_constraints", [])
        metadata["rejected_changes"] = review.get("rejected_changes", [])
        addendum = "" if bool(review.get("use_original", False)) else _clean_addendum(review.get("supplemental_instructions", ""))
        candidate = _candidate_with_addendum(original_prompt, addendum, config)
        ok, reasons = _validate_reviewed_prompt(original_prompt, candidate, addendum)
        metadata["validation_reasons"] = reasons
        metadata["addendum_chars"] = len(addendum)
        if ok:
            metadata["accepted"] = candidate != original_prompt
            metadata["fallback_to_original"] = candidate == original_prompt
        else:
            candidate = original_prompt
    except Exception as exc:
        metadata["error"] = str(exc)[:500]
        candidate = original_prompt
    metadata["reviewed_chars"] = len(candidate)
    _write_prompt_review_debug(hardened, config, prompt_kind, original_prompt, candidate, metadata)
    _prompt_review_cache[cache_key] = (candidate, metadata)
    return candidate


def _patch_sanitize_text(base: Any) -> None:
    original = getattr(base, "_dcoir_required_v6_original_sanitize_text", None)
    if original is None:
        original = getattr(base, "sanitize_text", None)
        base._dcoir_required_v6_original_sanitize_text = original
    if not callable(original):
        return

    def required_v6_sanitize_text(text: str, config: Any) -> str:
        protected_text, protected_values = _protect_env_provenance(str(text or ""))
        cleaned = original(protected_text, config)
        return _restore_env_provenance(cleaned, protected_values)

    base.sanitize_text = required_v6_sanitize_text


def _patch_yaml_metadata_priority() -> None:
    original_v4_line_kind = getattr(v4, "_dcoir_required_v6_original_line_kind", None)
    if original_v4_line_kind is None:
        original_v4_line_kind = v4._line_kind
        v4._dcoir_required_v6_original_line_kind = original_v4_line_kind

    def required_v6_v4_line_kind(path: str, text: str) -> str:
        suffix = Path(str(path or "").lower()).suffix
        if suffix in {".yml", ".yaml"} and v4._metadata_shell_line(str(text or "")):
            return v4.YAML_METADATA_SHELL
        return original_v4_line_kind(path, text)

    v4._line_kind = required_v6_v4_line_kind


def _patch_merge_summary(hardened: Any) -> None:
    original = getattr(hardened, "_dcoir_required_v6_original_merge_review_results", None)
    if original is None:
        original = getattr(hardened, "merge_review_results", None)
        hardened._dcoir_required_v6_original_merge_review_results = original
    if not callable(original):
        return

    def required_v6_merge_review_results(initial_result: dict[str, Any], retry_result: dict[str, Any]) -> dict[str, Any]:
        merged = original(initial_result, retry_result)
        retry_findings = hardened.result_findings(retry_result) if hasattr(hardened, "result_findings") else []
        retry_summary = str(retry_result.get("summary", "") if isinstance(retry_result, dict) else "")
        if not retry_findings and callable(getattr(hardened, "summary_suggests_problem", None)) and hardened.summary_suggests_problem(retry_summary):
            initial_summary = str(initial_result.get("summary", "") if isinstance(initial_result, dict) else "").strip()
            merged["summary"] = initial_summary or "Quality retry returned summary-only concerns; deterministic required fallback coverage was applied."
            merged["_dcoir_summary_only_retry_rejected"] = True
        return merged

    hardened.merge_review_results = required_v6_merge_review_results


def _patch_required_coverage_debug(hardened: Any) -> None:
    original = getattr(hardened, "_dcoir_required_v6_original_add_risk_sentinel_fallback_findings", None)
    if original is None:
        original = getattr(hardened, "add_risk_sentinel_fallback_findings", None)
        hardened._dcoir_required_v6_original_add_risk_sentinel_fallback_findings = original
    if not callable(original):
        return

    def required_v6_add_risk_sentinel_fallback_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        required = list(hardened.required_risk_sentinels(risk_sentinels)) if callable(getattr(hardened, "required_risk_sentinels", None)) else []
        before_covered = [
            sentinel for sentinel in required if any(hardened.finding_covers_risk_sentinel(finding, sentinel) for finding in [*findings, *(unanchored_findings or [])])
        ] if callable(getattr(hardened, "finding_covers_risk_sentinel", None)) else []
        result = original(findings, risk_sentinels, config, unanchored_findings)
        after_covered = [
            sentinel for sentinel in required if any(hardened.finding_covers_risk_sentinel(finding, sentinel) for finding in result)
        ] if callable(getattr(hardened, "finding_covers_risk_sentinel", None)) else []
        metadata = {
            "hard_required_count": len(required),
            "covered_before_count": len(before_covered),
            "covered_after_count": len(after_covered),
            "fallback_inserted_count": max(0, len(result) - len(findings)),
            "input_finding_count": len(findings),
            "postable_finding_count": len(result),
            "required_digest": [f"{getattr(item, 'path', '')}:{getattr(item, 'line', '')} {v5._sentinel_kind(item)}" for item in required],
            "covered_after_digest": [f"{getattr(item, 'path', '')}:{getattr(item, 'line', '')} {v5._sentinel_kind(item)}" for item in after_covered],
        }
        hardened.write_debug_json_artifact_safely(config, "metadata/required-v6-coverage.json", metadata)
        return result

    hardened.add_risk_sentinel_fallback_findings = required_v6_add_risk_sentinel_fallback_findings


def _patch_openrouter_prompt_review(hardened: Any, base: Any) -> None:
    original = getattr(hardened, "_dcoir_required_v6_original_openrouter_request_once", None)
    if original is None:
        original = getattr(hardened, "openrouter_request_once", None)
        hardened._dcoir_required_v6_original_openrouter_request_once = original
    if not callable(original):
        return

    def required_v6_openrouter_request_once(prompt: str, schema: dict[str, Any], config: Any, ignored_providers: list[str], model: str) -> tuple[dict[str, Any], str, str]:
        reviewed_prompt = prompt
        if _should_review_model(model, config):
            reviewed_prompt = _review_prompt_once(prompt, config, hardened, base)
        return original(reviewed_prompt, schema, config, ignored_providers, model)

    hardened.openrouter_request_once = required_v6_openrouter_request_once


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if base is None or hardened is None:
        return
    if not hasattr(v3, "_strip_fences"):
        v3._strip_fences = v2._strip_fences
    _patch_sanitize_text(base)
    _patch_yaml_metadata_priority()
    _patch_merge_summary(hardened)
    _patch_required_coverage_debug(hardened)
    _patch_openrouter_prompt_review(hardened, base)
