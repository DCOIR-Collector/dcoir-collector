# Knowledge - 02 - Elastic Quick Start

_Endpoint response-console usage versus local workstation usage_

**Summary:** Use this page when you need quick examples for endpoint-side DCOIR execution in Elastic Defend, while keeping those examples clearly separate from local testing commands.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; DCOIR_Collector.314.ps1.txt; LOG-01_DCOIR_Todo_Log.txt |
| Official external sources | Elastic Docs / endpoint response actions |
| Scope note | Examples are grounded in the collector quick next-step output and the project workflow rule that endpoint instructions use response-action syntax. |

## Execution context split

- Use Elastic Defend response-action syntax for endpoint instructions.
- Use PowerShell commands for local workstation and local regression tasks.
- Do not paste a local-only command directly into the response console without the response-action wrapper.
- Do not add the Elastic response-console wrapper when running the same command on a local workstation or test repo.

## Endpoint-side example commands

| Intent | Example |
| --- | --- |
| Run TCP enrichment | execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment" |
| Run raw Security-log enrichment | execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-start-lograw -Target Security" --comment "Run DCOIR raw Security log enrichment" |
| Cleanup current DCOIR run | execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector" |

## When to use Elastic quick start

- The endpoint already has the collector package staged and you want a controlled DCOIR action from the response console.
- You are following the collector's Elastic-facing next-step hints after a collect or enrich stage.
- You need one action at a time, not broad free-form shell work.

## Guardrails

- Keep command syntax explicit and minimal.
- Preserve the distinction between endpoint collection activity and analyst workstation analysis activity.
- Treat the response console as the place for endpoint actions; treat the local repo as the place for development and regression.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
