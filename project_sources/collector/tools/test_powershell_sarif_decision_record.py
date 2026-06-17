#!/usr/bin/env python3
"""Validate the #269 SARIF decision record stays decision-only."""
from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RECORD_PATH = REPO_ROOT / "project_sources/collector/powershell_sarif_decision_record.json"
MARKDOWN_PATH = REPO_ROOT / "project_sources/collector/powershell_sarif_decision_record.md"


class SarifDecisionRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        self.markdown = MARKDOWN_PATH.read_text(encoding="utf-8")

    def test_record_selects_defer_and_validates(self) -> None:
        self.assertEqual(self.record["schema_version"], "dcoir_powershell_sarif_decision_record_v1")
        self.assertEqual(self.record["issue"], 269)
        self.assertEqual(self.record["parent_issue"], 260)
        self.assertEqual(self.record["decision"], "defer_sarif_upload")
        self.assertTrue(self.record["validation"]["success"])
        self.assertFalse(self.record["validation"]["errors"])

    def test_prerequisite_evidence_is_named(self) -> None:
        evidence_by_issue = {entry["issue"]: entry for entry in self.record["evidence_inputs"]}
        self.assertEqual(set(evidence_by_issue), {266, 267, 268})
        self.assertEqual(evidence_by_issue[266]["summary"]["classified_finding_count"], 22)
        self.assertEqual(evidence_by_issue[266]["summary"]["baseline_record_count"], 0)
        self.assertEqual(evidence_by_issue[266]["summary"]["suppression_count"], 0)
        self.assertEqual(evidence_by_issue[268]["summary"]["normalized_finding_count"], 22)
        self.assertEqual(evidence_by_issue[268]["summary"]["optional_source_reports_missing"], 1)
        self.assertEqual(evidence_by_issue[267]["summary"]["workflow_readiness_claimed"], False)

    def test_required_no_upload_non_claims_are_present(self) -> None:
        non_claims = "\n".join(self.record["non_claims"])
        required_fragments = [
            "No SARIF file is generated",
            "No SARIF upload is performed",
            "No GitHub workflow file is changed",
            "No code-scanning alert",
            "No pull_request_target workflow design",
            "No parent #260 closeability",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, non_claims)

    def test_future_gate_requires_permission_and_alert_ownership(self) -> None:
        future_requirements = "\n".join(self.record["future_sarif_implementation_requirements"])
        for fragment in (
            "security-events: write",
            "pull_request_target avoidance",
            "Code-scanning alert ownership",
            "Upload run evidence",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, future_requirements)

    def test_markdown_matches_core_decision_and_boundary(self) -> None:
        self.assertIn("Decision: `defer_sarif_upload`", self.markdown)
        self.assertIn("No SARIF upload is performed by #269.", self.markdown)
        self.assertIn("No GitHub workflow file is changed by #269.", self.markdown)
        self.assertIn("Because SARIF upload is deferred", self.markdown)


if __name__ == "__main__":
    unittest.main()
