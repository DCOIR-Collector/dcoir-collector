#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reassemble_powershell_evidence_chunks as chunks


def write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


class ReassemblePowerShellEvidenceChunksTests(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        chunk_root = root / chunks.DEFAULT_CHUNK_ROOT

        json_source = {
            "schema_version": "fixture_v1",
            "summary": {"total": 3},
            "items": [{"id": 1}, {"id": 2}, {"id": 3}],
            "details": {"left": True, "right": False},
        }
        json_text = json.dumps(json_source, indent=2) + "\n"
        markdown_text = "# Fixture Report\n\n- status: pass\n"
        write(root / "project_sources/collector/fixture_report.json", json_text)
        write(root / "project_sources/collector/fixture_report.md", markdown_text)

        json_chunks = [
            {
                "chunk_kind": "json_value",
                "data": "fixture_v1",
                "json_pointer": "/schema_version",
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
            {
                "chunk_kind": "json_value",
                "data": {"total": 3},
                "json_pointer": "/summary",
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
            {
                "chunk_index": 0,
                "chunk_kind": "json_list_items",
                "data": [{"id": 1}, {"id": 2}],
                "item_count": 2,
                "item_start": 0,
                "json_pointer": "/items",
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
            {
                "chunk_index": 1,
                "chunk_kind": "json_list_items",
                "data": [{"id": 3}],
                "item_count": 1,
                "item_start": 2,
                "json_pointer": "/items",
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
            {
                "chunk_index": 0,
                "chunk_kind": "json_object_members",
                "data": {"left": True},
                "json_pointer": "/details",
                "key_count": 1,
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
            {
                "chunk_index": 1,
                "chunk_kind": "json_object_members",
                "data": {"right": False},
                "json_pointer": "/details",
                "key_count": 1,
                "report_id": "fixture",
                "schema_version": chunks.CHUNK_SCHEMA_VERSION,
                "source_report": "project_sources/collector/fixture_report.json",
                "source_sha256": sha256(json_text),
            },
        ]
        json_manifest_chunks = []
        for index, chunk in enumerate(json_chunks):
            rel = chunks.DEFAULT_CHUNK_ROOT / "fixture/json" / f"chunk_{index:03d}.json"
            text = json.dumps(chunk, indent=2) + "\n"
            write(root / rel, text)
            info = {
                "bytes": len(text.encode("utf-8")),
                "chunk_kind": chunk["chunk_kind"],
                "format": "json",
                "path": rel.as_posix(),
                "sha256": sha256(text),
            }
            if "json_pointer" in chunk:
                info["json_pointer"] = chunk["json_pointer"]
            if "chunk_index" in chunk:
                info["chunk_index"] = chunk["chunk_index"]
            if "item_start" in chunk:
                info["item_start"] = chunk["item_start"]
                info["item_count"] = chunk["item_count"]
            if "key_count" in chunk:
                info["key_count"] = chunk["key_count"]
            json_manifest_chunks.append(info)

        markdown_rel = chunks.DEFAULT_CHUNK_ROOT / "fixture/markdown/chunk_000.md"
        write(root / markdown_rel, markdown_text)

        json_manifest = {
            "chunk_count": len(json_manifest_chunks),
            "chunks": json_manifest_chunks,
            "report_id": "fixture",
            "schema_version": chunks.REPORT_MANIFEST_SCHEMA_VERSION,
            "source_bytes": len(json_text.encode("utf-8")),
            "source_format": "json",
            "source_report": "project_sources/collector/fixture_report.json",
            "source_sha256": sha256(json_text),
        }
        markdown_manifest = {
            "chunk_count": 1,
            "chunks": [
                {
                    "bytes": len(markdown_text.encode("utf-8")),
                    "chunk_kind": "markdown_section",
                    "format": "markdown",
                    "path": markdown_rel.as_posix(),
                    "sha256": sha256(markdown_text),
                }
            ],
            "report_id": "fixture",
            "schema_version": chunks.REPORT_MANIFEST_SCHEMA_VERSION,
            "source_bytes": len(markdown_text.encode("utf-8")),
            "source_format": "markdown",
            "source_report": "project_sources/collector/fixture_report.md",
            "source_sha256": sha256(markdown_text),
        }
        json_manifest_rel = chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
        markdown_manifest_rel = chunks.DEFAULT_CHUNK_ROOT / "fixture/markdown/manifest.json"
        write(root / json_manifest_rel, json.dumps(json_manifest, indent=2) + "\n")
        write(root / markdown_manifest_rel, json.dumps(markdown_manifest, indent=2) + "\n")

        root_manifest = {
            "file_count": 4 + len(json_chunks),
            "issue": 349,
            "pull_request": 350,
            "report_count": 2,
            "reports": [
                {
                    "chunk_count": len(json_manifest_chunks),
                    "manifest_path": json_manifest_rel.as_posix(),
                    "report_id": "fixture",
                    "source_bytes": len(json_text.encode("utf-8")),
                    "source_format": "json",
                    "source_report": "project_sources/collector/fixture_report.json",
                    "source_sha256": sha256(json_text),
                },
                {
                    "chunk_count": 1,
                    "manifest_path": markdown_manifest_rel.as_posix(),
                    "report_id": "fixture",
                    "source_bytes": len(markdown_text.encode("utf-8")),
                    "source_format": "markdown",
                    "source_report": "project_sources/collector/fixture_report.md",
                    "source_sha256": sha256(markdown_text),
                },
            ],
            "schema_version": chunks.ROOT_SCHEMA_VERSION,
        }
        write(chunk_root / "manifest.json", json.dumps(root_manifest, indent=2) + "\n")
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": root.as_posix(),
            "chunk_root": chunks.DEFAULT_CHUNK_ROOT.as_posix(),
            "strict_source_hash": True,
            "allow_lossy_json_order_reconstruction": False,
            "compare_canonical": True,
            "require_canonical_parity": False,
            "write_output_dir": "",
            "json_output": "",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_reassembles_fixture_and_matches_canonical_reports(self) -> None:
        with self.make_repo() as temp:
            report, outputs = chunks.validate_chunk_set(self.args(Path(temp)))

        self.assertTrue(report["validation"]["success"], report["validation"])
        self.assertEqual(report["report_count"], 2)
        self.assertIn("project_sources/collector/fixture_report.json", outputs)
        self.assertTrue(all(item["canonical_parity"]["status"] == "pass" for item in report["reports"]))

    def test_missing_chunk_file_fails_with_path_context(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_003.json").unlink()
            with self.assertRaisesRegex(chunks.ChunkValidationError, "missing chunk file"):
                chunks.validate_chunk_set(self.args(root))

    def test_tampered_chunk_fails_sha_check(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_000.json"
            original = chunk_path.read_text(encoding="utf-8")
            write(chunk_path, original.replace("fixture_v1", "fixture_v2"))
            with self.assertRaisesRegex(chunks.ChunkValidationError, "sha256 mismatch"):
                chunks.validate_chunk_set(self.args(root))

    def test_json_list_gap_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][3]["item_start"] = 3
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_003.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk["item_start"] = 3
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest["chunks"][3]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][3]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "gap or overlap"):
                chunks.validate_chunk_set(self.args(root))

    def test_json_object_member_collision_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_005.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk["data"] = {"left": False}
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][5]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][5]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "duplicate object member"):
                chunks.validate_chunk_set(self.args(root))

    def test_path_traversal_fails_before_file_read(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][0]["path"] = "../outside.json"
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "repo-relative without traversal"):
                chunks.validate_chunk_set(self.args(root))

    def test_canonical_mismatch_is_reported_separately(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "project_sources/collector/fixture_report.md", "# Stale\n")
            report, _outputs = chunks.validate_chunk_set(self.args(root, strict_source_hash=True))

        markdown_report = next(item for item in report["reports"] if item["source_format"] == "markdown")
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(markdown_report["canonical_parity"]["status"], "mismatch")
        self.assertFalse(markdown_report["canonical_parity"]["source_sha256_match"])
        self.assertFalse(report["canonical_parity_success"])
        self.assertTrue(report["readiness_gaps"])

    def set_json_source_sha(self, root: Path, replacement_sha: str) -> None:
        root_manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "manifest.json"
        root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
        json_report = root_manifest["reports"][0]
        json_report["source_sha256"] = replacement_sha
        report_manifest_path = root / json_report["manifest_path"]
        report_manifest = json.loads(report_manifest_path.read_text(encoding="utf-8"))
        report_manifest["source_sha256"] = replacement_sha
        for chunk_info in report_manifest["chunks"]:
            chunk_path = root / chunk_info["path"]
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk["source_sha256"] = replacement_sha
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            chunk_info["bytes"] = len(text.encode("utf-8"))
            chunk_info["sha256"] = sha256(text)
        write(report_manifest_path, json.dumps(report_manifest, indent=2) + "\n")
        write(root_manifest_path, json.dumps(root_manifest, indent=2) + "\n")

    def test_source_hash_mismatch_fails_without_explicit_lossy_flag(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            self.set_json_source_sha(root, "0" * 64)
            report, _outputs = chunks.validate_chunk_set(
                self.args(root, strict_source_hash=False, allow_lossy_json_order_reconstruction=False)
            )

        self.assertFalse(report["validation"]["success"])
        self.assertFalse(report["reconstruction_exact_success"])
        self.assertTrue(any("reconstructed SHA-256" in error for error in report["validation"]["errors"]))

    def test_explicit_lossy_flag_keeps_byte_gap_visible_without_writable_output(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            self.set_json_source_sha(root, "0" * 64)
            report, outputs = chunks.validate_chunk_set(
                self.args(root, strict_source_hash=False, allow_lossy_json_order_reconstruction=True)
            )

        self.assertTrue(report["validation"]["success"], report["validation"])
        self.assertFalse(report["reconstruction_exact_success"])
        self.assertTrue(report["readiness_gaps"])
        self.assertNotIn("project_sources/collector/fixture_report.json", outputs)
        self.assertIn("project_sources/collector/fixture_report.md", outputs)

    def test_lossy_flag_does_not_downgrade_markdown_source_hash_mismatch(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            root_manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "manifest.json"
            root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
            markdown_report = root_manifest["reports"][1]
            markdown_report["source_sha256"] = "0" * 64
            report_manifest_path = root / markdown_report["manifest_path"]
            report_manifest = json.loads(report_manifest_path.read_text(encoding="utf-8"))
            report_manifest["source_sha256"] = "0" * 64
            write(report_manifest_path, json.dumps(report_manifest, indent=2) + "\n")
            write(root_manifest_path, json.dumps(root_manifest, indent=2) + "\n")

            report, _outputs = chunks.validate_chunk_set(
                self.args(root, strict_source_hash=False, allow_lossy_json_order_reconstruction=True)
            )

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture_report.md" in error for error in report["validation"]["errors"]))

    def test_main_refuses_to_write_outputs_when_validation_fails(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            self.set_json_source_sha(root, "0" * 64)
            output_dir = root / "reconstructed"
            with contextlib.redirect_stdout(io.StringIO()):
                status = chunks.main(
                    [
                        "--repo-root",
                        root.as_posix(),
                        "--write-output-dir",
                        output_dir.as_posix(),
                    ]
                )

        self.assertEqual(status, 1)
        self.assertFalse(output_dir.exists())

    def test_chunk_paths_must_stay_inside_chunk_root(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][0]["path"] = "project_sources/collector/fixture_report.json"
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "inside the chunk root"):
                chunks.validate_chunk_set(self.args(root))

    def test_chunk_index_metadata_mismatch_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_002.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk["chunk_index"] = 99
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][2]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][2]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "chunk_index mismatch"):
                chunks.validate_chunk_set(self.args(root))

    def test_key_count_metadata_mismatch_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_004.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk["key_count"] = 2
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][4]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][4]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "key_count"):
                chunks.validate_chunk_set(self.args(root))

    def test_missing_chunk_index_metadata_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_002.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk.pop("chunk_index")
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][2]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][2]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "chunk_index"):
                chunks.validate_chunk_set(self.args(root))

    def test_missing_key_count_metadata_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            chunk_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/chunk_004.json"
            chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunk.pop("key_count")
            text = json.dumps(chunk, indent=2) + "\n"
            write(chunk_path, text)
            manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "fixture/json/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunks"][4]["bytes"] = len(text.encode("utf-8"))
            manifest["chunks"][4]["sha256"] = sha256(text)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "key_count"):
                chunks.validate_chunk_set(self.args(root))

    def test_duplicate_source_report_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            root_manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "manifest.json"
            root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
            root_manifest["reports"][1]["source_report"] = root_manifest["reports"][0]["source_report"]
            write(root_manifest_path, json.dumps(root_manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "duplicate source_report"):
                chunks.validate_chunk_set(self.args(root))

    def test_normalized_duplicate_source_report_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            root_manifest_path = root / chunks.DEFAULT_CHUNK_ROOT / "manifest.json"
            root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
            root_manifest["reports"][1]["source_report"] = "./" + root_manifest["reports"][0]["source_report"]
            markdown_manifest_path = root / root_manifest["reports"][1]["manifest_path"]
            markdown_manifest = json.loads(markdown_manifest_path.read_text(encoding="utf-8"))
            markdown_manifest["source_report"] = root_manifest["reports"][1]["source_report"]
            write(markdown_manifest_path, json.dumps(markdown_manifest, indent=2) + "\n")
            write(root_manifest_path, json.dumps(root_manifest, indent=2) + "\n")

            with self.assertRaisesRegex(chunks.ChunkValidationError, "duplicate source_report"):
                chunks.validate_chunk_set(self.args(root))


if __name__ == "__main__":
    unittest.main()
