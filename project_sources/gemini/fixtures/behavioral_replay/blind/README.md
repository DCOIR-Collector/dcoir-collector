# Production-Like Gemini Blind Behavioral Scenarios

This directory contains committed blind scenario definitions for the #179 Gemini Agent behavioral harness.

The committed scenario matrix currently lives in `index.json` so the #179 harness is reviewable as one compact authority file. The scenario entries describe what the model may see during a replay and keep grading metadata separate from the prompt payload. The live or simulated Gemini prompt must never include answer keys, hidden grading rubrics, required markers, forbidden markers, known-good response packs, known-bad response packs, or scenario owner labels.

Large or replaceable artifacts belong under `../blind_artifacts/`, which is ignored by git and excluded from workflow triggers. Commit only manifests, checksums, structure, small representative excerpts, and pointers that are safe to version.

Readiness claims for this harness require reading the uploaded workflow artifacts and reports. A green workflow conclusion alone does not prove Gemini behavior passed.
