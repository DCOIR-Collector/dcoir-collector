# Preflight Task Families

Use memory preflight before execution for these task families:
- GitHub create/update/delete work
- grouped multi-file repo edits
- structural renames or repo layout changes
- control-plane updates
- bundle generation and packaging
- skill repair, maintenance, or regression
- coordinated multi-skill patch campaigns
- GitHub Desktop manual repo-update bundle preparation or grouped governed pushes
- repeated workflows with known prior friction

Use memory preflight again after blocker recovery when the resolved lesson could improve:
- a repeatable workflow
- a reusable procedure candidate
- a reusable limitation candidate
- a reusable failure-signature candidate
- a reusable helper-skill or process-document candidate

## Dynamic helper-skill routing family

When a task might map to a specialist DCOIR helper skill, query Airtable table `dcoir-memory-preflight` for `SKILLROUTE-*` rows before recommending a lane. Treat those rows as the live installed-skill routing catalog. Do not rely on a static skill list bundled inside this skill.

Use this family for:
- skill creation, update, package, validation, or troubleshooting
- GitHub Desktop lane and local repository friction
- Airtable schema, table, field, default, or registry work
- repo packaging or GitHub Desktop bundle generation
- source-authority, drift, governance, validation, collector QA, knowledge-doc, prompt-pack, release-scope, and skill-regression work

Output the matching `SKILLROUTE-*` row IDs and the specialist skill to invoke or pair with the preflight.
