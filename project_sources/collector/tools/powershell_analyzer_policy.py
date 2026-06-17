#!/usr/bin/env python3
"""PowerShell analyzer settings parsing and policy validation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from powershell_analyzer_contract import AnalyzerContractError, REQUIRED_POLICY_RULES, read_text, sha256_file

def strip_powershell_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    quote: str | None = None
    block_comment = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if block_comment:
            if char == "#" and next_char == ">":
                output.extend((" ", " "))
                block_comment = False
                index += 2
                continue
            output.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if quote:
            output.append(char)
            if char == quote:
                if quote == "'" and next_char == "'":
                    output.append(next_char)
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char == "<" and next_char == "#":
            output.extend((" ", " "))
            block_comment = True
            index += 2
            continue
        if char == "#":
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        output.append(char)
        index += 1
    return "".join(output)


def extract_outer_hashtable_body(text: str) -> str:
    start = text.find("@{")
    if start < 0:
        return ""
    index = start + 2
    output: list[str] = []
    quote: str | None = None
    depth = 1
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    output.append(char)
                    output.append(next_char)
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    output.append(char)
                    index += 1
                    continue
                quote = None
            output.append(char)
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            output.append(char)
            index += 1
            continue
        if char in "([{":
            depth += 1
            output.append(char)
            index += 1
            continue
        if char in ")]}":
            depth -= 1
            if depth == 0:
                return "".join(output)
            output.append(char)
            index += 1
            continue
        output.append(char)
        index += 1
    return ""


def top_level_assignment_values(text: str) -> dict[str, list[str]]:
    assignments: dict[str, list[str]] = {}
    index = 0
    quote: str | None = None
    depth = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char in "([{":
            depth += 1
            index += 1
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0:
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", text[index:])
            if match:
                key = match.group(1)
                value_start = index + match.end()
                value_index = value_start
                value_quote: str | None = None
                value_depth = 0
                while value_index < len(text):
                    value_char = text[value_index]
                    value_next = text[value_index + 1] if value_index + 1 < len(text) else ""
                    if value_quote:
                        if value_char == value_quote:
                            if value_quote == "'" and value_next == "'":
                                value_index += 2
                                continue
                            if value_quote == '"' and value_index > 0 and text[value_index - 1] == "`":
                                value_index += 1
                                continue
                            value_quote = None
                        value_index += 1
                        continue
                    if value_char in {"'", '"'}:
                        value_quote = value_char
                        value_index += 1
                        continue
                    if value_char in "([{":
                        value_depth += 1
                        value_index += 1
                        continue
                    if value_char in ")]}":
                        value_depth = max(0, value_depth - 1)
                        value_index += 1
                        continue
                    if value_depth == 0 and value_char == ";":
                        break
                    if (
                        value_depth == 0
                        and value_char == "\n"
                        and re.match(r"\s*[A-Za-z_][A-Za-z0-9_]*\s*=", text[value_index + 1 :])
                    ):
                        break
                    value_index += 1
                assignments.setdefault(key.casefold(), []).append(text[value_start:value_index].strip())
                index = value_index + 1 if value_index < len(text) and text[value_index] == ";" else value_index
                continue
        index += 1
    return assignments


def string_literals(text: str) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char not in {"'", '"'}:
            index += 1
            continue
        quote = char
        index += 1
        value: list[str] = []
        while index < len(text):
            current = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if current == quote:
                if quote == "'" and next_char == "'":
                    value.append("'")
                    index += 2
                    continue
                values.append("".join(value))
                index += 1
                break
            value.append(current)
            index += 1
    return values


def top_level_hashtable_keys(text: str) -> set[str]:
    keys: set[str] = set()
    index = 0
    quote: str | None = None
    depth = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 1:
            match = re.match(r"\s*([A-Za-z][A-Za-z0-9_-]*)\s*=", text[index:])
            if match:
                keys.add(match.group(1))
                index += match.end()
                continue
        index += 1
    return keys


def validate_policy(settings_path: Path) -> dict[str, Any]:
    text = read_text(settings_path, "analyzer settings file")
    uncommented_text = strip_powershell_comments(text)
    settings_body = extract_outer_hashtable_body(uncommented_text)
    assignments = top_level_assignment_values(settings_body) if settings_body else {}
    errors: list[str] = []
    warnings: list[str] = []
    if not text.strip():
        errors.append(f"{settings_path}: analyzer settings file is empty")
    if not settings_body:
        errors.append(f"{settings_path}: analyzer settings file does not look like a PowerShell data file")
    if "DCOIR_POLICY_ID:" not in text:
        errors.append(f"{settings_path}: missing DCOIR_POLICY_ID comment")

    policy_values: dict[str, str] = {}
    for key, label in (("severity", "Severity"), ("includerules", "IncludeRules"), ("rules", "Rules")):
        values = assignments.get(key, [])
        if not values:
            errors.append(f"{settings_path}: missing {label} declaration")
            continue
        if len(values) > 1:
            errors.append(f"{settings_path}: duplicate top-level {label} declarations are not allowed")
        policy_values[label] = values[0]
    exclude_values = assignments.get("excluderules", [])
    if len(exclude_values) > 1:
        errors.append(f"{settings_path}: duplicate top-level ExcludeRules declarations are not allowed")
    exclude_rules_value = exclude_values[0] if exclude_values else ""

    severity_value = policy_values.get("Severity", "")
    include_rules_value = policy_values.get("IncludeRules", "")
    rules_value = policy_values.get("Rules", "")

    active_severities = {severity.strip() for severity in string_literals(severity_value)}
    include_rules = set(string_literals(include_rules_value))
    rules_keys = top_level_hashtable_keys(rules_value)
    missing_severities = sorted(severity for severity in {"Error", "Warning"} if severity not in active_severities)
    if missing_severities:
        errors.append(f"{settings_path}: missing active Severity entries: {', '.join(missing_severities)}")
    missing_include_rules = sorted(rule for rule in REQUIRED_POLICY_RULES if rule not in include_rules)
    missing_rules_keys = sorted(rule for rule in REQUIRED_POLICY_RULES if rule not in rules_keys)
    if missing_include_rules:
        errors.append(f"{settings_path}: missing active IncludeRules entries: {', '.join(missing_include_rules)}")
    if missing_rules_keys:
        errors.append(f"{settings_path}: missing active Rules keys: {', '.join(missing_rules_keys)}")

    exclude_rules = {rule.strip().casefold() for rule in string_literals(exclude_rules_value)}
    if "*" in exclude_rules:
        errors.append(f"{settings_path}: wildcard ExcludeRules are not allowed")
    if "ps*" in exclude_rules:
        errors.append(f"{settings_path}: broad PS* ExcludeRules are not allowed")

    if exclude_values:
        warnings.append(f"{settings_path}: ExcludeRules present; every exclusion must be reviewed and justified")

    if errors:
        raise AnalyzerContractError("; ".join(errors))
    return {
        "path": settings_path.as_posix(),
        "sha256": sha256_file(settings_path),
        "required_rules": sorted(REQUIRED_POLICY_RULES),
        "active_severities": sorted(active_severities),
        "active_include_rules": sorted(include_rules),
        "active_rule_keys": sorted(rules_keys),
        "warnings": warnings,
        "exclusions_declared": bool(exclude_values),
    }
