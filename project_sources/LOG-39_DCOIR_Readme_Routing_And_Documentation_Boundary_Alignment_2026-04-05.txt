DCOIR Readme Routing And Documentation Boundary Alignment - 2026-04-05

Current state id: 2026-04-05-readme-routing-and-doc-boundary-alignment-v1

Purpose
- Record the documentation-navigation alignment pass across `dcoir-readme-maintainer`, `dcoir-knowledge-doc-maintainer`, `knowledge/DCOIR_Helper_Skills_Routing_Note.md`, `knowledge/README.md`, and `dcoir_skills/README.md`.

Decision summary
- Update `dcoir-readme-maintainer` so narrow routing-note refresh is explicitly in scope when current helper-skill inventory or workflow rules changed materially and the routing note would otherwise drift from the maintained README surfaces.
- Update `dcoir-knowledge-doc-maintainer` so its workflow references and reinventory prompt use GitHub-primary governed-readable-source wording consistently instead of older uploaded-project wording.
- Refresh the helper-skills routing note so the fast-routing matrix covers the current visible governed skill inventory more completely.
- Refresh `knowledge/README.md` and `dcoir_skills/README.md` so the maintained knowledge-doc lane, retained `supporting_knowledge_docs.zip` posture, grouped skill-wave delivery shape, and routing-note refresh rule are explicit in the local-guide surfaces.

Why it matters
- The documentation-and-knowledge todo lane called out both README-surface alignment and routing-note alignment as current work, and also asked for a clearer ownership boundary between the README maintainer and the broader knowledge-doc maintainer.
- The routing note still had a partial fast-routing matrix even though the current governed helper-skill inventory is broader and the grouped GitHub Desktop delivery posture is now part of the normal operating model.
- The knowledge-doc maintainer still had older uploaded-project wording in its references even after the maintained docs had been moved to GitHub-primary wording.

Validation notes
- The updated `dcoir-readme-maintainer` and `dcoir-knowledge-doc-maintainer` skill packages pass clean packaging validation.
- Readback review confirms that the refreshed routing note, `knowledge/README.md`, and `dcoir_skills/README.md` now match the current visible helper-skill set and grouped GitHub Desktop delivery posture.
- The documentation-boundary split is now clearer: README/navigation plus narrow routing-note alignment stays with `dcoir-readme-maintainer`, while broad knowledge-doc generation and retained knowledge-doc ZIP refresh stay with `dcoir-knowledge-doc-maintainer`.

Next immediate move
- Continue the coordinated campaign into the next prompt-pack assembly, triage-escalation, or large-file-intake helper-skill pass while keeping compatible fixes for the next meaningful grouped manual update/install wave.
