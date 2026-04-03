#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Tuple

CONTROL_FILE_ALIASES = {
    "manifest": [
        "CP-01_DCOIR_Version_Manifest.txt",
        "DCOIR_Version_Manifest.txt",
    ],
    "change_log": [
        "CP-02_DCOIR_Change_Log.txt",
        "DCOIR_Change_Log.txt",
    ],
    "setup": [
        "DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt",
        "AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt",
    ],
}

EXPECTED_ORDER = [
    "system",
    "output_schema",
    "baseline_triage",
    "enrichment_review",
    "retrieved_artifact_review",
    "final_case_synthesis",
    "guardrails",
]

PROMPT_ROLE_HINTS = {
    "PromptPack_System_Current": "system",
    "PromptPack_Output_Schema_Current": "output_schema",
    "PromptPack_Baseline_Triage_Current": "baseline_triage",
    "PromptPack_Enrichment_Review_Current": "enrichment_review",
    "PromptPack_Retrieved_Artifact_Review_Current": "retrieved_artifact_review",
    "PromptPack_Final_Case_Synthesis_Current": "final_case_synthesis",
    "PromptPack_Agent_Guardrails_Current": "guardrails",
}

IGNORED_PROMPTPACK_ROLE_KEYS = {
    "PromptPack_Combined_Master_Prompt_Current",
    "PromptPack_Gemini_Generator_Workflow_Current",
    "PromptPack_Gemini_Bounded_Design_Artifact_Current",
}

OUTPUT_DRAFT = "dcoir_combined_master_prompt_draft.txt"
OUTPUT_REPORT = "dcoir_prompt_pack_assembly_report.txt"
OUTPUT_JSON = "dcoir_prompt_pack_assembly_report.json"


class AssemblyError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_control_files(source_dir: Path) -> Dict[str, Path]:
    resolved: Dict[str, Path] = {}
    for role, aliases in CONTROL_FILE_ALIASES.items():
        matches = [source_dir / name for name in aliases if (source_dir / name).exists()]
        if not matches:
            raise AssemblyError(f"assembly refused: no {role} file found in workspace")
        # Prefer the current class-prefixed name when both current and legacy files coexist.
        preferred_name = aliases[0]
        preferred = [path for path in matches if path.name == preferred_name]
        if len(preferred) > 1:
            names = ", ".join(path.name for path in preferred)
            raise AssemblyError(f"assembly refused: multiple preferred {role} files found in workspace: {names}")
        if preferred:
            resolved[role] = preferred[0]
            continue
        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise AssemblyError(f"assembly refused: multiple legacy {role} files found in workspace with no preferred current file: {names}")
        resolved[role] = matches[0]
    return resolved


def parse_manifest_current_sources(manifest_text: str) -> Dict[str, str]:
    in_section = False
    sources: Dict[str, str] = {}
    for raw_line in manifest_text.splitlines():
        line = raw_line.strip()
        if line == "CURRENT UPLOADED PROJECT SOURCES":
            in_section = True
            continue
        if in_section:
            if not line:
                continue
            if line.isupper() and not line.startswith("-"):
                break
            if line.startswith("- ") and ":" in line:
                key, value = line[2:].split(":", 1)
                sources[key.strip()] = value.strip()
    if not sources:
        raise AssemblyError("manifest parse failure: could not read CURRENT UPLOADED PROJECT SOURCES")
    return sources


def classify_prompt_module(role_key: str, filename: str) -> str:
    if role_key in PROMPT_ROLE_HINTS:
        return PROMPT_ROLE_HINTS[role_key]

    name = filename.lower()
    checks: List[Tuple[str, Tuple[str, ...]]] = [
        ("retrieved_artifact_review", ("retrieved_artifact_review",)),
        ("final_case_synthesis", ("final_case_synthesis",)),
        ("baseline_triage", ("baseline_triage",)),
        ("enrichment_review", ("enrichment_review",)),
        ("output_schema", ("output_schema",)),
        ("system", ("system_prompt",)),
        ("guardrails", ("guardrail", "guardrails")),
    ]
    matches = []
    for module_name, needles in checks:
        if any(needle in name for needle in needles):
            matches.append(module_name)
    if len(matches) != 1:
        raise AssemblyError(f"cannot classify prompt-pack file: {filename}")
    return matches[0]


def discover_prompt_pack_files(current_sources: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    prompt_entries = {k: v for k, v in current_sources.items() if k.startswith("PromptPack_")}
    if not prompt_entries:
        raise AssemblyError("no current prompt-pack files were found in the manifest")

    discovered: Dict[str, str] = {}
    ignored: Dict[str, str] = {}
    unexpected_roles: List[str] = []

    for role_key, filename in prompt_entries.items():
        if role_key in IGNORED_PROMPTPACK_ROLE_KEYS:
            ignored[role_key] = filename
            continue
        try:
            module = classify_prompt_module(role_key, filename)
        except AssemblyError:
            unexpected_roles.append(f"{role_key}: {filename}")
            continue
        if module in discovered:
            raise AssemblyError(f"duplicate current prompt-pack module detected for {module}")
        discovered[module] = filename

    if unexpected_roles:
        raise AssemblyError(
            "stale skill: unexpected current prompt-pack role(s): " + ", ".join(sorted(unexpected_roles))
        )

    unexpected = sorted(set(discovered.keys()) - set(EXPECTED_ORDER))
    if unexpected:
        raise AssemblyError("stale skill: unexpected current prompt-pack module(s): " + ", ".join(unexpected))

    return discovered, ignored


def validate_current_module_set(discovered: Dict[str, str]) -> None:
    missing = [module for module in EXPECTED_ORDER if module not in discovered]
    if missing:
        if "guardrails" in missing:
            raise AssemblyError("assembly refused: guardrails is not current in the manifest")
        raise AssemblyError(
            "assembly refused: required current prompt-pack module(s) missing from manifest: " + ", ".join(missing)
        )


def verify_workspace_files(source_dir: Path, files: List[str]) -> None:
    missing = [name for name in files if not (source_dir / name).exists()]
    if missing:
        raise AssemblyError("assembly refused: required file(s) missing from workspace: " + ", ".join(missing))


def assemble_draft_text(ordered_files: List[Tuple[str, Path]], manifest_name: str) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines: List[str] = []
    lines.append("DCOIR COMBINED MASTER PROMPT DRAFT")
    lines.append("")
    lines.append("Generated artifact: do not treat this file as control-plane authority.")
    lines.append(f"Source of truth: the current modular prompt-pack files listed in {manifest_name}.")
    lines.append(f"Generated at: {timestamp}")
    lines.append("")
    lines.append("Included source files in canonical order:")
    for index, (_, path) in enumerate(ordered_files, start=1):
        lines.append(f"{index}. {path.name}")
    lines.append("")
    lines.append("=" * 80)
    for index, (module, path) in enumerate(ordered_files, start=1):
        lines.append("")
        lines.append(f"BEGIN MODULE {index}: {module.upper()}")
        lines.append(f"Source file: {path.name}")
        lines.append("-" * 80)
        lines.append(read_text(path).rstrip())
        lines.append("")
        lines.append(f"END MODULE {index}: {module.upper()}")
        lines.append("=" * 80)
    lines.append("")
    return "\n".join(lines)


def build_report(success: bool, reason: str, discovered: Dict[str, str], ignored: Dict[str, str], output_dir: Path, resolved: Dict[str, Path]) -> str:
    lines: List[str] = []
    lines.append("DCOIR Prompt Pack Assembly Report")
    lines.append("")
    lines.append(f"Status: {'success' if success else 'failure'}")
    if reason:
        lines.append(f"Reason: {reason}")
    lines.append("")
    lines.append("Resolved control files:")
    if resolved:
        for role in ("manifest", "change_log", "setup"):
            if role in resolved:
                lines.append(f"- {role}: {resolved[role].name}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Expected canonical module order:")
    for index, module in enumerate(EXPECTED_ORDER, start=1):
        lines.append(f"{index}. {module}")
    lines.append("")
    lines.append("Discovered current modular prompt-pack files:")
    if discovered:
        for module in EXPECTED_ORDER:
            if module in discovered:
                lines.append(f"- {module}: {discovered[module]}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Ignored current non-modular prompt-pack files:")
    if ignored:
        for role_key in sorted(ignored):
            lines.append(f"- {role_key}: {ignored[role_key]}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Output files:")
    if success:
        lines.append(f"- {output_dir / OUTPUT_DRAFT}")
        lines.append(f"- {output_dir / OUTPUT_REPORT}")
    else:
        lines.append(f"- {output_dir / OUTPUT_REPORT}")
        lines.append("- combined draft not emitted")
    lines.append("")
    return "\n".join(lines)


def write_json_report(path: Path, success: bool, reason: str, discovered: Dict[str, str], ignored: Dict[str, str], output_dir: Path, resolved: Dict[str, Path]) -> None:
    payload = {
        "success": success,
        "reason": reason,
        "resolved_control_files": {role: str(p) for role, p in resolved.items()},
        "expected_order": EXPECTED_ORDER,
        "discovered": discovered,
        "ignored_non_modular_promptpack_roles": ignored,
        "outputs": {
            "draft": str(output_dir / OUTPUT_DRAFT) if success else None,
            "report": str(output_dir / OUTPUT_REPORT),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble the current DCOIR combined master prompt draft.")
    parser.add_argument("--source-dir", required=True, help="Directory containing the DCOIR project files")
    parser.add_argument("--output-dir", required=True, help="Directory to receive generated outputs")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    discovered: Dict[str, str] = {}
    ignored: Dict[str, str] = {}
    resolved: Dict[str, Path] = {}
    reason = ""

    try:
        resolved = resolve_control_files(source_dir)
        manifest_text = read_text(resolved["manifest"])
        current_sources = parse_manifest_current_sources(manifest_text)
        discovered, ignored = discover_prompt_pack_files(current_sources)
        validate_current_module_set(discovered)
        verify_workspace_files(source_dir, list(discovered.values()))
        ordered_files = [(module, source_dir / discovered[module]) for module in EXPECTED_ORDER]
        draft_text = assemble_draft_text(ordered_files, resolved["manifest"].name)
        (output_dir / OUTPUT_DRAFT).write_text(draft_text, encoding="utf-8")
        reason = "assembly completed from the current prompt-pack set"
        success = True
    except AssemblyError as exc:
        reason = str(exc)
        success = False
    except Exception as exc:  # pragma: no cover
        reason = f"unexpected failure: {exc}"
        success = False

    report_text = build_report(success=success, reason=reason, discovered=discovered, ignored=ignored, output_dir=output_dir, resolved=resolved)
    (output_dir / OUTPUT_REPORT).write_text(report_text, encoding="utf-8")
    write_json_report(output_dir / OUTPUT_JSON, success=success, reason=reason, discovered=discovered, ignored=ignored, output_dir=output_dir, resolved=resolved)
    print(report_text)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
