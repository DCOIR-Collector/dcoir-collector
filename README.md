# DCOIR Collector

This repository is the governed GitHub source for the DCOIR collector, Gemini-related repository assets, workflow automation, operator tooling, and durable project guidance.

## Working model

- GitHub is the canonical source for repository content, workflows, tooling, and durable documentation.
- The current operating model is the compact `ircore` model: targeted retrieval, explicit authority checks, reuse before invention, and validation by readback.
- Legacy DCOIR helper-skill mirror and parity-maintenance surfaces have been retired from the active repository model.
- DCOIR naming remains valid where it identifies the collector, repo, product lineage, or historical artifacts.

## What this repo is for

- collector source and packaging
- Gemini-related source and documentation
- GitHub workflow automation
- operator tooling
- durable guidance that belongs in source control

## What this repo is not for

- live queue control
- chat-session continuity memory
- broad operational state mirrors that duplicate repo guidance

## Change discipline

- Prefer one scoped branch and one reviewable PR per coherent cleanup or feature wave.
- Keep workflow, documentation, and tooling assumptions in sync when a shared surface is removed.
- Prefer squash merge for broad governance or cleanup PRs so the default-branch history stays readable.
- Leave historical evidence alone unless it is actively misleading current behavior.
