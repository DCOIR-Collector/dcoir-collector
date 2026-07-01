# Issue 349 / PR 350 PowerShell Evidence Report Chunks

This directory is an additive connector-sized sidecar for the generated PowerShell evidence reports.

The canonical report files under `project_sources/collector/` remain unchanged by this sidecar. These chunks exist so future connector-only work can fetch, edit, and upload smaller functional fragments instead of moving large monolithic generated reports.

Chunk conventions:

- Each report has separate `json/` and/or `markdown/` subdirectories.
- Each subdirectory has a `manifest.json` with source report path, source SHA-256, source byte count, chunk order, and per-chunk hashes.
- JSON reports may use either byte-exact text slices or semantic JSON chunks.
- `json_text_slice` chunks reassemble by concatenating contiguous byte ranges in manifest order.
- Semantic JSON chunks carry a JSON pointer plus either a complete value, object members, or ordered list items.
- Markdown chunks reassemble by concatenating files in manifest order.

This sidecar is not a PR readiness claim and does not replace the canonical generated reports until a future loader/reassembly lane is explicitly implemented and validated.
