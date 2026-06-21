#!/usr/bin/env python3
"""Offline checks for Pareto routing and first-pass context wrapper."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openrouter_pr_review_pareto_context.py"

spec = importlib.util.spec_from_file_location("openrouter_pr_review_pareto_context", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load openrouter_pr_review_pareto_context.py")
mod = importlib.util.module_from_spec(spec)
import sys

sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

os.environ["GITHUB_REPOSITORY"] = "DCOIR-Collector/dcoir-collector"
os.environ["PR_NUMBER"] = "287"

config = mod.load_pareto_context_config(str(ROOT / ".github" / "openrouter-pr-review-pareto.yml"))
assert config.model == "openrouter/pareto-code"
assert config.model_stack == ["openrouter/pareto-code", "openrouter/auto"]
assert config.pareto_min_coding_score == 0.80
assert config.auto_cost_quality_tradeoff == 2
assert "google/gemini-*" not in config.auto_allowed_models
assert config.first_pass_deep_review is True
assert config.deep_review_max_files == 8

schema = json.loads((ROOT / "schemas" / "openrouter-pr-review.schema.json").read_text(encoding="utf-8"))
pareto_payload = mod.build_openrouter_payload("review prompt", schema, config, [], "openrouter/pareto-code")
assert pareto_payload["model"] == "openrouter/pareto-code"
assert pareto_payload["provider"]["require_parameters"] is True
assert pareto_payload["response_format"]["json_schema"]["strict"] is True
assert pareto_payload["plugins"] == [{"id": "pareto-router", "min_coding_score": 0.80}]

auto_payload = mod.build_openrouter_payload("review prompt", schema, config, ["venice"], "openrouter/auto")
assert auto_payload["model"] == "openrouter/auto"
assert auto_payload["provider"]["ignore"] == ["venice"]
assert auto_payload["plugins"][0]["id"] == "auto-router"
assert auto_payload["plugins"][0]["cost_quality_tradeoff"] == 2

assert mod.review_mode_for_command("/dcoir-review", "/dcoir-review", config, False) == "first-pass-deep"
assert mod.review_mode_for_command("/dcoir-review", "/dcoir-review", config, True) == "diff"
assert mod.review_mode_for_command("/dcoir-review deep", "/dcoir-review", config, True) == "deep-forced"
assert mod.review_mode_for_command("/dcoir-review exhaustive", "/dcoir-review", config, True) == "deep-forced"
assert mod.review_mode_for_command("/dcoir-review diff", "/dcoir-review", config, False) == "diff"


class FakeGitHubClient:
    repo = "DCOIR-Collector/dcoir-collector"

    def __init__(self, reviews: list[dict[str, str]] | None = None) -> None:
        self.reviews = reviews or []
        self.files = {
            "tools/review_probe.py": "def run_probe(command):\n    return subprocess.run(command, shell=True)\n",
            "docs/review.md": "# Review\n\nKeep governed review evidence visible.\n",
        }

    def request(self, _method: str, path: str):
        if path.startswith("/repos/DCOIR-Collector/dcoir-collector/pulls/287/reviews"):
            return self.reviews
        if "/contents/" not in path:
            raise AssertionError(f"unexpected GitHub path: {path}")
        encoded_path = path.split("/contents/", 1)[1].split("?", 1)[0]
        file_path = mod.urllib.parse.unquote(encoded_path)
        content = self.files[file_path].encode("utf-8")
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        }


assert mod.has_prior_successful_context_review(FakeGitHubClient([{"body": mod.base.MARKER}]), 287) is False
assert (
    mod.has_prior_successful_context_review(
        FakeGitHubClient([{"body": f"{mod.base.MARKER}\n\n{mod.CONTEXT_REVIEW_MARKER} `first-pass-deep`"}]),
        287,
    )
    is True
)

deep_block, deep_summary = mod.build_deep_context_block(
    FakeGitHubClient(),
    {"head": {"sha": "abc123def4567890"}},
    [
        {"filename": "tools/review_probe.py", "status": "added"},
        {"filename": "docs/review.md", "status": "modified"},
        {"filename": "old/deleted.py", "status": "removed"},
    ],
    config,
    "first-pass-deep",
)
assert "Deep changed-file context" in deep_block
assert "tools/review_probe.py" in deep_block
assert "subprocess.run(command, shell=True)" in deep_block
assert "included 2 file context block" in deep_summary
assert "old/deleted.py (deleted)" in deep_summary

prompt = mod.build_prompt(
    {"number": 287, "title": "Deep context probe", "body": "Test first-pass context."},
    [{"filename": "tools/review_probe.py", "status": "added", "additions": 2, "deletions": 0, "changes": 2}],
    "diff --git a/tools/review_probe.py b/tools/review_probe.py\n",
    config,
    [],
    deep_block,
    "first-pass-deep",
    deep_summary,
)
assert "Context mode: first-pass-deep" in prompt
assert "Deep changed-file context" in prompt
assert "subprocess.run(command, shell=True)" in prompt


class FakeErrorBody:
    def read(self) -> bytes:
        return json.dumps({"error": {"message": "No endpoints found that can handle the requested parameters."}}).encode("utf-8")

    def close(self) -> None:
        return None


called_models: list[str] = []
original_request_once = mod.hardened.openrouter_request_once


def fake_request_once(_prompt: str, _schema: dict, _config: object, _ignored: list[str], model: str):
    called_models.append(model)
    if model == "openrouter/pareto-code":
        raise urllib.error.HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=404,
            msg="No endpoints found",
            hdrs={},
            fp=FakeErrorBody(),
        )
    return {"summary": "No findings.", "findings": []}, "fallback-model", ""


mod.hardened.openrouter_request_once = fake_request_once
try:
    result, model_used, _tier = mod.hardened.openrouter_review("prompt", schema, config, None)
finally:
    mod.hardened.openrouter_request_once = original_request_once
assert called_models == ["openrouter/pareto-code", "openrouter/auto"]
assert model_used == "fallback-model"
assert result["findings"] == []

review_body = mod.append_context_to_review_body(mod.base.MARKER, "first-pass-deep", deep_summary)
assert "Context mode: `first-pass-deep`" in review_body
assert "Context readback:" in review_body

print("Pareto context OpenRouter selftest passed")
