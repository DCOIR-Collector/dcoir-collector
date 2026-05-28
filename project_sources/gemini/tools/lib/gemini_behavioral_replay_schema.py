from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


REQUIRED_FIXTURE_KEYS = [
    "fixture_id",
    "title",
    "source_issue_numbers",
    "source_pr_numbers",
    "scenario_tags",
    "system_surface",
    "model_target_profile",
    "turns",
    "available_evidence_by_turn",
    "artifact_inputs",
    "expected_behaviors",
    "forbidden_behaviors",
    "required_markers",
    "forbidden_markers",
    "expected_next_move_shapes",
    "anomaly_checks",
    "pass_thresholds",
    "report_expectations",
]

REQUIRED_TURN_KEYS = [
    "turn_id",
    "speaker",
    "content",
    "available_context_refs",
    "allowed_assumptions",
    "disallowed_assumptions",
    "expected_behavior_tags",
    "forbidden_behavior_tags",
    "scoring_notes",
]


@dataclass(frozen=True)
class ValidationMessage:
    level: str
    message: str


def missing_keys(payload: Dict[str, Any], required_keys: List[str]) -> List[str]:
    return [key for key in required_keys if key not in payload]


def validate_turn(turn: Dict[str, Any]) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []
    missing = missing_keys(turn, REQUIRED_TURN_KEYS)
    if missing:
        messages.append(
            ValidationMessage(
                "error",
                f"turn {turn.get('turn_id', '<missing-turn-id>')} is missing keys: {', '.join(missing)}",
            )
        )
    return messages


def validate_fixture_shape(fixture: Dict[str, Any]) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []
    missing = missing_keys(fixture, REQUIRED_FIXTURE_KEYS)
    if missing:
        messages.append(
            ValidationMessage(
                "error",
                f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} is missing keys: {', '.join(missing)}",
            )
        )

    turns = fixture.get("turns", [])
    if not isinstance(turns, list) or not turns:
        messages.append(
            ValidationMessage(
                "error",
                f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} must define at least one turn",
            )
        )
    else:
        seen_turn_ids = set()
        for turn in turns:
            for message in validate_turn(turn):
                messages.append(message)
            turn_id = turn.get("turn_id")
            if turn_id in seen_turn_ids:
                messages.append(
                    ValidationMessage(
                        "error",
                        f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} repeats turn_id {turn_id}",
                    )
                )
            seen_turn_ids.add(turn_id)

    model_target_profile = fixture.get("model_target_profile", {})
    for required_key in ("reference_baseline", "simulated_production", "default_live_target"):
        if required_key not in model_target_profile:
            messages.append(
                ValidationMessage(
                    "error",
                    f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} missing model_target_profile.{required_key}",
                )
            )

    evidence_by_turn = fixture.get("available_evidence_by_turn", {})
    for turn in turns if isinstance(turns, list) else []:
        turn_id = turn.get("turn_id")
        if turn_id not in evidence_by_turn:
            messages.append(
                ValidationMessage(
                    "error",
                    f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} has no available_evidence_by_turn entry for {turn_id}",
                )
            )

    if not fixture.get("required_markers"):
        messages.append(
            ValidationMessage(
                "warning",
                f"fixture {fixture.get('fixture_id', '<missing-fixture-id>')} has no required_markers",
            )
        )

    return messages
