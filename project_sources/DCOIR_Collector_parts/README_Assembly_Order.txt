DCOIR Collector Split Readable Source Set

Purpose
- This folder holds the split readable-source form of the collector so future governed updates can patch bounded sections without rewriting one very large file in a single GitHub operation.
- The intended manual assembly target remains the canonical runtime filename: DCOIR_Collector.ps1

Authority and use
- Until the control plane is fully refreshed, `project_sources/DCOIR_Collector.ps1` remains the previously assembled collector snapshot.
- The files in this folder are the new bounded readable-source working line for the collector split initiative.
- When assembled in the order listed below, the concatenated content forms the collector script.

Assembly order
1. 01_Header_and_Core_Utilities.ps1
2. 02_Run_Structure_and_Collection_Helpers.ps1
3. 03_Baseline_Report_and_Metadata.ps1
4. 04_Enrichment_Session_Framework.ps1
5. 05_Enrichment_Actions.ps1
6. 06_Quick_Aliases_and_Main.ps1

Notes
- Preserve file order exactly.
- Do not insert separators between files when assembling.
- The split line is designed to carry the pending full-path output cleanup so operator-facing suggested commands and emitted path values use absolute script paths rather than `.`-relative references.
