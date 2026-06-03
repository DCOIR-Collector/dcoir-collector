# write-chatgpt-report-section

Composite action scaffold for creating a standard `chatgpt-workflow-report-section` markdown payload.

Contract:

- Callers own the report content, title, output path, artifact upload, and readback expectations.
- The action only writes the supplied markdown section to the requested path.
- The action must not perform network calls, repository writes, or secret access.
- Compensating evidence is the caller-visible step name, stdout output path, and generated markdown file.
