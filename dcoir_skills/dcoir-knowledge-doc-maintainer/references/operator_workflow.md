# Operator workflow

1. Run `scripts/scan_project.py` to inventory current authoritative sources, any retained Knowledge-doc contents from `supporting_knowledge_docs.zip`, supporting assets, current hashes, collector-bundle tools, and any manifest-declared settings references relevant to workspace alignment. Do not assume the retired extracted folder `knowledge/supporting_knowledge_docs/` still exists or should be recreated.
2. Review the status report before writing docs.
3. If any code intent is unclear, ask targeted clarification questions or provide a targeted prompt to improve in-code documentation.
4. Gather only authoritative external facts from Microsoft Learn, Sysinternals, Elastic Docs, or official PowerShell docs.
5. When documenting execution or testing, reference the emitted runtime/downloaded filename the operator will use after repo-style or local bundle emission, while keeping the uploaded readable source name for provenance.
6. Draft the document content model.
7. Run `scripts/build_knowledge_docs.py` to create the stable `Knowledge - ## - Title.md.txt` set and one ZIP named `supporting_knowledge_docs.zip`.
8. Open every generated markdown file directly and inspect the title, source table, sections, tables, and footer note.
9. Return the ZIP plus operator next steps:
   - REPLACE the current `supporting_knowledge_docs.zip` file in retained supporting assets when replacing Knowledge docs and a ZIP delivery artifact is still required.
   - DO NOT recreate the retired extracted folder `knowledge/supporting_knowledge_docs/` unless the control plane explicitly restores that model.
   - DELETE any truly legacy `Knowledge - ## - *.docx` artifacts or out-of-band side copies only if they still exist outside the current GitHub-primary working line.
   - ONLY AFTER THAT, if the Knowledge-doc existence set changed, run the reinventory prompt.
