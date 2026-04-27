# DCOIR Collector

Airtable-first DCOIR workspace with GitHub retained as governed source/readback for the AFRICOM SOC DCOIR framework.

GitHub repo `malwaredevil/dcoir-collector` remains the governed readable source for retained repository files and helper-skill source. Project space is the bootstrap/runtime anchor. Airtable is the live operational authority for queue order, branch priority, active plans, plan tasks, session carry-forward, operator preferences, validation catalog state, and stateful helper-skill durable memory where tables exist.

## Working Model

- GitHub is the governed readable source for retained project files, helper-skill source, release history, and promoted workflow decisions.
- Airtable `Queue Control`, `Work Items`, active `Plans`, and `Plan Tasks` are the sole live todo authority for ordinary priority, execution order, and resume state.
- `Retained Repo Manifest` is the final-state keep-set and no-missing-reference validation surface for repo-reduction work.
- GitHub todo files are retained only as retired migration notes or promoted history, not as the live queue, unless Airtable explicitly reauthorizes them.
- On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, start with `dcoir-session-resume` and then `dcoir-memory-preflight` before other substantive project work.
- After resume and memory-preflight, recover Airtable leftovers and read Airtable queue authority before choosing the next branch.
- GitHub Desktop remains an approved operator path for bulk local placement, extracted-file ingestion, and patch-bundle application.

## Current-State and Final-State Authority

- For normal startup, resume, queue selection, administrative control, and active-plan recovery, use Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`, then Airtable `Session Checkpoints`, `Queue Control`, `Work Items`, active `Plans`, `Plan Tasks`, `Operator Preferences`, and relevant helper-memory tables.
- `project_sources/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/CP-02_DCOIR_Change_Log.txt` are retained source/promoted-history references, not normal startup authority. Read them only for repo source-role resolution, packaging/readback, promoted-history comparison, explicit repo-source inspection, or final keep/delete review.
- If final repo reduction later removes or relocates a previously referenced file, do not invent a replacement. Use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Retained Repo Manifest`, `Queue Control`, `Work Items`, `Plans`, and `Plan Tasks` to establish live operating state and report the missing retained source as a validation finding.
- Before adding or preserving a repo path reference in retained documentation, check whether that path is current, retained, or clearly historical.

## Queue Authority

Live queue priority should now come from Airtable, not GitHub todo files.
Use:

- `Queue Control` for the active branch decision
- `Work Items` for ranked queue rows and supersession
- `Plans` and `Plan Tasks` for structured active execution
- `Plan Checkpoints` and `Session Checkpoints` for durable resume/handoff context

Use GitHub only when the queue change needs to become promoted history or a durable workflow decision.
