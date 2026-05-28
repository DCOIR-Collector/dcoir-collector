from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from lib.gemini_behavioral_replay_schema import validate_fixture_shape


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parents[3]


def load_fixture_index(fixtures_root: Path) -> Dict[str, Any]:
    return load_json(fixtures_root / "index.json")


def resolve_fixture_path(repo_root: Path, entry: Dict[str, Any]) -> Path:
    raw_path = Path(entry["path"])
    if raw_path.is_absolute():
        return raw_path
    return (repo_root / raw_path).resolve()


def load_fixture_entry(repo_root: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    fixture_path = resolve_fixture_path(repo_root, entry)
    fixture_payload = load_json(fixture_path)
    return {
        "entry": entry,
        "fixture_path": fixture_path,
        "fixture": fixture_payload,
        "validation_messages": validate_fixture_shape(fixture_payload),
    }


def load_fixtures(fixtures_root: Path, script_path: Path, fixture_id: str | None = None) -> List[Dict[str, Any]]:
    repo_root = repo_root_from_script(script_path)
    index_payload = load_fixture_index(fixtures_root)
    entries = index_payload.get("fixtures", [])
    selected = []
    for entry in entries:
        if fixture_id is None or entry.get("fixture_id") == fixture_id:
            selected.append(load_fixture_entry(repo_root, entry))
    return selected


def load_response_pack(path: Path) -> Dict[str, Any]:
    return load_json(path)
