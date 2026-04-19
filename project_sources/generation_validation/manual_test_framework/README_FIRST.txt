DCOIR Manual Test Framework

What changed in this build
- Added a durable control file: dcoir_manual_test_control.json
- Added session-based naming so archived reports and state files do not overwrite each other
- Added transient-work cleanup rules so failed or partial work folders do not pile up between runs
- Kept a stable latest report path for quick access: _test_output\LATEST_DCOIR_Collector_Full_Signoff_Report.txt
- Kept a stable latest state path for quick access: _test_output\LATEST_runner_state.json

Recommended install/use location
- Use a short path such as C:\DCOIR to reduce Windows path-length issues.

What the launcher does
- checks for Git and Python
- tries to install them with winget if missing
- enables Git long-path support when possible
- starts the Python dashboard runner

What the runner does
- clones a fresh transient repo copy for the current test session
- builds and restores the live-style collector runtime
- stages DCOIR_Collector.ps1 and DCOIR_Collector.zip next to the framework during the run
- archives reports/state under _history\<session-id>\
- cleans up transient working folders and top-level staged runtime files after success or failure

How to run
1. Open PowerShell.
2. Change to the framework folder.
3. Run:
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .un_dcoir_manual_tests.ps1

Where to look first after a run
- latest report: _test_output\LATEST_DCOIR_Collector_Full_Signoff_Report.txt
- archived report: _history\<session-id>\<session-id>_DCOIR_Collector_Full_Signoff_Report.txt
