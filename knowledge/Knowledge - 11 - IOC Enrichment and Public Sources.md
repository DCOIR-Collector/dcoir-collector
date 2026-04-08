# Knowledge - 11 - IOC Enrichment and Public Sources

Purpose
- This knowledge file provides a deliberately expanded, operationally explicit reference for IOC parsing and evidence-grounded public enrichment.
- It is intentionally more verbose than earlier versions because the current major-version build assumes that underspecified knowledge files increase ambiguity, increase routing inconsistency, and increase the chance that the analyst will have to restate context that the bundle should already know.
- This file is written as a shared source-of-truth layer for both the maintained knowledge set and the synchronized Gemini prime-agent attachment set.

What this file is expected to do in the major-version build
- Spell out mixed-format IOC extraction in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out indicator typing in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out OSINT boundaries in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out KQL/ESQL/OSQuery/response-action follow-up generation in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out public source hierarchy in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how to keep provenance intact in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.

Operational detail
## 1. Mixed-Format Ioc Extraction
This section is intentionally long-form. The goal is to make mixed-format IOC extraction explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For mixed-format IOC extraction, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that mixed-format IOC extraction may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to mixed-format IOC extraction, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 2. Indicator Typing
This section is intentionally long-form. The goal is to make indicator typing explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For indicator typing, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that indicator typing may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to indicator typing, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 3. Osint Boundaries
This section is intentionally long-form. The goal is to make OSINT boundaries explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For OSINT boundaries, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that OSINT boundaries may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to OSINT boundaries, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 4. Kql/Esql/Osquery/Response-Action Follow-Up Generation
This section is intentionally long-form. The goal is to make KQL/ESQL/OSQuery/response-action follow-up generation explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For KQL/ESQL/OSQuery/response-action follow-up generation, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that KQL/ESQL/OSQuery/response-action follow-up generation may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to KQL/ESQL/OSQuery/response-action follow-up generation, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 5. Public Source Hierarchy
This section is intentionally long-form. The goal is to make public source hierarchy explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For public source hierarchy, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that public source hierarchy may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to public source hierarchy, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 6. How To Keep Provenance Intact
This section is intentionally long-form. The goal is to make how to keep provenance intact explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how to keep provenance intact, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how to keep provenance intact may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how to keep provenance intact, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

Major-version bundle rule
- If a future maintainer changes behavior in a way that touches this topic, update this maintained knowledge file first or at the same time as the bundle source tree.
- Do not let the maintained knowledge set drift silently away from the Gemini attachment set.
- If a branch is important enough to affect tomorrow's functionality test, it is important enough to be spelled out here.
