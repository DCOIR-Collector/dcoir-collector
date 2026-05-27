# GitHub workflow authority pointer

This folder holds repo-native GitHub workflow support surfaces.

Current authority model:

- The workflow YAML body is the executable source of truth.
- The top comment block in each `.github/workflows/*.yml` file owns workflow-specific execution guidance.
- GitHub is canonical for workflow and source truth.
- Supabase `ircore` is the operational routing, validation, lessons, and active-state surface.
- Legacy Airtable may still exist for migration or historical lookup, but it is not the active default workflow-routing authority.
