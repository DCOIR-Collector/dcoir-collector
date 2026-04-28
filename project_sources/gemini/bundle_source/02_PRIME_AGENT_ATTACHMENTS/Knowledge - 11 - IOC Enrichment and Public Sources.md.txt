# Knowledge - 11 - IOC Enrichment and Public Sources

Purpose
- This file defines the approved public-source enrichment policy for evidence-grounded IOCs in the DCOIR workflow.
- The goal is to enrich domains, IPs, URLs, hashes, signers, and related indicators without letting outside context override case evidence.

Core rule
- Public IOC enrichment is corroboration and context, not case truth.
- Tier 0 remains case artifacts.
- Tier 1 remains authoritative vendor or government sources for semantics, legitimacy, and exploit status.

Approved public sources that are freely available and readable

Domains and URLs
- urlscan: for webpage and domain context when a domain or URL is grounded in case evidence
- URLhaus: for malicious URL corroboration and known-bad URL context
- Cisco Talos Reputation Center: for domain, URL, and IP reputation context
- Google Safe Browsing: for website danger or unsafe-browsing context when available

IP addresses
- AbuseIPDB: for corroborative abuse reports and historic suspicion context
- Cisco Talos Reputation Center: for IP reputation context

File hashes
- MalwareBazaar: for malware-sample and hash corroboration
- Cisco Talos File Reputation: for SHA256-centered file context

Authoritative context sources
- Microsoft Learn
- Elastic documentation
- CISA advisories and KEV
- MITRE ATT&CK
- CVE.org
- NIST NVD
- vendor documentation directly tied to the observed artifact or product

Use rules
1. Only enrich evidence-grounded indicators.
2. State the provenance of the indicator before the lookup.
3. Prefer authoritative semantic context first.
4. Treat public reputation as support only.
5. If a result is mixed, stale, or weak, say so explicitly.
6. Do not let a single public reputation result prove compromise.
7. Keep the lookup result in the external-context lane and tie it back to the case question.

Indicator-type guidance
- Domain: use urlscan, URLhaus, Talos, and authoritative vendor context as needed.
- URL: use URLhaus, urlscan, Talos, and Safe Browsing where useful.
- IP: use AbuseIPDB and Talos as corroboration.
- Hash: use MalwareBazaar and Talos File Reputation as corroboration.
- Signer or product legitimacy: prefer vendor documentation, Microsoft, Elastic, and known official vendor sources first.

## Evidence-grounded IOC posture

Public-source enrichment is a support lane, not a truth engine. Outside context may help interpret a grounded indicator, but it cannot replace the case evidence that made the indicator worth caring about in the first place.

## Source tiers and how to treat them

### Tier 0: case artifacts
Case artifacts are the primary truth surface.

### Tier 1: authoritative semantic or vendor context
Vendor documentation, Microsoft Learn, Elastic docs, CISA advisories and KEV, MITRE ATT&CK, CVE.org, NVD, and product-owner sources help answer meaning questions.

### Tier 2: public corroboration and reputation
Public reputation and OSINT-style sources can help with corroboration and infrastructure context, but must remain subordinate to case evidence and authoritative context.

## Provenance before lookup

Before any enrichment, the operator should be able to restate the exact indicator, where it came from, whether it is raw or normalized, whether it is already grounded in case evidence or merely context from another document, and what question the lookup is supposed to answer.

## Indicator classes and what to watch for

### Domains and URLs
Domain and URL enrichment helps with infrastructure context, page visibility, known-bad corroboration, and related semantics. It does not prove execution, compromise, or successful communication by itself.

### IP addresses
IP enrichment may highlight abuse history or reputation context. It is useful when tied to a case-grounded connection question.

### File hashes
Hash enrichment can be powerful when the hash is truly grounded in the case.

## Mixed or stale results

Not every external result is strong. The operator should say plainly when a result is mixed, stale, weak, disputed, or context-rich but not case-dispositive. Weak public context can still be useful when framed properly.

## Writing the result back into the case

A good enrichment note should say what was looked up, why it was looked up, what external context was found, how strong or weak that context is, how it affects the current case question, and what it still does not prove.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

