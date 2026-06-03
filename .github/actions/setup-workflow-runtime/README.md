# setup-workflow-runtime

Composite action scaffold for mechanical workflow runtime setup evidence.

Contract:

- Callers keep triggers, permissions, secrets, runner choice, artifacts, and report paths visible in the workflow file.
- The action may prepare runtime prerequisites and emit caller-visible setup evidence.
- The action must not directly reference `secrets.*` or perform repository writes.
- Compensating evidence is the caller-visible step name, stdout contract lines, and optional `GITHUB_STEP_SUMMARY` content.
