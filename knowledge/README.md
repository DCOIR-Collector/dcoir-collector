# DCOIR Maintained Knowledge Set

This folder is the maintained readable source for the shared DCOIR knowledge set that feeds Gemini bundle attachments.

## Authority

- `knowledge/*.md` files are the editable maintained source.
- Gemini attachment copies live under `project_sources/gemini/bundle_source/02_PRIME_AGENT_ATTACHMENTS/*.md.txt`.
- The attachment copies are synced from this folder and should not be treated as the primary editing surface.
- Knowledge docs support operators and Gemini, but they do not override Airtable live state, Project Instructions, or governed GitHub source.

## Current pages

1. Knowledge - 01 - Overview and About
2. Knowledge - 02 - Elastic Quick Start
3. Knowledge - 03 - Local Test and Regression
4. Knowledge - 04 - Tier 1 Collect Runbook
5. Knowledge - 05 - Tier 2 Collect Runbook
6. Knowledge - 06 - Enrichment Actions
7. Knowledge - 07 - Artifact Review Guide
8. Knowledge - 08 - Troubleshooting
9. Knowledge - 09 - FAQ
10. Knowledge - 10 - AI Prompt and Agent Design
11. Knowledge - 11 - IOC Enrichment and Public Sources
12. Knowledge - 12 - Gemini Runtime Bundle and Source Tree
13. Knowledge - 13 - Gemini Agent Topology and Routing
14. Knowledge - 14 - Gemini Output Contract and Command-Lane Discipline
15. Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance
16. Knowledge - 16 - Collector EXE Usage and Runtime Behavior
17. Knowledge - 17 - Collector Feature and Output Contract Reference

## Maintenance triggers

When the page list, attachment set, collector behavior, EXE behavior, Gemini agent behavior, or workflow validation coverage changes, update these surfaces together:

- maintained `knowledge/*.md` source files;
- synced Gemini `.md.txt` attachment files;
- `Agent_Attachment_Map.md.txt`;
- `Gemini_Bundle_Source_Manifest.json`;
- GitHub Actions required-surface checks.
