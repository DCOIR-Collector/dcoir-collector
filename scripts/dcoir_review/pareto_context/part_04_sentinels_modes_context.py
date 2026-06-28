def detect_python_file_write_path_sentinels(diff: str) -> list[hardened.RiskSentinel]:
    sentinels: list[hardened.RiskSentinel] = []
    assigned_paths: dict[str, list[PythonTrackedPath]] = {}
    scope_stack: list[PythonScope] = []
    next_scope_id = 0
    path_constructor_names = set(DEFAULT_PYTHON_PATH_CONSTRUCTORS)
    os_module_names = set(DEFAULT_PYTHON_OS_MODULES)
    current_path = ""
    current_hunk = 0
    current_alias_path = ""
    pending_path_assignment: list[PythonDiffLine] = []

    def flush_pending_path_assignment() -> None:
        nonlocal pending_path_assignment
        if not pending_path_assignment:
            return
        statement = "\n".join(line.text for line in pending_path_assignment)
        dynamic_target = python_dynamic_path_target(statement, path_constructor_names, os_module_names)
        if dynamic_target:
            push_assigned_path(
                assigned_paths,
                dynamic_target,
                pending_path_assignment[0],
                current_python_scope_id(scope_stack),
            )
        pending_path_assignment = []

    for diff_line in iter_python_diff_lines_with_context(diff):
        if diff_line.path != current_alias_path:
            path_constructor_names = set(DEFAULT_PYTHON_PATH_CONSTRUCTORS)
            path_constructor_names.update(PYTHON_PATH_ALIAS_CONTEXT.get(diff_line.path, set()))
            os_module_names = set(DEFAULT_PYTHON_OS_MODULES)
            os_module_names.update(PYTHON_OS_ALIAS_CONTEXT.get(diff_line.path, set()))
            current_alias_path = diff_line.path
        if diff_line.path != current_path:
            flush_pending_path_assignment()
            current_path = diff_line.path
            current_hunk = diff_line.hunk
            assigned_paths.clear()
            scope_stack.clear()
            next_scope_id = seed_python_hunk_scope(scope_stack, diff_line.hunk_context, next_scope_id)
        elif diff_line.hunk != current_hunk:
            flush_pending_path_assignment()
            if not trim_python_scope_stack_to_hunk(scope_stack, diff_line.hunk_context):
                assigned_paths.clear()
                scope_stack.clear()
                next_scope_id = seed_python_hunk_scope(scope_stack, diff_line.hunk_context, next_scope_id)
            current_hunk = diff_line.hunk
        diff_line_indent = python_code_line_indent(diff_line.text)
        pop_python_scopes_for_indent(scope_stack, diff_line_indent)
        prune_assigned_paths_for_active_scopes(assigned_paths, active_python_scope_ids(scope_stack))
        if diff_line.inside_multiline_string:
            continue
        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):
            continue
        path_constructor_names.update(python_path_constructor_aliases(diff_line.text))
        os_module_names.update(python_os_module_aliases(diff_line.text))
        if pending_path_assignment:
            pending_path_assignment.append(diff_line)
            statement = "\n".join(line.text for line in pending_path_assignment)
            if python_statement_is_complete(statement):
                flush_pending_path_assignment()
            continue
        if python_is_scope_boundary(diff_line.text):
            next_scope_id += 1
            scope_indent = diff_line_indent or 0
            scope_stack.append(PythonScope(scope_indent, python_scope_key(diff_line.text), next_scope_id))
            remove_shadowed_assigned_paths(
                assigned_paths,
                python_scope_boundary_shadowed_names(diff_line.text),
                diff_line,
                current_python_scope_id(scope_stack),
            )
        current_scope_id = current_python_scope_id(scope_stack)
        dynamic_target = python_dynamic_path_target(diff_line.text, path_constructor_names, os_module_names)
        if dynamic_target:
            push_assigned_path(assigned_paths, dynamic_target, diff_line, current_scope_id)
            continue
        augmented_dynamic_target = python_augmented_dynamic_path_target(diff_line.text, path_constructor_names, os_module_names)
        if augmented_dynamic_target:
            push_assigned_path(assigned_paths, augmented_dynamic_target, diff_line, current_scope_id)
            continue
        if python_path_assignment_start(diff_line.text, path_constructor_names, os_module_names) and not python_statement_is_complete(diff_line.text):
            pending_path_assignment = [diff_line]
            continue
        augmented_targets = python_augmented_assignment_targets(diff_line.text)
        assignment_indent = diff_line_indent or 0
        for assigned_target in python_assignment_target_names(diff_line.text):
            keep_exact_target = current_assigned_path(assigned_paths, assigned_target) is not None and (
                assigned_target in augmented_targets
                or python_assignment_value_references_target(
                    diff_line.text,
                    assigned_target,
                )
            )
            if keep_exact_target:
                assignment = current_assigned_path(assigned_paths, assigned_target)
                if diff_line.is_added and assignment is not None and not assignment.is_added:
                    push_assigned_path(assigned_paths, assigned_target, diff_line, current_scope_id)
            else:
                clear_assigned_path_in_scope(assigned_paths, assigned_target, assignment_indent, current_scope_id)
        write_target = python_file_write_target(diff_line.text, path_constructor_names, os_module_names)
        if not write_target:
            write_target = python_wrapped_file_write_target(diff_line.text, path_constructor_names, os_module_names)
        if not write_target:
            if diff_line.is_added and python_direct_dynamic_file_write(diff_line.text, path_constructor_names, os_module_names):
                append_file_write_sentinel(sentinels, diff_line)
            continue
        assignment = current_assigned_path(assigned_paths, write_target)
        if not assignment:
            if diff_line.is_added and python_direct_dynamic_file_write(diff_line.text, path_constructor_names, os_module_names):
                append_file_write_sentinel(sentinels, diff_line)
            continue
        if not assignment.is_added and not diff_line.is_added:
            continue
        anchor = assignment if assignment.is_added else diff_line
        append_file_write_sentinel(sentinels, anchor)
    flush_pending_path_assignment()
    return sentinels


def detect_github_actions_yaml_sentinels(diff: str) -> list[hardened.RiskSentinel]:
    sentinels: list[hardened.RiskSentinel] = []
    seen: set[tuple[str, int, str]] = set()
    for changed_line in hardened.iter_added_diff_lines(diff):
        if Path(changed_line.path).suffix.lower() not in {".yml", ".yaml"}:
            continue
        if hardened.is_comment_only_added_line(changed_line.path, changed_line.text):
            continue
        line_text = changed_line.text
        if GITHUB_ACTIONS_WRITE_PERMISSION_RE.search(line_text):
            key = (changed_line.path, changed_line.line, GITHUB_ACTIONS_BROAD_WRITE_PERMISSION_LABEL)
            if key not in seen:
                seen.add(key)
                sentinels.append(
                    hardened.RiskSentinel(
                        path=changed_line.path,
                        line=changed_line.line,
                        label=GITHUB_ACTIONS_BROAD_WRITE_PERMISSION_LABEL,
                        detail=GITHUB_ACTIONS_BROAD_WRITE_PERMISSION_DETAIL,
                        text=changed_line.text,
                    )
                )
        if GITHUB_ACTIONS_UNTRUSTED_CHECKOUT_REF_RE.search(line_text):
            key = (changed_line.path, changed_line.line, GITHUB_ACTIONS_UNTRUSTED_CHECKOUT_REF_LABEL)
            if key not in seen:
                seen.add(key)
                sentinels.append(
                    hardened.RiskSentinel(
                        path=changed_line.path,
                        line=changed_line.line,
                        label=GITHUB_ACTIONS_UNTRUSTED_CHECKOUT_REF_LABEL,
                        detail=GITHUB_ACTIONS_UNTRUSTED_CHECKOUT_REF_DETAIL,
                        text=changed_line.text,
                    )
                )
    return sentinels


def detect_risk_sentinels(diff: str, max_anchors: int | None = None) -> list[hardened.RiskSentinel]:
    diff_fixture_added_lines = python_diff_fixture_added_line_keys(diff)
    combined = [
        *detect_python_file_write_path_sentinels(diff),
        *detect_python_dynamic_exec_sentinels(diff),
        *detect_github_actions_yaml_sentinels(diff),
        *[
            sentinel
            for sentinel in _original_detect_risk_sentinels(diff, None)
            if (sentinel.path, sentinel.line) not in diff_fixture_added_lines
        ],
    ]
    deduped: list[hardened.RiskSentinel] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in combined:
        key = (sentinel.path, sentinel.line, sentinel.label)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    return hardened.select_risk_sentinels(deduped, max_anchors)


hardened.detect_risk_sentinels = detect_risk_sentinels


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
        # Exact multiples of 100 cost one extra empty-page readback, which is
        # acceptable for the small PR review counts this workflow expects.
        page += 1
    return reviews


def has_prior_successful_context_review(gh: Any, pr_number: int) -> bool:
    markers = (base.MARKER, *getattr(base, "LEGACY_MARKERS", ()))
    for review in list_pr_reviews(gh, pr_number):
        body = str(review.get("body", ""))
        if any(marker in body for marker in markers) and CONTEXT_REVIEW_MARKER in body:
            return True
    return False


def language_hint(path: str) -> str:
    suffix = Path(path).suffix.lower()
    # Common review surfaces get language hints; uncommon suffixes safely fall
    # back to plain text instead of expanding the prompt grammar surface.
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
    encoding = payload.get("encoding")
    content = payload.get("content")
    if content is None or (content == "" and encoding == "none"):
        raise RuntimeError("file exceeds GitHub content API limit (>1 MB); omitting from deep context")
    if encoding != "base64":
        raise RuntimeError("content API did not return base64 text")
    raw = base64.b64decode(str(content).replace("\n", ""))
    return raw.decode("utf-8")


FIX_SYNTHESIS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "DCOIR Review Fix Synthesis",
    "type": "object",
    "additionalProperties": False,
    "required": ["suggested_replacement", "remove", "replace", "add", "notes", "validation"],
    "properties": {
        "suggested_replacement": {
            "type": "string",
            "description": "Exact replacement code for the anchored review line only. Empty string if unsafe or not exact.",
        },
        "remove": {"type": "string", "description": "Code or behavior to remove when no native suggestion is safe."},
        "replace": {"type": "string", "description": "Replacement code or behavior when no native suggestion is safe."},
        "add": {"type": "string", "description": "Additional guard, validation, or test code to add when needed."},
        "notes": {"type": "string", "description": "Short implementation caveat. Empty when unnecessary."},
        "validation": {"type": "string", "description": "Exact validation command or commands that should pass after the fix."},
    },
}


def safe_artifact_name(path: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", path).strip("-")
    return (cleaned or fallback)[:120]


def added_diff_lines_for_path(diff: str, path: str) -> list[hardened.ChangedLine]:
    return [line for line in hardened.iter_added_diff_lines(diff) if line.path == path]


def is_probably_github_actions_workflow(path: str, text: str) -> bool:
    lower_path = path.lower()
    if lower_path.startswith(".github/workflows/"):
        return True
    if Path(lower_path).suffix not in {".yml", ".yaml"}:
        return False
    if "workflow" in Path(lower_path).name or "github" in lower_path or "actions" in lower_path:
        return True
    return bool(re.search(r"(?m)^\s*on\s*:\s*$", text) and re.search(r"(?m)^\s*jobs\s*:\s*$", text))


def file_specialization(path: str, text: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".ps1", ".psm1", ".psd1"}:
        return (
            "PowerShell specialization: inspect Invoke-Expression, Start-Process, Invoke-WebRequest/Invoke-RestMethod, "
            "Expand-Archive, Set-Content/Add-Content/Out-File/Copy-Item/Move-Item, Remove-Item, Set-Acl, request-controlled "
            "paths, credential forwarding, Windows PowerShell 5.1 compatibility, parser behavior, and PSScriptAnalyzer-style risks."
        )
    if suffix == ".py":
        return (
            "Python specialization: inspect unsafe deserialization, eval/exec/dynamic code evaluation, subprocess/shell execution, tar/zip/archive extraction, "
            "pathlib/os.path containment, raw SQL/query construction, requests/urllib/httpx outbound requests, secret/env persistence, "
            "temporary files, exception handling, and focused py_compile/Bandit/unit validation."
        )
    if suffix in {".yml", ".yaml"}:
        if is_probably_github_actions_workflow(path, text):
            return (
                "GitHub Actions YAML specialization: inspect pull_request_target, broad permissions, checkout of untrusted refs, "
                "untrusted github.event metadata in shell, token or secret forwarding, action pinning, command injection, and workflow "
                "inventory/readback validation."
            )
        return (
            "YAML specialization: inspect security-sensitive configuration, secret material, command fields, path or URL sinks, "
            "privilege settings, schema validity, and whether the file appears to define CI/CD or operational behavior."
        )
    if suffix in {".ts", ".js", ".mjs", ".cjs"}:
        return (
            "TypeScript/JavaScript specialization: inspect child_process execution, dynamic Function/eval, path joins/resolves before "
            "file writes, fetch/webhook token forwarding, raw SQL strings, async error handling, and TypeScript validation."
        )
    if suffix == ".json":
        return "JSON specialization: inspect schema validity, generated-report markers, duplicated or conflicting keys, and secret material."
    if suffix == ".md":
        return "Markdown/governance specialization: inspect misleading operator guidance, missing validation evidence, stale authority, and unsafe instructions."
    return "Generic specialization: inspect correctness, security, validation, and governance risk in the changed file."


def per_file_priority(item: dict[str, Any], file_text: str) -> tuple[int, int, str]:
    path = str(item.get("filename", "") or "")
    suffix = Path(path.lower()).suffix
    if suffix in {".ps1", ".psm1", ".psd1", ".py"}:
        family = 0
    elif suffix in {".yml", ".yaml"} and is_probably_github_actions_workflow(path, file_text):
        family = 0
    elif suffix in {".yml", ".yaml"}:
        family = 1
    elif suffix in {".ts", ".js", ".mjs", ".cjs"}:
        family = 2
    else:
        family = 3
    changes = int(item.get("changes") or 0)
    return family, -changes, path


def normalized_finding_text(value: Any, max_chars: int = 240) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())[:max_chars]


def finding_review_family(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "").strip()
    lower_path = path.lower()
    suffix = Path(lower_path).suffix
    title = str(finding.get("title", "") or "")
    body = str(finding.get("body", "") or "")
    haystack = f"{title}\n{body}".lower()
    if suffix in {".ps1", ".psm1", ".psd1"}:
        return "powershell"
    if suffix == ".py":
        return "python"
    if suffix in {".yml", ".yaml"}:
        if (
            lower_path.startswith(".github/workflows/")
            or "github action" in haystack
            or "workflow" in Path(lower_path).name
            or "/actions/" in lower_path
        ):
            return "github-actions-yaml"
        if (
            "kubernetes" in lower_path
            or lower_path.startswith("k8s/")
            or "/k8s/" in lower_path
            or "kubernetes" in haystack
            or "kubectl" in haystack
        ):
            return "kubernetes-yaml"
        return "yaml"
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        return "typescript"
    return "other"


def finding_dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(finding.get("path", "") or "").strip(),
        str(finding.get("line", "") or "").strip(),
        normalized_finding_text(finding.get("title", "")),
        normalized_finding_text(finding.get("body", "")),
    )


def dedupe_findings_for_ranking(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for finding in findings:
        key = finding_dedupe_key(finding)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


