"""Twelfth required-coverage layer for DCOIR Review.

This connector-safe layer fixes the #336 selection/ledger failure without
editing the large reviewer script. It keeps v11's public rendering behavior,
then adds:

- deterministic Python archive/path-write sentinel insertion
- deterministic fallback for privileged untrusted checkout
- post-suppression required backfill so inline budget is not wasted
- final ledger accounting for every detected required sentinel
- same-line Python env-token/SSRF coalescing for callback sinks
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v9 as v9
import dcoir_review_required_runtime_patch_v9_core as core
import dcoir_review_required_runtime_patch_v9_selection as selection
import dcoir_review_required_runtime_patch_v10 as v10
import dcoir_review_required_runtime_patch_v11 as v11

SentinelKey = tuple[str, int, str]

VERSION = "v12"


def _preserve_v11_helper(name: str) -> Any:
    storage_name = f"_dcoir_required_v12_original_{name.lstrip('_')}"
    existing = getattr(v11, storage_name, None)
    if callable(existing):
        return existing
    helper = getattr(v11, name)
    setattr(v11, storage_name, helper)
    return helper


_ORIGINAL_V11_POSTABLE_KEY = _preserve_v11_helper("_postable_key")
_ORIGINAL_V11_VALIDATION_FOR_KEY = _preserve_v11_helper("_validation_for_key")
REQUIRED_KINDS = {
    v10.YAML_TOKEN_TO_PR_URL,
    v4.YAML_METADATA_SHELL,
    v4.YAML_SHELL_PIPE,
    v4.YAML_PULL_REQUEST_TARGET,
    v4.YAML_UNTRUSTED_CHECKOUT,
    v4.YAML_BROAD_WRITE,
    v9.PYTHON_PICKLE_LOAD,
    v5.PYTHON_YAML_LOAD,
    v5.PYTHON_SHELL_EXEC,
    v5.PYTHON_ENV_TOKEN,
    v11.PYTHON_ARCHIVE_EXTRACT,
    v11.PYTHON_PATH_WRITE,
    v9.PS_DYNAMIC_EXEC,
    v4.PS_ACL,
    v4.PS_PROCESS_LAUNCH,
    v5.PS_ENV_TOKEN,
}


def _canonical_kind(kind: str, text: str = "", detail: str = "") -> str:
    value = str(kind or "")
    context = v11._normalize(f"{text}\n{detail}")
    if value == getattr(v4, "PYTHON_SSRF", "python_ssrf"):
        has_token_source = "dcoir_token" in context or "os.environ" in context or "os.getenv" in context
        has_auth_token = "authorization" in context and ("bearer" in context or "token" in context)
        has_callback = (
            "callback" in context
            or "requests." in context
            or "request-controlled" in context
        )
        if has_callback and (has_token_source or has_auth_token):
            return v5.PYTHON_ENV_TOKEN
    return v11._canonical_kind(value)


def _sentinel_key(sentinel: Any) -> SentinelKey:
    path = str(getattr(sentinel, "path", "") or "")
    line = core._line_number(getattr(sentinel, "line", 0))
    text = str(getattr(sentinel, "text", "") or "")
    detail = "\n".join(str(getattr(sentinel, name, "") or "") for name in ("label", "detail"))
    kind = v11._line_kind(path, text) or v11._base_sentinel_key(sentinel)[2]
    if not kind:
        kinds = v11._text_kinds(path, f"{text}\n{detail}")
        kind = sorted(kinds, key=lambda item: _kind_rank(item))[0] if kinds else ""
    return path, line, _canonical_kind(kind, text, detail)


def _postable_key(finding: dict[str, Any]) -> SentinelKey:
    path, line, kind = _ORIGINAL_V11_POSTABLE_KEY(finding)
    text = "\n".join(
        str(finding.get(name, "") or "")
        for name in ("title", "body", "description", "_anchored_line_text")
    )
    return path, line, _canonical_kind(kind, text, text)


def _coverage_key(key: SentinelKey) -> SentinelKey:
    path, line, kind = key
    if kind == v4.YAML_BROAD_WRITE:
        return path, 0, kind
    if kind == v11.PYTHON_ARCHIVE_EXTRACT:
        return path, 0, kind
    return path, line, kind


def _kind_rank(kind: str) -> int:
    order = {
        v10.YAML_TOKEN_TO_PR_URL: 0,
        v4.YAML_SHELL_PIPE: 1,
        v4.YAML_UNTRUSTED_CHECKOUT: 2,
        v4.YAML_METADATA_SHELL: 3,
        v4.YAML_PULL_REQUEST_TARGET: 4,
        v4.YAML_BROAD_WRITE: 5,
        v9.PS_DYNAMIC_EXEC: 10,
        v4.PS_ACL: 11,
        v4.PS_PROCESS_LAUNCH: 12,
        v5.PS_ENV_TOKEN: 13,
        v9.PYTHON_PICKLE_LOAD: 20,
        v5.PYTHON_YAML_LOAD: 21,
        v5.PYTHON_SHELL_EXEC: 22,
        v5.PYTHON_ENV_TOKEN: 23,
        v11.PYTHON_ARCHIVE_EXTRACT: 24,
        v11.PYTHON_PATH_WRITE: 25,
        v11.K8S_HOST_NETWORK: 40,
        v11.K8S_PRIVILEGED_CONTAINER: 41,
        v11.K8S_PRIVILEGE_ESCALATION: 42,
        v11.K8S_HOST_PATH: 43,
    }
    return order.get(str(kind or ""), 99)


def _sentinel_sort_key(sentinel: Any) -> tuple[int, str, int, str]:
    path, line, kind = _sentinel_key(sentinel)
    text = str(getattr(sentinel, "text", "") or "")
    bonus = 1 if kind == v11.PYTHON_ARCHIVE_EXTRACT and "extractall" not in v11._normalize(text) else 0
    return _kind_rank(kind) + bonus, path, line, text


def _family(kind: str) -> str:
    if kind.startswith("yaml_"):
        return "yaml"
    if kind.startswith("ps_"):
        return "powershell"
    if kind.startswith("python_"):
        return "python"
    if kind.startswith("k8s_"):
        return "kubernetes"
    return "other"


def _spare_priority(finding: dict[str, Any]) -> tuple[int, int, int, float, str, int]:
    path, line, kind = _postable_key(finding)
    optional = "/optional_" in path.lower() or path.rsplit("/", 1)[-1].startswith("optional_")
    family_rank = {"yaml": 0, "powershell": 1, "python": 2, "kubernetes": 4, "other": 5}.get(_family(kind), 5)
    if optional:
        family_rank += 5
    return family_rank, _kind_rank(kind), core._severity_rank(finding), -core._confidence(finding), path, line


def _required_sentinels(hardened: Any, risk_sentinels: list[Any]) -> list[Any]:
    required: list[Any] = []
    seen: set[SentinelKey] = set()
    for sentinel in v11._base_required_sentinels(hardened, risk_sentinels):
        key = _sentinel_key(sentinel)
        if key[2] in REQUIRED_KINDS and key not in seen:
            required.append(sentinel)
            seen.add(key)
    for sentinel in risk_sentinels:
        key = _sentinel_key(sentinel)
        if key[2] in REQUIRED_KINDS and key not in seen:
            required.append(sentinel)
            seen.add(key)
    return required


def _coalesce_required(required: list[Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    targets: list[Any] = []
    seen: set[SentinelKey] = set()
    duplicates: list[dict[str, Any]] = []
    for sentinel in sorted(required, key=_sentinel_sort_key):
        key = _sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in seen:
            duplicates.append(_sentinel_record(sentinel, "duplicate_covered", set(), set(), 0))
            continue
        seen.add(coverage)
        targets.append(sentinel)
    return targets, duplicates


def _expected_by_line(hardened: Any, risk_sentinels: list[Any]) -> dict[tuple[str, int], set[str]]:
    expected: dict[tuple[str, int], set[str]] = {}
    for sentinel in _required_sentinels(hardened, risk_sentinels):
        path, line, kind = _sentinel_key(sentinel)
        expected.setdefault((path, line), set()).add(kind)
    return expected


def _semantic_mismatch(finding: dict[str, Any], expected: dict[tuple[str, int], set[str]]) -> bool:
    path, line, kind = _postable_key(finding)
    allowed = expected.get((path, line), set())
    if not allowed:
        return False
    explicit = v11._explicit_kind(finding)
    if explicit and _canonical_kind(explicit) not in allowed:
        return True
    title_kinds = v11._title_kinds(finding)
    if title_kinds and not ({_canonical_kind(item) for item in title_kinds} & allowed):
        return True
    return kind not in allowed


def _fallback_for_sentinel(hardened: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    path, line, kind = key
    line_text = str(getattr(sentinel, "text", "") or "")
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        fallback = {
            "title": "Privileged workflow checks out untrusted PR code",
            "severity": "critical",
            "confidence": 0.99,
            "path": path,
            "line": line,
            "body": (
                "This privileged workflow checks out pull request controlled code. "
                "Do not combine `pull_request_target` privileges with PR-controlled refs or head SHAs."
            ),
            "suggested_replacement": "",
            "validation": _validation_for_key(kind, path, line),
            "fix_guidance": {
                "language": "yaml",
                "notes": "Use a trusted base ref, or split privileged metadata handling from untrusted code checkout/execution.",
                "validation": _validation_for_key(kind, path, line),
            },
        }
    else:
        fallback = v11._fallback_for_sentinel(hardened, sentinel, config)
    fallback["_risk_sentinel_key"] = [path, line, kind]
    fallback["_risk_sentinel_kind"] = kind
    fallback["_anchored_line_text"] = line_text
    return fallback


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    if kind == v10.YAML_TOKEN_TO_PR_URL:
        return v10._validation_for_token_to_pr_url(path)
    return _ORIGINAL_V11_VALIDATION_FOR_KEY(kind, path, line)


def _dedupe(findings: list[dict[str, Any]], expected: dict[tuple[str, int], set[str]]) -> tuple[list[dict[str, Any]], list[str]]:
    kept: dict[SentinelKey, dict[str, Any]] = {}
    order: list[SentinelKey] = []
    dropped: list[str] = []
    for finding in findings:
        item = v5._normalize_comment_finding(finding)
        key = _postable_key(item)
        if _semantic_mismatch(item, expected):
            dropped.append(f"{key[0]}:{key[1]} expected={','.join(sorted(expected.get((key[0], key[1]), set())))} actual={key[2]}")
            continue
        if not key[2]:
            dropped.append(f"{key[0]}:{key[1]} empty semantic kind")
            continue
        if key not in kept:
            kept[key] = item
            order.append(key)
            continue
        dropped.append(f"{key[0]}:{key[1]} duplicate {key[2]}")
        if (core._severity_rank(item), -core._confidence(item)) < (
            core._severity_rank(kept[key]),
            -core._confidence(kept[key]),
        ):
            kept[key] = item
    return [kept[key] for key in order], dropped


def _balanced_required_order(targets: list[Any]) -> list[Any]:
    buckets: dict[str, list[Any]] = {}
    for sentinel in targets:
        buckets.setdefault(_family(_sentinel_key(sentinel)[2]), []).append(sentinel)
    for family, values in list(buckets.items()):
        buckets[family] = sorted(values, key=_sentinel_sort_key)
    result: list[Any] = []
    family_order = ["yaml", "powershell", "python", "other", "kubernetes"]
    while any(buckets.get(family) for family in family_order):
        for family in family_order:
            bucket = buckets.get(family) or []
            if bucket:
                result.append(bucket.pop(0))
    return result


def _fallback_candidate(
    hardened: Any,
    sentinel: Any,
    config: Any,
    expected: dict[tuple[str, int], set[str]],
) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    fallback = _fallback_for_sentinel(hardened, sentinel, config)
    normalized = dict(fallback) if fallback.get("_dcoir_v9_known_fallback") or fallback.get("_dcoir_v10_known_fallback") else v5._normalize_comment_finding(fallback)
    normalized["_risk_sentinel_key"] = list(key)
    normalized["_risk_sentinel_kind"] = key[2]
    normalized["_anchored_line_text"] = str(getattr(sentinel, "text", "") or "")
    if _semantic_mismatch(normalized, expected):
        # Keep the deterministic fallback authoritative even if an older normalizer
        # tries to infer a contextual title from surrounding text.
        normalized["title"] = str(fallback.get("title") or str(getattr(sentinel, "label", "") or key[2]))
        normalized["body"] = str(fallback.get("body") or str(getattr(sentinel, "detail", "") or "Required changed-line risk."))
    return normalized


def _select_once(
    hardened: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    required_all = _required_sentinels(hardened, risk_sentinels)
    required_targets, duplicate_covered = _coalesce_required(required_all)
    expected = _expected_by_line(hardened, risk_sentinels)
    required_coverage = {_coverage_key(_sentinel_key(item)) for item in required_targets}

    candidates, dropped = _dedupe([item for item in findings if isinstance(item, dict)], expected)
    by_key = {_postable_key(item): item for item in candidates}
    fallback_by_key: dict[SentinelKey, dict[str, Any]] = {}
    for sentinel in required_targets:
        key = _sentinel_key(sentinel)
        fallback_by_key[key] = _fallback_candidate(hardened, sentinel, config, expected)
        if key not in by_key:
            by_key[key] = fallback_by_key[key]
            candidates.append(fallback_by_key[key])

    selected: list[dict[str, Any]] = []
    selected_coverage: set[SentinelKey] = set()
    suppressed: set[str] = set()

    def add_item(item: dict[str, Any], source_key: SentinelKey | None = None) -> None:
        key = _postable_key(item)
        if source_key is not None:
            key = source_key
        coverage = _coverage_key(key)
        if len(selected) >= limit or coverage in selected_coverage:
            return
        if _semantic_mismatch(item, expected):
            suppressed.add(_key_text(key))
            fallback = fallback_by_key.get(key)
            if fallback and not _semantic_mismatch(fallback, expected):
                selected.append(fallback)
                selected_coverage.add(coverage)
            return
        selected.append(item)
        selected_coverage.add(coverage)

    for sentinel in _balanced_required_order(required_targets):
        key = _sentinel_key(sentinel)
        add_item(by_key.get(key, fallback_by_key[key]), key)

    for item in sorted(candidates, key=_spare_priority):
        key = _postable_key(item)
        if not key[2] or _coverage_key(key) in selected_coverage:
            continue
        add_item(item, key)

    for item in selected:
        path, line, kind = _postable_key(item)
        validation = _validation_for_key(kind, path, line)
        if validation:
            item["validation"] = validation
            guidance = item.get("fix_guidance")
            if isinstance(guidance, dict):
                guidance["validation"] = validation
        v10._scrub_shell_pipe_wording(item)

    final_invalid = [_key_text(_postable_key(item)) for item in selected if _semantic_mismatch(item, expected)]
    selected_keys = [_postable_key(item) for item in selected]
    selected_coverage = {_coverage_key(key) for key in selected_keys}
    omitted_required = [
        _sentinel_record(item, "auto", required_coverage, selected_coverage, limit)
        for item in required_targets
        if _coverage_key(_sentinel_key(item)) not in selected_coverage
    ]
    optional_high_risk = [
        _sentinel_record(item, "auto", required_coverage, selected_coverage, limit)
        for item in risk_sentinels
        if _coverage_key(_sentinel_key(item)) not in selected_coverage
        and _coverage_key(_sentinel_key(item)) not in required_coverage
        and _sentinel_key(item)[2]
    ]
    required_ledger_keys = sorted(
        {
            _key_text(_coverage_key(key))
            for key in selected_keys
            if _coverage_key(key) in required_coverage
        }
        | {
            _key_text(_coverage_key(_sentinel_key(item)))
            for item in required_targets
            if _coverage_key(_sentinel_key(item)) not in selected_coverage
        }
    )
    duplicate_required_keys = {
        _key_text(_coverage_key((str(item.get("path", "") or ""), int(item.get("line", 0) or 0), str(item.get("kind", "") or ""))))
        for item in duplicate_covered
    }
    required_ledger_keys = sorted(set(required_ledger_keys) | duplicate_required_keys)
    metadata = {
        "version": VERSION,
        "hard_required_count": len(required_all),
        "coalesced_required_count": len(required_targets),
        "final_postable_count": len(selected),
        "inline_limit": limit,
        "partial_overflow": bool(omitted_required or optional_high_risk),
        "overflow_required_count": len(omitted_required),
        "overflow_optional_high_risk_count": len(optional_high_risk),
        "selected_keys": [_key_text(key) for key in selected_keys],
        "duplicate_covered_sentinels": duplicate_covered[:80],
        "dropped_invalid_or_duplicate_candidates": dropped[:120],
        "suppressed_invalid_selected_keys": sorted(suppressed),
        "final_invalid_selected_keys": final_invalid,
        "omitted_required_sentinels": omitted_required[:80],
        "omitted_optional_high_risk_sentinels": optional_high_risk[:80],
        "omitted_sentinels": (omitted_required + optional_high_risk)[:80],
        "final_uncovered": [f"{item.get('path')}:{item.get('line')} {item.get('kind')}" for item in omitted_required],
        "required_ledger_keys": required_ledger_keys[:120],
        "required_ledger_accounted_count": len(required_ledger_keys),
    }
    return selected, metadata


def _key_text(key: SentinelKey) -> str:
    return f"{key[0]}:{key[1]} {key[2]}"


def _sentinel_record(
    sentinel: Any,
    reason: str,
    required: set[SentinelKey],
    selected: set[SentinelKey],
    limit: int,
) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    coverage = _coverage_key(key)
    bucket = "hard-required" if coverage in required else "optional-pressure" if key[2].startswith("k8s_") else "high-risk"
    actual_reason = reason
    if reason == "auto":
        actual_reason = "duplicate_covered" if coverage in selected else "omitted_due_to_inline_budget" if len(selected) >= limit else "not_selected"
    return {
        "path": key[0],
        "line": key[1],
        "kind": key[2],
        "priority_bucket": bucket,
        "reason": actual_reason,
        "label": str(getattr(sentinel, "label", "") or ""),
        "detail": str(getattr(sentinel, "detail", "") or "")[:240],
        "text": str(getattr(sentinel, "text", "") or "")[:240],
    }


def _select_required_postable(
    hardened: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    del unanchored_findings
    selected, metadata = _select_once(hardened, findings, risk_sentinels, config)
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
        writer(config, "metadata/required-v12-final-selection.json", metadata)
        writer(config, "metadata/required-v11-final-selection.json", metadata)
        writer(config, "metadata/required-v10-final-selection.json", metadata)
        writer(config, "metadata/required-v9-final-selection.json", metadata)
    if metadata["final_invalid_selected_keys"]:
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            "DCOIR Review quality failure: final selected findings have semantic mismatches: "
            + "; ".join(metadata["final_invalid_selected_keys"])
        )
    v9._ensure_prompt_review(config)
    return selected


def _patch_required_selection(module: Any, hardened: Any) -> None:
    def add_risk_sentinel_fallback_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        return _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    def enforce_risk_sentinel_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> None:
        findings[:] = _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    hardened.add_risk_sentinel_fallback_findings = add_risk_sentinel_fallback_findings
    hardened.enforce_risk_sentinel_findings = enforce_risk_sentinel_findings
    module.rank_findings_for_required_budget = lambda findings, config: sorted(
        [v5._normalize_comment_finding(item) for item in findings if isinstance(item, dict)],
        key=_spare_priority,
    )[: max(0, int(getattr(config, "max_inline_comments", 12)))]


def _patch_python_extra_sentinels(owner: Any, sentinel_owner: Any | None = None) -> None:
    original = getattr(owner, "_dcoir_required_v12_original_detect_risk_sentinels", None)
    if original is None:
        original = getattr(owner, "detect_risk_sentinels", None)
        owner._dcoir_required_v12_original_detect_risk_sentinels = original
    if not callable(original):
        return

    def detect_risk_sentinels(diff: str, *args: Any, **kwargs: Any) -> list[Any]:
        widened_args = list(args)
        if widened_args and isinstance(widened_args[0], int):
            widened_args[0] = None
        widened_kwargs = dict(kwargs)
        for name in ("max_anchors", "max_sentinels", "limit"):
            if name in widened_kwargs:
                widened_kwargs[name] = None
        try:
            sentinels = list(original(diff, *widened_args, **widened_kwargs))
        except TypeError:
            sentinels = list(original(diff, *args, **kwargs))
        existing = {_sentinel_key(item) for item in sentinels}
        risk_sentinel_type = getattr(owner, "RiskSentinel", None) or getattr(sentinel_owner, "RiskSentinel", None)
        if risk_sentinel_type is None:
            return sentinels
        for path, line, text in selection._iter_added_diff_lines(diff):
            if Path(path.lower()).suffix != ".py":
                continue
            comment_checker = getattr(owner, "is_comment_only_added_line", None) or getattr(sentinel_owner, "is_comment_only_added_line", None)
            if callable(comment_checker) and comment_checker(path, text):
                continue
            kind = v11._line_kind(path, text)
            if kind not in {v11.PYTHON_ARCHIVE_EXTRACT, v11.PYTHON_PATH_WRITE}:
                continue
            key = (path, line, kind)
            if key in existing:
                continue
            if kind == v11.PYTHON_ARCHIVE_EXTRACT:
                label = "Python unsafe archive extraction"
                detail = "archive extraction needs destination containment and member traversal checks before unpacking untrusted archives"
            else:
                label = "Python request-controlled file write"
                detail = "request-controlled paths must be resolved under an allowlisted base directory before writing"
            sentinels.append(risk_sentinel_type(path=path, line=line, label=label, detail=detail, text=text))
            existing.add(key)
        return sentinels

    owner.detect_risk_sentinels = detect_risk_sentinels


def _patch_core_semantics() -> None:
    core._sentinel_key = _sentinel_key
    core._postable_key = _postable_key
    core._coverage_key = _coverage_key
    core._required_sentinels = _required_sentinels
    core._expected_by_line = _expected_by_line
    core._semantic_mismatch = _semantic_mismatch
    core._dedupe = _dedupe
    core._spare_priority = _spare_priority
    core._validation_for_key = _validation_for_key
    v9._sentinel_key = _sentinel_key
    v9._postable_key = _postable_key
    v9._semantic_mismatch = _semantic_mismatch
    v11._sentinel_key = _sentinel_key
    v11._postable_key = _postable_key
    v11._coverage_key = _coverage_key
    v11._required_sentinels = _required_sentinels
    v11._expected_by_line = _expected_by_line
    v11._semantic_mismatch = _semantic_mismatch
    v11._dedupe = _dedupe
    v11._spare_priority = _spare_priority
    v11._validation_for_key = _validation_for_key


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    _patch_core_semantics()
    _patch_python_extra_sentinels(module, hardened)
    if hardened is not None:
        _patch_python_extra_sentinels(hardened)
        _patch_required_selection(module, hardened)
    if base is not None:
        v11._patch_progress_comment(base, hardened)
