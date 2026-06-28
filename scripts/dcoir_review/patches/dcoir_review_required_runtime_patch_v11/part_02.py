def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    if kind == PYTHON_ARCHIVE_EXTRACT:
        quoted = shlex.quote(path)
        return f"python3 -m py_compile {quoted}\n" + v8._py_here_doc(path, "assert '.extractall(' not in text\nassert 'extractall(' not in text")
    if kind == PYTHON_PATH_WRITE:
        quoted = shlex.quote(path)
        body = (
            "import re\n"
            "pathlib_write = re.search(r'\\.(write_text|write_bytes)\\s*\\(', text)\n"
            "open_write = re.search(r'\\bopen\\s*\\([^\\n)]*,\\s*[\\'\\\"][^\\'\\\"]*(?:[wax]|r\\+)[^\\'\\\"]*[\\'\\\"]', text) or re.search(r'\\bopen\\s*\\([^\\n)]*\\bmode\\s*=\\s*[\\'\\\"][^\\'\\\"]*(?:[wax]|r\\+)[^\\'\\\"]*[\\'\\\"]', text)\n"
            "path_open_write = re.search(r'\\.open\\s*\\(\\s*(?:mode\\s*=\\s*)?[\\'\\\"][^\\'\\\"]*(?:[wax]|r\\+)[^\\'\\\"]*[\\'\\\"]', text)\n"
            "assert not (pathlib_write or open_write or path_open_write)"
        )
        return f"python3 -m py_compile {quoted}\n" + v8._py_here_doc(path, body)
    return v10._validation_for_key(kind, path, line)


def _fallback_for_sentinel(hardened: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    path, line, kind = key
    line_text = str(getattr(sentinel, "text", "") or "")
    if kind == PYTHON_ARCHIVE_EXTRACT:
        fallback = {
            "title": "Archive extraction trusts archive paths",
            "severity": "high",
            "confidence": 0.98,
            "path": path,
            "line": line,
            "body": "This extraction can write files outside the destination if the archive contains absolute paths or parent traversal. Validate every archive member before extraction.",
            "validation": _validation_for_key(kind, path, line),
            "fix_guidance": {
                "language": "python",
                "notes": "Validate archive member paths before extracting, or use a safe extraction helper.",
                "validation": _validation_for_key(kind, path, line),
            },
        }
    elif kind == PYTHON_PATH_WRITE:
        fallback = {
            "title": "Request-controlled path can be written",
            "severity": "high",
            "confidence": 0.96,
            "path": path,
            "line": line,
            "body": "This write path can be influenced by request data. Resolve it under an allowlisted base directory and reject traversal before writing.",
            "validation": _validation_for_key(kind, path, line),
            "fix_guidance": {
                "language": "python",
                "notes": "Resolve and validate the destination path before writing.",
                "validation": _validation_for_key(kind, path, line),
            },
        }
    else:
        fallback = v10._fallback_for_sentinel(hardened, sentinel, config)
    fallback["_risk_sentinel_key"] = [path, line, kind]
    fallback["_risk_sentinel_kind"] = kind
    fallback["_anchored_line_text"] = line_text
    return fallback


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


def _record_from_key_text(key_text: str, reason: str) -> dict[str, Any]:
    try:
        path_line, kind = str(key_text).rsplit(" ", 1)
        path, line_text = path_line.rsplit(":", 1)
        line = int(line_text)
    except (ValueError, TypeError):
        path, line, kind = str(key_text), 0, ""
    return {
        "path": path,
        "line": line,
        "kind": kind,
        "priority_bucket": "hard-required",
        "reason": reason,
        "label": "",
        "detail": "",
        "text": "",
    }


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
    for sentinel in required_targets:
        key = _sentinel_key(sentinel)
        if key not in by_key:
            fallback = _fallback_for_sentinel(hardened, sentinel, config)
            normalized = v5._normalize_comment_finding(fallback)
            normalized["_risk_sentinel_key"] = list(key)
            normalized["_risk_sentinel_kind"] = key[2]
            normalized["_anchored_line_text"] = str(getattr(sentinel, "text", "") or "")
            by_key[key] = normalized
            candidates.append(normalized)

    selected: list[dict[str, Any]] = []
    selected_coverage: set[SentinelKey] = set()
    for sentinel in _balanced_required_order(required_targets):
        key = _sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in selected_coverage or len(selected) >= limit:
            continue
        item = by_key.get(key)
        if not item:
            continue
        selected.append(item)
        selected_coverage.add(coverage)

    for item in sorted(candidates, key=_spare_priority):
        key = _postable_key(item)
        coverage = _coverage_key(key)
        if len(selected) >= limit:
            break
        if coverage in selected_coverage or not key[2]:
            continue
        selected.append(item)
        selected_coverage.add(coverage)

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
    metadata = {
        "version": "v11",
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
        "final_invalid_selected_keys": final_invalid,
        "omitted_required_sentinels": omitted_required[:80],
        "omitted_optional_high_risk_sentinels": optional_high_risk[:80],
        "omitted_sentinels": (omitted_required + optional_high_risk)[:80],
        "final_uncovered": [f"{item.get('path')}:{item.get('line')} {item.get('kind')}" for item in omitted_required],
    }
    return selected, metadata


def _select_required_postable(
    hardened: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    del unanchored_findings
    selected, metadata = _select_once(hardened, findings, risk_sentinels, config)
    if metadata["final_invalid_selected_keys"]:
        invalid = set(metadata["final_invalid_selected_keys"])
        retry_findings = [item for item in findings if _key_text(_postable_key(v5._normalize_comment_finding(item))) not in invalid]
        selected, retry_metadata = _select_once(hardened, retry_findings, risk_sentinels, config)
        retry_metadata["first_pass_invalid_selected_keys"] = metadata["final_invalid_selected_keys"]
        metadata = retry_metadata
    if metadata["final_invalid_selected_keys"]:
        invalid = set(metadata["final_invalid_selected_keys"])
        selected = [item for item in selected if _key_text(_postable_key(item)) not in invalid]
        metadata["suppressed_invalid_selected_keys"] = sorted(invalid)
        metadata["final_invalid_selected_keys"] = []
        metadata["selected_keys"] = [_key_text(_postable_key(item)) for item in selected]
        metadata["final_postable_count"] = len(selected)
        metadata["partial_overflow"] = True
        metadata["selection_quality_warning"] = "invalid selected findings were suppressed instead of posted"
        suppressed_records = [_record_from_key_text(key, "suppressed_invalid_selected_finding") for key in sorted(invalid)]
        omitted_required = list(metadata.get("omitted_required_sentinels") or []) + suppressed_records
        omitted_optional = list(metadata.get("omitted_optional_high_risk_sentinels") or [])
        metadata["omitted_required_sentinels"] = omitted_required[:80]
        metadata["omitted_sentinels"] = (omitted_required + omitted_optional)[:80]
        metadata["overflow_required_count"] = len(omitted_required)
        metadata["overflow_optional_high_risk_count"] = len(omitted_optional)
        metadata["final_uncovered"] = sorted(set(metadata.get("final_uncovered") or []) | invalid)
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
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


def _patch_core_semantics() -> None:
    if not hasattr(core, "_dcoir_required_v11_original_line_kind"):
        core._dcoir_required_v11_original_line_kind = core._line_kind
    if not hasattr(core, "_dcoir_required_v11_original_semantic_kind"):
        core._dcoir_required_v11_original_semantic_kind = core._semantic_kind
    if not hasattr(core, "_dcoir_required_v11_original_sentinel_key"):
        core._dcoir_required_v11_original_sentinel_key = core._sentinel_key
    if not hasattr(core, "_dcoir_required_v11_original_required_sentinels"):
        core._dcoir_required_v11_original_required_sentinels = core._required_sentinels
    core._line_kind = _line_kind
    core._semantic_kind = _semantic_kind
    core._postable_key = _postable_key
    core._sentinel_key = _sentinel_key
    core._expected_by_line = _expected_by_line
    core._required_sentinels = _required_sentinels
    core._semantic_mismatch = _semantic_mismatch
    core._dedupe = _dedupe
    core._spare_priority = _spare_priority
    core._validation_for_key = _validation_for_key
    v9._line_kind = _line_kind
    v9._semantic_kind = _semantic_kind
    v9._postable_key = _postable_key
    v9._sentinel_key = _sentinel_key
    v9._semantic_mismatch = _semantic_mismatch


def _patch_progress_comment(base: Any, hardened: Any | None = None) -> None:
    owner = base if hasattr(base, "ProgressReporter") else hardened if hasattr(hardened, "ProgressReporter") else None
    reporter = getattr(owner, "ProgressReporter", None) if owner is not None else None
    if reporter is None:
        return
    if getattr(reporter, "_dcoir_required_v11_patched", False):
        return
    original_body = getattr(reporter, "_body", None)
    if not callable(original_body):
        return
    reporter._dcoir_required_v11_original_body = original_body

    def body(self: Any, state: str, final_lines: list[str] | None = None) -> str:
        rendered = original_body(self, state, final_lines)
        if not getattr(self.config, "debug", False):
            return rendered
        required = list(core.SELECTION_SUMMARY.get("omitted_required_sentinels") or [])
        optional = list(core.SELECTION_SUMMARY.get("omitted_optional_high_risk_sentinels") or [])
        raw_command = (
            _raw_trigger_command_from_event()
            or getattr(self, "command", "")
            or getattr(self, "review_command", "")
            or getattr(self.config, "command", "")
            or getattr(self.config, "review_command", "")
            or ""
        )
        lines: list[str] = ["", "Selection overflow details:"]
        lines.append(f"- Omitted required changed-line signals: `{len(required)}`.")
        for item in required[:10]:
            lines.append(_progress_item(base, item))
        lines.append(f"- Omitted optional/high-risk pressure signals: `{len(optional)}`.")
        for item in optional[:8]:
            lines.append(_progress_item(base, item))
        if raw_command:
            safe_command = base.sanitize_public_identity(str(raw_command))
            rendered, replacements = re.subn(
                r"(?m)^- Command:\s*`[^`\n]*`\.",
                f"- Command: `{safe_command}`.",
                rendered,
                count=1,
            )
            if replacements == 0:
                lines.insert(1, f"- Raw trigger command: `{safe_command}`.")
        return base.github_safe_body(f"{rendered.rstrip()}\n" + "\n".join(lines), limit=20000)

    reporter._body = body
    reporter._dcoir_required_v11_patched = True


def _raw_trigger_command_from_event() -> str:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        return ""
    try:
        data = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    body = str(((data.get("comment") or {}).get("body")) or "")
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("/dcoir-review"):
            return stripped
    return ""


def _progress_item(base: Any, item: dict[str, Any]) -> str:
    path = base.sanitize_public_identity(str(item.get("path", "") or ""))
    line = item.get("line", "")
    kind = base.sanitize_public_identity(str(item.get("kind", "") or ""))
    reason = base.sanitize_public_identity(str(item.get("reason", "") or ""))
    label = base.sanitize_public_identity(str(item.get("label", "") or ""))
    return f"- `{path}:{line}` `{kind}` reason=`{reason}` label=`{label}`."


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    _patch_core_semantics()
    v10._patch_yaml_extra_sentinels(module, hardened)
    if hardened is not None:
        v10._patch_yaml_extra_sentinels(hardened)
        _patch_required_selection(module, hardened)
    if base is not None:
        _patch_progress_comment(base, hardened)
