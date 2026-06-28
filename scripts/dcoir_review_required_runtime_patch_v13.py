"""Thirteenth required-coverage layer for DCOIR Review.

Connector-safe overlay for the #338 live-test failures. This layer keeps v12's
selection machinery, then tightens semantic identity, final inline rendering,
overflow reporting, validation text, and workflow/Kubernetes domain boundaries.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v9 as v9
import dcoir_review_required_runtime_patch_v9_core as core
import dcoir_review_required_runtime_patch_v9_selection as selection
import dcoir_review_required_runtime_patch_v10 as v10
import dcoir_review_required_runtime_patch_v11 as v11
import dcoir_review_required_runtime_patch_v12 as v12

SentinelKey = tuple[str, int, str]
VERSION = "v13"

PS_PLAINTEXT_SECURE_STRING = "ps_plaintext_secure_string"
PS_RUN_KEY_PERSISTENCE = "ps_run_key_persistence"
TS_INNER_HTML = "ts_inner_html"
TS_DYNAMIC_EXECUTION = "ts_dynamic_execution"
K8S_HOST_PID = "k8s_host_pid"
K8S_HOST_NETWORK = getattr(v11, "K8S_HOST_NETWORK", "k8s_host_network")
K8S_PRIVILEGED_CONTAINER = getattr(v11, "K8S_PRIVILEGED_CONTAINER", "k8s_privileged_container")
K8S_PRIVILEGE_ESCALATION = getattr(v11, "K8S_PRIVILEGE_ESCALATION", "k8s_privilege_escalation")
K8S_HOST_PATH = getattr(v11, "K8S_HOST_PATH", "k8s_host_path")

REQUIRED_KINDS = set(getattr(v12, "REQUIRED_KINDS", set()))
TRACKED_HIGH_RISK_KINDS = REQUIRED_KINDS | {
    PS_PLAINTEXT_SECURE_STRING,
    PS_RUN_KEY_PERSISTENCE,
    TS_INNER_HTML,
    TS_DYNAMIC_EXECUTION,
    K8S_HOST_PID,
    K8S_HOST_NETWORK,
    K8S_PRIVILEGED_CONTAINER,
    K8S_PRIVILEGE_ESCALATION,
    K8S_HOST_PATH,
}


def _preserve(module: Any, name: str) -> Any:
    storage = f"_dcoir_required_v13_original_{name.lstrip('_')}"
    existing = getattr(module, storage, None)
    if callable(existing):
        return existing
    helper = getattr(module, name)
    setattr(module, storage, helper)
    return helper


_ORIGINAL_V12_SELECT_ONCE = _preserve(v12, "_select_once")
_ORIGINAL_V12_POSTABLE_KEY = _preserve(v12, "_postable_key")
_ORIGINAL_V12_SENTINEL_KEY = _preserve(v12, "_sentinel_key")
_ORIGINAL_V12_FALLBACK_FOR_SENTINEL = _preserve(v12, "_fallback_for_sentinel")
_ORIGINAL_V12_VALIDATION_FOR_KEY = _preserve(v12, "_validation_for_key")
_ORIGINAL_V12_CANONICAL_KIND = _preserve(v12, "_canonical_kind")
_ORIGINAL_V11_LINE_KIND = _preserve(v11, "_line_kind")


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _is_workflow_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return normalized.startswith(".github/workflows/") and normalized.endswith((".yml", ".yaml"))


def _is_probable_k8s(path: str, text: str = "") -> bool:
    if _is_workflow_path(path):
        return False
    normalized_path = path.replace("\\", "/").lower()
    basename = normalized_path.rsplit("/", 1)[-1]
    if any(token in normalized_path or token in basename for token in ("/k8s/", "/kubernetes/", "_k8s", "k8s", "kubernetes", "deployment", "manifest", "pod")):
        return True
    normalized_text = _normalize(text)
    return any(token in normalized_text for token in ("apiversion:", "kind: pod", "kind: deployment", "securitycontext:", "hostpid:", "hostnetwork:", "privileged: true", "hostpath:"))


def _domain_filtered_kind(path: str, kind: str, text: str = "") -> str:
    value = str(kind or "")
    if not value:
        return ""
    if _is_workflow_path(path) and value.startswith("k8s_"):
        return ""
    if _is_probable_k8s(path, text) and value.startswith("yaml_"):
        return ""
    return value


def _workflow_line_kind(path: str, text: str) -> str:
    if not _is_workflow_path(path):
        return ""
    lower = _normalize(text)
    if "github_token" in lower and "github.event.pull_request.body" in lower:
        return v10.YAML_TOKEN_TO_PR_URL
    if "pull_request_target" in lower:
        return v4.YAML_PULL_REQUEST_TARGET
    if "write-all" in lower or re.search(r"\b[a-z_-]+\s*:\s*write\b", lower):
        return v4.YAML_BROAD_WRITE
    if "pull_request.head" in lower or "head.sha" in lower or "github.head_ref" in lower:
        return v4.YAML_UNTRUSTED_CHECKOUT
    if ("curl" in lower or "wget" in lower) and ("| sh" in lower or "| bash" in lower):
        return v4.YAML_SHELL_PIPE
    if "github.event.pull_request" in lower and any(token in lower for token in ("sh -c", "bash -lc", "shell:", "run:")):
        return v4.YAML_METADATA_SHELL
    return ""


def _python_line_kind(path: str, text: str) -> str:
    if Path(path.lower()).suffix != ".py":
        return ""
    lower = _normalize(text)
    if "pickle.load" in lower or "pickle.loads" in lower:
        return v9.PYTHON_PICKLE_LOAD
    if "yaml.load" in lower:
        return v5.PYTHON_YAML_LOAD
    if "shell=true" in lower or "os.system(" in lower or "os.popen(" in lower:
        return v5.PYTHON_SHELL_EXEC
    if "requests." in lower and "callback" in lower and ("authorization" in lower or "bearer" in lower or "dcoir_token" in lower):
        return v5.PYTHON_ENV_TOKEN
    if "extractall" in lower:
        return v11.PYTHON_ARCHIVE_EXTRACT
    if (".open(" in lower or "open(" in lower) and any(token in lower for token in ("write", "wb", "w+b", "w\"")):
        return v11.PYTHON_PATH_WRITE
    return ""


def _powershell_line_kind(path: str, text: str) -> str:
    if Path(path.lower()).suffix != ".ps1":
        return ""
    lower = _normalize(text)
    if "invoke-expression" in lower or "iex " in lower:
        return v9.PS_DYNAMIC_EXEC
    if "convertto-securestring" in lower and "-asplaintext" in lower:
        return PS_PLAINTEXT_SECURE_STRING
    if "filesystemaccessrule" in lower or "set-acl" in lower:
        return v4.PS_ACL
    if "start-process" in lower:
        return v4.PS_PROCESS_LAUNCH
    if ("invoke-webrequest" in lower or "invoke-restmethod" in lower) and ("authorization" in lower or "bearer" in lower):
        return v5.PS_ENV_TOKEN
    if "\\currentversion\\run" in lower or "currentversion\\run" in lower:
        return PS_RUN_KEY_PERSISTENCE
    return ""


def _k8s_line_kind(path: str, text: str) -> str:
    if not _is_probable_k8s(path, text):
        return ""
    lower = _normalize(text)
    if "hostpid:" in lower:
        return K8S_HOST_PID
    if "hostnetwork:" in lower:
        return K8S_HOST_NETWORK
    if "privileged: true" in lower:
        return K8S_PRIVILEGED_CONTAINER
    if "allowprivilegeescalation:" in lower:
        return K8S_PRIVILEGE_ESCALATION
    if "hostpath:" in lower:
        return K8S_HOST_PATH
    return ""


def _typescript_line_kind(path: str, text: str) -> str:
    if Path(path.lower()).suffix not in {".ts", ".tsx", ".js", ".jsx"}:
        return ""
    lower = _normalize(text)
    if ".innerhtml" in lower or ".outerhtml" in lower or "insertadjacenthtml" in lower:
        return TS_INNER_HTML
    if "settimeout(" in lower or "setinterval(" in lower or "new function(" in lower:
        return TS_DYNAMIC_EXECUTION
    return ""


def _line_kind(path: str, text: str) -> str:
    for classifier in (_workflow_line_kind, _python_line_kind, _powershell_line_kind, _k8s_line_kind, _typescript_line_kind):
        kind = classifier(path, text)
        if kind:
            return _domain_filtered_kind(path, kind, text)
    return _domain_filtered_kind(path, _ORIGINAL_V11_LINE_KIND(path, text), text)


def _canonical_kind(kind: str, text: str = "", detail: str = "", path: str = "") -> str:
    value = _ORIGINAL_V12_CANONICAL_KIND(kind, text, detail)
    context = _normalize(f"{text}\n{detail}")
    if value == getattr(v4, "PYTHON_SSRF", "python_ssrf"):
        has_token = "dcoir_token" in context or "os.environ" in context or "os.getenv" in context
        has_auth = "authorization" in context and ("bearer" in context or "token" in context)
        if ("callback" in context or "requests." in context) and (has_token or has_auth):
            value = v5.PYTHON_ENV_TOKEN
    return _domain_filtered_kind(path, value, context) if path else value


def _trusted_key_from_finding(finding: dict[str, Any]) -> SentinelKey | None:
    raw = finding.get("_risk_sentinel_key")
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        return None
    path = str(raw[0] or "")
    line = core._line_number(raw[1])
    kind = str(raw[2] or "")
    anchored_text = str(finding.get("_anchored_line_text", "") or "")
    if not path or not line or not kind or not anchored_text:
        return None
    if _line_kind(path, anchored_text) != kind:
        return None
    filtered = _domain_filtered_kind(path, kind, anchored_text)
    return (path, line, filtered) if filtered else None


def _sentinel_key(sentinel: Any) -> SentinelKey:
    path, line, base_kind = _ORIGINAL_V12_SENTINEL_KEY(sentinel)
    text = str(getattr(sentinel, "text", "") or "")
    detail = "\n".join(str(getattr(sentinel, name, "") or "") for name in ("label", "detail"))
    kind = _line_kind(path, text) or _canonical_kind(base_kind, text, detail, path)
    return path, line, _domain_filtered_kind(path, kind, text)


def _postable_key(finding: dict[str, Any]) -> SentinelKey:
    trusted = _trusted_key_from_finding(finding)
    if trusted:
        return trusted
    path, line, base_kind = _ORIGINAL_V12_POSTABLE_KEY(finding)
    text = "\n".join(str(finding.get(name, "") or "") for name in ("_anchored_line_text", "title", "body", "description"))
    kind = _line_kind(path, text) or _canonical_kind(base_kind, text, text, path)
    return path, line, _domain_filtered_kind(path, kind, text)


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
        v4.YAML_METADATA_SHELL: 1,
        v4.YAML_SHELL_PIPE: 3,
        v4.YAML_UNTRUSTED_CHECKOUT: 4,
        v4.YAML_PULL_REQUEST_TARGET: 5,
        v4.YAML_BROAD_WRITE: 6,
        v9.PS_DYNAMIC_EXEC: 10,
        v4.PS_ACL: 11,
        v4.PS_PROCESS_LAUNCH: 12,
        v5.PS_ENV_TOKEN: 13,
        PS_PLAINTEXT_SECURE_STRING: 14,
        PS_RUN_KEY_PERSISTENCE: 15,
        v9.PYTHON_PICKLE_LOAD: 20,
        v5.PYTHON_YAML_LOAD: 21,
        v5.PYTHON_SHELL_EXEC: 22,
        v5.PYTHON_ENV_TOKEN: 23,
        v11.PYTHON_ARCHIVE_EXTRACT: 24,
        v11.PYTHON_PATH_WRITE: 25,
        K8S_HOST_PID: 40,
        K8S_HOST_NETWORK: 41,
        K8S_PRIVILEGED_CONTAINER: 42,
        K8S_PRIVILEGE_ESCALATION: 43,
        K8S_HOST_PATH: 44,
        TS_INNER_HTML: 50,
        TS_DYNAMIC_EXECUTION: 51,
    }
    return order.get(str(kind or ""), 99)


def _text_kinds(path: str, text: str) -> set[str]:
    result: set[str] = set()
    for line in str(text or "").splitlines() or [str(text or "")]:
        kind = _line_kind(path, line)
        if kind:
            result.add(kind)
    return result


def _semantic_mismatch(finding: dict[str, Any], expected: dict[tuple[str, int], set[str]]) -> bool:
    path, line, kind = _postable_key(finding)
    allowed = expected.get((path, line), set())
    if allowed and kind not in allowed:
        return True
    rendered_kinds = _text_kinds(path, "\n".join(str(finding.get(name, "") or "") for name in ("title", "body")))
    contradictory = {candidate for candidate in rendered_kinds if candidate != kind and candidate in TRACKED_HIGH_RISK_KINDS}
    return bool(contradictory)


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    quoted_path = repr(path)
    if kind.startswith("python_"):
        return f"python3 -m py_compile {path}"
    if kind.startswith("ps_"):
        ps_path = path.replace("'", "''")
        script = "$errors=$null; " + f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{ps_path}'), [ref]$errors) | Out-Null; " + "if ($errors) { throw ($errors | Out-String) }"
        return "pwsh -NoProfile -Command " + shlex.quote(script)
    if kind == v10.YAML_TOKEN_TO_PR_URL:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert not ('GITHUB_TOKEN' in text and 'github.event.pull_request.body' in text)")
    if kind == v4.YAML_METADATA_SHELL:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert 'github.event.pull_request.labels' not in text and 'github.event.pull_request.body' not in text")
    if kind == v4.YAML_SHELL_PIPE:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert '| sh' not in text and '| bash' not in text")
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert 'github.event.pull_request.head' not in text and 'github.head_ref' not in text")
    if kind == v4.YAML_BROAD_WRITE:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert 'write-all' not in text and ': write' not in text")
    if kind == v4.YAML_PULL_REQUEST_TARGET:
        return "python3 -c " + shlex.quote(f"from pathlib import Path; text=Path({quoted_path}).read_text(); assert 'pull_request_target' not in text")
    if kind.startswith(("yaml_", "k8s_")):
        return "python3 -c " + shlex.quote(f"from pathlib import Path; Path({quoted_path}).read_text()")
    return _ORIGINAL_V12_VALIDATION_FOR_KEY(kind, path, line)


def _template_for_kind(kind: str) -> tuple[str, str, str]:
    templates = {
        v10.YAML_TOKEN_TO_PR_URL: ("Workflow sends repository token to PR-controlled URL", "This workflow sends a repository token to a URL taken from pull request metadata.", "Use a trusted allowlisted endpoint or remove the outbound request from the privileged workflow."),
        v4.YAML_METADATA_SHELL: ("Workflow executes pull request metadata in a shell", "This line passes pull request metadata into shell execution.", "Do not execute PR metadata; use explicit allowlisted values outside privileged shell steps."),
        v4.YAML_SHELL_PIPE: ("Workflow pipes a network-fetched script into a shell", "This line executes network-fetched content directly in the shell.", "Download, pin, and verify the content before execution."),
        v4.YAML_UNTRUSTED_CHECKOUT: ("Privileged workflow checks out untrusted PR code", "This privileged workflow checks out pull request controlled code.", "Use a trusted base ref or split privileged metadata handling from untrusted code checkout."),
        v4.YAML_PULL_REQUEST_TARGET: ("Privileged pull_request_target workflow context", "pull_request_target runs with base-repository privileges.", "Keep untrusted PR code and shell execution out of this workflow."),
        v4.YAML_BROAD_WRITE: ("GitHub Actions workflow grants broad write permissions", "This workflow grants write-scoped permissions.", "Reduce permissions to the least privilege required by each job."),
        v9.PS_DYNAMIC_EXEC: ("PowerShell executes caller-controlled code", "This line executes input as PowerShell code.", "Replace dynamic execution with an allowlisted command path."),
        PS_PLAINTEXT_SECURE_STRING: ("PowerShell converts plaintext into a SecureString", "This line treats plaintext input as secret material.", "Load secrets from the platform secret store instead of caller plaintext."),
        v4.PS_ACL: ("PowerShell grants broad filesystem ACL access", "This line grants broad filesystem permissions.", "Grant only the least-privileged identity and access rights needed."),
        v4.PS_PROCESS_LAUNCH: ("PowerShell launches a caller-controlled process", "This line launches a process from caller-controlled values.", "Resolve executables from an allowlist and pass structured arguments."),
        v5.PS_ENV_TOKEN: ("PowerShell forwards an environment token to a request-controlled callback", "This line reads an environment token and forwards it to a request-controlled callback.", "Allowlist destinations and keep authorization headers scoped to trusted endpoints."),
        PS_RUN_KEY_PERSISTENCE: ("PowerShell writes a Windows Run-key persistence location", "This line writes to a Run-key persistence location.", "Remove the Run-key write or gate it behind a governed audited operation."),
        v9.PYTHON_PICKLE_LOAD: ("Python deserializes untrusted pickle data", "pickle can execute code during deserialization.", "Use a safe data format or only unpickle trusted authenticated data."),
        v5.PYTHON_YAML_LOAD: ("Python loads YAML with an unsafe loader", "yaml.load with an unsafe loader can construct arbitrary objects.", "Use yaml.safe_load for untrusted YAML."),
        v5.PYTHON_SHELL_EXEC: ("Python executes caller-controlled shell text", "This line executes shell text from caller-controlled input.", "Use an allowlisted executable and argument list with shell=False."),
        v5.PYTHON_ENV_TOKEN: ("Python forwards an environment token to a request-controlled callback", "This line reads an environment token and forwards it to a request-controlled callback.", "Allowlist callback hosts and keep authorization headers scoped to trusted endpoints."),
        v11.PYTHON_ARCHIVE_EXTRACT: ("Python extracts an archive without path containment checks", "Archive extraction can write outside the intended directory.", "Validate each member path resolves under the destination before extraction."),
        v11.PYTHON_PATH_WRITE: ("Python writes to a request-controlled filesystem path", "This write may use a request-controlled path.", "Resolve and verify the destination is inside the governed output directory."),
        K8S_HOST_PID: ("Kubernetes workload shares the host PID namespace", "hostPID exposes the host process namespace.", "Remove hostPID unless there is a governed operational requirement."),
        K8S_HOST_NETWORK: ("Kubernetes workload shares the host network namespace", "hostNetwork exposes host networking to the workload.", "Remove hostNetwork unless the workload has a documented need."),
        K8S_PRIVILEGED_CONTAINER: ("Kubernetes container runs privileged", "privileged: true gives broad host-level capabilities.", "Drop privileged mode and grant only required capabilities."),
        K8S_PRIVILEGE_ESCALATION: ("Kubernetes container allows privilege escalation", "allowPrivilegeEscalation permits additional privileges.", "Set allowPrivilegeEscalation: false and drop unnecessary capabilities."),
        K8S_HOST_PATH: ("Kubernetes workload mounts a hostPath volume", "hostPath mounts host filesystem paths into the workload.", "Use a scoped persistent volume or remove the host filesystem mount."),
        TS_INNER_HTML: ("TypeScript writes untrusted data into HTML", "Writing untrusted data to innerHTML can create DOM injection.", "Use textContent or a vetted sanitizer."),
        TS_DYNAMIC_EXECUTION: ("TypeScript executes dynamic string code", "Dynamic string execution can run attacker-controlled JavaScript.", "Use function callbacks and allowlisted behavior instead of executable strings."),
    }
    return templates.get(kind, ("Security-sensitive changed line", "This changed line matched a high-risk review sentinel.", "Replace the risky pattern with a governed safe implementation."))


def _language_for_kind(kind: str) -> str:
    if kind.startswith("python_"):
        return "python"
    if kind.startswith("ps_"):
        return "powershell"
    if kind.startswith(("yaml_", "k8s_")):
        return "yaml"
    if kind.startswith("ts_"):
        return "typescript"
    return "text"


def _scrub_model_footer(value: Any) -> Any:
    if isinstance(value, str):
        scrubbed = re.sub(r"\n?\s*_Reviewed with [^._]+(?:\.[^_]*)?\._\s*", "", value)
        return re.sub(r"(?im)^\s*_?Reviewed with .+?_?\s*$", "", scrubbed).strip()
    if isinstance(value, dict):
        return {key: _scrub_model_footer(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_model_footer(item) for item in value]
    return value


def _safe_validation(kind: str, path: str, line: int, value: Any = "") -> str:
    current = str(value or "")
    if not current.strip() or "<<" in current or current.count("```") % 2 or "assert text.strip()" in current or current.strip().lower().startswith(("validate ", "validation:")):
        return _validation_for_key(kind, path, line)
    return current


def _integrity_finding(finding: dict[str, Any], key: SentinelKey | None = None, *, force_template: bool = False) -> dict[str, Any]:
    path, line, kind = key or _postable_key(finding)
    item = dict(_scrub_model_footer(finding))
    if not kind:
        return item
    title, body, notes = _template_for_kind(kind)
    rendered_kinds = _text_kinds(path, "\n".join(str(item.get(name, "") or "") for name in ("title", "body")))
    contradictory = {candidate for candidate in rendered_kinds if candidate != kind and candidate in TRACKED_HIGH_RISK_KINDS}
    if force_template or contradictory or kind in TRACKED_HIGH_RISK_KINDS:
        item["title"] = title
        item["body"] = body
    validation = _safe_validation(kind, path, line, item.get("validation", ""))
    item["validation"] = validation
    guidance = item.get("fix_guidance") if isinstance(item.get("fix_guidance"), dict) else {}
    guidance = dict(_scrub_model_footer(guidance))
    guidance.setdefault("language", _language_for_kind(kind))
    guidance["notes"] = notes
    guidance["validation"] = validation
    item["fix_guidance"] = guidance
    item["_risk_sentinel_key"] = [path, line, kind]
    item["_risk_sentinel_kind"] = kind
    return item


def _fallback_for_sentinel(hardened: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    path, line, kind = key
    if kind in TRACKED_HIGH_RISK_KINDS:
        return _integrity_finding({"severity": "critical" if kind in REQUIRED_KINDS else "high", "confidence": 0.99, "path": path, "line": line, "_anchored_line_text": str(getattr(sentinel, "text", "") or "")}, key, force_template=True)
    fallback = _ORIGINAL_V12_FALLBACK_FOR_SENTINEL(hardened, sentinel, config)
    fallback["_risk_sentinel_key"] = [path, line, kind]
    fallback["_risk_sentinel_kind"] = kind
    return _integrity_finding(fallback, key)


def _sentinel_sort_key(sentinel: Any) -> tuple[int, str, int, str]:
    path, line, kind = _sentinel_key(sentinel)
    return _kind_rank(kind), path, line, str(getattr(sentinel, "text", "") or "")


def _balanced_required_order(targets: list[Any]) -> list[Any]:
    return sorted(targets, key=_sentinel_sort_key)


def _spare_priority(finding: dict[str, Any]) -> tuple[int, int, int, float, str, int]:
    path, line, kind = _postable_key(finding)
    family_rank = 0 if kind.startswith("yaml_") else 1 if kind.startswith("ps_") else 2 if kind.startswith("python_") else 5 if kind.startswith("k8s_") else 6 if kind.startswith("ts_") else 7
    if "/optional_" in path.lower() or path.rsplit("/", 1)[-1].startswith("optional_"):
        family_rank += 5
    return family_rank, _kind_rank(kind), core._severity_rank(finding), -core._confidence(finding), path, line


def _dedupe(findings: list[dict[str, Any]], expected: dict[tuple[str, int], set[str]]) -> tuple[list[dict[str, Any]], list[str]]:
    kept: dict[SentinelKey, dict[str, Any]] = {}
    order: list[SentinelKey] = []
    dropped: list[str] = []
    for raw in findings:
        item = v5._normalize_comment_finding(raw)
        key = _postable_key(item)
        if _semantic_mismatch(item, expected):
            rendered_as = ",".join(sorted(_text_kinds(key[0], "\n".join(str(item.get(name, "") or "") for name in ("title", "body")))))
            dropped.append(f"{key[0]}:{key[1]} reason=contradictory_render_kind expected={','.join(sorted(expected.get((key[0], key[1]), set())))} actual={key[2]} rendered_as={rendered_as}")
            continue
        if not key[2]:
            dropped.append(f"{key[0]}:{key[1]} reason=empty_kind")
            continue
        normalized = _integrity_finding(item, key)
        if key not in kept:
            kept[key] = normalized
            order.append(key)
        elif (core._severity_rank(normalized), -core._confidence(normalized)) < (core._severity_rank(kept[key]), -core._confidence(kept[key])):
            kept[key] = normalized
    return [kept[key] for key in order], dropped


def _deterministic_inline_comment(finding: dict[str, Any]) -> str:
    item = _integrity_finding(finding, _postable_key(finding), force_template=True)
    guidance = item.get("fix_guidance") if isinstance(item.get("fix_guidance"), dict) else {}
    lines = [f"### {item.get('title', 'Security-sensitive changed line')}", "", str(item.get("body", "") or "").strip()]
    notes = str(guidance.get("notes", "") or "").strip()
    validation = str(item.get("validation", "") or guidance.get("validation", "") or "").strip()
    if notes:
        lines.extend(["", "**Suggested fix:**", notes])
    if validation:
        lines.extend(["", "**Validation:**", f"`{validation}`"])
    return "\n".join(lines).strip()


def _rendered_comment_has_problem(rendered: str, finding: dict[str, Any]) -> bool:
    path, _line, kind = _postable_key(finding)
    if "Reviewed with " in rendered or "_Reviewed with " in rendered:
        return True
    if "<<" in rendered or "assert text.strip()" in rendered or rendered.count("```") % 2:
        return True
    return bool({candidate for candidate in _text_kinds(path, rendered) if candidate != kind and candidate in TRACKED_HIGH_RISK_KINDS})


def _sanitize_rendered_inline_comment(rendered: Any, finding: dict[str, Any]) -> str:
    text = str(_scrub_model_footer(rendered or "")).strip()
    if not text or _rendered_comment_has_problem(text, finding):
        return _deterministic_inline_comment(finding)
    return text


def _overflow_section(metadata: dict[str, Any]) -> str:
    omitted_required = list(metadata.get("omitted_required_sentinels", []) or [])
    optional = list(metadata.get("omitted_optional_high_risk_sentinels", []) or [])
    detector = list(metadata.get("detector_only_high_risk_overflow", []) or [])
    if not omitted_required and not optional and not detector:
        return ""
    def line(prefix: str, item: dict[str, Any]) -> str:
        return f"- {prefix}: `{item.get('path')}:{item.get('line')}` `{item.get('kind')}` ({item.get('reason', 'overflow')})"
    lines = ["", "---", "", "### DCOIR Review Overflow", "The inline review comment budget was reached. The findings below were not posted inline and should still be reviewed."]
    if omitted_required:
        lines.extend(["", "**Omitted hard-required findings:**"])
        lines.extend(line("Required", item) for item in omitted_required[:12])
    if optional:
        lines.extend(["", "**Omitted optional/high-risk findings:**"])
        lines.extend(line("High risk", item) for item in optional[:8])
    if detector:
        lines.extend(["", "**Detected high-risk findings outside selected sentinel budget:**"])
        lines.extend(line("Detected", item) for item in detector[:8])
    return "\n".join(lines).strip()


def _append_overflow_to_review_body(body: Any) -> str:
    text = str(_scrub_model_footer(body or "")).strip()
    section = _overflow_section(dict(core.SELECTION_SUMMARY))
    if not section or "### DCOIR Review Overflow" in text:
        return text
    return f"{text}\n\n{section}".strip()


def _sentinel_record(sentinel: Any, reason: str, required: set[SentinelKey], selected: set[SentinelKey], limit: int) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    coverage = _coverage_key(key)
    if reason == "auto":
        reason = "duplicate_covered" if coverage in selected else "omitted_due_to_inline_budget" if len(selected) >= limit else "not_selected"
    return {"path": key[0], "line": key[1], "kind": key[2], "reason": reason, "label": str(getattr(sentinel, "label", "") or ""), "detail": str(getattr(sentinel, "detail", "") or "")[:240], "text": str(getattr(sentinel, "text", "") or "")[:240]}


def _augment_metadata(selected: list[dict[str, Any]], findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, metadata: dict[str, Any]) -> dict[str, Any]:
    limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    required_targets = list(v12._coalesce_required(v12._required_sentinels(None, risk_sentinels))[0])
    required_cov = {_coverage_key(_sentinel_key(item)) for item in required_targets}
    selected_keys = [_postable_key(item) for item in selected]
    selected_cov = {_coverage_key(key) for key in selected_keys}
    omitted_required = [_sentinel_record(item, "auto", required_cov, selected_cov, limit) for item in required_targets if _coverage_key(_sentinel_key(item)) not in selected_cov]
    optional = [_sentinel_record(item, "auto", required_cov, selected_cov, limit) for item in risk_sentinels if _coverage_key(_sentinel_key(item)) not in selected_cov and _coverage_key(_sentinel_key(item)) not in required_cov and _sentinel_key(item)[2] in TRACKED_HIGH_RISK_KINDS]
    detector: list[dict[str, Any]] = []
    seen: set[SentinelKey] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        key = _postable_key(finding)
        coverage = _coverage_key(key)
        if key[2] in TRACKED_HIGH_RISK_KINDS and coverage not in selected_cov and coverage not in required_cov and key not in seen:
            detector.append({"path": key[0], "line": key[1], "kind": key[2], "reason": "detected_not_selected", "title": str(finding.get("title", "") or "")[:160]})
            seen.add(key)
    metadata = dict(metadata)
    metadata.pop("required_ledger_keys", None)
    metadata.pop("required_ledger_accounted_count", None)
    metadata.update({
        "version": VERSION,
        "selected_keys": [f"{path}:{line} {kind}" for path, line, kind in selected_keys],
        "final_postable_count": len(selected),
        "inline_limit": limit,
        "posted_required_sentinels": [f"{path}:{line} {kind}" for path, line, kind in selected_keys if _coverage_key((path, line, kind)) in required_cov],
        "omitted_required_sentinels": omitted_required[:80],
        "omitted_optional_high_risk_sentinels": optional[:80],
        "detector_only_high_risk_overflow": detector[:80],
        "overflow_required_count": len(omitted_required),
        "overflow_optional_high_risk_count": len(optional),
        "overflow_detector_high_risk_count": len(detector),
        "partial_overflow": bool(omitted_required or optional or detector),
        "required_ledger_schema": "v13_split_posted_omitted_duplicate_suppressed",
        "final_invalid_selected_keys": [],
        "final_uncovered": [f"{item['path']}:{item['line']} {item['kind']}" for item in omitted_required],
    })
    return metadata


def _select_once(hardened: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _patch_v12_globals()
    selected, metadata = _ORIGINAL_V12_SELECT_ONCE(hardened, findings, risk_sentinels, config)
    selected = [_integrity_finding(item, _postable_key(item), force_template=True) for item in selected]
    return selected, _augment_metadata(selected, findings, risk_sentinels, config, metadata)


def _select_required_postable(hardened: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    del unanchored_findings
    selected, metadata = _select_once(hardened, findings, risk_sentinels, config)
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
        writer(config, "metadata/required-v13-final-selection.json", metadata)
        writer(config, "metadata/required-v12-final-selection.json", metadata)
    v9._ensure_prompt_review(config)
    return selected


def _patch_detect(owner: Any, sentinel_owner: Any | None = None) -> None:
    original = getattr(owner, "_dcoir_required_v13_original_detect_risk_sentinels", None)
    if original is None:
        original = getattr(owner, "detect_risk_sentinels", None)
        owner._dcoir_required_v13_original_detect_risk_sentinels = original
    if not callable(original):
        return
    def detect_risk_sentinels(diff: str, *args: Any, **kwargs: Any) -> list[Any]:
        try:
            sentinels = list(original(diff, *args, **kwargs))
        except TypeError:
            sentinels = list(original(diff))
        risk_sentinel_type = getattr(owner, "RiskSentinel", None) or getattr(sentinel_owner, "RiskSentinel", None)
        if risk_sentinel_type is None:
            return sentinels
        existing = {_sentinel_key(item) for item in sentinels}
        for path, line, text in selection._iter_added_diff_lines(diff):
            checker = getattr(owner, "is_comment_only_added_line", None) or getattr(sentinel_owner, "is_comment_only_added_line", None)
            if callable(checker) and checker(path, text):
                continue
            kind = _line_kind(path, text)
            if kind not in TRACKED_HIGH_RISK_KINDS:
                continue
            key = (path, line, kind)
            if key in existing:
                continue
            title, body, _notes = _template_for_kind(kind)
            sentinels.append(risk_sentinel_type(path=path, line=line, label=title, detail=body, text=text))
            existing.add(key)
        return sentinels
    owner.detect_risk_sentinels = detect_risk_sentinels


def _patch_required_selection(module: Any, hardened: Any) -> None:
    def add_risk_sentinel_fallback_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        return _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)
    def enforce_risk_sentinel_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> None:
        findings[:] = _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)
    hardened.add_risk_sentinel_fallback_findings = add_risk_sentinel_fallback_findings
    hardened.enforce_risk_sentinel_findings = enforce_risk_sentinel_findings
    module.rank_findings_for_required_budget = lambda findings, config: sorted([_integrity_finding(v5._normalize_comment_finding(item)) for item in findings if isinstance(item, dict)], key=_spare_priority)[: max(0, int(getattr(config, "max_inline_comments", 12)))]


def _patch_final_rendering(base: Any) -> None:
    original = getattr(base, "_dcoir_v13_original_build_inline_comment", None)
    if original is None:
        original = getattr(base, "build_inline_comment", None)
        base._dcoir_v13_original_build_inline_comment = original
    if not callable(original):
        return
    def v13_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
        del model_used
        item = _integrity_finding(finding, _postable_key(finding), force_template=True)
        rendered = original(item, "", config)
        return _sanitize_rendered_inline_comment(rendered, item)
    base.build_inline_comment = v13_build_inline_comment


def _patch_review_body_overflow(hardened: Any) -> None:
    original = getattr(hardened, "_dcoir_v13_original_build_review_body_with_unanchored", None)
    if original is None:
        original = getattr(hardened, "build_review_body_with_unanchored", None)
        hardened._dcoir_v13_original_build_review_body_with_unanchored = original
    if not callable(original):
        return
    def v13_build_review_body_with_unanchored(*args: Any, **kwargs: Any) -> str:
        return _append_overflow_to_review_body(original(*args, **kwargs))
    hardened.build_review_body_with_unanchored = v13_build_review_body_with_unanchored


def _patch_v12_globals() -> None:
    v12._canonical_kind = _canonical_kind
    v12._sentinel_key = _sentinel_key
    v12._postable_key = _postable_key
    v12._coverage_key = _coverage_key
    v12._kind_rank = _kind_rank
    v12._sentinel_sort_key = _sentinel_sort_key
    v12._balanced_required_order = _balanced_required_order
    v12._spare_priority = _spare_priority
    v12._semantic_mismatch = _semantic_mismatch
    v12._validation_for_key = _validation_for_key
    v12._fallback_for_sentinel = _fallback_for_sentinel
    v12._dedupe = _dedupe


def _patch_core_semantics() -> None:
    _patch_v12_globals()
    core._sentinel_key = _sentinel_key
    core._postable_key = _postable_key
    core._coverage_key = _coverage_key
    core._semantic_mismatch = _semantic_mismatch
    core._dedupe = _dedupe
    core._spare_priority = _spare_priority
    core._validation_for_key = _validation_for_key
    v9._sentinel_key = _sentinel_key
    v9._postable_key = _postable_key
    v9._semantic_mismatch = _semantic_mismatch
    v11._line_kind = _line_kind
    v11._sentinel_key = _sentinel_key
    v11._postable_key = _postable_key
    v11._coverage_key = _coverage_key
    v11._semantic_mismatch = _semantic_mismatch
    v11._dedupe = _dedupe
    v11._spare_priority = _spare_priority
    v11._validation_for_key = _validation_for_key


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    _patch_core_semantics()
    _patch_detect(module, hardened)
    if base is not None:
        _patch_final_rendering(base)
    if hardened is not None:
        _patch_detect(hardened)
        _patch_required_selection(module, hardened)
        _patch_review_body_overflow(hardened)
    if base is not None:
        v11._patch_progress_comment(base, hardened)
