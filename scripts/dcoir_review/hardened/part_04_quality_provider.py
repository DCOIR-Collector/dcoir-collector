def raw_findings_digest(result: dict[str, Any]) -> str:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return "findings field was not a list"
    details: list[str] = []
    for item in raw_findings[:6]:
        if not isinstance(item, dict):
            details.append("invalid finding shape")
            continue
        raw_path = item.get("path")
        raw_line = item.get("line")
        raw_title = item.get("title")
        path = str(raw_path).strip() if raw_path else "<missing-path>"
        line = str(raw_line).strip() if raw_line else "<missing-line>"
        title = (str(raw_title).strip() if raw_title else "untitled")[:80]
        try:
            confidence = float(item.get("confidence", 0))
            confidence_text = f"{confidence:.2f}"
        except (TypeError, ValueError):
            confidence_text = "invalid"
        details.append(f"{path}:{line} confidence {confidence_text} ({title})")
    return "; ".join(details) if details else "no structured findings"


def finding_text_for_quality(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title", "") or ""),
        str(item.get("body", "") or ""),
        str(item.get("validation", "") or ""),
    ]
    return re.sub(r"\s+", " ", "\n".join(parts)).strip()


def non_actionable_finding_reason(item: dict[str, Any]) -> str:
    text = finding_text_for_quality(item)
    if not text:
        return ""
    for pattern, reason in NON_ACTIONABLE_FINDING_PATTERNS:
        if pattern.search(text):
            return reason
    return ""


def non_actionable_findings_digest(result: dict[str, Any], config: Any) -> str:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return ""
    details: list[str] = []
    for item in raw_findings[:6]:
        if not isinstance(item, dict):
            continue
        reason = non_actionable_finding_reason(item)
        if not reason:
            continue
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < config.minimum_confidence:
            continue
        raw_path = item.get("path")
        raw_line = item.get("line")
        raw_title = item.get("title")
        path = str(raw_path).strip() if raw_path else "<missing-path>"
        line = str(raw_line).strip() if raw_line else "<missing-line>"
        title = (str(raw_title).strip() if raw_title else "untitled")[:80]
        details.append(f"{path}:{line} {reason} ({title})")
    return "; ".join(details)



def has_minimum_confidence_finding(result: dict[str, Any], config: Any) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        try:
            if float(item.get("confidence", 0)) >= config.minimum_confidence:
                return True
        except (TypeError, ValueError):
            continue
    return False



def has_actionable_minimum_confidence_finding(result: dict[str, Any], config: Any) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict) or non_actionable_finding_reason(item):
            continue
        try:
            if float(item.get("confidence", 0)) >= config.minimum_confidence:
                return True
        except (TypeError, ValueError):
            continue
    return False

def has_actionable_changed_line_finding(
    result: dict[str, Any],
    config: Any,
    line_index: dict[tuple[str, int], int],
) -> bool:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list):
        return False
    for item in raw_findings:
        if not isinstance(item, dict) or non_actionable_finding_reason(item):
            continue
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", "")).strip()
        except (TypeError, ValueError):
            continue
        if confidence >= config.minimum_confidence and (path, line) in line_index:
            return True
    return False


def review_quality_retry_reason(
    result: dict[str, Any],
    config: Any,
    risk_sentinels: list[RiskSentinel],
    line_index: dict[tuple[str, int], int] | None = None,
) -> str:
    gated_sentinels = required_risk_sentinels(risk_sentinels)
    if (
        gated_sentinels
        and getattr(config, "risk_sentinel_quality_gate", True)
        and getattr(config, "risk_sentinel_retry_on_empty", True)
        and has_no_structured_findings(result)
    ):
        return "model returned zero findings despite high-risk changed-line signals"

    if not getattr(config, "review_quality_retry_on_rejected_output", True):
        return ""

    summary = str(result.get("summary", "")).strip()
    if has_no_structured_findings(result):
        if getattr(config, "fail_on_summary_only_problem", True) and summary_suggests_problem(summary):
            return "model summary indicated a possible issue while the structured findings array was empty"
        return ""

    raw_findings = result.get("findings", [])
    if raw_findings and getattr(config, "fail_on_unanchored_findings", True):
        non_actionable_details = non_actionable_findings_digest(result, config)
        if non_actionable_details and not has_actionable_minimum_confidence_finding(result, config):
            return (
                "model returned only self-described non-actionable or informational findings: "
                f"{non_actionable_details}"
            )
        if not has_minimum_confidence_finding(result, config):
            return (
                "model returned structured findings, but none met the configured minimum confidence "
                f"{config.minimum_confidence:.2f}: {raw_findings_digest(result)}"
            )
        if line_index is not None and not has_actionable_changed_line_finding(result, config, line_index):
            return (
                "model returned high-confidence structured findings, but none were anchored to changed diff lines: "
                f"{raw_findings_digest(result)}"
            )
        if (
            gated_sentinels
            and line_index is not None
            and getattr(config, "risk_sentinel_quality_gate", True)
        ):
            try:
                findings, unanchored_findings = split_findings(result, config, line_index)
            except ReviewQualityError:
                findings, unanchored_findings = [], []
            uncovered = uncovered_risk_sentinels(findings, gated_sentinels, config, unanchored_findings)
            if uncovered:
                return (
                    "model returned actionable findings, but they did not cover high-risk changed-line signals: "
                    f"{risk_sentinel_coverage_digest(uncovered)}"
                )

    return ""


def build_quality_retry_prompt(
    prompt: str,
    previous_result: dict[str, Any],
    risk_sentinels: list[RiskSentinel],
    config: Any,
    quality_issue: str | None = None,
) -> str:
    previous_summary = str(previous_result.get("summary", "")).strip() or "No previous summary returned."
    raw_findings = previous_result.get("findings", [])
    try:
        previous_findings = json.dumps(raw_findings[:6] if isinstance(raw_findings, list) else raw_findings, ensure_ascii=False, indent=2)
    except TypeError:
        previous_findings = str(raw_findings)
    if len(previous_findings) > 1800:
        previous_findings = f"{previous_findings[:1770]}... [truncated]"
    issue_line = quality_issue or "the previous response did not clear review-quality checks"
    anchor_block = risk_sentinel_block(risk_sentinels, config) if risk_sentinels else "No high-risk changed-line anchors were detected."
    retry_guidance = f"""
Review quality retry:
The previous response failed review-quality checks: {issue_line}.
Re-review the changed diff and return one of two valid outputs:
- Actionable findings anchored to changed right-side file/line entries with confidence at or above {config.minimum_confidence:.2f}, covering every high-risk anchor by path, nearby line, and risk class; or
- An empty findings array with a clean summary that does not imply a remaining issue.
Return the full corrected finding set. Preserve previous real actionable findings while adding or repairing missing anchor coverage; do not narrow the retry response to only the uncovered anchor.
Do not place actionable concerns only in the summary. Do not return low-confidence, unanchored, or speculative findings.
Do not return informational/advisory findings that explain there is no realized risk; use a clean summary for those.
Do not satisfy a high-risk anchor with an unrelated finding on another risk class.
If a previous finding was real but poorly anchored or below confidence threshold, convert it into a valid finding with exact file, changed line, observed behavior, impact, correction guidance, and validation/readback guidance.

{anchor_block}

Previous summary:
{previous_summary}

Previous structured findings:
{previous_findings}
""".strip()
    return append_with_budget(prompt, base.sanitize_text(retry_guidance, config), config.max_prompt_chars)


def has_no_structured_findings(result: dict[str, Any]) -> bool:
    findings = result.get("findings", [])
    return not isinstance(findings, list) or len(findings) == 0


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
        "X-OpenRouter-Title": base.REVIEW_DISPLAY_NAME,
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


