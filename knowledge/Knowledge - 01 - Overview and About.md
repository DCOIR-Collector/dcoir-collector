# Knowledge - 01 - Overview and About

Purpose
- This knowledge file provides a deliberately expanded, operationally explicit reference for DCOIR overview, bundle scope, and workflow context.
- It is intentionally more verbose than earlier versions because the current major-version build assumes that underspecified knowledge files increase ambiguity, increase routing inconsistency, and increase the chance that the analyst will have to restate context that the bundle should already know.
- This file is written as a shared source-of-truth layer for both the maintained knowledge set and the synchronized Gemini prime-agent attachment set.

What this file is expected to do in the major-version build
- Spell out what DCOIR is in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out what the collector does in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out what the Gemini bundle does in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how the workflow moves from alert to collection to artifact review to synthesis in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out why evidence discipline matters in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.
- Spell out how tonight's build and tomorrow's functionality test fit together in enough detail that the analyst or the Gemini bundle can apply it without having to guess what the author intended.

Operational detail
## 1. What Dcoir Is
This section is intentionally long-form. The goal is to make what DCOIR is explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For what DCOIR is, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that what DCOIR is may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to what DCOIR is, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 2. What The Collector Does
This section is intentionally long-form. The goal is to make what the collector does explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For what the collector does, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that what the collector does may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to what the collector does, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 3. What The Gemini Bundle Does
This section is intentionally long-form. The goal is to make what the Gemini bundle does explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For what the Gemini bundle does, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that what the Gemini bundle does may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to what the Gemini bundle does, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 4. How The Workflow Moves From Alert To Collection To Artifact Review To Synthesis
This section is intentionally long-form. The goal is to make how the workflow moves from alert to collection to artifact review to synthesis explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how the workflow moves from alert to collection to artifact review to synthesis, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how the workflow moves from alert to collection to artifact review to synthesis may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how the workflow moves from alert to collection to artifact review to synthesis, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 5. Why Evidence Discipline Matters
This section is intentionally long-form. The goal is to make why evidence discipline matters explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For why evidence discipline matters, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that why evidence discipline matters may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to why evidence discipline matters, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

## 6. How Tonight'S Build And Tomorrow'S Functionality Test Fit Together
This section is intentionally long-form. The goal is to make how tonight's build and tomorrow's functionality test fit together explicit enough that it can be used as operational guidance rather than as a vague reminder. When the analyst or the Gemini bundle consults this file, the file should already explain the purpose of the branch, the conditions under which the branch should be used, the exact kinds of evidence that support the branch, the mistakes that should be avoided, and the follow-up actions that become appropriate if the branch is confirmed.

For how tonight's build and tomorrow's functionality test fit together, the operator should expect the workflow to state what is known, what is still unknown, why the next step is being recommended, what narrower alternative still exists, and what evidence would make the current path unnecessary. The workflow should not hide behind short reminders or generic wording.

The current major-version bundle also assumes that how tonight's build and tomorrow's functionality test fit together may need to be discussed across multiple surfaces: the collector script, the harness or validation workflows, the Gemini parent agent, one or more Gemini sub-agents, and leadership-facing write-ups. Because of that, this file deliberately restates the same concept from multiple angles: execution, interpretation, bounded confidence, and testing.

When writing or reviewing functionality tied to how tonight's build and tomorrow's functionality test fit together, prefer explicit conditions, explicit examples, explicit command-lane distinctions, and explicit truth boundaries. Do not summarize away caveats that materially affect safety, branch choice, or operator trust.

Major-version bundle rule
- If a future maintainer changes behavior in a way that touches this topic, update this maintained knowledge file first or at the same time as the bundle source tree.
- Do not let the maintained knowledge set drift silently away from the Gemini attachment set.
- If a branch is important enough to affect tomorrow's functionality test, it is important enough to be spelled out here.
