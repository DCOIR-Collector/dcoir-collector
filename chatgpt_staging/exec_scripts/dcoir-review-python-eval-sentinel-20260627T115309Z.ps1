$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$global:PSNativeCommandUseErrorActionPreference = $true

$patch = @'
from pathlib import Path

pareto_path = Path("scripts/openrouter_pr_review_pareto_context.py")
selftest_path = Path("scripts/openrouter_pr_review_pareto_context_selftest.py")

pareto_lines = pareto_path.read_text(encoding="utf-8").splitlines()
if not any(line == 'PYTHON_DYNAMIC_EXEC_LABEL = "Python eval/exec dynamic code execution"' for line in pareto_lines):
    marker_index = pareto_lines.index('FILE_WRITE_PATH_DETAIL = (')
    insert_at = marker_index
    while insert_at < len(pareto_lines) and pareto_lines[insert_at] != ')':
        insert_at += 1
    if insert_at >= len(pareto_lines):
        raise SystemExit("FILE_WRITE_PATH_DETAIL block end not found")
    insert_at += 1
    pareto_lines[insert_at:insert_at] = [
        'PYTHON_DYNAMIC_EXEC_LABEL = "Python eval/exec dynamic code execution"',
        'PYTHON_DYNAMIC_EXEC_DETAIL = (',
        '    "eval/exec can execute caller-controlled Python expressions; remove dynamic evaluation "',
        '    "or replace it with ast.literal_eval, a constrained parser, or an explicit allowlist"',
        ')',
        'PYTHON_DYNAMIC_EXEC_CALL_NAMES = frozenset(',
        '    {"eval", "exec", "builtins.eval", "builtins.exec", "__builtins__.eval", "__builtins__.exec"}',
        ')',
    ]

pareto_text = "\n".join(pareto_lines) + "\n"
if "def python_dynamic_exec_call_name" not in pareto_text:
    function_block = """
def python_dynamic_exec_call_name(text: str) -> str | None:
    if "eval" not in text and "exec" not in text:
        return None
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return None
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        call_name = python_call_name(node.func)
        if call_name in PYTHON_DYNAMIC_EXEC_CALL_NAMES:
            return call_name
    return None


def detect_python_dynamic_exec_sentinels(diff: str) -> list[hardened.RiskSentinel]:
    sentinels: list[hardened.RiskSentinel] = []
    for diff_line in iter_python_diff_lines_with_context(diff):
        if not diff_line.is_added or diff_line.inside_multiline_string:
            continue
        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):
            continue
        call_name = python_dynamic_exec_call_name(diff_line.text)
        if not call_name:
            continue
        sentinels.append(
            hardened.RiskSentinel(
                path=diff_line.path,
                line=diff_line.line,
                label=PYTHON_DYNAMIC_EXEC_LABEL,
                detail=(
                    f"{call_name} can execute caller-controlled Python code; "
                    "replace dynamic evaluation with literal parsing, a constrained parser, or an explicit allowlist"
                ),
                text=diff_line.text,
            )
        )
    return sentinels

"""
    pareto_text = pareto_text.replace("\ndef python_is_scope_boundary(text: str) -> bool:\n", f"{function_block}\ndef python_is_scope_boundary(text: str) -> bool:\n", 1)

if "*detect_python_dynamic_exec_sentinels(diff)," not in pareto_text:
    pareto_text = pareto_text.replace(
        "    combined = [\n        *detect_python_file_write_path_sentinels(diff),\n        *[\n",
        "    combined = [\n        *detect_python_file_write_path_sentinels(diff),\n        *detect_python_dynamic_exec_sentinels(diff),\n        *[\n",
        1,
    )

pareto_text = pareto_text.replace(
    "Python specialization: inspect unsafe deserialization, subprocess/shell execution, tar/zip/archive extraction, ",
    "Python specialization: inspect unsafe deserialization, eval/exec/dynamic code evaluation, subprocess/shell execution, tar/zip/archive extraction, ",
    1,
)

for expected in [
    'PYTHON_DYNAMIC_EXEC_LABEL = "Python eval/exec dynamic code execution"',
    'def detect_python_dynamic_exec_sentinels(diff: str) -> list[hardened.RiskSentinel]:',
    '*detect_python_dynamic_exec_sentinels(diff),',
    'eval/exec/dynamic code evaluation',
]:
    if expected not in pareto_text:
        raise SystemExit(f"patch did not produce expected text: {expected}")
pareto_path.write_text(pareto_text, encoding="utf-8")

selftest_text = selftest_path.read_text(encoding="utf-8")
if "python_dynamic_exec_sentinels = mod.detect_risk_sentinels" not in selftest_text:
    selftest_lines = selftest_text.splitlines()
    insert_at = selftest_lines.index("class FakeGitHubClient:")
    block = [
        "",
        "python_dynamic_exec_sentinels = mod.detect_risk_sentinels(",
        '    """diff --git a/tools/eval_probe.py b/tools/eval_probe.py',
        "index 0000000..1111111 100644",
        "--- /dev/null",
        "+++ b/tools/eval_probe.py",
        "@@ -0,0 +1,5 @@",
        "+import os",
        "+def evaluate_operator_expression(expression):",
        '+    return eval(expression, {"__builtins__": __builtins__}, {"os": os})',
        "+def execute_operator_expression(expression):",
        "+    exec(expression)",
        '"""',
        ")",
        "assert any(",
        '    item.path == "tools/eval_probe.py"',
        "    and item.line == 3",
        "    and item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL",
        "    for item in python_dynamic_exec_sentinels",
        ")",
        "assert any(",
        '    item.path == "tools/eval_probe.py"',
        "    and item.line == 5",
        "    and item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL",
        "    for item in python_dynamic_exec_sentinels",
        ")",
        "literal_eval_sentinels = mod.detect_risk_sentinels(",
        '    """diff --git a/tools/literal_probe.py b/tools/literal_probe.py',
        "index 0000000..1111111 100644",
        "--- /dev/null",
        "+++ b/tools/literal_probe.py",
        "@@ -0,0 +1,4 @@",
        "+import ast",
        "+def parse_literal(expression):",
        "+    return ast.literal_eval(expression)",
        '"""',
        ")",
        "assert not any(item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL for item in literal_eval_sentinels)",
        "fixture_eval_string_sentinels = mod.detect_risk_sentinels(",
        "    '''diff --git a/scripts/openrouter_pr_review_pareto_context_selftest.py b/scripts/openrouter_pr_review_pareto_context_selftest.py",
        "index 0000000..1111111 100644",
        "--- /dev/null",
        "+++ b/scripts/openrouter_pr_review_pareto_context_selftest.py",
        "@@ -0,0 +1,3 @@",
        "+# Intentional fixture string; never executed by this selftest.",
        '+fixture = "return eval(expression)"',
        "'''",
        ")",
        "assert not any(item.label == mod.PYTHON_DYNAMIC_EXEC_LABEL for item in fixture_eval_string_sentinels)",
        "",
    ]
    selftest_lines[insert_at:insert_at] = block
    selftest_text = "\n".join(selftest_lines) + "\n"

if "python_dynamic_exec_sentinels = mod.detect_risk_sentinels" not in selftest_text:
    raise SystemExit("selftest insertion missing")
selftest_path.write_text(selftest_text, encoding="utf-8")
'@

$patch | python -
python3 scripts/openrouter_pr_review_pareto_context_selftest.py

git status --short
git add scripts/openrouter_pr_review_pareto_context.py scripts/openrouter_pr_review_pareto_context_selftest.py
git rm --ignore-unmatch chatgpt_staging/exec_scripts/dcoir-review-python-eval-sentinel-20260627T115309Z.ps1
git commit -m "Add Python eval exec risk sentinel"
git push origin HEAD:main
