$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$patch = @'
from pathlib import Path

pareto_path = Path("scripts/openrouter_pr_review_pareto_context.py")
selftest_path = Path("scripts/openrouter_pr_review_pareto_context_selftest.py")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    pareto_path,
    '''FILE_WRITE_PATH_DETAIL = (\n    "dynamic path segments reached a file write; verify or add segment validation, "\n    "normalization, and root containment checks before writing or staging files"\n)\n''',
    '''FILE_WRITE_PATH_DETAIL = (\n    "dynamic path segments reached a file write; verify or add segment validation, "\n    "normalization, and root containment checks before writing or staging files"\n)\nPYTHON_DYNAMIC_EXEC_LABEL = "Python eval/exec dynamic code execution"\nPYTHON_DYNAMIC_EXEC_DETAIL = (\n    "eval/exec can execute caller-controlled Python expressions; remove dynamic evaluation "\n    "or replace it with ast.literal_eval, a constrained parser, or an explicit allowlist"\n)\nPYTHON_DYNAMIC_EXEC_CALL_NAMES = frozenset(\n    {"eval", "exec", "builtins.eval", "builtins.exec", "__builtins__.eval", "__builtins__.exec"}\n)\n''',
)

replace_once(
    pareto_path,
    '''\ndef python_is_scope_boundary(text: str) -> bool:\n''',
    '''\ndef python_dynamic_exec_call_name(text: str) -> str | None:\n    if "eval" not in text and "exec" not in text:\n        return None\n    try:\n        module = ast.parse(text.lstrip())\n    except SyntaxError:\n        return None\n    for node in ast.walk(module):\n        if not isinstance(node, ast.Call):\n            continue\n        call_name = python_call_name(node.func)\n        if call_name in PYTHON_DYNAMIC_EXEC_CALL_NAMES:\n            return call_name\n    return None\n\n\ndef detect_python_dynamic_exec_sentinels(diff: str) -> list[hardened.RiskSentinel]:\n    sentinels: list[hardened.RiskSentinel] = []\n    for diff_line in iter_python_diff_lines_with_context(diff):\n        if not diff_line.is_added or diff_line.inside_multiline_string:\n            continue\n        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):\n            continue\n        call_name = python_dynamic_exec_call_name(diff_line.text)\n        if not call_name:\n            continue\n        sentinels.append(\n            hardened.RiskSentinel(\n                path=diff_line.path,\n                line=diff_line.line,\n                label=PYTHON_DYNAMIC_EXEC_LABEL,\n                detail=(\n                    f"{call_name} can execute caller-controlled Python code; "\n                    "replace dynamic evaluation with literal parsing, a constrained parser, or an explicit allowlist"\n                ),\n                text=diff_line.text,\n            )\n        )\n    return sentinels\n\n\ndef python_is_scope_boundary(text: str) -> bool:\n''',
)

replace_once(
    pareto_path,
    '''    combined = [\n        *detect_python_file_write_path_sentinels(diff),\n        *[\n''',
    '''    combined = [\n        *detect_python_file_write_path_sentinels(diff),\n        *detect_python_dynamic_exec_sentinels(diff),\n        *[\n''',
)

replace_once(
    pareto_path,
    '''            "Python specialization: inspect unsafe deserialization, subprocess/shell execution, tar/zip/archive extraction, "\n''',
    '''            "Python specialization: inspect unsafe deserialization, eval/exec/dynamic code evaluation, subprocess/shell execution, tar/zip/archive extraction, "\n''',
)

replace_once(
    selftest_path,
    '''assert captured_max_anchors == [None]\nassert len(bounded_path_sentinels) == 3\nassert bounded_path_sentinels[0].label == mod.FILE_WRITE_PATH_LABEL\n\n\nclass FakeGitHubClient:\n''',
    '''assert captured_max_anchors == [None]\nassert len(bounded_path_sentinels) == 3\nassert bounded_path_sentinels[0].label == mod.FILE_WRITE_PATH_LABEL\n\npython_dynamic_exec_sentinels = mod.detect_risk_sentinels(\n    """diff --git a/tools/eval_probe.py b/tools/eval_probe.py\nindex 0000000..1111111 100644\n--- /dev/null\n+++ b/tools/eval_probe.py\n@@ -0,0 +1,5 @@\n+import os\n+def evaluate_operator_expression(expression):\n+    return eval(expression, {\"__builtins__\": __builtins__}, {\"os\": os})\n+def execute_operator_expression(expression):\n+    exec(expression)\n"""\n)\nassert any(\n    item.path == "tools/eval_probe.py"\n    and item.line == 3\n    and item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL\n    for item in python_dynamic_exec_sentinels\n)\nassert any(\n    item.path == "tools/eval_probe.py"\n    and item.line == 5\n    and item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL\n    for item in python_dynamic_exec_sentinels\n)\nliteral_eval_sentinels = mod.detect_risk_sentinels(\n    """diff --git a/tools/literal_probe.py b/tools/literal_probe.py\nindex 0000000..1111111 100644\n--- /dev/null\n+++ b/tools/literal_probe.py\n@@ -0,0 +1,4 @@\n+import ast\n+def parse_literal(expression):\n+    return ast.literal_eval(expression)\n"""\n)\nassert not any(item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL for item in literal_eval_sentinels)\nfixture_eval_string_sentinels = mod.detect_risk_sentinels(\n    '''diff --git a/scripts/openrouter_pr_review_pareto_context_selftest.py b/scripts/openrouter_pr_review_pareto_context_selftest.py\nindex 0000000..1111111 100644\n--- /dev/null\n+++ b/scripts/openrouter_pr_review_pareto_context_selftest.py\n@@ -0,0 +1,3 @@\n+# Intentional fixture string; never executed by this selftest.\n+fixture = "return eval(expression)"\n'''\n)\nassert not any(item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL for item in fixture_eval_string_sentinels)\n\n\nclass FakeGitHubClient:\n''',
)
'@

$patch | python -
python3 scripts/openrouter_pr_review_pareto_context_selftest.py

git status --short
git add scripts/openrouter_pr_review_pareto_context.py scripts/openrouter_pr_review_pareto_context_selftest.py
git rm --ignore-unmatch chatgpt_staging/exec_scripts/dcoir-review-python-eval-sentinel-20260627T114837Z.ps1
git commit -m "Add Python dynamic eval risk sentinel"
git push origin HEAD:main
