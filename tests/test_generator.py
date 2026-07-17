from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from novel_evidence.generator import generate_base_stories, generate_raw_records


class GeneratorTests(unittest.TestCase):
    def test_generates_twenty_unique_base_stories(self) -> None:
        stories = generate_base_stories()
        self.assertEqual(20, len(stories))
        self.assertEqual(20, len({story["work_id"] for story in stories}))
        self.assertEqual(20, len({story["text"] for story in stories}))
        self.assertEqual(10, len({story["author_id"] for story in stories}))
        self.assertTrue(all(story["demo"] is True for story in stories))
        self.assertTrue(all(story["rights_record_id"] for story in stories))

    def test_raw_records_include_deliberate_defects(self) -> None:
        first = generate_raw_records()
        second = generate_raw_records()
        self.assertEqual(first, second)
        self.assertEqual(27, len(first))
        self.assertEqual(list(range(1, 28)), [row["ingest_sequence"] for row in first])
        self.assertEqual(2, sum(row["rights"]["status"] != "active" for row in first))


if __name__ == "__main__":
    unittest.main()

