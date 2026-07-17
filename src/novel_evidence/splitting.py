"""Leakage-resistant deterministic author/work split assignment."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

from .constants import DATA_VERSION


def _stable_rank(value: str) -> tuple[str, str]:
    return hashlib.sha256(f"novel-evidence-v0.1:{value}".encode("utf-8")).hexdigest(), value


def assign_splits(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assign 60/20/20 of author groups to train/validation/evaluation."""
    authors = sorted({record["author_id"] for record in records}, key=_stable_rank)
    if len(authors) < 5:
        raise ValueError("at least five authors are required for a three-way group split")
    train_end = int(len(authors) * 0.60)
    validation_end = train_end + int(len(authors) * 0.20)
    author_split = {
        author: (
            "train"
            if index < train_end
            else "validation"
            if index < validation_end
            else "evaluation"
        )
        for index, author in enumerate(authors)
    }
    return [
        {
            **record,
            "split": author_split[record["author_id"]],
            "split_strategy": "author_group_hash_v1",
            "dataset_version": DATA_VERSION,
        }
        for record in sorted(records, key=lambda row: row["work_id"])
    ]


def leakage_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = {
        "author_id": defaultdict(set),
        "work_id": defaultdict(set),
        "content_sha256": defaultdict(set),
    }
    split_counts: dict[str, int] = defaultdict(int)
    for record in records:
        split = record["split"]
        split_counts[split] += 1
        for field, values in dimensions.items():
            values[record[field]].add(split)

    overlaps = {
        field: sorted(value for value, splits in values.items() if len(splits) > 1)
        for field, values in dimensions.items()
    }
    passed = not any(overlaps.values())
    return {
        "demo": True,
        "status": "passed" if passed else "failed",
        "isolation_unit": ["author_id", "work_id", "content_sha256"],
        "split_counts": dict(sorted(split_counts.items())),
        "overlap_counts": {field: len(values) for field, values in overlaps.items()},
        "overlap_examples": {field: values[:5] for field, values in overlaps.items()},
    }


def assert_no_leakage(records: list[dict[str, Any]]) -> None:
    report = leakage_report(records)
    if report["status"] != "passed":
        raise ValueError(f"split leakage detected: {report['overlap_examples']}")
