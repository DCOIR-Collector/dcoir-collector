#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_REFERENCE_MODEL = "gemini-3.1-pro-preview"
DEFAULT_CANDIDATES = ["gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"]
JSON_ONLY_INSTRUCTION = (
    "Return exactly one JSON object and no surrounding prose. Use these keys only: "
    "protocol_version, decision_summary, state_gaps, recommended_actions, caution_notes, final_response_markdown."
)
ANOMALY_TERMS = ["routing_state", "planner_payloads", "readiness_confirmed", "enterprise_web_search_status", "missing_minimum_evidence"]
CONTRADICTION_PAIRS = [("wait", "kill"), ("rerun", "leave it alone"), ("cleanup now", "do not clean up yet")]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_model_name(name: str) -> str:
    lowered = name.strip().lower()
    if lowered.startswith("models/"):
        lowered = lowered.split("/", 1)[1]
    for token in ("-preview", "-latest"):
        lowered = lowered.replace(token, "")
    return lowered


def list_models(api_key: str, api_base: str) -> List[Dict[str, Any]]:
    url = f"{api_base}/models?key={urllib.parse.quote(api_key)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8")).get("models", [])


def resolve_requested_models(requested: List[str], available_models: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    exact: Dict[str, Dict[str, Any]] = {}
    normalized: Dict[str, List[Dict[str, Any]]] = {}
    for model in available_models:
        raw_name = model.get("name", "")
        model_id = raw_name.split("/", 1)[1] if raw_name.startswith("models/") else raw_name
        exact[model_id.lower()] = model
        normalized.setdefault(normalize_model_name(model_id), []).append(model)
    resolved: Dict[str, Dict[str, Any]] = {}
    for requested_name in requested:
        candidate = exact.get(requested_name.lower())
        if candidate is None:
            matches = normalized.get(normalize_model_name(requested_name), [])
            if matches:
                candidate = sorted(matches, key=lambda item: item.get("name", ""))[0]
        if candidate is not None:
            resolved[requested_name] = candidate
    return resolved


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def build_case_prompt(case: Dict[str, Any]) -> str:
    conversation_lines = []
    for turn in case.get("turns", []):
        role = str(turn.get("role", "user")).upper()
        text = str(turn.get("text", "")).strip()
        conversation_lines.append(f"{role}:\n{text}")
    sections = [
        "You are simulating the next assistant turn for a governed DCOIR Gemini agent evaluation.",
        JSON_ONLY_INSTRUCTION,
        f"Case ID: {case['id']}",
        f"Case goal: {case.get('goal', '')}",
        "Available evidence constraints:",
        str(case.get("allowed_evidence", "")).strip(),
        "Conversation so far:",
        "\n\n".join(conversation_lines).strip(),
    ]
    if case.get("notes"):
        sections.extend(["Evaluator notes:", str(case["notes"]).strip()])
    return "\n\n".join(section for section in sections if section)


def extract_response_text(payload: Dict[str, Any]) -> str:
    text_parts: List[str] = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                text_parts.append(str(part["text"]))
    return "\n".join(text_parts).strip()


def call_model(api_key: str, api_base: str, resolved_model: Dict[str, Any], prompt: str, temperature: float, max_retries: int, retry_base_seconds: float) -> Dict[str, Any]:
    endpoint = f"{api_base}/{resolved_model.get('name', '')}:generateContent"
    request_body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"},
        }
    ).encode("utf-8")
    attempts: List[Dict[str, Any]] = []
    for attempt_index in range(1, max_retries + 1):
        start = time.monotonic()
        request = urllib.request.Request(endpoint, data=request_body, headers={"Content-Type": "application/json", "X-goog-api-key": api_key}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                payload = json.loads(response.read().decode("utf-8"))
                attempts.append({"attempt": attempt_index, "status_code": response.status, "latency_ms": latency_ms})
                return {"ok": True, "attempts": attempts, "payload": payload, "response_text": extract_response_text(payload), "usage_metadata": payload.get("usageMetadata", {})}
        except urllib.error.HTTPError as exc:
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            error_body = exc.read().decode("utf-8", errors="ignore")
            attempts.append({"attempt": attempt_index, "status_code": exc.code, "latency_ms": latency_ms, "error_body_excerpt": error_body[:1000]})
            if exc.code == 429 and attempt_index < max_retries:
                time.sleep(retry_base_seconds * attempt_index)
                continue
            return {"ok": False, "attempts": attempts, "error": f"http_{exc.code}", "error_body": error_body[:4000]}
        except Exception as exc:
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            attempts.append({"attempt": attempt_index, "latency_ms": latency_ms, "error": str(exc)})
            if attempt_index < max_retries:
                time.sleep(retry_base_seconds * attempt_index)
                continue
            return {"ok": False, "attempts": attempts, "error": str(exc)}
    return {"ok": False, "attempts": attempts, "error": "unknown"}


def parse_model_json(response_text: str) -> Tuple[bool, Dict[str, Any], str | None]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        return False, {}, f"json_decode_error: {exc}"
    required = {"protocol_version", "decision_summary", "state_gaps", "recommended_actions", "caution_notes", "final_response_markdown"}
    missing = sorted(required - set(parsed))
    if missing:
        return False, parsed, f"missing_keys: {', '.join(missing)}"
    return True, parsed, None


def evaluate_case_output(case: Dict[str, Any], parsed_response: Dict[str, Any]) -> Dict[str, Any]:
    final_markdown = str(parsed_response.get("final_response_markdown", ""))
    lowered = final_markdown.lower()
    required_markers = list(case.get("required_markers", []))
    forbidden_markers = list(case.get("forbidden_markers", []))
    any_groups = list(case.get("any_marker_groups", []))
    matched_required = [marker for marker in required_markers if marker.lower() in lowered]
    missing_required = [marker for marker in required_markers if marker.lower() not in lowered]
    matched_forbidden = [marker for marker in forbidden_markers if marker.lower() in lowered]
    group_results = []
    for group in any_groups:
        matched = [marker for marker in group if marker.lower() in lowered]
        group_results.append({"expected_any_of": group, "matched": matched, "passed": bool(matched)})
    anomalies = [term for term in ANOMALY_TERMS if term in lowered]
    contradictions = [f"{left} <-> {right}" for left, right in CONTRADICTION_PAIRS if left in lowered and right in lowered]
    traits: Dict[str, bool] = {}
    for marker in required_markers:
        traits[f"required::{marker}"] = marker.lower() in lowered
    for marker in forbidden_markers:
        traits[f"forbidden::{marker}"] = marker.lower() in lowered
    for index, group in enumerate(any_groups, start=1):
        traits[f"any_group::{index}"] = any(marker.lower() in lowered for marker in group)
    for term in ANOMALY_TERMS:
        traits[f"anomaly::{term}"] = term in lowered
    for pair in contradictions:
        traits[f"contradiction::{pair}"] = True
    total_checks = len(required_markers) + len(any_groups) + max(1, len(forbidden_markers))
    passed_checks = len(matched_required) + sum(1 for group in group_results if group["passed"]) + (len(forbidden_markers) - len(matched_forbidden))
    rubric_score = round((passed_checks / total_checks) * 100, 2) if total_checks else 100.0
    case_pass = rubric_score >= float(case.get("minimum_rubric_score", 75.0)) and not matched_forbidden and not anomalies and not contradictions and all(group["passed"] for group in group_results)
    return {
        "final_response_markdown": final_markdown,
        "matched_required_markers": matched_required,
        "missing_required_markers": missing_required,
        "matched_forbidden_markers": matched_forbidden,
        "group_results": group_results,
        "anomaly_terms": anomalies,
        "contradictions": contradictions,
        "traits": traits,
        "rubric_score": rubric_score,
        "case_pass": case_pass,
    }


def compare_traits(reference_traits: Dict[str, bool], candidate_traits: Dict[str, bool]) -> float:
    keys = sorted(set(reference_traits) | set(candidate_traits))
    if not keys:
        return 100.0
    matches = sum(1 for key in keys if reference_traits.get(key, False) == candidate_traits.get(key, False))
    return round((matches / len(keys)) * 100, 2)


def summarize_model_run(requested_model: str, resolved_model: Dict[str, Any] | None, case_results: List[Dict[str, Any]], profile_hints: Dict[str, Any] | None, minimum_case_score: float, minimum_behavior_score: float, critical_case_ids: List[str]) -> Dict[str, Any]:
    available = resolved_model is not None
    protocol_passes = [case for case in case_results if case.get("protocol_ok")]
    rubric_scores = [case.get("rubric_score", 0.0) for case in protocol_passes]
    closeness_scores = [case.get("closeness_to_reference", 0.0) for case in protocol_passes]
    latencies = [case.get("latency_ms", 0.0) for case in case_results if case.get("latency_ms") is not None]
    retries = [max(0, case.get("attempt_count", 1) - 1) for case in case_results]
    anomaly_count = sum(len(case.get("anomaly_terms", [])) + len(case.get("contradictions", [])) for case in case_results)
    failure_count = sum(1 for case in case_results if not case.get("protocol_ok"))
    failed_cases = [case["case_id"] for case in case_results if not case.get("protocol_ok") or not case.get("case_pass") or case.get("rubric_score", 0.0) < minimum_case_score]
    critical_failures = sorted(set(failed_cases) & set(critical_case_ids))
    hint_score = None
    if profile_hints:
        rpm = float(profile_hints.get("rpm", 0) or 0)
        tpm = float(profile_hints.get("tpm", 0) or 0)
        rpd = float(profile_hints.get("rpd", 0) or 0)
        throughput_score = min(100.0, round((rpm / 25.0) * 40 + min(tpm / 2000000.0, 1.0) * 40 + min(rpd / 250.0, 1.0) * 20, 2))
        cost_modifier = {"low": 10.0, "medium": 0.0, "high": -10.0, "unknown": -5.0}.get(str(profile_hints.get("cost_tier", "unknown")).lower(), -5.0)
        hint_score = max(0.0, min(100.0, throughput_score + cost_modifier))
    observed_operational = 100.0
    if latencies:
        observed_operational -= min(35.0, statistics.median(latencies) / 200.0)
    observed_operational -= min(25.0, statistics.mean(retries) * 10.0 if retries else 0.0)
    observed_operational -= min(25.0, failure_count * 10.0)
    observed_operational = round(max(0.0, observed_operational), 2)
    operational_fit = round(((hint_score if hint_score is not None else observed_operational) + observed_operational) / 2, 2) if available else 0.0
    protocol_score = round((len(protocol_passes) / len(case_results)) * 100, 2) if case_results else 0.0
    behavior_score = round(statistics.mean(rubric_scores), 2) if rubric_scores else 0.0
    closeness_score = round(statistics.mean(closeness_scores), 2) if closeness_scores else 0.0
    anomaly_penalty = min(20.0, anomaly_count * 5.0)
    composite = round(max(0.0, protocol_score * 0.25 + behavior_score * 0.45 + closeness_score * 0.20 + operational_fit * 0.10 - anomaly_penalty), 2) if available else 0.0
    behavior_pass = available and protocol_score == 100.0 and behavior_score >= minimum_behavior_score and not failed_cases and not critical_failures and anomaly_count == 0
    return {
        "requested_model": requested_model,
        "resolved_model_name": resolved_model.get("name") if resolved_model else None,
        "available": available,
        "protocol_score": protocol_score,
        "behavior_score": behavior_score,
        "closeness_score": closeness_score,
        "operational_fit_score": operational_fit,
        "observed_operational_score": observed_operational,
        "profile_hint_score": hint_score,
        "anomaly_count": anomaly_count,
        "composite_score": composite,
        "median_latency_ms": round(statistics.median(latencies), 2) if latencies else None,
        "mean_retry_count": round(statistics.mean(retries), 2) if retries else 0.0,
        "failed_cases": failed_cases,
        "critical_failures": critical_failures,
        "behavior_pass": behavior_pass,
        "recommendation_status": "recommended_for_simulated_production" if behavior_pass else "relative_only_not_behavior_qualified",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-profile-path", default=None)
    parser.add_argument("--api-key-env", default="DCOIR_GEMINI_API")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--reference-model", default=DEFAULT_REFERENCE_MODEL)
    parser.add_argument("--candidate-models", default=",".join(DEFAULT_CANDIDATES))
    parser.add_argument("--repeat-count", type=int, default=1)
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--inter-request-delay-seconds", type=float, default=3.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=5.0)
    parser.add_argument("--minimum-case-score", type=float, default=75.0)
    parser.add_argument("--minimum-behavior-score", type=float, default=80.0)
    parser.add_argument("--critical-case-ids", default="GEM-PHASE1-STATE-001,GEM-PHASE1-CHUNKS-001")
    args = parser.parse_args()
    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        print(f"Missing API key env: {args.api_key_env}", file=sys.stderr)
        return 1
    fixture_path = Path(args.fixtures).resolve()
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)
    fixtures = load_json(fixture_path)
    model_profiles = load_json(Path(args.model_profile_path).resolve()) if args.model_profile_path else {"models": {}}
    requested_models = []
    for name in [args.reference_model, *[part.strip() for part in args.candidate_models.split(",") if part.strip()]]:
        if name not in requested_models:
            requested_models.append(name)
    available_models = list_models(api_key, args.api_base)
    resolved_models = resolve_requested_models(requested_models, available_models)
    cases = list(fixtures.get("cases", []))
    if args.max_cases > 0:
        cases = cases[: args.max_cases]
    critical_case_ids = [part.strip() for part in args.critical_case_ids.split(",") if part.strip()]
    all_case_records: List[Dict[str, Any]] = []
    trait_baselines: Dict[str, Dict[str, bool]] = {}
    for model_name in requested_models:
        resolved_model = resolved_models.get(model_name)
        if resolved_model is None:
            for case in cases:
                all_case_records.append({"requested_model": model_name, "resolved_model_name": None, "case_id": case["id"], "protocol_ok": False, "protocol_error": "model_not_available", "rubric_score": 0.0, "case_pass": False, "closeness_to_reference": 0.0, "attempt_count": 0, "latency_ms": None, "anomaly_terms": [], "contradictions": []})
            continue
        for case in cases:
            for repetition in range(1, args.repeat_count + 1):
                prompt = build_case_prompt(case)
                call = call_model(api_key, args.api_base, resolved_model, prompt, args.temperature, args.max_retries, args.retry_base_seconds)
                protocol_ok = False
                parsed_response: Dict[str, Any] = {}
                protocol_error = None
                evaluation: Dict[str, Any] = {"rubric_score": 0.0, "case_pass": False, "traits": {}, "anomaly_terms": [], "contradictions": [], "matched_required_markers": [], "missing_required_markers": list(case.get("required_markers", [])), "matched_forbidden_markers": [], "group_results": [], "final_response_markdown": ""}
                usage = call.get("usage_metadata", {})
                if call.get("ok"):
                    protocol_ok, parsed_response, protocol_error = parse_model_json(call["response_text"])
                    if protocol_ok:
                        evaluation = evaluate_case_output(case, parsed_response)
                        if model_name == args.reference_model:
                            trait_baselines[case["id"]] = evaluation["traits"]
                if call.get("ok") and not protocol_ok:
                    protocol_error = protocol_error or "protocol_parse_failed"
                if not call.get("ok"):
                    protocol_error = call.get("error", "model_call_failed")
                all_case_records.append({
                    "requested_model": model_name,
                    "resolved_model_name": resolved_model.get("name"),
                    "case_id": case["id"],
                    "case_description": case.get("description"),
                    "repeat_index": repetition,
                    "protocol_ok": protocol_ok,
                    "protocol_error": protocol_error,
                    "decision_summary": parsed_response.get("decision_summary") if parsed_response else None,
                    "recommended_actions": parsed_response.get("recommended_actions") if parsed_response else None,
                    "rubric_score": evaluation["rubric_score"],
                    "case_pass": evaluation["case_pass"],
                    "matched_required_markers": evaluation["matched_required_markers"],
                    "missing_required_markers": evaluation["missing_required_markers"],
                    "matched_forbidden_markers": evaluation["matched_forbidden_markers"],
                    "group_results": evaluation["group_results"],
                    "anomaly_terms": evaluation["anomaly_terms"],
                    "contradictions": evaluation["contradictions"],
                    "traits": evaluation["traits"],
                    "final_response_markdown": evaluation["final_response_markdown"],
                    "attempt_count": len(call.get("attempts", [])),
                    "attempts": call.get("attempts", []),
                    "latency_ms": call.get("attempts", [{}])[-1].get("latency_ms") if call.get("attempts") else None,
                    "usage_metadata": usage,
                    "estimated_prompt_tokens": estimate_tokens(prompt),
                    "error_body": call.get("error_body"),
                })
                time.sleep(args.inter_request_delay_seconds)
    for record in all_case_records:
        baseline = trait_baselines.get(record["case_id"])
        if baseline and record["protocol_ok"]:
            record["closeness_to_reference"] = compare_traits(baseline, record["traits"])
        elif record["requested_model"] == args.reference_model and record["protocol_ok"]:
            record["closeness_to_reference"] = 100.0
        else:
            record["closeness_to_reference"] = 0.0
    model_summaries = [
        summarize_model_run(model_name, resolved_models.get(model_name), [record for record in all_case_records if record["requested_model"] == model_name], model_profiles.get("models", {}).get(model_name), args.minimum_case_score, args.minimum_behavior_score, critical_case_ids)
        for model_name in requested_models
    ]
    rankings = sorted(model_summaries, key=lambda item: (-item["composite_score"], -item["behavior_score"], -item["closeness_score"]))
    qualified = [item for item in rankings if item["behavior_pass"]]
    report = {
        "success": bool(qualified),
        "fixture_path": str(fixture_path),
        "requested_models": requested_models,
        "resolved_models": {name: model.get("name") for name, model in resolved_models.items()},
        "reference_model": args.reference_model,
        "repeat_count": args.repeat_count,
        "case_count": len(cases),
        "available_model_catalog_size": len(available_models),
        "minimum_case_score": args.minimum_case_score,
        "minimum_behavior_score": args.minimum_behavior_score,
        "critical_case_ids": critical_case_ids,
        "best_relative_model": rankings[0]["requested_model"] if rankings else None,
        "recommended_model": qualified[0]["requested_model"] if qualified else None,
        "model_summaries": model_summaries,
        "rankings": rankings,
        "case_results": all_case_records,
    }
    (output_dir / "gemini_model_comparison_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Gemini model comparison summary", "", f"- reference_model: {args.reference_model}", f"- fixture_path: {fixture_path.as_posix()}", f"- repeat_count: {args.repeat_count}", f"- case_count: {len(cases)}", f"- minimum_case_score: {args.minimum_case_score}", f"- minimum_behavior_score: {args.minimum_behavior_score}", f"- best_relative_model: {report['best_relative_model']}", f"- recommended_model: {report['recommended_model'] or 'none'}", "", "## Ranking", ""]
    for rank, summary in enumerate(rankings, start=1):
        lines.append(f"{rank}. `{summary['requested_model']}` -> composite={summary['composite_score']}, behavior={summary['behavior_score']}, closeness={summary['closeness_score']}, operational_fit={summary['operational_fit_score']}, protocol={summary['protocol_score']}, behavior_pass={str(summary['behavior_pass']).lower()}, status={summary['recommendation_status']}")
        if summary.get("failed_cases"):
            lines.append(f"   failed_cases: {', '.join(summary['failed_cases'])}")
    lines.extend(["", "## Availability", ""])
    for name in requested_models:
        resolved = resolved_models.get(name)
        lines.append(f"- `{name}` -> `{resolved.get('name')}`" if resolved else f"- `{name}` -> unavailable")
    (output_dir / "gemini_model_comparison_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
