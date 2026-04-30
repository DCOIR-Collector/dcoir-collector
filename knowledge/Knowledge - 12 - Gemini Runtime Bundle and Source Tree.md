# Knowledge - 12 - Gemini Runtime Bundle and Source Tree

_Gemini stored-source runtime layout and compile path_

**Summary:** The Gemini bundle is compiled from maintained stored source. Inventory, attachments, and validation surfaces must stay aligned.

---

## Source model

The editable Gemini runtime source lives under:

```text
project_sources/gemini/bundle_source/
```

Generated or packaged outputs are delivery artifacts, not the editing surface.

---

## Runtime tree

| Path | Purpose |
| --- | --- |
| `00_START_HERE/` | Entry surfaces, quick start, attachment map |
| `01_GEMINI_AGENT_BUILD/` | Prime agent, sub-agents, generated index |
| `02_PRIME_AGENT_ATTACHMENTS/` | Generated release-ZIP attachment path populated from `knowledge/*.md` at package time |
| `Gemini_Bundle_Source_Manifest.json` | Required inventory and topology |

---

## Compile workflow

1. Edit maintained source files.
2. Update manifest/map/index surfaces when inventory changes.
3. Sync knowledge attachments from `knowledge/*.md`.
4. Run Gemini bundle validation/build.
5. Inspect generated bundle outputs.

---

## Coherence checks

After Gemini source changes, verify:

- generated attachment inventory matches maintained `knowledge/*.md` sources;
- manifest required files include the current inventory;
- attachment map explains each attachment;
- workflow required-surface checks match the inventory;
- validation scenarios still reflect runtime behavior.

---

## Boundaries

The bundle does not create unavailable retrieval or connector capability. Agent text must not claim enterprise search, internal lookup, or external grounding unless the runtime has that support surface.

---

## Cross-reference boundaries

- Use this page for source-tree layout and compile workflow.
- Use Knowledge 15 for attachment inventory and direct package-time generation rules.
- Use Knowledge 13 for agent topology.
- Use Knowledge 14 for Gemini output and command-lane discipline.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
