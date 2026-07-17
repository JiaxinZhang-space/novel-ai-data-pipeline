from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from novel_evidence.datasets import (
    build_evaluation_tasks,
    build_preference_pairs,
    build_sft_samples,
    validate_dataset_isolation,
)
from novel_evidence.dedup import deduplicate, normalize_records
from novel_evidence.generator import generate_raw_records
from novel_evidence.splitting import assign_splits, leakage_report
from novel_evidence.validation import partition_by_rights


def canonical_split_stories() -> list[dict]:
    accepted, _ = partition_by_rights(generate_raw_records())
    canonical, _ = deduplicate(normalize_records(accepted))
    return assign_splits(canonical)


class SplittingAndDatasetTests(unittest.TestCase):
    def test_author_group_split_is_deterministic_and_leak_free(self) -> None:
        stories = canonical_split_stories()
        counts = Counter(story["split"] for story in stories)
        self.assertEqual({"train": 12, "validation": 4, "evaluation": 4}, dict(counts))
        report = leakage_report(stories)
        self.assertEqual("passed", report["status"])
        self.assertEqual(
            {"author_id": 0, "work_id": 0, "content_sha256": 0},
            report["overlap_counts"],
        )

    def test_training_and_evaluation_datasets_are_isolated(self) -> None:
        stories = canonical_split_stories()
        sft = build_sft_samples(stories)
        preference = build_preference_pairs(stories)
        evaluation = build_evaluation_tasks(stories)
        self.assertEqual(48, len(sft))
        self.assertEqual(24, len(preference))
        self.assertEqual(30, len(evaluation))
        isolation = validate_dataset_isolation(sft, preference, evaluation)
        self.assertEqual("passed", isolation["status"])

        for row in [*sft, *preference, *evaluation]:
            for key in (
                "source_work_id",
                "source_author_id",
                "work_id",
                "author_id",
                "source_id",
                "document_id",
                "rights_record_id",
                "content_sha256",
                "dataset_version",
                "shard_id",
            ):
                self.assertTrue(row[key], f"{key} missing from {row}")


if __name__ == "__main__":
    unittest.main()
