#!/usr/bin/env python3
"""Validate the local JSON cache shape used by dcoir-memory-preflight."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_TOP = ["schema_version", "skill_name", "generated_at_utc", "base_id", "tables", "freshness"]
REQUIRED_TABLE = ["table_name", "table_id", "primary_key_field", "record_count", "included_fields", "excluded_fields", "field_map", "scope_filter", "records"]
ROUTINE_TABLES = {"dcoir-memory-preflight", "Operator Preferences", "Session Checkpoints", "Queue Control", "Plans", "Work Items"}


def validate_cache(data: Dict[str, Any], require_routine_name: bool = False) -> List[str]:
    errors: List[str] = []
    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"missing top-level key: {key}")
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if data.get("skill_name") != "dcoir-memory-preflight":
        errors.append("skill_name must be dcoir-memory-preflight")
    tables = data.get("tables")
    if not isinstance(tables, list):
        errors.append("tables must be a list")
        return errors
    for i, table in enumerate(tables):
        if not isinstance(table, dict):
            errors.append(f"tables[{i}] must be an object")
            continue
        for key in REQUIRED_TABLE:
            if key not in table:
                errors.append(f"tables[{i}] missing key: {key}")
        name = table.get("table_name")
        if require_routine_name and name not in ROUTINE_TABLES:
            errors.append(f"tables[{i}] table_name is not a routine cached table: {name}")
        if "records" in table and not isinstance(table["records"], list):
            errors.append(f"tables[{i}].records must be a list")
        if "included_fields" in table and not isinstance(table["included_fields"], list):
            errors.append(f"tables[{i}].included_fields must be a list")
        if "excluded_fields" in table and not isinstance(table["excluded_fields"], list):
            errors.append(f"tables[{i}].excluded_fields must be a list")
    freshness = data.get("freshness")
    if not isinstance(freshness, dict):
        errors.append("freshness must be an object")
    else:
        if "max_age_minutes" not in freshness:
            errors.append("freshness missing max_age_minutes")
        if "source" not in freshness:
            errors.append("freshness missing source")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache_file", type=Path)
    parser.add_argument("--require-routine-name", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.cache_file.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to read JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("ERROR: cache file must contain a JSON object", file=sys.stderr)
        return 1
    errors = validate_cache(data, args.require_routine_name)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("cache contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
