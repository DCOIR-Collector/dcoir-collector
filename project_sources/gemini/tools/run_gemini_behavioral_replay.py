#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from lib.gemini_behavioral_replay_reporting import write_reports
from lib.gemini_behavioral_replay_runner import load_fixtures, load_response_pack
from lib.gemini_behavioral_replay_schema import EXPECTED_RESPONSE_PACK_SCHEMA_VERSION, validate_response_pack_shape
from lib.gemini_behavioral_replay_scoring import score_response_pack


DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.5-flash"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_live_prompt(fixture: Dict[str, Any], turn: Dict[str, Any]) -> str:
    evidence = fixture.get("available_evidence_by_turn", {}).get(turn.get("turn_id"), [])
    sections = [
        "You are producing the next operator-facing answer for a governed DCOIR Gemini behavioral replay.",
        "Return only the assistant answer text. Do not include JSON, scoring notes, or hidden reasoning.",
        f"Fixture: {fixture.get('fixture_id')}",
        f"Scenario: {fixture.get('title')}",
        "Available evidence for this turn:",
        "\n".join(f"- {item}" for item in evidence) or "- No additional evidence is available.",
        "Allowed assumptions:",
        "\n".join(f"- {item}" for item in turn.get("allowed_assumptions", [])) or "- None.",
        "Disallowed assumptions:",
        "\n".join(f"- {item}" for item in turn.get("disallowed_assumptions", [])) or "- None.",
        "Expected behavior tags:",
        ", ".join(turn.get("expected_behavior_tags", [])) or "none",
        "User turn:",
        str(turn.get("content", "")).strip(),
    ]
    return "\n\n".join(sections)


def extract_response_text(payload: Dict[str, Any]) -> str:
    text_parts: List[str] = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if "text" in part:
                text_parts.append(str(part["text"]))
    return "\n".join(text_parts).strip()


def call_gemini(
    api_key: str,
    api_base: str,
    model: str,
    prompt: str,
    temperature: float,
    max_retries: int,
    retry_base_seconds: float,
) -> Dict[str, Any]:
    model_name = model if model.startswith("models/") else f"models/{model}"
    endpoint = f"{api_base}/{model_name}:generateContent?key={urllib.parse.quote(api_key)}"
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "candidateCount": 1},
        }
    ).encode("utf-8")
    attempts: List[Dict[str, Any]] = []
    for attempt_index in range(1, max_retries + 1):
        start = time.monotonic()
        request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                payload = json.loads(response.read().decode("utf-8"))
                attempts.append({"attempt": attempt_index, "status_code": response.status, "latency_ms": latency_ms})
                return {"ok": True, "attempts": attempts, "payload": payload, "response_text": extract_response_text(payload)}
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


def make_fallback_response_pack(fixture: Dict[str, Any], model_name: str, reason: str) -> Dict[str, Any]:
    return {
        "schema_version": EXPECTED_RESPONSE_PACK_SCHEMA_VERSION,
        "fixture_id": fixture.get("fixture_id"),
        "mode": "fallback_emulation",
        "model_name": model_name,
        "turns": [
            {
                "turn_id": turn.get("turn_id"),
                "assistant_response": (
                    "Live Gemini replay was not verified. The replay is in fallback mode because "
                    f"{reason}. The smallest safe next step is to rerun the manual live replay lane "
                    "with DCOIR_GEMINI_API available and read back the generated response pack."
                ),
            }
            for turn in fixture.get("turns", [])
        ],
        "metadata": {"fallback_reason": reason, "live_execution": False},
    }


def make_live_response_pack(
    fixture: Dict[str, Any],
    api_key: str,
    api_base: str,
    model_name: str,
    temperature: float,
    max_retries: int,
    retry_base_seconds: float,
) -> Dict[str, Any]:
    turns = []
    metadata_turns = []
    for turn in fixture.get("turns", []):
        prompt = build_live_prompt(fixture, turn)
        call = call_gemini(api_key, api_base, model_name, prompt, temperature, max_retries, retry_base_seconds)
        response_text = call.get("response_text", "") if call.get("ok") else f"LIVE_REPLAY_CALL_FAILED: {call.get('error', 'unknown')}"
        turns.append({"turn_id": turn.get("turn_id"), "assistant_response": response_text})
        metadata_turns.append({"turn_id": turn.get("turn_id"), "ok": call.get("ok"), "attempts": call.get("attempts", []), "error": call.get("error")})
    return {
        "schema_version": EXPECTED_RESPONSE_PACK_SCHEMA_VERSION,
        "fixture_id": fixture.get("fixture_id"),
        "mode": "live_gemini",
        "model_name": model_name,
        "turns": turns,
        "metadata": {"live_execution": True, "turn_calls": metadata_turns},
    }


def score_pack_for_fixture(response_pack: Dict[str, Any], fixture: Dict[str, Any]) -> tuple[Dict[str, Any] | None, List[Dict[str, str]]]:
    messages = validate_response_pack_shape(response_pack, fixture)
    validation_messages = [{"level": message.level, "message": message.message} for message in messages]
    if any(message.level == "error" for message in messages):
        return None, validation_messages
    return score_response_pack(fixture, response_pack), validation_messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fixture-id")
    parser.add_argument("--mode", choices=["deterministic", "live", "fallback"], default="deterministic")
    parser.add_argument("--response-pack")
    parser.add_argument("--api-key-env", default="DCOIR_GEMINI_API")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=5.0)
    parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()

    fixtures_root = Path(args.fixtures_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)
    fixtures = load_fixtures(fixtures_root, Path(__file__), args.fixture_id)
    if not fixtures:
        raise SystemExit(f"No fixtures matched fixture_id={args.fixture_id!r}")

    results: List[Dict[str, Any]] = []
    validation_messages: List[Dict[str, str]] = []
    generated_pack_paths: List[str] = []
    fallback_reason = ""
    checked_evidence = ["fixture index", "fixture definitions", "response-pack schema", "deterministic scorer"]
    unchecked_evidence: List[str] = []

    deterministic_pack = load_response_pack(Path(args.response_pack).resolve()) if args.response_pack else None
    api_key = os.environ.get(args.api_key_env, "").strip()
    effective_mode = args.mode
    if args.mode == "live" and not api_key:
        fallback_reason = f"missing API key env {args.api_key_env}"
        if not args.allow_fallback:
            print(f"Missing API key env: {args.api_key_env}", file=sys.stderr)
            return 1
        effective_mode = "fallback"

    for row in fixtures:
        fixture = row["fixture"]
        if effective_mode == "deterministic":
            if deterministic_pack is None:
                raise SystemExit("--response-pack is required in deterministic mode")
            if deterministic_pack.get("fixture_id") and deterministic_pack.get("fixture_id") != fixture.get("fixture_id"):
                continue
            response_pack = deterministic_pack
        elif effective_mode == "live":
            checked_evidence.append("live Gemini API response")
            response_pack = make_live_response_pack(fixture, api_key, args.api_base, args.model, args.temperature, args.max_retries, args.retry_base_seconds)
            pack_path = output_dir / f"{fixture.get('fixture_id')}_live_response_pack.json"
            pack_path.write_text(json.dumps(response_pack, indent=2), encoding="utf-8")
            generated_pack_paths.append(str(pack_path))
        else:
            fallback_reason = fallback_reason or "fallback mode requested"
            unchecked_evidence.append("live Gemini API response")
            response_pack = make_fallback_response_pack(fixture, args.model, fallback_reason)
            pack_path = output_dir / f"{fixture.get('fixture_id')}_fallback_response_pack.json"
            pack_path.write_text(json.dumps(response_pack, indent=2), encoding="utf-8")
            generated_pack_paths.append(str(pack_path))

        result, messages = score_pack_for_fixture(response_pack, fixture)
        validation_messages.extend(messages)
        if result is not None:
            results.append(result)

    if not results and not validation_messages:
        raise SystemExit("No response packs matched selected fixtures.")

    metadata = {
        "replay_mode": effective_mode,
        "model_name": args.model,
        "live_execution": effective_mode == "live",
        "fallback_reason": fallback_reason,
        "fixture_count": len(results),
        "checked_evidence": checked_evidence,
        "unchecked_evidence": unchecked_evidence,
        "live_environment_fidelity_gap": "none" if effective_mode == "live" else "Live Gemini API behavior was not measured in this run.",
        "generated_response_packs": generated_pack_paths,
        "validation_messages": validation_messages,
    }
    report_paths = write_reports(output_dir, "gemini_behavioral_replay_run_report", results, metadata)
    summary = {
        "success": bool(results) and all(result["success"] for result in results) and not any(message["level"] == "error" for message in validation_messages),
        "result_count": len(results),
        "metadata": metadata,
        "report_paths": report_paths,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    if effective_mode == "fallback":
        return 0
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
