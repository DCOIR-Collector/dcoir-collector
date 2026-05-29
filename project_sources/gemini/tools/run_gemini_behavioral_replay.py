#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any, Dict, List

from lib.gemini_behavioral_replay_runner import load_fixture_entry, load_fixture_index, load_response_pack, repo_root_from_script
from lib.gemini_behavioral_replay_schema import EXPECTED_RESPONSE_PACK_SCHEMA_VERSION, validate_response_pack_shape
from lib.gemini_behavioral_replay_scoring import score_response_pack

DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.5-flash"
HARDCODED_MODELS = ["gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-pro"]
GOVERNED_PAIR_MODELS = ["gemini-3.5-flash", "gemini-3.1-pro-preview"]
EXCLUDED_MODEL_SUBSTRINGS = ["antigravity", "aqa", "embedding", "imagen", "image-generation", "native-audio", "robotics", "tts", "veo"]


def csv(raw: str | None) -> List[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def safe(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "unknown")).strip("._") or "unknown"


def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def model_exclusion_reason(model: Dict[str, Any]) -> str:
    name = str(model.get("name", "")).split("/")[-1]
    low = name.lower()
    if not low.startswith("gemini-"):
        return "not a Gemini model"
    for token in EXCLUDED_MODEL_SUBSTRINGS:
        if token in low:
            return f"excluded family: {token}"
    methods = model.get("supportedGenerationMethods") or []
    return "" if not methods or "generateContent" in methods else "does not advertise generateContent"


def fetch_catalog(api_key: str, api_base: str) -> Dict[str, Any]:
    if not api_key:
        return {"ok": False, "error": "missing API key", "viable_models": [], "excluded_models": []}
    endpoint = f"{api_base}/models?key={urllib.parse.quote(api_key)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(endpoint, method="GET"), timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_{exc.code}: {exc.read().decode('utf-8', errors='ignore')[:500]}", "viable_models": [], "excluded_models": []}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "viable_models": [], "excluded_models": []}
    viable, excluded = [], []
    for model in payload.get("models", []):
        name = str(model.get("name", "")).split("/")[-1]
        reason = model_exclusion_reason(model)
        if reason:
            excluded.append({"model": name, "reason": reason})
        else:
            viable.append(name)
    return {"ok": True, "error": "", "viable_models": sorted(set(viable)), "excluded_models": excluded}


def resolve_models(args: argparse.Namespace, api_key: str) -> Dict[str, Any]:
    catalog = fetch_catalog(api_key, args.api_base)
    viable = catalog["viable_models"]
    checked = csv(args.models_csv) or ([args.model] if args.model else [])
    custom = csv(args.custom_models_csv)
    rejected: List[Dict[str, str]] = []
    if args.run_all_viable_catalog_models:
        selected, source = viable, "all_viable_catalog_models"
    elif custom:
        selected, source = [], "custom_models_csv"
        for model in custom:
            if catalog["ok"] and model not in viable:
                rejected.append({"model": model, "reason": "not in currently viable catalog model set"})
            else:
                selected.append(model)
    else:
        selected, source = [], "checkbox_models"
        for model in checked:
            if model not in HARDCODED_MODELS:
                rejected.append({"model": model, "reason": "not present in hard-coded checkbox model list"})
            else:
                selected.append(model)
    selected = sorted(dict.fromkeys(selected))
    return {
        "selection_source": source, "catalog_ok": catalog["ok"], "catalog_error": catalog["error"],
        "hardcoded_models": HARDCODED_MODELS, "governed_pair_models": GOVERNED_PAIR_MODELS,
        "selected_models_to_run": selected, "rejected_selected_models": rejected,
        "hardcoded_and_viable": sorted(set(HARDCODED_MODELS).intersection(viable)),
        "viable_missing_from_hardcoded": sorted(set(viable).difference(HARDCODED_MODELS)),
        "hardcoded_not_currently_viable": sorted(set(HARDCODED_MODELS).difference(viable)) if catalog["ok"] else [],
        "excluded_catalog_models": catalog["excluded_models"],
    }


def resolve_fixtures(args: argparse.Namespace, fixtures_root: Path) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    repo_root = repo_root_from_script(Path(__file__))
    entries = [e for e in load_fixture_index(fixtures_root).get("fixtures", []) if e.get("status") == "active"]
    active = [e.get("fixture_id") for e in entries]
    checked = csv(args.fixture_ids_csv) or ([args.fixture_id] if args.fixture_id else [])
    custom = csv(args.custom_fixtures_csv)
    rejected: List[Dict[str, str]] = []
    if args.run_all_active_fixtures or (not checked and not custom):
        selected, source = active, "all_active_fixtures"
    elif custom:
        selected, source = [], "custom_fixtures_csv"
        for fid in custom:
            if fid in active:
                selected.append(fid)
            else:
                rejected.append({"fixture_id": fid, "reason": "not in active fixture index"})
    else:
        selected, source = [], "checkbox_fixtures"
        for fid in checked:
            if fid in active:
                selected.append(fid)
            else:
                rejected.append({"fixture_id": fid, "reason": "not in active fixture index"})
    loaded = [load_fixture_entry(repo_root, e) for e in entries if e.get("fixture_id") in set(selected)]
    return loaded, {"selection_source": source, "active_fixtures": active, "selected_fixtures_to_run": selected, "rejected_selected_fixtures": rejected}


def live_prompt(fixture: Dict[str, Any], turn: Dict[str, Any]) -> str:
    evidence = fixture.get("available_evidence_by_turn", {}).get(turn.get("turn_id"), [])
    return "\n\n".join([
        "You are producing the next operator-facing answer for a governed DCOIR Gemini behavioral replay.",
        "Return only the assistant answer text. Do not include JSON, scoring notes, or hidden reasoning.",
        f"Fixture: {fixture.get('fixture_id')}", f"Scenario: {fixture.get('title')}",
        "Available evidence for this turn:\n" + ("\n".join(f"- {x}" for x in evidence) or "- No additional evidence is available."),
        "Allowed assumptions:\n" + ("\n".join(f"- {x}" for x in turn.get("allowed_assumptions", [])) or "- None."),
        "Disallowed assumptions:\n" + ("\n".join(f"- {x}" for x in turn.get("disallowed_assumptions", [])) or "- None."),
        "Expected behavior tags: " + (", ".join(turn.get("expected_behavior_tags", [])) or "none"),
        "User turn:\n" + str(turn.get("content", "")).strip(),
    ])


def extract_text(payload: Dict[str, Any]) -> str:
    out = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                out.append(str(part["text"]))
    return "\n".join(out).strip()


def call_gemini(api_key: str, args: argparse.Namespace, model: str, prompt: str) -> Dict[str, Any]:
    endpoint = f"{args.api_base}/models/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": args.temperature, "candidateCount": 1}}).encode()
    attempts = []
    for attempt in range(1, args.max_retries + 1):
        start = time.monotonic()
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
                attempts.append({"attempt": attempt, "status_code": response.status, "latency_ms": round((time.monotonic() - start) * 1000, 2)})
                return {"ok": True, "attempts": attempts, "payload": payload, "response_text": extract_text(payload)}
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="ignore")
            attempts.append({"attempt": attempt, "status_code": exc.code, "latency_ms": round((time.monotonic() - start) * 1000, 2), "error_body_excerpt": body_text[:1000]})
            if exc.code == 429 and attempt < args.max_retries:
                time.sleep(args.retry_base_seconds * attempt); continue
            return {"ok": False, "attempts": attempts, "error": f"http_{exc.code}", "error_body": body_text[:4000]}
        except Exception as exc:
            attempts.append({"attempt": attempt, "latency_ms": round((time.monotonic() - start) * 1000, 2), "error": str(exc)})
            if attempt < args.max_retries:
                time.sleep(args.retry_base_seconds * attempt); continue
            return {"ok": False, "attempts": attempts, "error": str(exc)}
    return {"ok": False, "attempts": attempts, "error": "unknown"}


def make_pack(fixture: Dict[str, Any], args: argparse.Namespace, model: str, mode: str, api_key: str, reason: str) -> Dict[str, Any]:
    turns, calls = [], []
    for turn in fixture.get("turns", []):
        if mode == "live":
            call = call_gemini(api_key, args, model, live_prompt(fixture, turn))
            response = call.get("response_text") if call.get("ok") else f"LIVE_REPLAY_CALL_FAILED: {call.get('error', 'unknown')}"
            calls.append({"turn_id": turn.get("turn_id"), "ok": call.get("ok"), "attempts": call.get("attempts", []), "error": call.get("error")})
        else:
            response = f"Live Gemini replay evidence was not produced because {reason}. Rerun with live API access and read back the generated artifacts."
        turns.append({"turn_id": turn.get("turn_id"), "assistant_response": response})
    return {
        "schema_version": EXPECTED_RESPONSE_PACK_SCHEMA_VERSION,
        "fixture_id": fixture.get("fixture_id"),
        "mode": "live_gemini" if mode == "live" else "fallback_emulation",
        "model_name": model,
        "turns": turns,
        "metadata": {"live_execution": mode == "live", "fallback_reason": reason if mode != "live" else "", "turn_calls": calls},
    }


def score_pack(pack: Dict[str, Any], fixture: Dict[str, Any]) -> tuple[Dict[str, Any] | None, List[Dict[str, str]]]:
    messages = [{"level": m.level, "message": m.message} for m in validate_response_pack_shape(pack, fixture)]
    return (None, messages) if any(m["level"] == "error" for m in messages) else (score_response_pack(fixture, pack), messages)


def row_counts(result: Dict[str, Any]) -> tuple[int, int, int]:
    calls = result.get("metadata", {}).get("turn_calls", [])
    ok = sum(1 for call in calls if call.get("ok"))
    return len(calls), ok, len(calls) - ok


def matrix_rows(results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not results:
        return [{"model": metadata.get("model_name", ""), "fixture_id": "", "mode": metadata.get("replay_mode", "unknown"), "api_ok": "0/0", "turns": "0/0", "required_ratio": 0, "forbidden_hits": 0, "anomalies": 0, "validation_errors": len([m for m in metadata.get("validation_messages", []) if m.get("level") == "error"]), "scorer": "not_scored", "workflow": metadata.get("workflow_verdict", "success"), "meaning": "Diagnostic report produced."}]
    rows = []
    for result in results:
        count, ok, _ = row_counts(result)
        rows.append({"model": result.get("model_name"), "fixture_id": result.get("fixture_id"), "mode": result.get("mode"), "api_ok": f"{ok}/{count}", "turns": f"{result.get('turn_success_count')}/{result.get('turn_count')}", "required_ratio": result.get("overall_required_marker_ratio"), "forbidden_hits": len(result.get("forbidden_marker_hits", [])), "anomalies": result.get("anomaly_count"), "validation_errors": 0, "scorer": "pass" if result.get("success") else "fail", "workflow": metadata.get("workflow_verdict", "success"), "meaning": "Model/scorer verdict is shown here; workflow success means artifacts were produced."})
    return rows


def write_reports(output_dir: Path, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
    rows = matrix_rows(results, metadata)
    summary = {"workflow_success": metadata.get("workflow_verdict", "success") == "success", "scorer_success": bool(results) and all(r.get("success") for r in results), "result_count": len(results), "matrix": rows}
    payload = {"summary": summary, "metadata": metadata, "results": results}
    (output_dir / "gemini_behavioral_replay_run_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Gemini Behavioral Replay Report", "", "## Summary", "", f"- workflow_verdict: `{metadata.get('workflow_verdict', 'success')}`", f"- aggregate_scorer_success: `{str(summary['scorer_success']).lower()}`", f"- result_count: `{len(results)}`", f"- live_execution: `{metadata.get('live_execution')}`", f"- fallback_reason: `{metadata.get('fallback_reason', '')}`", "", "## Evidence Buckets", "", f"- checked_evidence: `{metadata.get('checked_evidence', [])}`", f"- unchecked_evidence: `{metadata.get('unchecked_evidence', [])}`", "", "## Viable Model Check", ""]
    mr = metadata["model_resolution"]
    for key in ("selection_source", "catalog_ok", "catalog_error", "hardcoded_models", "governed_pair_models", "selected_models_to_run", "hardcoded_and_viable", "viable_missing_from_hardcoded", "hardcoded_not_currently_viable"):
        lines.append(f"- {key}: `{mr.get(key)}`")
    lines += ["", "## Fixture Selection", ""]
    fr = metadata["fixture_resolution"]
    for key in ("selection_source", "active_fixtures", "selected_fixtures_to_run"):
        lines.append(f"- {key}: `{fr.get(key)}`")
    lines += ["", "## Pass/Fail Matrix", "", "| Model | Fixture | Mode | API OK | Turns | Required Ratio | Forbidden Hits | Anomalies | Scorer | Workflow | Meaning |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['model']} | {row['fixture_id']} | {row['mode']} | {row['api_ok']} | {row['turns']} | {row['required_ratio']} | {row['forbidden_hits']} | {row['anomalies']} | {row['scorer']} | {row['workflow']} | {row['meaning']} |")
    if metadata.get("validation_messages"):
        lines += ["", "## Validation Messages", ""] + [f"- `{m.get('level')}`: {m.get('message')}" for m in metadata["validation_messages"]]
    markdown = "\n".join(lines).rstrip() + "\n"
    (output_dir / "gemini_behavioral_replay_run_report.md").write_text(markdown, encoding="utf-8")
    (output_dir / "chatgpt_workflow_report_section.md").write_text("## Source Workflow Custom Report\n\n" + markdown, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures-root", required=True); p.add_argument("--output-dir", required=True)
    p.add_argument("--fixture-id"); p.add_argument("--fixture-ids-csv", default=""); p.add_argument("--custom-fixtures-csv", default=""); p.add_argument("--run-all-active-fixtures", action="store_true")
    p.add_argument("--mode", choices=["deterministic", "live", "fallback"], default="deterministic"); p.add_argument("--response-pack")
    p.add_argument("--api-key-env", default="DCOIR_GEMINI_API"); p.add_argument("--api-base", default=DEFAULT_API_BASE)
    p.add_argument("--model", default=DEFAULT_MODEL); p.add_argument("--models-csv", default=""); p.add_argument("--custom-models-csv", default=""); p.add_argument("--run-all-viable-catalog-models", action="store_true"); p.add_argument("--selection-report-only", action="store_true")
    p.add_argument("--temperature", type=float, default=0.1); p.add_argument("--max-retries", type=int, default=4); p.add_argument("--retry-base-seconds", type=float, default=5.0); p.add_argument("--allow-fallback", action="store_true")
    args = p.parse_args()
    output_dir = Path(args.output_dir).resolve(); mkdir(output_dir)
    fixtures_root = Path(args.fixtures_root).resolve(); api_key = os.environ.get(args.api_key_env, "").strip()
    models = resolve_models(args, api_key); fixtures, fixture_resolution = resolve_fixtures(args, fixtures_root)
    metadata: Dict[str, Any] = {"workflow_verdict": "success", "replay_mode": args.mode, "model_name": ",".join(models["selected_models_to_run"]), "fixture_count": len(fixtures), "model_resolution": models, "fixture_resolution": fixture_resolution, "validation_messages": [], "checked_evidence": ["fixture index", "fixture definitions"], "unchecked_evidence": []}
    if models["rejected_selected_models"] or fixture_resolution["rejected_selected_fixtures"]:
        metadata["validation_messages"].append({"level": "error", "message": "One or more selected models or fixtures were rejected."})
    if not models["selected_models_to_run"]:
        metadata["validation_messages"].append({"level": "error", "message": "No models selected for replay."})
    if not fixtures:
        metadata["validation_messages"].append({"level": "error", "message": "No active fixtures selected for replay."})
    if args.selection_report_only:
        if any(message.get("level") == "error" for message in metadata.get("validation_messages", [])):
            metadata["workflow_verdict"] = "failure"
            write_reports(output_dir, [], metadata); return 1
        write_reports(output_dir, [], metadata); return 0
    mode, reason = args.mode, ""
    if args.mode == "fallback":
        reason = "fallback mode requested"
        metadata["unchecked_evidence"].append("live Gemini API response")
    if args.mode == "live" and not api_key:
        reason = f"missing API key env {args.api_key_env}"
        if args.allow_fallback:
            mode = "fallback"; metadata["unchecked_evidence"].append("live Gemini API response")
        else:
            metadata["workflow_verdict"] = "failure"; metadata["validation_messages"].append({"level": "error", "message": reason}); metadata["unchecked_evidence"].append("live Gemini API response"); write_reports(output_dir, [], metadata); return 1
    results: List[Dict[str, Any]] = []; calls: List[Dict[str, Any]] = []
    deterministic = load_response_pack(Path(args.response_pack).resolve()) if args.response_pack else None
    for row in fixtures:
        fixture = row["fixture"]
        loop_models = [args.model] if mode == "deterministic" else models["selected_models_to_run"]
        for model in loop_models:
            if mode == "deterministic":
                if deterministic is None:
                    metadata["validation_messages"].append({"level": "error", "message": "--response-pack is required in deterministic mode."}); continue
                if deterministic.get("fixture_id") and deterministic.get("fixture_id") != fixture.get("fixture_id"):
                    continue
                pack = deterministic
            else:
                pack = make_pack(fixture, args, model, mode, api_key, reason or "fallback mode requested")
                calls.extend(pack.get("metadata", {}).get("turn_calls", []))
                suffix = "live" if mode == "live" else "fallback"
                (output_dir / f"{safe(fixture.get('fixture_id'))}_{safe(model)}_{suffix}_response_pack.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
            result, messages = score_pack(pack, fixture); metadata["validation_messages"].extend(messages)
            if "response-pack schema" not in metadata["checked_evidence"]:
                metadata["checked_evidence"].append("response-pack schema")
            if result is not None:
                if "deterministic scorer" not in metadata["checked_evidence"]:
                    metadata["checked_evidence"].append("deterministic scorer")
                results.append(result)
    ok = sum(1 for call in calls if call.get("ok"))
    live_complete = mode == "live" and bool(calls) and ok == len(calls)
    if mode == "live":
        target_bucket = metadata["checked_evidence"] if live_complete else metadata["unchecked_evidence"]
        if "live Gemini API response" not in target_bucket:
            target_bucket.append("live Gemini API response")
    metadata.update({"replay_mode": mode, "live_execution": mode == "live" and bool(calls), "fallback_reason": reason, "api_call_count": len(calls), "api_call_success_count": ok, "api_call_failure_count": len(calls)-ok, "live_response_complete": live_complete, "prompt_profile": "behavioral_replay_operator_turn", "production_prompt_equivalent": "partial_fixture_replay_prompt", "live_environment_fidelity_gap": "Manual live replay uses fixture prompts and does not prove full production runtime parity."})
    has_errors = any(message.get("level") == "error" for message in metadata.get("validation_messages", []))
    scorer_failed = bool(results) and not all(result.get("success") for result in results)
    deterministic_failed = mode == "deterministic" and (has_errors or scorer_failed or not results)
    live_failed = mode == "live" and bool(calls) and not live_complete
    workflow_failed = has_errors or not results or live_failed
    if deterministic_failed or workflow_failed:
        metadata["workflow_verdict"] = "failure"
    write_reports(output_dir, results, metadata)
    if deterministic_failed or workflow_failed:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
