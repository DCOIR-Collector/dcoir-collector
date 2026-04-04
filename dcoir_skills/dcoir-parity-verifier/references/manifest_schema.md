# Skill parity manifest schema

Canonical machine-readable surface:
- `dcoir_skills/skill_parity_manifest.json`

Human-readable companion surface:
- `dcoir_skills/skill_parity_summary.md`

## Primary rules
- treat the JSON manifest as the canonical parity source
- treat the markdown summary as generated from the manifest
- prefer per-file `sha256` and a normalized tree hash over zip hash alone
- treat zip hash as a secondary package/install check because zip metadata can drift without content drift

## Manifest shape
```json
{
  "schema_version": 1,
  "project": "AFRICOM_SOC_IR / DCOIR",
  "generated_at_utc": "2026-04-04T00:00:00Z",
  "baseline_origin": "repo_source|installed_skill_tree|mixed_bootstrap",
  "hash_policy": {
    "file_hash": "sha256",
    "tree_hash": "sha256 over sorted path+hash lines",
    "zip_hash": "sha256"
  },
  "skills": {
    "dcoir-parity-verifier": {
      "source_root": "dcoir_skills/dcoir-parity-verifier",
      "source_tree_hash": "...",
      "release_zip_name": "dcoir-parity-verifier.zip",
      "release_zip_hash": "...",
      "status": "verified|bootstrap|mismatch",
      "files": [
        {"path": "SKILL.md", "sha256": "...", "size_bytes": 123}
      ]
    }
  }
}
```
