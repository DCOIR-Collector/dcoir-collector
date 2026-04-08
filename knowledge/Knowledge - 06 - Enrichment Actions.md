# Knowledge - 06 - Enrichment Actions

Purpose
- This knowledge file provides a deliberately expanded, operationally explicit reference for enrichment session action guide.
- It is intentionally more verbose than earlier versions because the current major-version build assumes that underspecified knowledge files increase ambiguity, increase routing inconsistency, and increase the chance that the analyst will have to restate context that the bundle should already know.
- This file is written as a shared source-of-truth layer for both the maintained knowledge set and the synchronized Gemini prime-agent attachment set.

What this file is expected to do in the major-version build
- Spell out enrich start/add/finalize semantics in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out session reuse in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out artifact retrieval in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out Sigcheck/ListDlls/Strings/Streams/LogText/LogRaw in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how to chain actions without losing scope in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.

Operational detail
## 1. Enrich Start/Add/Finalize Semantics
This section is intentionally long-form. The goal is to make enrich start/add/finalize semantics explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For enrich start/add/finalize semantics, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that enrich start/add/finalize semantics may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to enrich start/add/finalize semantics, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 2. Session Reuse
This section is intentionally long-form. The goal is to make session reuse explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For session reuse, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that session reuse may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to session reuse, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 3. Artifact Retrieval
This section is intentionally long-form. The goal is to make artifact retrieval explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For artifact retrieval, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that artifact retrieval may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to artifact retrieval, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 4. Sigcheck/Listdlls/Strings/Streams/Logtext/Lograw
This section is intentionally long-form. The goal is to make Sigcheck/ListDlls/Strings/Streams/LogText/LogRaw explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For Sigcheck/ListDlls/Strings/Streams/LogText/LogRaw, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that Sigcheck/ListDlls/Strings/Streams/LogText/LogRaw may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to Sigcheck/ListDlls/Strings/Streams/LogText/LogRaw, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 5. How To Chain Actions Without Losing Scope
This section is intentionally long-form. The goal is to make how to chain actions without losing scope explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how to chain actions without losing scope, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how to chain actions without losing scope may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how to chain actions without losing scope, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

Major-version bundle rule
- If a future maintainer changes behavior in a way that touches this topic, update this maintained knowledge file first or at the same time as the bundle source tree.
- Do not let the maintained knowledge set drift silently away from the Gemini attachment set.
- If a branch is important enough to affect tomorrow's functionality test, it is important enough to be spelled out here.
