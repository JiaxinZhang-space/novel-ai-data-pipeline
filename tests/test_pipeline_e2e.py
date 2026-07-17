from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from novel_evidence.cli import main as cli_main
from novel_evidence.io_utils import read_jsonl
from novel_evidence.pipeline import run_demo_pipeline, verify_checksums


class PipelineEndToEndTests(unittest.TestCase):
    def test_pipeline_outputs_are_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "artifacts"
            summary = run_demo_pipeline(output)
            first_checksums = (output / "manifests/checksums.sha256").read_text(
                encoding="utf-8"
            )
            self.assertEqual("passed", summary["status"])
            self.assertEqual([], verify_checksums(output))

            required = [
                "raw/raw_records.jsonl",
                "processed/canonical_stories.jsonl",
                "datasets/sft_train.jsonl",
                "datasets/sft_validation.jsonl",
                "datasets/preference_train.jsonl",
                "datasets/evaluation_isolated.jsonl",
                "operations/editor_events.jsonl",
                "metrics/quality_metrics.json",
                "reports/overview.html",
                "manifests/release_manifest.json",
                "manifests/version_lineage.json",
                "manifests/checksums.sha256",
            ]
            for relative in required:
                self.assertTrue((output / relative).is_file(), relative)

            metrics = json.loads(
                (output / "metrics/quality_metrics.json").read_text(encoding="utf-8")
            )
            manifest = json.loads(
                (output / "manifests/release_manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(metrics["demo"])
            self.assertEqual("passed", metrics["status"])
            self.assertEqual(20, metrics["data_volume"]["canonical_stories"])
            self.assertEqual(30, metrics["data_volume"]["isolated_evaluation_tasks"])
            self.assertEqual("DEMO_ONLY_NOT_FOR_PRODUCTION", manifest["release_status"])
            self.assertEqual(
                "normalized_source_sha256",
                manifest["source_snapshot"]["type"],
            )
            self.assertRegex(manifest["source_snapshot"]["sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(
                any(
                    row["path"] == "src/novel_evidence/pipeline.py"
                    for row in manifest["source_snapshot"]["files"]
                )
            )
            self.assertEqual(
                30, len(read_jsonl(output / "datasets/evaluation_isolated.jsonl"))
            )

            run_demo_pipeline(output)
            second_checksums = (output / "manifests/checksums.sha256").read_text(
                encoding="utf-8"
            )
            self.assertEqual(first_checksums, second_checksums)

    def test_cli_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = cli_main(["--output-dir", str(Path(temporary) / "out"), "--quiet"])
            self.assertEqual(0, result)

    def test_refuses_to_clean_unmanaged_generated_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "unsafe"
            protected = output / "reports" / "keep.txt"
            protected.parent.mkdir(parents=True)
            protected.write_text("user-owned", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unmanaged output directory"):
                run_demo_pipeline(output)
            self.assertEqual("user-owned", protected.read_text(encoding="utf-8"))
            self.assertFalse((output / ".novel_evidence_demo_root").exists())

    def test_refuses_source_checkout_as_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "source checkout"):
            run_demo_pipeline(ROOT)

    def test_contract_documents_are_valid_json_schema_documents(self) -> None:
        schemas = sorted((ROOT / "contracts").glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 6)
        for schema_path in schemas:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "https://json-schema.org/draft/2020-12/schema", schema["$schema"]
            )
            self.assertEqual("object", schema["type"])


if __name__ == "__main__":
    unittest.main()
