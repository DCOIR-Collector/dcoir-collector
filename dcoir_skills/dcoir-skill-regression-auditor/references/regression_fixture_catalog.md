# Regression Fixture Catalog

## Fixture families
- current-workspace success fixture
- current-control-plane narrative-manifest fixture
- missing-control-plane fixture
- missing-required-file fixture
- unexpected-manifest-role fixture
- output-structure verification fixture
- anti-pattern detection fixture
- helper-memory read-write fixture
- package replacement smoke fixture
- package cleanliness fixture

## Usage principle
Choose the smallest fixture set that still proves:
- correct success behavior
- correct stop behavior
- correct artifact verification
- correct control-plane interpretation for the current GitHub-primary workflow

## Campaign rule
When a broad `dcoir-*` helper-skill scan or patch cycle is underway, start by validating `dcoir-skill-regression-auditor` itself before using it to assess other skills.
