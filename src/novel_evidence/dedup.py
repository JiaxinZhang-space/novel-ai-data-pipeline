"""Normalization, SHA-256 exact deduplication, and simplified MinHash+LSH."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable

from .constants import (
    LSH_BANDS,
    MINHASH_PERMUTATIONS,
    NEAR_DUPLICATE_THRESHOLD,
    NORMALIZATION_VERSION,
    SHINGLE_SIZE,
)
from .io_utils import sha256_text


WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
BLANK_LINES_RE = re.compile(r"\n{3,}")
TOKEN_RE = re.compile(r"[\u3400-\u9fffA-Za-z0-9]+")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(lines).strip()
    return BLANK_LINES_RE.sub("\n\n", normalized)


def normalize_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        normalized = normalize_text(record["text"])
        output.append(
            {
                **record,
                "normalized_text": normalized,
                "content_sha256": sha256_text(normalized),
                "normalization_version": NORMALIZATION_VERSION,
            }
        )
    return output


def character_shingles(text: str, size: int = SHINGLE_SIZE) -> set[str]:
    compact = "".join(TOKEN_RE.findall(normalize_text(text))).lower()
    if len(compact) <= size:
        return {compact} if compact else set()
    return {compact[index : index + size] for index in range(len(compact) - size + 1)}


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def minhash_signature(
    shingles: set[str],
    permutations: int = MINHASH_PERMUTATIONS,
) -> tuple[int, ...]:
    if not shingles:
        return tuple(0 for _ in range(permutations))
    signature: list[int] = []
    for seed in range(permutations):
        signature.append(
            min(
                int.from_bytes(
                    hashlib.sha256(f"{seed}:{shingle}".encode("utf-8")).digest()[:8],
                    "big",
                )
                for shingle in shingles
            )
        )
    return tuple(signature)


def lsh_keys(signature: tuple[int, ...], bands: int = LSH_BANDS) -> list[tuple[int, str]]:
    if not signature or len(signature) % bands != 0:
        raise ValueError("signature length must be non-zero and divisible by bands")
    rows = len(signature) // bands
    keys: list[tuple[int, str]] = []
    for band in range(bands):
        values = signature[band * rows : (band + 1) * rows]
        payload = ",".join(str(value) for value in values)
        keys.append((band, hashlib.sha256(payload.encode("ascii")).hexdigest()[:20]))
    return keys


def deduplicate(
    records: list[dict[str, Any]],
    *,
    near_threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep the earliest record and reject exact or LSH-confirmed near duplicates."""
    if not 0.0 <= near_threshold <= 1.0:
        raise ValueError("near_threshold must be between 0 and 1")

    exact_seen: dict[str, dict[str, Any]] = {}
    exact_survivors: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda row: row["ingest_sequence"]):
        canonical = exact_seen.get(record["content_sha256"])
        if canonical is not None:
            rejected.append(
                {
                    **record,
                    "rejection_stage": "sha256_exact_dedup",
                    "rejection_reason": "exact_duplicate",
                    "duplicate_of": canonical["record_id"],
                    "similarity": 1.0,
                }
            )
            continue
        exact_seen[record["content_sha256"]] = record
        exact_survivors.append(record)

    buckets: dict[tuple[int, str], list[int]] = defaultdict(list)
    kept: list[dict[str, Any]] = []
    kept_shingles: list[set[str]] = []
    for record in exact_survivors:
        shingles = character_shingles(record["normalized_text"])
        signature = minhash_signature(shingles)
        keys = lsh_keys(signature)
        candidate_indices = sorted(
            {index for key in keys for index in buckets.get(key, [])}
        )

        best_index: int | None = None
        best_similarity = 0.0
        for candidate_index in candidate_indices:
            similarity = jaccard_similarity(shingles, kept_shingles[candidate_index])
            if similarity > best_similarity:
                best_index = candidate_index
                best_similarity = similarity

        if best_index is not None and best_similarity >= near_threshold:
            rejected.append(
                {
                    **record,
                    "rejection_stage": "minhash_lsh_near_dedup",
                    "rejection_reason": "near_duplicate",
                    "duplicate_of": kept[best_index]["record_id"],
                    "similarity": round(best_similarity, 6),
                }
            )
            continue

        kept_index = len(kept)
        kept.append(record)
        kept_shingles.append(shingles)
        for key in keys:
            buckets[key].append(kept_index)
    return kept, rejected

