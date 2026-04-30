# Knowledge - 11 - IOC Enrichment and Public Sources

_Public-source context for evidence-grounded indicators_

**Summary:** Use public IOC enrichment only to support or contextualize case-grounded indicators. External reputation does not replace case evidence.

---

## Core rule

Public enrichment is corroboration and context, not case truth.

Do not look up indicators that are not grounded in case evidence or an explicitly identified investigative question.

---

## Source tiers

| Tier | Source type | Use |
| --- | --- | --- |
| Tier 0 | Case artifacts | Primary truth surface |
| Tier 1 | Vendor, government, product, and vulnerability sources | Meaning, legitimacy, exploit/status context |
| Tier 2 | Public reputation and OSINT-style services | Corroboration and infrastructure context |

---

## Approved source examples

| Indicator | Useful sources |
| --- | --- |
| Domain / URL | urlscan, URLhaus, Cisco Talos, Google Safe Browsing where available |
| IP address | AbuseIPDB, Cisco Talos |
| File hash | MalwareBazaar, Cisco Talos File Reputation |
| Vulnerability / technique | CISA KEV, CVE.org, NIST NVD, MITRE ATT&CK, vendor documentation |
| Product or signer legitimacy | Microsoft Learn, Elastic docs, vendor documentation, official product sources |

---

## Before lookup

State:

- the exact indicator;
- where it came from;
- whether it is raw or normalized;
- what question the lookup should answer;
- how the result will affect the next action.

---

## Interpretation rules

- A single reputation hit does not prove compromise.
- Weak, stale, mixed, or disputed results must be labeled as such.
- Public context must be tied back to the case artifact that justified the lookup.
- Absence of public reputation does not prove benignity.

---

## Write-back format

Record:

1. indicator and provenance;
2. source checked;
3. result strength;
4. relevance to the case question;
5. what the result does not prove;
6. next evidence-producing action, if any.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
