# Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance

_Gemini knowledge attachment inventory and maintenance rules_

**Summary:** The Gemini attachment set is synced from maintained `knowledge/*.md` files and must stay aligned with the manifest, attachment map, and workflow checks.

---

## Attachment model

| Surface | Role |
| --- | --- |
| `knowledge/*.md` | Maintained editable source |
| `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` | Gemini runtime attachment copies |
| `Agent_Attachment_Map.md.txt` | Human/runtime inventory explanation |
| `Gemini_Bundle_Source_Manifest.json` | Required file inventory |
| GitHub Actions workflows | Validation and required-surface enforcement |

---

## Current inventory

The maintained set contains 17 knowledge pages. Knowledge 16 covers optional EXE usage and runtime behavior. Knowledge 17 covers collector features and output contract reference.

---

## Update rule

When the knowledge set changes:

1. Update maintained `knowledge/*.md` source.
2. Sync `.md.txt` attachment copies.
3. Update the attachment map.
4. Update the manifest required-files list.
5. Update GitHub Actions required-surface checks.
6. Add or update Airtable validation rows if runtime behavior changed.

---

## Validation expectations

After attachment changes, verify:

- every required attachment exists;
- maintained source and attachment copies match;
- manifest and attachment map include the same inventory;
- workflow checks enforce the current count and required files;
- agent instructions reference the correct attachment surfaces;
- no stale duplicated filler or meta-writing text remains.

---

## Grounding boundary

Attachments can provide stable project context. They do not create live connector access, enterprise retrieval, or web-grounding capability by themselves.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
