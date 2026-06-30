#!/usr/bin/env python3
from __future__ import annotations

import unittest

from powershell_rule_risk_fixtures_test_findings import PowerShellRuleRiskFixtureFindingTests
from powershell_rule_risk_fixtures_test_paths import PowerShellRuleRiskFixturePathSafetyTests
from powershell_rule_risk_fixtures_test_report import PowerShellRuleRiskFixtureReportTests

__all__ = (
    "PowerShellRuleRiskFixtureFindingTests",
    "PowerShellRuleRiskFixturePathSafetyTests",
    "PowerShellRuleRiskFixtureReportTests",
)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
