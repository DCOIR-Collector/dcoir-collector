"""Fourteenth required-coverage layer for DCOIR Review.

This connector-safe overlay fixes the #339 live-test regression without
rewriting the large reviewer script. v13 made semantic titles much better, but
it still allowed adjacent duplicate findings to consume budget, let Python be
starved under required-risk pressure, and preserved validation text that
belonged to a different semantic kind. v14 tightens those final-stage gates.
"""

from __future__ import annotations

import re
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v9 as v9
import dcoir_review_required_runtime_patch_v9_core as core
import dcoir_review_required_runtime_patch_v10 as v10
import dcoir_review_required_runtime_patch_v11 as v11
import dcoir_review_required_runtime_patch_v12 as v12
import dcoir_review_required_runtime_patch_v13 as v13

SentinelKey = tuple[str, int, str]

VERSION = "v14"
FAMILY_ORDER = ("yaml", "powershell", "python", "other", "kubernetes", "typescript")
SELECTION_KIND_RANK = {
    v10.YAML_TOKEN_TO_PR_URL: 0,
    v4.YAML_METADATA_SHELL: 1,
    v4.YAML_SHELL_PIPE: 2,
    v4.YAML_UNTRUSTED_CHECKOUT: 3,
    v4.YAML_PULL_REQUEST_TARGET: 10,
    v4.YAML_BROAD_WRITE: 11,
    v9.PS_DYNAMIC_EXEC: 0,
    v4.PS_PROCESS_LAUNCH: 1,
    v5.PS_ENV_TOKEN: 2,
    v4.PS_ACL: 3,
    v9.PYTHON_PICKLE_LOAD: 0,
    v5.PYTHON_SHELL_EXEC: 1,
    v11.PYTHON_ARCHIVE_EXTRACT: 2,
    v11.PYTHON_PATH_WRITE: 3,
    v5.PYTHON_YAML_LOAD: 4,
    v5.PYTHON_ENV_TOKEN: 5,
    v13.K8S_HOST_PID: 0,
    v13.K8S_PRIVILEGED_CONTAINER: 1,
    v13.K8S_PRIVILEGE_ESCALATION: 2,
    v13.K8S_HOST_PATH: 3,
    v13.K8S_HOST_NETWORK: 4,
    v13.TS_INNER_HTML: 0,
    v13.TS_DYNAMIC_EXECUTION: 1,
}


def _missing_render_integrity_errors(_findings: list[dict[str, Any]], _expected: dict[tuple[str, int], set[str]]) -> list[str]:
    return []


def _preserve_v13_helper(name: str, fallback: Any = None) -> Any:
    storage_name = f"_dcoir_required_v14_original_{name.lstrip('_')}"
    existing = getattr(v13, storage_name, None)
    if callable(existing):
        return existing
    helper = getattr(v13, name, fallback)
    if not callable(helper):
        raise AttributeError(f"v13 helper {name} is unavailable and no callable fallback was provided")
    setattr(v13, storage_name, helper)
    return helper


_ORIGINAL_V13_COVERAGE_KEY = _preserve_v13_helper("_coverage_key")
_ORIGINAL_V13_SENTINEL_SORT_KEY = _preserve_v13_helper("_sentinel_sort_key")
_ORIGINAL_V13_BALANCED_REQUIRED_ORDER = _preserve_v13_helper("_balanced_required_order")
_ORIGINAL_V13_SPARE_PRIORITY = _preserve_v13_helper("_spare_priority")
_ORIGINAL_V13_SAFE_VALIDATION = _preserve_v13_helper("_safe_validation")
_ORIGINAL_V13_TEMPLATE_FOR_KIND = _preserve_v13_helper("_template_for_kind")
_ORIGINAL_V13_INTEGRITY_FINDING = _preserve_v13_helper("_integrity_finding")
_ORIGINAL_V13_RENDER_ERRORS = _preserve_v13_helper("_render_integrity_errors", _missing_render_integrity_errors)
_ORIGINAL_V13_RENDERED_PROBLEM = _preserve_v13_helper(
    "_rendered_comment_has_integrity_problem",
    getattr(v13, "_rendered_comment_has_problem", None),
)
_ORIGINAL_V13_AUGMENT_METADATA = _preserve_v13_helper("_augment_metadata")
_ORIGINAL_V13_SELECT_REQUIRED = _preserve_v13_helper("_select_required_postable")
_ORIGINAL_V13_PATCH_V12_GLOBALS = _preserve_v13_helper("_patch_v12_globals")
_ORIGINAL_V13_PATCH_CORE_SEMANTICS = _preserve_v13_helper("_patch_core_semantics")


def _coverage_key(key: SentinelKey) -> SentinelKey:
    path, line, kind = key
    if kind in {v4.YAML_BROAD_WRITE, v4.PS_ACL, v11.PYTHON_ARCHIVE_EXTRACT, v13.K8S_HOST_PATH}:
        return path, 0, kind
    return _ORIGINAL_V13_COVERAGE_KEY(key)


def _sink_preference(kind: str, text: str) -> int:
    normalized = v13._normalize(text)
    if kind == v4.PS_ACL:
        if "set-acl" in normalized:
            return 0
        if "filesystemaccessrule" in normalized:
            return 1
        return 3
    if kind == v11.PYTHON_ARCHIVE_EXTRACT:
        if "extractall" in normalized:
            return 0
        if "tarfile.open" in normalized:
            return 2
        if "import tarfile" in normalized:
            return 5
        return 4
    if kind == v13.K8S_HOST_PATH:
        if "hostpath:" in normalized:
            return 0
        if "mountpath:" in normalized:
            return 4
        return 3
    return 0


def _sentinel_sort_key(sentinel: Any) -> tuple[int, int, str, int, str]:
    path, line, kind = v13._sentinel_key(sentinel)
    text = str(getattr(sentinel, "text", "") or "")
    return SELECTION_KIND_RANK.get(kind, v13._kind_rank(kind)), _sink_preference(kind, text), path, line, text


def _family(kind: str) -> str:
    return v13._family(kind)


def _spread_same_kind(values: list[Any]) -> list[Any]:
    by_kind: dict[str, list[Any]] = {}
    for sentinel in sorted(values, key=_sentinel_sort_key):
        by_kind.setdefault(v13._sentinel_key(sentinel)[2], []).append(sentinel)
    kinds = sorted(by_kind, key=lambda kind: SELECTION_KIND_RANK.get(kind, v13._kind_rank(kind)))
    result: list[Any] = []
    while any(by_kind.get(kind) for kind in kinds):
        for kind in kinds:
            bucket = by_kind.get(kind) or []
            if bucket:
                result.append(bucket.pop(0))
    return result


def _balanced_required_order(targets: list[Any]) -> list[Any]:
    buckets: dict[str, list[Any]] = {}
    for sentinel in targets:
        kind = v13._sentinel_key(sentinel)[2]
        buckets.setdefault(_family(kind), []).append(sentinel)
    for family, values in list(buckets.items()):
        buckets[family] = _spread_same_kind(values)
    ordered: list[Any] = []
    while any(buckets.get(family) for family in FAMILY_ORDER):
        for family in FAMILY_ORDER:
            bucket = buckets.get(family) or []
            if bucket:
                ordered.append(bucket.pop(0))
    for family in sorted(set(buckets) - set(FAMILY_ORDER)):
        ordered.extend(buckets.get(family) or [])
    return ordered


def _spare_priority(finding: dict[str, Any]) -> tuple[int, int, int, float, str, int]:
    path, line, kind = v13._postable_key(finding)
    optional_path = "/optional_" in path.lower() or path.rsplit("/", 1)[-1].startswith("optional_")
    family_rank = {
        "yaml": 0,
        "powershell": 1,
        "python": 2,
        "other": 4,
        "kubernetes": 6,
        "typescript": 7,
    }.get(_family(kind), 8)
    if optional_path:
        family_rank += 6
    return family_rank, SELECTION_KIND_RANK.get(kind, v13._kind_rank(kind)), core._severity_rank(finding), -core._confidence(finding), path, line


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    return v13._validation_for_key(kind, path, line)


def _template_for_kind(kind: str) -> tuple[str, str, str]:
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        return (
            "Privileged workflow checks out untrusted PR code",
            "This privileged workflow checks out pull request controlled code by using a PR-controlled ref or head SHA.",
            "Use a trusted base ref, or split privileged metadata handling from untrusted code checkout and execution.",
        )
    if kind == v4.YAML_PULL_REQUEST_TARGET:
        return (
            "Privileged pull request target workflow context",
            "This trigger runs with base-repository privileges. Keep untrusted pull request code and shell execution out of this workflow.",
            "Use an unprivileged pull request workflow for untrusted code paths, or limit this workflow to metadata-only operations.",
        )
    return _ORIGINAL_V13_TEMPLATE_FOR_KIND(kind)


def _safe_validation(kind: str, path: str, line: int, value: Any = "") -> str:
    if kind in v13.TRACKED_HIGH_RISK_KINDS:
        return _validation_for_key(kind, path, line)
    return _ORIGINAL_V13_SAFE_VALIDATION(kind, path, line, value)


def _looks_like_prose(value: str) -> bool:
    normalized = v13._normalize(value)
    return normalized.startswith(
        (
            "remove ",
            "replace ",
            "use ",
            "validate ",
            "the ",
            "if ",
            "this ",
            "set only ",
            "download ",
        )
    )


def _replacement_repeats_kind(kind: str, value: str) -> bool:
    normalized = v13._normalize(value)
    if not normalized:
        return False
    if kind == v4.YAML_BROAD_WRITE:
        return "write-all" in normalized or bool(re.search(r"\b[a-z_-]+\s*:\s*write\b", normalized))
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        return "pull_request.head" in normalized or "github.head_ref" in normalized or "merge_commit_sha" in normalized
    if kind == v10.YAML_TOKEN_TO_PR_URL:
        return "github_token" in normalized and "github.event.pull_request.body" in normalized
    if kind == v4.YAML_METADATA_SHELL:
        return "github.event.pull_request" in normalized and any(token in normalized for token in ("bash", "sh -c", "shell:", "run:"))
    if kind == v4.YAML_SHELL_PIPE:
        return ("curl" in normalized or "wget" in normalized) and ("| sh" in normalized or "| bash" in normalized)
    if kind == v4.YAML_PULL_REQUEST_TARGET:
        return "pull_request_target" in normalized
    if kind == v9.PS_DYNAMIC_EXEC:
        return "invoke-expression" in normalized or bool(re.search(r"\biex\b", normalized))
    if kind == v4.PS_ACL:
        return "set-acl" in normalized or "filesystemaccessrule" in normalized or "fullcontrol" in normalized
    if kind == v4.PS_PROCESS_LAUNCH:
        return "start-process" in normalized
    if kind == v5.PS_ENV_TOKEN:
        return ("invoke-webrequest" in normalized or "invoke-restmethod" in normalized) and (
            "authorization" in normalized or "bearer" in normalized or "$env:dcoir_token" in normalized
        )
    if kind == v13.PS_PLAINTEXT_SECURE_STRING:
        return "convertto-securestring" in normalized and "-asplaintext" in normalized
    if kind == v13.PS_RUN_KEY_PERSISTENCE:
        return "currentversion\\run" in normalized
    if kind == v9.PYTHON_PICKLE_LOAD:
        return "pickle.load" in normalized or "pickle.loads" in normalized
    if kind == v5.PYTHON_YAML_LOAD:
        return "yaml.load" in normalized and ("loader=yaml.loader" in normalized or "unsafe" in normalized or "loader=" in normalized)
    if kind == v5.PYTHON_SHELL_EXEC:
        return "shell=true" in normalized or "os.system(" in normalized or "os.popen(" in normalized
    if kind == v5.PYTHON_ENV_TOKEN:
        return ("requests." in normalized or "urlopen" in normalized) and (
            "authorization" in normalized or "bearer" in normalized or "dcoir_token" in normalized
        )
    if kind == v11.PYTHON_ARCHIVE_EXTRACT:
        return "extractall" in normalized
    if kind == v11.PYTHON_PATH_WRITE:
        return (".open(" in normalized or "open(" in normalized or "write_text(" in normalized or "write_bytes(" in normalized) and (
            "user_path" in normalized or "request" in normalized or "callback" in normalized
        )
    if kind == v13.K8S_HOST_PID:
        return "hostpid: true" in normalized
    if kind == v13.K8S_HOST_NETWORK:
        return "hostnetwork: true" in normalized
    if kind == v13.K8S_PRIVILEGED_CONTAINER:
        return "privileged: true" in normalized
    if kind == v13.K8S_PRIVILEGE_ESCALATION:
        return "allowprivilegeescalation: true" in normalized
    if kind == v13.K8S_HOST_PATH:
        return "hostpath:" in normalized
    if kind == v13.TS_INNER_HTML:
        return ".innerhtml" in normalized or ".outerhtml" in normalized or "insertadjacenthtml" in normalized
    if kind == v13.TS_DYNAMIC_EXECUTION:
        return "settimeout(" in normalized or "setinterval(" in normalized or "new function(" in normalized
    return False


def _safe_suggested_replacement(kind: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = v13._normalize(text)
    if _looks_like_prose(text):
        return ""
    if _replacement_repeats_kind(kind, text):
        return ""
    if kind == v4.YAML_BROAD_WRITE and ("write-all" in normalized or re.search(r"\b[a-z_-]+\s*:\s*write\b", normalized)):
        return ""
    if kind == v4.YAML_UNTRUSTED_CHECKOUT and (
        "pull_request.head" in normalized or "github.head_ref" in normalized or "merge_commit_sha" in normalized
    ):
        return ""
    if kind in {v10.YAML_TOKEN_TO_PR_URL, v4.YAML_METADATA_SHELL} and "github.event.pull_request" in normalized:
        return ""
    return text if len(text.splitlines()) <= 20 else ""


def _safe_guidance_code_field(kind: str, field: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if kind not in v13.TRACKED_HIGH_RISK_KINDS:
        return text
    field_name = str(field or "").lower()
    if field_name in {"replace", "replace_code", "add", "add_code", "suggested_replacement"}:
        return _safe_suggested_replacement(kind, text)
    # Remove snippets for tracked sentinel kinds are often the dangerous source
    # line. Keeping them fenced has repeatedly confused reviewers, so prefer the
    # deterministic prose template unless the snippet is clearly harmless.
    return _safe_suggested_replacement(kind, text)


def _sanitize_fix_guidance(kind: str, guidance: dict[str, Any], validation: str) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in guidance.items():
        if key in {"remove", "replace", "add", "remove_code", "replace_code", "add_code", "suggested_replacement"}:
            safe_value = _safe_guidance_code_field(kind, key, value)
            if safe_value:
                cleaned[key] = safe_value
            continue
        cleaned[key] = value
    if kind not in v13.TRACKED_HIGH_RISK_KINDS:
        cleaned["validation"] = validation
    else:
        cleaned.pop("validation", None)
    return cleaned


def _integrity_finding(finding: dict[str, Any], key: SentinelKey | None = None, *, force_template: bool = False) -> dict[str, Any]:
    item = _ORIGINAL_V13_INTEGRITY_FINDING(finding, key, force_template=force_template)
    path, line, kind = key or v13._postable_key(item)
    if not kind:
        return item
    validation = _safe_validation(kind, path, line, item.get("validation", ""))
    item["validation"] = validation
    if kind in v13.TRACKED_HIGH_RISK_KINDS:
        item["suggested_replacement"] = _safe_suggested_replacement(kind, item.get("suggested_replacement", ""))
    guidance = item.get("fix_guidance")
    if not isinstance(guidance, dict):
        guidance = {}
    guidance = dict(v13._scrub_model_footer(guidance))
    guidance["validation"] = validation
    item["fix_guidance"] = _sanitize_fix_guidance(kind, guidance, validation)
    item["_risk_sentinel_key"] = [path, line, kind]
    item["_risk_sentinel_kind"] = kind
    item["_dcoir_v14_trusted_key"] = True
    return item


def _validation_matches_kind(kind: str, rendered: str) -> bool:
    normalized = v13._normalize(rendered)
    if kind == v10.YAML_TOKEN_TO_PR_URL:
        return "github_token" in normalized and "github.event.pull_request.body" in normalized and "| bash" not in normalized and "| sh" not in normalized
    if kind == v4.YAML_SHELL_PIPE:
        return "| bash" in normalized or "| sh" in normalized
    if kind == v4.YAML_METADATA_SHELL:
        return "github.event.pull_request.labels" in normalized or "github.event.pull_request.body" in normalized
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        return "pull_request.head" in normalized or "github.head_ref" in normalized
    if kind == v4.YAML_BROAD_WRITE:
        return ": write" in normalized or "write-all" in normalized
    if kind == v4.YAML_PULL_REQUEST_TARGET:
        return "pull_request_target" in normalized
    if kind.startswith("ps_"):
        return "$errors" in rendered and "PSParser" in rendered
    if kind.startswith("python_"):
        return "py_compile" in normalized
    return True


def _render_integrity_errors(findings: list[dict[str, Any]], expected: dict[tuple[str, int], set[str]]) -> list[str]:
    errors = list(_ORIGINAL_V13_RENDER_ERRORS(findings, expected))
    for finding in findings:
        path, line, kind = v13._postable_key(finding)
        validation = str(finding.get("validation", "") or "")
        if kind in v13.TRACKED_HIGH_RISK_KINDS and not _validation_matches_kind(kind, validation):
            errors.append(f"{path}:{line} validation_mismatch kind={kind}")
        suggestion = str(finding.get("suggested_replacement", "") or "")
        if suggestion and suggestion != _safe_suggested_replacement(kind, suggestion):
            errors.append(f"{path}:{line} unsafe_suggested_replacement kind={kind}")
    return sorted(set(errors))


def _rendered_comment_has_integrity_problem(rendered: str, finding: dict[str, Any]) -> bool:
    if _ORIGINAL_V13_RENDERED_PROBLEM(rendered, finding):
        return True
    _path, _line, kind = v13._postable_key(finding)
    marker = "**Validation:**"
    validation_text = rendered.split(marker, 1)[1] if marker in rendered else rendered
    if kind in v13.TRACKED_HIGH_RISK_KINDS and not _validation_matches_kind(kind, validation_text):
        return True
    for suggestion in re.findall(r"```suggestion\s*\n(.*?)```", rendered, flags=re.IGNORECASE | re.DOTALL):
        if _replacement_repeats_kind(kind, suggestion):
            return True
    if rendered.lower().count("validation") > 1:
        return True
    validation = _validation_for_key(kind, _path, _line)
    return bool(validation and rendered.count(validation) > 1)


def _family_counts(keys: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in keys:
        kind = key.rsplit(" ", 1)[-1] if " " in key else ""
        family = _family(kind)
        counts[family] = counts.get(family, 0) + 1
    return counts


def _coalesce_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: dict[SentinelKey, dict[str, Any]] = {}
    for record in records:
        key = (
            str(record.get("path", "") or ""),
            int(record.get("line", 0) or 0),
            str(record.get("kind", "") or ""),
        )
        coverage = _coverage_key(key)
        current = kept.get(coverage)
        if current is None:
            kept[coverage] = record
            continue
        current_key = (
            str(current.get("path", "") or ""),
            int(current.get("line", 0) or 0),
            str(current.get("kind", "") or ""),
        )
        current_score = (SELECTION_KIND_RANK.get(current_key[2], v13._kind_rank(current_key[2])), _sink_preference(current_key[2], str(current.get("text", "") or "")), current_key[1])
        next_score = (SELECTION_KIND_RANK.get(key[2], v13._kind_rank(key[2])), _sink_preference(key[2], str(record.get("text", "") or "")), key[1])
        if next_score < current_score:
            kept[coverage] = record
    return list(kept.values())


def _augment_metadata(
    selected: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    *args: Any,
) -> dict[str, Any]:
    if len(args) == 2:
        hardened = None
        config, metadata = args
    elif len(args) == 3:
        hardened, config, metadata = args
    else:
        raise TypeError("_augment_metadata expected selected, findings, risk_sentinels, [hardened], config, metadata")
    try:
        updated = _ORIGINAL_V13_AUGMENT_METADATA(selected, findings, risk_sentinels, hardened, config, metadata)
    except TypeError:
        try:
            updated = _ORIGINAL_V13_AUGMENT_METADATA(selected, findings, risk_sentinels, config, metadata)
        except NameError:
            updated = dict(metadata)
    except NameError:
        updated = dict(metadata)
    updated["version"] = VERSION
    for key in ("omitted_required_sentinels", "omitted_optional_high_risk_sentinels", "detector_only_high_risk_overflow"):
        updated[key] = _coalesce_records(list(updated.get(key, []) or []))
    updated["overflow_required_count"] = len(updated.get("omitted_required_sentinels", []) or [])
    updated["overflow_optional_high_risk_count"] = len(updated.get("omitted_optional_high_risk_sentinels", []) or [])
    updated["overflow_detector_high_risk_count"] = len(updated.get("detector_only_high_risk_overflow", []) or [])
    updated["final_uncovered"] = [
        f"{item['path']}:{item['line']} {item['kind']}"
        for item in (updated.get("omitted_required_sentinels", []) or [])
        if item.get("path") and item.get("kind")
    ]
    updated["required_ledger_omitted_keys"] = list(updated["final_uncovered"])
    posted = list(updated.get("posted_required_sentinels", []) or [])
    omitted = list(updated.get("required_ledger_omitted_keys", []) or updated.get("final_uncovered", []) or [])
    updated["posted_required_family_counts"] = _family_counts(posted)
    updated["omitted_required_family_counts"] = _family_counts(omitted)
    updated["required_family_balancing"] = "round_robin_after_coverage_coalescing"
    return updated


def _select_required_postable(
    hardened: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    _patch_core_semantics()
    selected = _ORIGINAL_V13_SELECT_REQUIRED(hardened, findings, risk_sentinels, config, unanchored_findings)
    metadata = dict(core.SELECTION_SUMMARY)
    metadata["version"] = VERSION
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
        writer(config, "metadata/required-v14-final-selection.json", metadata)
    return selected


def _patch_v12_globals() -> None:
    _ORIGINAL_V13_PATCH_V12_GLOBALS()
    v12._coverage_key = _coverage_key
    v12._sentinel_sort_key = _sentinel_sort_key
    v12._balanced_required_order = _balanced_required_order
    v12._spare_priority = _spare_priority
    v12._validation_for_key = _validation_for_key


def _patch_core_semantics() -> None:
    _ORIGINAL_V13_PATCH_CORE_SEMANTICS()
    _patch_v12_globals()
    v13._coverage_key = _coverage_key
    v13._sentinel_sort_key = _sentinel_sort_key
    v13._balanced_required_order = _balanced_required_order
    v13._spare_priority = _spare_priority
    v13._template_for_kind = _template_for_kind
    v13._safe_validation = _safe_validation
    v13._integrity_finding = _integrity_finding
    v13._render_integrity_errors = _render_integrity_errors
    v13._rendered_comment_has_integrity_problem = _rendered_comment_has_integrity_problem
    v13._rendered_comment_has_problem = _rendered_comment_has_integrity_problem
    v13._augment_metadata = _augment_metadata
    v13._select_required_postable = _select_required_postable
    core._coverage_key = _coverage_key
    core._spare_priority = _spare_priority
    core._validation_for_key = _validation_for_key
    v11._coverage_key = _coverage_key
    v11._spare_priority = _spare_priority
    v11._validation_for_key = _validation_for_key


def apply_pareto_context_module(module: Any) -> None:
    _patch_core_semantics()
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if hardened is not None:
        v13._patch_required_selection(module, hardened)
        v13._patch_review_body_overflow(hardened)
    if base is not None:
        v13._patch_final_rendering(base)
        v11._patch_progress_comment(base, hardened)
