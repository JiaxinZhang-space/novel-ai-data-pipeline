from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_schema_subset import assert_valid, validate
from novel_evidence.io_utils import read_jsonl
from novel_evidence.pipeline import run_demo_pipeline


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))


class GeneratedArtifactContractTests(unittest.TestCase):
    def test_every_generated_contract_artifact_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "artifacts"
            run_demo_pipeline(artifacts)

            jsonl_contracts = [
                (
                    "raw_record.schema.json",
                    ["raw/raw_records.jsonl"],
                ),
                (
                    "canonical_story.schema.json",
                    ["processed/canonical_stories.jsonl"],
                ),
                (
                    "sft_sample.schema.json",
                    [
                        "datasets/sft_train.jsonl",
                        "datasets/sft_validation.jsonl",
                    ],
                ),
                (
                    "preference_pair.schema.json",
                    ["datasets/preference_train.jsonl"],
                ),
                (
                    "evaluation_task.schema.json",
                    ["datasets/evaluation_isolated.jsonl"],
                ),
            ]
            for schema_name, relative_paths in jsonl_contracts:
                schema = load_schema(schema_name)
                for relative_path in relative_paths:
                    rows = read_jsonl(artifacts / relative_path)
                    self.assertGreater(len(rows), 0, relative_path)
                    for index, row in enumerate(rows):
                        assert_valid(row, schema, f"{relative_path}[{index}]")

            json_contracts = [
                (
                    "release_manifest.schema.json",
                    "manifests/release_manifest.json",
                ),
                (
                    "quality_metrics.schema.json",
                    "metrics/quality_metrics.json",
                ),
            ]
            for schema_name, relative_path in json_contracts:
                instance = json.loads(
                    (artifacts / relative_path).read_text(encoding="utf-8")
                )
                assert_valid(instance, load_schema(schema_name), relative_path)

    def test_required_const_enum_pattern_and_type_reject_mutated_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "artifacts"
            run_demo_pipeline(artifacts)
            raw = read_jsonl(artifacts / "raw/raw_records.jsonl")[0]
            canonical = read_jsonl(
                artifacts / "processed/canonical_stories.jsonl"
            )[0]
            metrics = json.loads(
                (artifacts / "metrics/quality_metrics.json").read_text(encoding="utf-8")
            )
            raw_schema = load_schema("raw_record.schema.json")
            canonical_schema = load_schema("canonical_story.schema.json")
            metrics_schema = load_schema("quality_metrics.schema.json")

            mutations: list[tuple[str, dict[str, Any], dict[str, Any], str]] = []

            missing_required = copy.deepcopy(raw)
            del missing_required["record_id"]
            mutations.append(("required", missing_required, raw_schema, "missing required"))

            wrong_const = copy.deepcopy(raw)
            wrong_const["demo"] = False
            mutations.append(("const", wrong_const, raw_schema, "expected const"))

            wrong_enum = copy.deepcopy(canonical)
            wrong_enum["split"] = "holdout"
            mutations.append(("enum", wrong_enum, canonical_schema, "not in enum"))

            wrong_pattern = copy.deepcopy(raw)
            wrong_pattern["record_id"] = "NOT-A-RAW-ID"
            mutations.append(("pattern", wrong_pattern, raw_schema, "does not match"))

            wrong_type = copy.deepcopy(metrics)
            wrong_type["data_volume"] = []
            mutations.append(("type", wrong_type, metrics_schema, "expected type"))

            for keyword, instance, schema, expected_message in mutations:
                with self.subTest(keyword=keyword):
                    errors = validate(instance, schema)
                    self.assertTrue(errors)
                    self.assertTrue(
                        any(expected_message in error for error in errors),
                        errors,
                    )


if __name__ == "__main__":
    unittest.main()

