# Knowledge - 08 - Troubleshooting

Purpose
- This knowledge file provides a deliberately expanded, operationally explicit reference for bounded troubleshooting and failure handling.
- It is intentionally more verbose than earlier versions because the current major-version build assumes that underspecified knowledge files increase ambiguity, increase routing inconsistency, and increase the chance that the analyst will have to restate context that the bundle should already know.
- This file is written as a shared source-of-truth layer for both the maintained knowledge set and the synchronized Gemini prime-agent attachment set.

What this file is expected to do in the major-version build
- Spell out zero rows in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out tool availability ambiguity in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out syntax vs coverage issues in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out response-action command shape in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out collector package pitfalls in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out when not to overreact in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.

Operational detail
## 1. Zero Rows
This section is intentionally long-form. The goal is to make zero rows explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For zero rows, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that zero rows may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to zero rows, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 2. Tool Availability Ambiguity
This section is intentionally long-form. The goal is to make tool availability ambiguity explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For tool availability ambiguity, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that tool availability ambiguity may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to tool availability ambiguity, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 3. Syntax Vs Coverage Issues
This section is intentionally long-form. The goal is to make syntax vs coverage issues explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For syntax vs coverage issues, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that syntax vs coverage issues may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to syntax vs coverage issues, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 4. Response-Action Command Shape
This section is intentionally long-form. The goal is to make response-action command shape explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For response-action command shape, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that response-action command shape may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to response-action command shape, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 5. Collector Package Pitfalls
This section is intentionally long-form. The goal is to make collector package pitfalls explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For collector package pitfalls, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that collector package pitfalls may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to collector package pitfalls, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 6. When Not To Overreact
This section is intentionally long-form. The goal is to make when not to overreact explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For when not to overreact, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that when not to overreact may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to when not to overreact, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

Major-version bundle rule
- If a future maintainer changes behavior in a way that touches this topic, update this maintained knowledge file first or at the same time as the bundle source tree.
- Do not let the maintained knowledge set drift silently away from the Gemini attachment set.
- If a branch is important enough to affect tomorrow's functionality test, it is important enough to be spelled out here.
