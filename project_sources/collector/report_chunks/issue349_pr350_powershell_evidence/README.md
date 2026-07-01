# Issue 349 / PR 350 PowerShell Evidence Report Chunks

This directory is an additive connector-sized sidecar for the generated PowerShell evidence reports.

The canonical report files under `project_sources/collector/` remain unchanged by this sidecar. These chunks exist so future connector-only work can fetch, edit, and upload smaller functional fragments instead of moving large monolithic generated reports.

The chunks in this refresh were generated from rebuilt report outputs for PR source commit `c3671269e6749447406b575cc41682293fc6a702`. The `source_report` fields in manifests identify the canonical report path and report contract only; they are not a claim that the current branch's monolithic canonical report files match these chunks. Use `--compare-canonical` to test that boundary before treating the sidecar as a canonical report replacement.

Chunk conventions:

- Each report has separate `json/` and/or `markdown/` subdirectories.
- Each subdirectory has a `manifest.json` with source report path, source SHA-256, source byte count, chunk order, and per-chunk hashes.
- JSON reports use byte-exact text slices in this refresh.
- `json_text_slice` chunks reassemble by concatenating contiguous byte ranges in manifest order.
- Markdown chunks reassemble by concatenating files in manifest order.

This sidecar is not a PR readiness claim and does not replace the canonical generated reports until a future loader/reassembly lane is explicitly implemented and validated.
