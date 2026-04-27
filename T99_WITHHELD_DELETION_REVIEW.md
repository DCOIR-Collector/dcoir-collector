# T99 Withheld Deletion Review

The final bundle removed only authority-safe cleanup targets. The following classes were intentionally retained because Airtable Retained Repo Manifest or Repo Surface Registry still marks them as keep/defer/needs-review, or because older exact-delete tasks conflict with retained-source registry evidence:

- `project_sources/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/CP-02_DCOIR_Change_Log.txt` retained as source/promoted-history references.
- CP-01-named control/governance files retained where the Retained Repo Manifest says keep.
- Historical Gemini/reference folders retained when manifest status is defer rather than remove.
- `knowledge/task_memory/` retained because Retained Repo Manifest still says verify live dependency before final cleanup.
- `release_notes/` retained as promoted delivery history.
- `.github/`, issue templates, workflows, and GitHub repo support files retained.

Removed items are listed in `T99_REMOVAL_REPORT.json`.
