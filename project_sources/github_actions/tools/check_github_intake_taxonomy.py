#!/usr/bin/env python3
"""Validate GitHub issue/PR intake surfaces against the approved label taxonomy."""

from __future__ import annotations

import re
import sys
from pathlib import Path


APPROVED_LABELS = {
    "area:collector",
    "area:docs",
    "area:gemini-agent",
    "area:github-repo",
    "area:knowledge-docs",
    "area:operator-tooling",
    "area:project-tracking",
    "area:repo-governance",
    "area:supabase-ircore",
    "area:validation",
    "area:workflows",
    "type:accidental",
    "type:bug",
    "type:cleanup",
    "type:decision",
    "type:enhancement",
    "type:idea",
    "type:maintenance",
    "type:meta",
    "type:planning",
    "type:refactor",
    "type:research",
}

RETIRED_LABELS = {
    "administrative",
    "agent-instructions",
    "architecture",
    "area:airtable-ircore",
    "area:gemini",
    "blocked",
    "bug",
    "codex",
    "collector",
    "dependencies",
    "documentation",
    "duplicate",
    "enhancement",
    "gemini",
    "gemini-agent",
    "github_actions",
    "github-actions",
    "governance",
    "governance-cleanup",
    "ignore",
    "invalid",
    "ircore",
    "mirror",
    "needs-triage",
    "prompt-pack",
    "question",
    "test-failure",
    "workflow",
    "wontfix",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.as_posix()}: {message}")


def extract_top_level_labels(text: str) -> list[str]:
    lines = text.splitlines()
    labels: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("labels:"):
            continue
        base_indent = len(line) - len(line.lstrip())
        remainder = stripped.split(":", 1)[1].strip()
        if remainder:
            return [
                value.strip().strip("'\"")
                for value in remainder.strip("[]").split(",")
                if value.strip()
            ]
        for follow in lines[index + 1 :]:
            follow_indent = len(follow) - len(follow.lstrip())
            if follow.strip().startswith("- ") and follow_indent > base_indent:
                labels.append(follow.strip().split("- ", 1)[1].strip().strip("'\""))
                continue
            if follow.strip() == "":
                continue
            if follow_indent <= base_indent:
                break
        if labels:
            return labels
    return labels


def validate_issue_forms(root: Path, errors: list[str]) -> None:
    template_dir = root / ".github" / "ISSUE_TEMPLATE"
    markdown_templates = sorted(template_dir.glob("*.md"))
    for path in markdown_templates:
        fail(errors, path.relative_to(root), "Markdown issue templates are retired; use YAML issue forms")

    forms = sorted(template_dir.glob("*.yml")) + sorted(template_dir.glob("*.yaml"))
    forms = [path for path in forms if path.name != "config.yml"]
    if not forms:
        fail(errors, template_dir.relative_to(root), "No YAML issue forms found")

    for path in forms:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        labels = extract_top_level_labels(text)
        if not labels:
            fail(errors, rel, "issue form must declare labels")
            continue
        unknown = [label for label in labels if label not in APPROVED_LABELS]
        if unknown:
            fail(errors, rel, f"unknown labels: {', '.join(unknown)}")
        area = [label for label in labels if label.startswith("area:")]
        kind = [label for label in labels if label.startswith("type:")]
        if len(area) != 1:
            fail(errors, rel, f"expected exactly one area label, got {len(area)}")
        if len(kind) != 1:
            fail(errors, rel, f"expected exactly one type label, got {len(kind)}")


def quoted_label_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"['\"]([^'\"]+)['\"]", text))
    tokens.update(re.findall(r"(?m)^\s*-\s+([A-Za-z0-9:_-]+)\s*$", text))
    return tokens


def validate_label_references(root: Path, errors: list[str]) -> None:
    paths = [
        root / ".github" / "PULL_REQUEST_TEMPLATE.md",
        root / ".github" / "dependabot.yml",
    ]
    paths.extend((root / ".github" / "ISSUE_TEMPLATE").glob("*.yml"))
    paths.extend((root / ".github" / "ISSUE_TEMPLATE").glob("*.yaml"))

    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        tokens = quoted_label_tokens(text)
        retired = sorted(token for token in tokens if token in RETIRED_LABELS)
        if retired:
            fail(errors, rel, f"retired label references: {', '.join(retired)}")
        label_like = sorted(
            token
            for token in tokens
            if token.startswith(("area:", "type:")) and token not in APPROVED_LABELS
        )
        if label_like:
            fail(errors, rel, f"unapproved taxonomy labels: {', '.join(label_like)}")


def validate_dependabot(root: Path, errors: list[str]) -> None:
    path = root / ".github" / "dependabot.yml"
    if not path.exists():
        return
    labels = extract_top_level_labels(path.read_text(encoding="utf-8"))
    expected = {"area:github-repo", "type:maintenance"}
    if set(labels) != expected:
        fail(
            errors,
            path.relative_to(root),
            f"dependabot labels must be exactly {sorted(expected)}; got {labels}",
        )


def main() -> int:
    root = repo_root()
    errors: list[str] = []
    validate_issue_forms(root, errors)
    validate_label_references(root, errors)
    validate_dependabot(root, errors)
    if errors:
        print("GitHub intake taxonomy validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GitHub intake taxonomy validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
