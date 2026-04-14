# README FIRST

This source tree is the governed editable runtime source for the major-version Gemini bundle. The purpose of this README is not just to say where the files are. The purpose is to force future edits to respect the explicit topology contract, the explicit knowledge-sync path, the explicit attachment-inventory contract, and the explicit high-verbosity design rule adopted for this major-version build.

## Major-version writing rule

The parent agent, the sub-agents, and the shared attachment set in this bundle are intentionally verbose. The design assumption is that underspecified agent fields and underspecified shared knowledge pages create routing ambiguity, command inconsistency, attachment drift, and unpredictable behavior. Therefore, when a branch matters operationally, the file should spell out the branch instead of hinting at it.

Do not aggressively summarize.
Do not compress away edge cases.
Do not rely on shorthand when a more explicit instruction materially reduces ambiguity.

## What to edit

- Edit `knowledge/*.md` when the shared knowledge layer changes.
- Edit `01_GEMINI_AGENT_BUILD/*.md.txt` when parent or sub-agent behavior changes.
- Edit `00_START_HERE/*.md.txt` when the operator-facing build guidance or attachment inventory changes.
- Edit the manifest when the topology or required-file contract changes.

## Topology rule

The manifest is the explicit source of truth for the active topology. A file dropped into the folder is not automatically an active sub-agent. It becomes active only when the manifest lists it.

## Knowledge sync rule

The build wrapper syncs the maintained `knowledge/*.md` files into `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` before validation and compile. The maintained knowledge files are therefore the editable knowledge source of truth for shared content in this major-version build.

## Attachment-inventory rule

The attachment map, the maintained `knowledge/*.md` set, the synced `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` set, and the manifest required-files inventory must stay synchronized. If the shared attachment set changes, update all four surfaces in the same bounded change set so manual build, validate-on-push, and compile all continue to agree about what the bundle is supposed to ship.
