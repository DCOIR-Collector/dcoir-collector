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
