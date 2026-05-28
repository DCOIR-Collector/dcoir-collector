# Gemini Behavioral Replay Fixtures

This fixture family supports the broader behavioral replay harness described in issue `#145`.

## Purpose

These fixtures are transcript-derived, not raw chat dumps.

Each fixture is expected to:

- preserve the real decision points and turn ordering
- constrain the assistant to only the evidence available at each turn
- encode expected and forbidden behaviors explicitly
- support deterministic scoring and live Gemini replay

## Model split

The broader replay harness uses a locked model split:

- reference baseline: `gemini-3.1-pro-preview`
- simulated production lane: `gemini-3.5-flash`

The reference baseline supports comparison, drift checks, and closeness scoring.

The simulated production lane is the default live replay target unless an operator explicitly overrides it.

## Initial fixture family

The first governed fixture covers the `#124` failure family around:

- workflow-state readback discipline
- cleanup/restage/execute/retrieve sequencing
- PowerShell boundedness
- collector contract boundedness
- chunk continuity and artifact recovery
- partial-evidence handling

## Registry

Use `index.json` as the family registry.

Each listed fixture must pass `validate_gemini_behavioral_replay_fixtures.py` before it is used by any replay or scoring lane.
