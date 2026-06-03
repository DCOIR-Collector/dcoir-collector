# upload-chatgpt-artifact

Composite action scaffold for standardized ChatGPT workflow artifact upload.

Contract:

- Callers supply artifact name, path, and retention explicitly.
- Callers keep report paths and artifact semantics visible in the workflow file.
- The action must not infer secret names or mutate repository content.
- Compensating evidence is stdout showing artifact name/path/retention plus the GitHub-recorded artifact.
