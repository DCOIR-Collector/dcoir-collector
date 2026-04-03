# Post-Blocker Classification

After a blocker or failed attempt is successfully overcome, classify the lesson as one of:
- `one_off_only`
- `reusable_procedure_candidate`
- `reusable_limitation_candidate`
- `reusable_failure_signature_candidate`
- `reusable_helper_skill_or_process_doc_candidate`

## Classification intent
- `one_off_only`: the fix was specific to the moment and should stay only in local continuity notes
- `reusable_procedure_candidate`: a repeatable better lane or execution method was discovered
- `reusable_limitation_candidate`: a tool, connector, or environment boundary should be preserved explicitly
- `reusable_failure_signature_candidate`: the failure is recognizable and should map to a repeatable response
- `reusable_helper_skill_or_process_doc_candidate`: the lesson belongs in helper-skill instructions or governed workflow docs rather than canonical task memory alone

## Promotion posture
- do not silently persist
- stage a promotion-ready candidate with the blocker signature, failed attempt summary, successful mitigation, and why the lesson appears reusable
