DCOIR Manual Test Framework Bundle v9

What changed in v8
- The Git and Python prerequisite rows are now bound to bootstrap results instead of staying stuck at PENDING.
- The staged collector runtime now lives under _test_output\live_runtime instead of cluttering the root folder.
- The admin phase now launches through the PowerShell launcher so the elevated window follows the same dashboard path.
- The framework now removes staged runtime files and transient build/staging folders during cleanup.
- Expected non-admin collector limitations are graded as PASS with honest notes instead of surfacing as framework PARTIAL results.
- Quick help is now expected to print and return cleanly without relying on the old nonzero-exit quirk.
- Contextual help is now part of the graded manual test surface.
- Review-surface tuning checks are now part of the graded manual test surface.
- The framework now records a bounded T2-pathway mapping follow-on note so the operator does not lose that required live proof step.

Files
- run_dcoir_manual_tests.ps1 : bootstrap launcher
- dcoir_manual_test_runner.py : terminal dashboard and test engine
- dcoir_manual_test_control.json : durable control surface for step/order/cleanup naming
- DCOIR_manual_test_plan.md : ordered manual test plan
- README_FIRST.txt : this file
- install_and_run_from_downloads.ps1 : optional one-shot installer/runner helper

How to run
1. Put all files from this bundle in one folder, for example C:\DCOIR_TESTER.
2. Open a normal PowerShell window.
3. Either run the install helper, or run:
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_dcoir_manual_tests.ps1

What the launcher does
- Checks Git and Python.
- Tries to install missing prerequisites with winget.
- Refreshes the current PATH.
- Launches the dashboard.

What the dashboard does
- Shows every test on load.
- Updates STATUS live as each test starts and finishes.
- Shows only high-level status and next-action text in the terminal.
- Writes all command output, errors, and detailed traces into:
  .\_test_output\DCOIR_Collector_Full_Signoff_Report.txt

Important notes
- The framework now stages runtime files inside _test_output\live_runtime.
- The framework intentionally preserves the report/state/runs for review after the run.
- Richer contextual help is now part of the current testable collector surface.
- Review-surface tuning and the bounded T2-pathway follow-on are now part of the current testable collector surface.
