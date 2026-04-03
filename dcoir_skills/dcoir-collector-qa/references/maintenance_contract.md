# Maintenance contract

This skill must preserve both human-readable and machine-friendly maintenance artifacts.

## Human-readable maintenance outputs
Every meaningful run should support a markdown report that preserves:
- authoritative basis
- what was executed versus not executed
- current limitations
- failures and likely causes
- recommended fixes
- next operator steps

## Machine-friendly maintenance outputs
When useful, emit a companion JSON results file that preserves:
- source inventory
- hashes or lightweight identity data
- test inventory and status
- output-contract markers
- code block inventory
- known-failure lane status

## Code block maintenance requirement
Copyable code blocks are part of the maintained surface.

Treat any of these as a defect:
- stale runtime filenames
- stale harness commands
- broken quoting
- command blocks that no longer match current readable sources
- examples that drift from the emitted runtime alias rules

## Minimum maintained command blocks
Prefer to keep these current when evidence supports them:
- local harness PS1 invocation
- local harness CMD wrapper invocation
- any collector cleanup or delete command emitted directly by the collector source


## In-code documentation maintenance requirement
When repair mode or documentation mode is active, maintain targeted in-code documentation as part of the controlled output.

Prefer this order:
1. file-level comment-based help for the top-level script
2. function-level help for externally-invoked, operator-facing, or output-contract-critical functions
3. short inline comments only where control flow, quoting, or emitted-field handling is easy to misread

Treat any of these as documentation defects when the user asked for maintenance refresh:
- no file-level help on a primary entry-point script
- comments that still mention stale runtime filenames or stale harness behavior
- comments that contradict emitted markers, cleanup behavior, or operator sequence
- function names that are heavily used externally but have no concise maintenance cue nearby

Do not add broad comment noise. The goal is future maintenance clarity, not line-by-line narration.
