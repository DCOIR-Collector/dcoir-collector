# Knowledge - 09 - FAQ

Purpose
- This knowledge file provides a deliberately expanded, operationally explicit reference for operator faq.
- It is intentionally more verbose than earlier versions because the current major-version build assumes that underspecified knowledge files increase ambiguity, increase routing inconsistency, and increase the chance that the analyst will have to restate context that the bundle should already know.
- This file is written as a shared source-of-truth layer for both the maintained knowledge set and the synchronized Gemini prime-agent attachment set.

What this file is expected to do in the major-version build
- Spell out why not jump to containment in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out why the collector may be better than another query in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out why a targeted collect may be enough in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how to use the bundle in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how to ask the agent to parse IOCs in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.

Operational detail
## 1. Why Not Jump To Containment
This section is intentionally long-form. The goal is to make why not jump to containment explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For why not jump to containment, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that why not jump to containment may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to why not jump to containment, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 2. Why The Collector May Be Better Than Another Query
This section is intentionally long-form. The goal is to make why the collector may be better than another query explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For why the collector may be better than another query, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that why the collector may be better than another query may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to why the collector may be better than another query, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 3. Why A Targeted Collect May Be Enough
This section is intentionally long-form. The goal is to make why a targeted collect may be enough explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For why a targeted collect may be enough, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that why a targeted collect may be enough may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to why a targeted collect may be enough, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 4. How To Use The Bundle
This section is intentionally long-form. The goal is to make how to use the bundle explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how to use the bundle, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how to use the bundle may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how to use the bundle, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 5. How To Ask The Agent To Parse Iocs
This section is intentionally long-form. The goal is to make how to ask the agent to parse IOCs explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how to ask the agent to parse IOCs, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how to ask the agent to parse IOCs may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how to ask the agent to parse IOCs, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

Major-version bundle rule
- If a future maintainer changes behavior in a way that touches this topic, update this maintained knowledge file first or at the same time as the bundle source tree.
- Do not let the maintained knowledge set drift silently away from the Gemini attachment set.
- If a branch is important enough to affect tomorrow's functionality test, it is important enough to be spelled out here.
