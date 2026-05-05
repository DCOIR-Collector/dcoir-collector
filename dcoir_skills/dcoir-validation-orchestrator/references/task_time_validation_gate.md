# Task-time Validation Gate

Use this reference when a DCOIR task may need validation, verification, evidence, readiness language, install/readback confirmation, or regression planning.

## Fire this gate when
- a response will claim something is ready, valid, installed, verified, complete, package-clean, schema-safe, regression-covered, or safe to use;
- a helper skill is patched, packaged, installed, read back, or promoted to source/parity;
- a ZIP/package/bundle/artifact is created or corrected;
- Airtable/GitHub/workflow/local-tool execution needs evidence or readback;
- the operator reports a malformed package, missing marker, stale readback, failed workflow, or incomplete verification;
- a cleanup/migration/delete/schema/task changes live operational state;
- a blocker is recovered and should produce a repeatable test, guardrail, or evidence requirement.

## Compact output
Return only:
1. validation target;
2. phase: pre-live, post-patch, failed-run, routine, install-readback, or evidence-gap;
3. evidence available;
4. evidence missing;
5. minimum required checks;
6. companion skills to invoke;
7. Airtable Validation Evidence/Test Cases or helper-memory update need;
8. safest readiness statement allowed.

## Readiness language rules
- Say `validated` only when the relevant checks actually ran or readback evidence exists.
- Say `package-valid` only after package validation or structural inspection passes.
- Say `installed marker confirmed` only after installed skill readback shows the expected marker.
- Say `bounded validation only` when full execution was unavailable.
- Do not treat successful creation of an artifact as proof that the artifact was installed or live.

## Companion skill routing
- Use dcoir-memory-preflight when routing or reusable lesson capture applies.
- Use dcoir-decision-policy for proceed/ask/stop, approval gates, or readiness wording.
- Use dcoir-airtable-schema-cache for Airtable schema/readback-dependent validation.
- Use dcoir-repo-packager for package-shape/ZIP/bundle validation.
- Use dcoir-github-desktop-lane-advisor for local operator-tool or GitHub Desktop verification.
- Use dcoir-session-manager when validation status should be checkpointed or carried forward.
