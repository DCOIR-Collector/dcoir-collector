# DCOIR Collector

GitHub-primary working source for the AFRICOM SOC DCOIR framework.

GitHub repo `malwaredevil/dcoir-collector` remains the sole working source for governed readable text files.
Project space is the bootstrap and runtime anchor. Airtable is the live todo authority.

## Working Model

- GitHub is the control plane and governed readable source.
- Airtable `Queue Control`, Airtable `Work Items`, and active Airtable `Plans` are the sole live todo authority for ordinary priority and resume order.
- GitHub todo files are retained only as retired migration notes or promoted history, not as the live queue.
- On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, start with `dcoir-session-resume` and then `dcoir-memory-preflight` before other substantive project work.
- After resume and memory-preflight, recover Airtable leftovers and read Airtable queue authority before choosing the next branch.
- GitHub Desktop remains an approved operator path for bulk local placement, extracted-file ingestion, and patch-bundle application.

## Queue Authority

Live queue priority should now come from Airtable, not GitHub todo files.
Use:
- `Queue Control` for the active branch decision
- `Work Items` for ranked queue rows and supersession
- `Plans` for structured active execution

Use GitHub only when the queue change needs to become promoted history or a durable workflow decision.
