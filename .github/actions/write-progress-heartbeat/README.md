# write-progress-heartbeat

Composite action scaffold for writing a caller-owned progress heartbeat file.

Contract:

- Callers own heartbeat path selection, report path shape, and polling/readback semantics.
- The action only writes the supplied status/detail JSON to the requested path.
- The action must not perform network calls, repository writes, or secret access.
- Compensating evidence is the caller-visible step name, stdout output path, and generated heartbeat file.
