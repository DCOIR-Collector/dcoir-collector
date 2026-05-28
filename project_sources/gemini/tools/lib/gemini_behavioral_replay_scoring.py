from __future__ import annotations

import re
from typing import Any, Dict, List


UNSUPPORTED_CERTAINTY_TERMS = [
    "definitely",
    "guarantee",
    "guaranteed",
    "certainly",
    "confirmed",
]

INVENTED_TOOL_TERMS = [
    "invoke-dcoir",
    "enterprise_web_search_status",
    "planner_payloads",
    "routing_state",
]

CONTRADICTION_PAIRS = [
    ("wait", "kill"),
    ("rerun", "leave it alone"),
    ("cleanup now", "do not clean up yet"),
]

NEGATION_PATTERN = re.compile(
    r"(?:do not|don't|dont|never|avoid|must not|should not|cannot|can't|can not)\s+$"
)

QUOTE_CHARS = {'"', "'", '`'}


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def score_marker_presence(response_text: str, markers: List[str]) -> Dict[str, Any]:
    lowered = normalize_text(response_text)
    matched = [marker for marker in markers if normalize_text(marker) in lowered]
    missing = [marker for marker in markers if normalize_text(marker) not in lowered]
    ratio = 1.0 if not markers else round(len(matched) / len(markers), 4)
    return {
        "matched": matched,
        "missing": missing,
        "ratio": ratio,
    }


def _occurrence_is_quoted(text: str, start: int, end: int) -> bool:
    if start <= 0 or end >= len(text):
        return False
    before = text[start - 1]
    after = text[end]
    return before in QUOTE_CHARS and after == before


def _occurrence_is_negated(text: str, start: int) -> bool:
    context = text[max(0, start - 32):start]
    return bool(NEGATION_PATTERN.search(context))


def _marker_has_forbidden_hit(text: str, marker: str) -> bool:
    pattern = re.escape(normalize_text(marker))
    for match in re.finditer(pattern, text):
        if _occurrence_is_quoted(text, match.start(), match.end()):
            continue
        if _occurrence_is_negated(text, match.start()):
            continue
        return True
    return False


def score_forbidden_markers(response_text: str, markers: List[str]) -> Dict[str, Any]:
    lowered = normalize_text(response_text)
    hits = [marker for marker in markers if _marker_has_forbidden_hit(lowered, marker)]
    return {
        "hits": hits,
        "count": len(hits),
    }


def detect_anomalies(response_text: str, requested_checks: List[str]) -> List[Dict[str, str]]:
    lowered = normalize_text(response_text)
    anomalies: List[Dict[str, str]] = []

    if "unsupported_certainty_claims" in requested_checks:
        hits = [term for term in UNSUPPORTED_CERTAINTY_TERMS if term in lowered]
        for hit in hits:
            anomalies.append({"type": "unsupported_certainty_claims", "detail": hit})

    if "invented_tool_or_workflow" in requested_checks:
        hits = [term for term in INVENTED_TOOL_TERMS if term in lowered]
        for hit in hits:
            anomalies.append({"type": "invented_tool_or_workflow", "detail": hit})

    if "contradictory_next_steps" in requested_checks:
        for first, second in CONTRADICTION_PAIRS:
            if first in lowered and second in lowered:
                anomalies.append(
                    {
                        "type": "contradictory_next_steps",
                        "detail": f"{first} + {second}",
                    }
                )

    if "missing_state_gap_language" in requested_checks:
        if (
            "not verified" not in lowered
            and "state gap" not in lowered
            and "cannot confirm" not in lowered
            and "without readback" not in lowered
        ):
            anomalies.append(
                {
                    "type": "missing_state_gap_language",
                    "detail": "No bounded state-gap phrasing found.",
                }
            )

    if "output_shape_drift" in requested_checks:
        if len(response_text.strip().split()) < 20:
            anomalies.append(
                {
                    "type": "output_shape_drift",
                    "detail": "Response is unusually short for an operator-guidance turn.",
                }
            )

    return anomalies


def score_turn(
    fixture: Dict[str, Any],
    turn: Dict[str, Any],
    response_turn: Dict[str, Any],
) -> Dict[str, Any]:
    response_text = str(response_turn.get("assistant_response", ""))
    turn_required_markers = turn.get("required_markers", fixture.get("required_markers", []))
    turn_forbidden_markers = turn.get("forbidden_markers", fixture.get("forbidden_markers", []))
    turn_anomaly_checks = turn.get("anomaly_checks", fixture.get("anomaly_checks", []))
    required = score_marker_presence(response_text, turn_required_markers)
    forbidden = score_forbidden_markers(response_text, turn_forbidden_markers)
    anomalies = detect_anomalies(response_text, turn_anomaly_checks)
    success = forbidden["count"] == 0 and required["ratio"] >= fixture.get("pass_thresholds", {}).get(
        "minimum_required_marker_ratio",
        1.0,
    ) and len(anomalies) <= fixture.get("pass_thresholds", {}).get("maximum_anomaly_count", 0)
    return {
        "turn_id": turn.get("turn_id"),
        "response_length": len(response_text),
        "required_markers": required,
        "forbidden_markers": forbidden,
        "anomalies": anomalies,
        "success": success,
    }


def score_response_pack(fixture: Dict[str, Any], response_pack: Dict[str, Any]) -> Dict[str, Any]:
    fixture_turns = fixture.get("turns", [])
    response_turns = {turn.get("turn_id"): turn for turn in response_pack.get("turns", [])}
    per_turn = []
    missing_turns = []
    for turn in fixture_turns:
        turn_id = turn.get("turn_id")
        response_turn = response_turns.get(turn_id)
        if response_turn is None:
            missing_turns.append(turn_id)
            per_turn.append(
                {
                    "turn_id": turn_id,
                    "response_length": 0,
                    "required_markers": {"matched": [], "missing": turn.get("required_markers", fixture.get("required_markers", [])), "ratio": 0.0},
                    "forbidden_markers": {"hits": [], "count": 0},
                    "anomalies": [{"type": "missing_turn", "detail": "No response supplied for turn."}],
                    "success": False,
                }
            )
            continue
        per_turn.append(score_turn(fixture, turn, response_turn))

    turn_successes = sum(1 for row in per_turn if row["success"])
    all_anomalies = [anomaly for row in per_turn for anomaly in row["anomalies"]]
    forbidden_hits = [hit for row in per_turn for hit in row["forbidden_markers"]["hits"]]
    overall_required_ratio = round(
        sum(row["required_markers"]["ratio"] for row in per_turn) / max(len(per_turn), 1),
        4,
    )
    success = (
        not missing_turns
        and len(forbidden_hits) <= fixture.get("pass_thresholds", {}).get("maximum_forbidden_marker_hits", 0)
        and len(all_anomalies) <= fixture.get("pass_thresholds", {}).get("maximum_anomaly_count", 0)
        and overall_required_ratio >= fixture.get("pass_thresholds", {}).get("minimum_required_marker_ratio", 1.0)
    )

    return {
        "fixture_id": fixture.get("fixture_id"),
        "response_pack_schema_version": response_pack.get("schema_version"),
        "mode": response_pack.get("mode"),
        "model_name": response_pack.get("model_name"),
        "success": success,
        "turn_count": len(fixture_turns),
        "turn_success_count": turn_successes,
        "missing_turns": missing_turns,
        "overall_required_marker_ratio": overall_required_ratio,
        "forbidden_marker_hits": forbidden_hits,
        "anomaly_count": len(all_anomalies),
        "per_turn": per_turn,
        "metadata": response_pack.get("metadata", {}),
    }
