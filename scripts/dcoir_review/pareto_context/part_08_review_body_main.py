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
    mode_lines = [
        f"{CONTEXT_REVIEW_MARKER} {review_mode}",
        f"Context readback: {context_summary}",
        "When deep context is present, use it to reason about full changed-file behavior, but anchor actionable findings to changed lines when practical.",
        "Every finding must include exact correction guidance or the smallest safe patch direction, plus validation/readback guidance.",
        "Prefer GitHub apply-ready suggestions only when a finding has a precise single-line replacement for the commented line; put only that exact replacement code in suggested_replacement so the renderer emits a Suggested fix with a ```suggestion block; leave suggested_replacement empty for multiline, range, or speculative fixes.",
        "Inspect dynamic path construction and file writes for traversal, arbitrary overwrite, missing root-containment checks, and unsafe staging side effects.",
        "For this repository, give extra attention to PowerShell, Python, and GitHub Actions/YAML because they carry most operational and workflow risk; keep findings generalizable and do not tune to any single fixture.",
    ]
    context = base.sanitize_text(deep_context_block.strip(), config)
    suffix = ""
    # Extremely small budgets preserve the hardened core review prompt and rely
    # on workflow progress/review readback for context-mode visibility.
    if config.max_prompt_chars >= 3000:
        suffix_budget = config.max_prompt_chars // 3
        budget = max(0, min(len(context), int(getattr(config, "deep_review_max_total_chars", 24000)), suffix_budget))
        if len(context) > budget:
            context = truncate_with_balanced_fences(context, budget, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)
        suffix = "\n\n".join(["\n".join(mode_lines), context]).strip()
        if len(suffix) > suffix_budget:
            suffix = truncate_with_balanced_fences(suffix, suffix_budget, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)

    prompt_config = copy.copy(config)
    separator = "\n\n"
    reserve = min(len(suffix), config.max_prompt_chars // 3) if suffix else 0
    prompt_config.max_prompt_chars = max(0, config.max_prompt_chars - reserve - len(separator))
    prompt = hardened.build_prompt(pr, files, diff, prompt_config, risk_sentinels)
    if not suffix:
        return prompt[: config.max_prompt_chars]
    if len(prompt) + len(separator) + len(suffix) <= config.max_prompt_chars:
        return f"{prompt}{separator}{suffix}"
    remaining = config.max_prompt_chars - len(prompt) - len(separator)
    if remaining <= len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER):
        retained_prompt = max(0, config.max_prompt_chars - len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER))
        return f"{prompt[:retained_prompt]}{DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER}"
    return f"{prompt}{separator}{truncate_with_balanced_fences(suffix, remaining, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)}"


def neutralize_github_mentions(text: str) -> str:
    return re.sub(r"@(?=[A-Za-z0-9])", "@<!-- -->", text)


def sanitize_context_summary(context_summary: str, config: Any) -> str:
    return neutralize_github_mentions(hardened.sanitize_github_output(context_summary, config))


def append_context_to_review_body(body: str, review_mode: str, context_summary: str, config: Any) -> str:
    safe_context_summary = sanitize_context_summary(context_summary, config)
    return base.github_safe_body(f"{body}\n\n{CONTEXT_REVIEW_MARKER} `{review_mode}`\n\nContext readback: {safe_context_summary}")


FINDING_ANCHOR_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("pickle", "deserial"), ("pickle.loads", "pickle.load", "pickle")),
    (("yaml", "loader", "deserial"), ("yaml.load", "yaml.loader", "loader=yaml.loader")),
    (("ssrf", "outbound", "request url"), ("requests.get", "requests.post", "requests.request", "httpx.", "url")),
    (("securestring", "plain text", "plaintext"), ("convertto-securestring", "-asplaintext", "securestring")),
    (("start-process", "process launch"), ("start-process", "-filepath", "-argumentlist")),
    (("run key", "persistence", "set-itemproperty"), ("set-itemproperty", "currentversion\\run", "\\run", "run")),
    (("pull_request_target", "privileged pr"), ("pull_request_target",)),
    (("broad write", "write permission", "permissions"), ("permissions:", "contents:", "pull-requests:", "write")),
    (("checkout", "untrusted", "head sha", "head ref"), ("actions/checkout", "github.event.pull_request.head.sha", "github.event.pull_request.head.ref")),
    (("curl", "pipe", "bash"), ("curl", "bash", "|")),
    (("eval", "exec", "dynamic code"), ("eval(", "exec(")),
)
ANCHOR_TERM_STOP_WORDS = {
    "actionable",
    "affected",
    "anchored",
    "changed",
    "command",
    "confidence",
    "correction",
    "expected",
    "finding",
    "github",
    "impact",
    "line",
    "review",
    "risk",
    "security",
    "should",
    "source",
    "validation",
}


def normalized_anchor_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def finding_anchor_terms(finding: dict[str, Any]) -> list[str]:
    haystack = normalized_anchor_text(
        "\n".join(
            [
                str(finding.get("title", "") or ""),
                str(finding.get("body", "") or ""),
                str(finding.get("validation", "") or ""),
            ]
        )
    )
    terms: set[str] = set()
    for triggers, anchors in FINDING_ANCHOR_HINTS:
        if any(trigger in haystack for trigger in triggers):
            terms.update(anchors)
    for token in re.findall(r"[a-z_][a-z0-9_.:-]{3,}", haystack):
        if token not in ANCHOR_TERM_STOP_WORDS and len(token) <= 48:
            terms.add(token)
    return sorted(terms, key=lambda term: (-len(term), term))[:24]


def finding_text_matches_sentinel(finding: dict[str, Any], sentinel: hardened.RiskSentinel) -> bool:
    haystack = normalized_anchor_text(
        "\n".join(
            [
                str(finding.get("title", "") or ""),
                str(finding.get("body", "") or ""),
                str(finding.get("validation", "") or ""),
            ]
        )
    )
    return any(normalized_anchor_text(term) in haystack for term in hardened.risk_sentinel_terms(sentinel))


def anchor_candidate_score(
    finding: dict[str, Any],
    candidate: hardened.ChangedLine,
    original_line: int,
    terms: list[str],
    risk_sentinels: list[hardened.RiskSentinel],
) -> int:
    distance = abs(candidate.line - original_line) if original_line > 0 else 1000
    score = max(0, 24 - distance)
    line_text = normalized_anchor_text(candidate.text)
    for term in terms:
        normalized_term = normalized_anchor_text(term)
        if normalized_term and normalized_term in line_text:
            score += 36 if len(normalized_term) >= 8 or any(char in normalized_term for char in ".:-_\\|") else 14
    if candidate.line == original_line:
        score += 3
    for sentinel in risk_sentinels:
        if sentinel.path == candidate.path and sentinel.line == candidate.line and finding_text_matches_sentinel(finding, sentinel):
            score += 90
    return score


def reanchor_finding_to_changed_line(
    finding: dict[str, Any],
    line_index: dict[tuple[str, int], int],
    changed_lines_by_path: dict[str, list[hardened.ChangedLine]],
    risk_sentinels: list[hardened.RiskSentinel],
) -> dict[str, Any]:
    path = str(finding.get("path", "") or "").strip()
    try:
        original_line = int(finding.get("line", 0) or 0)
    except (TypeError, ValueError):
        return finding
    candidates = changed_lines_by_path.get(path, [])
    if not path or not candidates:
        return finding
    terms = finding_anchor_terms(finding)
    if not terms and (path, original_line) in line_index:
        return finding
    scored = [
        (
            anchor_candidate_score(finding, candidate, original_line, terms, risk_sentinels),
            -abs(candidate.line - original_line) if original_line > 0 else 0,
            candidate.line,
            candidate,
        )
        for candidate in candidates
    ]
    scored.sort(reverse=True)
    best_score, _best_distance_sort, _best_line_sort, best_candidate = scored[0]
    exact_candidate = next((candidate for candidate in candidates if candidate.line == original_line), None)
    exact_score = (
        anchor_candidate_score(finding, exact_candidate, original_line, terms, risk_sentinels)
        if exact_candidate is not None
        else -1
    )
    if exact_candidate is not None and best_score < exact_score + 8:
        return finding
    if best_score < 24:
        return finding
    anchored = dict(finding)
    anchored["line"] = best_candidate.line
    if original_line != best_candidate.line:
        anchored["_reanchored_from_line"] = original_line
    return anchored


def split_findings_with_review_body_fallback(
    result: dict[str, Any],
    config: Any,
    line_index: dict[tuple[str, int], int],
    diff: str = "",
    risk_sentinels: list[hardened.RiskSentinel] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list) or not raw_findings:
        return hardened.split_findings(result, config, line_index)
    changed_paths = {path for path, _line in line_index}
    changed_lines_by_path: dict[str, list[hardened.ChangedLine]] = {}
    if diff:
        for changed_line in hardened.iter_added_diff_lines(diff):
            changed_lines_by_path.setdefault(changed_line.path, []).append(changed_line)
    risk_sentinels = risk_sentinels or []
    findings: list[dict[str, Any]] = []
    unanchored_findings: list[dict[str, Any]] = []
    track_unanchored = bool(getattr(config, "fail_on_unanchored_findings", True))
    for item in raw_findings:
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", "")).strip()
        except (AttributeError, TypeError, ValueError):
            continue
        if not path or line <= 0:
            continue
        if confidence < config.minimum_confidence or hardened.non_actionable_finding_reason(item):
            continue
        if path not in changed_paths:
            continue
        anchored_item = reanchor_finding_to_changed_line(dict(item), line_index, changed_lines_by_path, risk_sentinels)
        try:
            line = int(anchored_item.get("line", 0) or 0)
            path = str(anchored_item.get("path", "")).strip()
        except (AttributeError, TypeError, ValueError):
            continue
        if (path, line) in line_index:
            findings.append(anchored_item)
            continue
        if track_unanchored:
            unanchored = dict(anchored_item)
            location_text = hardened.finding_location_text(path, line)
            unanchored["_unanchored_reason"] = f"{location_text} is not an added changed line for this PR"
            unanchored_findings.append(unanchored)
    findings = rank_findings_for_required_budget(findings, config)
    unanchored_findings = dedupe_findings_for_ranking(unanchored_findings)
    unanchored_findings.sort(key=hardened.severity_sort_key)
    unanchored_findings = unanchored_findings[: config.max_inline_comments]
    if findings or unanchored_findings:
        return findings, unanchored_findings
    return hardened.split_findings(result, config, line_index)



def review_assist_context_path(raw_path: str) -> Path | None:
    """Return the trusted review-assist context path or reject unexpected paths."""
    if not raw_path.strip():
        return None

    root = REVIEW_ASSIST_CONTEXT_ROOT.resolve(strict=False)
    expected = (root / REVIEW_ASSIST_CONTEXT_REPORT).resolve(strict=False)
    candidate = Path(raw_path).resolve(strict=False)
    if candidate != expected:
        raise ValueError(f"unexpected review-assist context path: {candidate}")
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"review-assist context path escapes trusted extraction root: {candidate}")
    return candidate


def load_review_assist_context(config: Any) -> str:
    """Read the trusted PSScriptAnalyzer/review-assist markdown context if set."""
    context_path = os.environ.get("REVIEW_ASSIST_CONTEXT_PATH", "").strip()
    if not context_path:
        return ""
    try:
        trusted_context_path = review_assist_context_path(context_path)
        if trusted_context_path is None:
            return ""
        content = trusted_context_path.read_text(encoding="utf-8")
        max_chars = int(getattr(config, "deep_review_max_total_chars", 24000)) // 2
        if len(content) > max_chars:
            content = content[:max_chars] + "\n...(review-assist context truncated)"
        return content.strip()
    except Exception as exc:
        print(f"WARN: could not load review-assist context from {context_path}: {exc}", file=sys.stderr, flush=True)
        return ""


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
    if hasattr(base, "apply_debug_flag"):
        base.apply_debug_flag(config, comment_body, command)

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise hardened.ReviewTimeoutError(f"{base.REVIEW_DISPLAY_NAME} exceeded script timeout of {config.script_timeout_seconds} seconds")

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
        base.env_required("OPENROUTER_API_KEY")  # Validate required secret; request code reads it again.
        reporter.start()
        reporter.update("reaction", f"eyes add: {reaction_status['added']}")
        reporter.update("github", "fetching PR metadata")
        pr = gh.get_pr(pr_number)
        reporter.update("github", "fetching PR diff")
        diff = gh.get_pr_diff(pr_number)
        reporter.update("github", "fetching changed file list")
        files = gh.list_files(pr_number)
        set_python_path_alias_context(build_python_path_alias_context(gh, pr, files))
        set_python_os_alias_context(build_python_os_alias_context(gh, pr, files))
        try:
            prior_successful_review = has_prior_successful_context_review(gh, pr_number)
            reporter.update("review-mode", f"prior context review found: {str(prior_successful_review).lower()}")
        except Exception as exc:
            prior_successful_review = False
            reporter.update("review-mode", f"prior context review readback failed; using first-pass posture: {str(exc)[:240]}")
        review_mode = review_mode_for_command(comment_body, command, config, prior_successful_review)
        deep_context_block, context_summary = build_deep_context_block(gh, pr, files, config, review_mode)
        review_assist_ctx = load_review_assist_context(config)
        if review_assist_ctx:
            ra_header = "PowerShell static analysis context from last validate-on-pr run (PSScriptAnalyzer + review-assist):"
            deep_context_block = f"{ra_header}\n\n{review_assist_ctx}\n\n---\n\n{deep_context_block}".strip()
            reporter.update("review-assist-context", f"injected {len(review_assist_ctx)} chars of PSScriptAnalyzer context")
        safe_context_summary = sanitize_context_summary(context_summary, config)
        reporter.update("context", safe_context_summary)
        risk_sentinels = hardened.detect_risk_sentinels(diff, getattr(config, "risk_sentinel_max_anchors", 12))
        if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
            reporter.update("risk-sentinel", f"detected {len(risk_sentinels)} high-risk changed-line signals: {hardened.risk_sentinel_digest(risk_sentinels)}")
        line_index = hardened.build_added_line_index(diff)
        prompt_mode = "per-file first-pass prompts" if should_use_per_file_first_pass(review_mode, config) else "bounded whole-PR prompt"
        reporter.update("prompt", f"building {prompt_mode} from {len(files)} changed files")
        hardened.write_debug_json_artifact_safely(
            config,
            "metadata/review-context.json",
            {
                "pr_number": pr_number,
                "reviewed_head_sha": str(pr.get("head", {}).get("sha", "") or ""),
                "command": command,
                "debug": bool(getattr(config, "debug", False)),
                "workflow_run_id": base.workflow_run_id() if hasattr(base, "workflow_run_id") else os.environ.get("GITHUB_RUN_ID", ""),
                "workflow_run_url": base.workflow_run_url() if hasattr(base, "workflow_run_url") else "",
                "review_mode": review_mode,
                "context_summary": context_summary,
                "review_assist_context_chars": len(review_assist_ctx),
                "deep_context_chars": len(deep_context_block),
                "prompt_mode": prompt_mode,
                "prompt_chars": 0 if should_use_per_file_first_pass(review_mode, config) else "",
                "risk_sentinel_count": len(risk_sentinels),
                "risk_sentinel_digest": hardened.risk_sentinel_digest(risk_sentinels) if risk_sentinels else "",
                "line_index_entries": len(line_index),
                "changed_files": [
                    {
                        "filename": str(item.get("filename", "")),
                        "status": str(item.get("status", "")),
                        "additions": item.get("additions"),
                        "deletions": item.get("deletions"),
                        "changes": item.get("changes"),
                    }
                    for item in files
                ],
            },
        )
        hardened.write_debug_text_artifact_safely(config, "context/deep-context.md", deep_context_block or "(no deep context block)")
        if review_assist_ctx:
            hardened.write_debug_text_artifact_safely(config, "context/static-validation-context.md", review_assist_ctx)
        result, model_used, service_tier = openrouter_review_with_hybrid_first_pass(
            pr,
            files,
            diff,
            schema,
            config,
            reporter,
            risk_sentinels,
            line_index,
            deep_context_block,
            review_mode,
            context_summary,
            gh,
        )
        reporter.update("normalize", "mapping model findings to changed diff lines")
        findings, unanchored_findings = split_findings_with_review_body_fallback(result, config, line_index, diff, risk_sentinels)
        findings = hardened.add_risk_sentinel_fallback_findings(findings, risk_sentinels, config, unanchored_findings)
        hardened.enforce_risk_sentinel_findings(findings, risk_sentinels, config, unanchored_findings)
        findings = synthesize_fixes_for_findings(findings, gh, pr, FIX_SYNTHESIS_SCHEMA, config, reporter)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "line": line, "side": "RIGHT", "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        reviewed_commit = str(pr.get("head", {}).get("sha", "") or "")
        review_body = append_context_to_review_body(
            hardened.build_review_body_with_unanchored(result, findings, unanchored_findings, model_used, config, reviewed_commit),
            review_mode,
            context_summary,
            config,
        )
        unanchored_note = f" and {len(unanchored_findings)} unanchored review-body findings" if unanchored_findings else ""
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments{unanchored_note}")
        gh.create_review(pr_number, review_body, event, comments, reviewed_commit)
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
        set_python_path_alias_context({})
        set_python_os_alias_context({})
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)


if __name__ == "__main__":
    main()
