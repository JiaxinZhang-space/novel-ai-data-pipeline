from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from novel_evidence.dedup import (
    character_shingles,
    deduplicate,
    jaccard_similarity,
    normalize_records,
    normalize_text,
)
from novel_evidence.generator import generate_raw_records
from novel_evidence.validation import partition_by_rights


class RightsAndDedupTests(unittest.TestCase):
    def test_rights_gate_rejects_unlicensed_and_expired_records(self) -> None:
        accepted, rejected = partition_by_rights(generate_raw_records())
        self.assertEqual(25, len(accepted))
        self.assertEqual(2, len(rejected))
        reasons = {error for row in rejected for error in row["validation_errors"]}
        self.assertIn("rights_status_not_active", reasons)
        self.assertIn("license_outside_validity_window", reasons)

    def test_sha_and_minhash_lsh_leave_twenty_stories(self) -> None:
        accepted, _ = partition_by_rights(generate_raw_records())
        canonical, rejected = deduplicate(normalize_records(accepted))
        counts = Counter(row["rejection_reason"] for row in rejected)
        self.assertEqual(20, len(canonical))
        self.assertEqual(2, counts["exact_duplicate"])
        self.assertEqual(3, counts["near_duplicate"])
        self.assertTrue(all(row.get("duplicate_of") for row in rejected))

    def test_normalization_and_similarity_are_stable(self) -> None:
        self.assertEqual("A段\n\n第二段", normalize_text("Ａ段  \r\n\r\n\r\n第二段"))
        left = character_shingles("甲乙丙丁戊己庚辛壬癸")
        right = character_shingles("甲乙丙丁戊己庚辛壬甲")
        self.assertGreater(jaccard_similarity(left, right), 0.4)


if __name__ == "__main__":
    unittest.main()
