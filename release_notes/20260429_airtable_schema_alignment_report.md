# DCOIR Airtable schema alignment report

- Project attachments referenced Skill State Registry, Plan Tasks, Plan Checkpoints, Schema Registry, Tracking Registry, Repo File Coverage Detail, and Retained Repo Manifest as if guaranteed, but current schema readback did not confirm those as default live tables.
- Current Airtable schema contains Delete Queue, DCOIR Lifecycle Ledger, Validation Evidence, Admin Registry, and Local Configuration Registry, which were not yet durable in skill instructions or GitHub source search.
- GitHub search for Delete Queue / DCOIR Lifecycle Ledger / Local Configuration Registry returned no repo hits before this patch.
- GitHub search for T99/cutover wording returned multiple dcoir skill SKILL.md files.
- Many installed dcoir SKILL.md files had marker comments before YAML frontmatter or no YAML frontmatter; this package normalizes changed SKILL.md files to start with YAML.
