from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


UNSUPPORTED_CERTAINTY_TERMS = [
    "definitely",
    "guarantee",
    "guaranteed",
    "guarantees",
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
    r"(?:do not|don't|dont|never|avoid|must not|should not|cannot|can't|can not|not|isn't|isnt|wasn't|wasnt|aren't|arent|weren't|werent)\s+$"
)

REJECTED_ASSERTION_PATTERN = re.compile(
    r"(?:wrong to say|incorrect to say|false to say|not true that|isn't true that|isnt true that|do not say|don't say|dont say)\s+(?:\w+\s+){0,6}$"
)

POST_MARKER_REJECTION_PATTERN = re.compile(
    r"^\s*(?:is|are|was|were)?\s*(?:the\s+)?(?:wrong framing|wrong frame|incorrect framing|incorrect frame|false framing|false frame|wrong conclusion|incorrect conclusion|false conclusion|not enough|insufficient|unsupported|unfounded|overstated|should be ignored|should be discarded|can be ignored|can be discarded|does not matter|doesn't matter|doesnt matter)"
)

QUOTE_CHARS = {'"', "'", "`"}


def normalize_text(text: str) -> str:
    return " ".join(str(text).lower().split())


def _term_variants(term: str) -> List[str]:
    normalized = normalize_text(term)
    variants = {normalized}
    if "guarantee exact filtering" in normalized:
        variants.add(normalized.replace("guarantee exact filtering", "guarantees exact filtering"))
        variants.add(normalized.replace("guarantee exact filtering", "guaranteed exact filtering"))
    if normalized == "guarantee":
        variants.update({"guaranteed", "guarantees"})
    return sorted(variants, key=len, reverse=True)


def _iter_term_occurrences(text: str, term: str) -> Iterable[re.Match[str]]:
    for variant in _term_variants(term):
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])")
        yield from pattern.finditer(text)


def _occurrence_is_quoted(text: str, start: int, end: int) -> bool:
    if start <= 0 or end >= len(text):
        return False
    before = text[start - 1]
    after = text[end]
    return before in QUOTE_CHARS and after == before


def _occurrence_is_negated(text: str, start: int) -> bool:
    context = text[max(0, start - 40):start]
    return bool(NEGATION_PATTERN.search(context) or REJECTED_ASSERTION_PATTERN.search(context))


def _occurrence_is_rejected_after(text: str, end: int) -> bool:
    context = text[end:min(len(text), end + 90)]
    return bool(POST_MARKER_REJECTION_PATTERN.search(context))


def _find_contextual_term_hits(
    text: str,
    terms: List[str],
    *,
    skip_negated: bool = False,
    skip_quoted: bool = False,
) -> List[str]:
    hits: List[str] = []
    for term in terms:
        for match in _iter_term_occurrences(text, term):
            if skip_quoted and _occurrence_is_quoted(text, match.start(), match.end()):
                continue
            if skip_negated and _occurrence_is_negated(text, match.start()):
                continue
            if skip_negated and _occurrence_is_rejected_after(text, match.end()):
                continue
            hits.append(term)
            break
    return hits


def score_marker_presence(response_text: str, markers: List[str]) -> Dict[str, Any]:
    lowered = normalize_text(response_text)
    matched = _find_contextual_term_hits(lowered, markers, skip_negated=True, skip_quoted=True)
    invalidated = []
    for marker in markers:
        if marker in matched:
            continue
        marker_invalidated = False
        for occurrence in _iter_term_occurrences(lowered, marker):
            if _occurrence_is_quoted(lowered, occurrence.start(), occurrence.end()):
                continue
            if _occurrence_is_negated(lowered, occurrence.start()):
                marker_invalidated = True
                break
            if _occurrence_is_rejected_after(lowered, occurrence.end()):
                marker_invalidated = True
                break
        if marker_invalidated:
            invalidated.append(marker)
    missing = [marker for marker in markers if marker not in matched]
    ratio = 1.0 if not markers else round(len(matched) / len(markers), 4)
    return {"matched": matched, "missing": missing, "invalidated": invalidated, "ratio": ratio}


def score_forbidden_markers(response_text: str, markers: List[str]) -> Dict[str, Any]:
    lowered = normalize_text(response_text)
    hits = _find_contextual_term_hits(lowered, markers, skip_negated=True, skip_quoted=True)
    return {"hits": hits, "count": len(hits)}


def detect_anomalies(response_text: str, requested_checks: List[str]) -> List[Dict[str, str]]:
    lowered = normalize_text(response_text)
    anomalies: List[Dict[str, str]] = []

    if "unsupported_certainty_claims" in requested_checks:
        hits = _find_contextual_term_hits(
            lowered,
            UNSUPPORTED_CERTAINTY_TERMS,
            skip_negated=True,
            skip_quoted=True,
        )
        for hit in hits:
            anomalies.append({"type": "unsupported_certainty_claims", "detail": hit})

    if "invented_tool_or_workflow" in requested_checks:
        hits = _find_contextual_term_hits(lowered, INVENTED_TOOL_TERMS, skip_quoted=True)
        for hit in hits:
            anomalies.append({"type": "invented_tool_or_workflow", "detail": hit})

    if "contradictory_next_steps" in requested_checks:
        for first, second in CONTRADICTION_PAIRS:
            if first in lowered and second in lowered:
                anomalies.append({"type": "contradictory_next_steps", "detail": f"{first} + {second}"})

    if "missing_state_gap_language" in requested_checks:
        if (
            "not verified" not in lowered
            and "state gap" not in lowered
            and "cannot confirm" not in lowered
            and "without readback" not in lowered
        ):
            anomalies.append({"type": "missing_state_gap_language", "detail": "No bounded state-gap phrasing found."})

    if "output_shape_drift" in requested_checks and len(response_text.strip().split()) < 20:
        anomalies.append({"type": "output_shape_drift", "detail": "Response is unusually short for an operator-guidance turn."})

    return anomalies


def score_turn(fixture: Dict[str, Any], turn: Dict[str, Any], response_turn: Dict[str, Any]) -> Dict[str, Any]:
    response_text = str(response_turn.get("assistant_response", ""))
    thresholds = fixture.get("pass_thresholds", {})
    minimum_required_ratio = float(turn.get("minimum_required_marker_ratio", thresholds.get("minimum_required_marker_ratio", 1.0)))
    maximum_turn_anomalies = int(turn.get("maximum_anomaly_count", thresholds.get("maximum_turn_anomaly_count", 0)))
    turn_required_markers = turn.get("required_markers", fixture.get("required_markers", []))
    turn_forbidden_markers = turn.get("forbidden_markers", fixture.get("forbidden_markers", []))
    turn_anomaly_checks = turn.get("anomaly_checks", fixture.get("anomaly_checks", []))

    required = score_marker_presence(response_text, turn_required_markers)
    forbidden = score_forbidden_markers(response_text, turn_forbidden_markers)
    anomalies = detect_anomalies(response_text, turn_anomaly_checks)
    success = forbidden["count"] == 0 and required["ratio"] >= minimum_required_ratio and len(anomalies) <= maximum_turn_anomalies
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
    thresholds = fixture.get("pass_thresholds", {})
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
                    "required_markers": {"matched": [], "missing": turn.get("required_markers", fixture.get("required_markers", [])), "invalidated": [], "ratio": 0.0},
                    "forbidden_markers": {"hits": [], "count": 0},
                    "anomalies": [{"type": "missing_turn", "detail": "No response supplied for turn."}],
                    "success": False,
                }
            )
            continue
        per_turn.append(score_turn(fixture, turn, response_turn))

    turn_successes = sum(1 for row in per_turn if row["success"])
    all_turns_pass = turn_successes == len(per_turn)
    all_anomalies = [anomaly for row in per_turn for anomaly in row["anomalies"]]
    forbidden_hits = [hit for row in per_turn for hit in row["forbidden_markers"]["hits"]]
    overall_required_ratio = round(sum(row["required_markers"]["ratio"] for row in per_turn) / max(len(per_turn), 1), 4)
    maximum_anomaly_count = int(thresholds.get("maximum_anomaly_count", 0))
    success = (
        not missing_turns
        and all_turns_pass
        and len(forbidden_hits) <= int(thresholds.get("maximum_forbidden_marker_hits", 0))
        and len(all_anomalies) <= maximum_anomaly_count
        and overall_required_ratio >= float(thresholds.get("minimum_required_marker_ratio", 1.0))
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
