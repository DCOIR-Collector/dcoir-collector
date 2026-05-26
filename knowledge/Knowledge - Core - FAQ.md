# Knowledge - Core - FAQ

_Short answers to recurring DCOIR operator questions_

**Summary:** Fast answers for authority, command lanes, collector use, EXE behavior, Gemini attachments, and validation.

---

## Authority and source

| Question | Answer |
| --- | --- |
| Are knowledge docs authoritative? | No. They support operators and Gemini but do not override Project Instructions, governed GitHub source, implemented source behavior, or Supabase `ircore` operational records. |
| Which files should be edited? | Edit `knowledge/*.md` as the maintained source. Gemini `.md.txt` attachment files are generated runtime surfaces inside the release ZIP. |
| Why do old references mention `.ps1.txt` or `.cmd.txt`? | Older bundle/readable-text surfaces used suffixes more heavily. Current governed runtime files use native repo paths. |
| Is `DCOIR_Collector.zip` source of truth? | No. It is a retained supporting asset for delivery/execution support. |

---

## Execution lanes

| Question | Answer |
| --- | --- |
| When do I use Elastic endpoint shell execution? | Use it only for endpoint response-console execution. |
| When do I use local PowerShell? | Use it for workstation testing, harness runs, and repo-local validation. |
| What is the biggest command mistake? | Mixing endpoint response syntax with local PowerShell syntax. |
| Is there a default CMD harness wrapper? | No current default CMD wrapper is part of the governed guidance. Use `run_DCOIR_Tests.ps1`. |

---

## Collection and enrichment

| Question | Answer |
| --- | --- |
| When should I use Tier 1? | Use Tier 1 for a first-pass host evidence package when current evidence is insufficient. |
| When should I use Tier 2? | Use Tier 2 only when a specific unresolved question needs deeper persistence/configuration context. |
| When is retrieval better than more collection? | When current output already points to a specific artifact likely to answer the next question. |
| Why one enrichment action at a time? | It keeps each action tied to one follow-up question. |

---

## EXE behavior

| Question | Answer |
| --- | --- |
| Is the optional EXE a separate product line? | No. It is a packaged execution form of the same collector source. |
| Can EXE FailureGates differ from PS1? | Yes. EXE wrapping can hide native PowerShell bind-reject diagnostics. Use EXE-aware interpretation. |
| Does EXE build success prove runtime correctness? | No. Runtime behavior is proven by harness suites and output/artifact checks. |

---

## Gemini and attachments

| Question | Answer |
| --- | --- |
| Why does Gemini need knowledge attachments? | They provide stable operational context for routing, output interpretation, and command-lane discipline. |
| What happens when attachment files change? | Update maintained source, attachment map, manifest, and workflow checks together; release packaging regenerates attachment files from `knowledge/*.md`. |
| Where does validation and receipt state belong? | Supabase `ircore` stores operational validation rules, consultation receipts, and readback state. GitHub remains source and packaging authority. |

---

## Review and evidence

| Question | Answer |
| --- | --- |
| What should I read first after Tier 1? | Merged baseline report, metadata, final artifacts, then high-signal referenced artifacts. |
| Are metadata reports evidence? | They are workflow context. They can support interpretation but are not automatically proof of suspicious activity. |
| What does public IOC enrichment provide? | Context and corroboration only; it does not replace case evidence. |

---

## FAQ boundary

FAQ answers are intentionally short. When the answer requires procedure, feature detail, EXE nuance, or output-contract interpretation, follow the owner page instead of expanding this FAQ into duplicate guidance.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.