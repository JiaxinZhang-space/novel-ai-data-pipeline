"""End-to-end deterministic DEMO artifact build."""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from .constants import (
    DATA_VERSION,
    DEMO_DISCLAIMER,
    DEMO_MARKER,
    EVALUATION_VERSION,
    GENERATED_AT,
    MODEL_VERSION,
    NEAR_DUPLICATE_THRESHOLD,
    PIPELINE_VERSION,
    RIGHTS_SNAPSHOT_VERSION,
    RUN_ID,
)
from .datasets import (
    build_editor_events,
    build_evaluation_tasks,
    build_preference_pairs,
    build_sft_samples,
    build_story_catalog,
    validate_dataset_isolation,
)
from .dedup import deduplicate, normalize_records
from .generator import generate_raw_records
from .io_utils import (
    relative_posix,
    sha256_bytes,
    sha256_file,
    write_json,
    write_jsonl,
)
from .reports import build_quality_metrics, render_overview_html, write_metric_csvs
from .splitting import assert_no_leakage, assign_splits, leakage_report
from .validation import partition_by_rights


GENERATED_SUBDIRECTORIES = (
    "raw",
    "processed",
    "datasets",
    "operations",
    "metrics",
    "reports",
    "manifests",
)
TRAINING_RUN_ID = "DEMO-TRAINING-NOT-EXECUTED-v0.1.0"
OUTPUT_MARKER_NAME = ".novel_evidence_demo_root"


def _source_snapshot() -> dict[str, Any]:
    """Hash the executable source contract with normalized line endings."""
    project_root = Path(__file__).resolve().parents[2]
    candidates = sorted((project_root / "src" / "novel_evidence").glob("*.py"))
    candidates.extend(sorted((project_root / "scripts").glob("*.py")))
    candidates.append(project_root / "pyproject.toml")
    candidates.extend(sorted((project_root / "contracts").glob("*.schema.json")))

    entries: list[dict[str, str]] = []
    for path in sorted(set(candidates)):
        normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        entries.append(
            {
                "path": relative_posix(path, project_root),
                "sha256": sha256_bytes(normalized),
            }
        )
    listing = "".join(f"{row['sha256']}  {row['path']}\n" for row in entries)
    return {
        "type": "normalized_source_sha256",
        "sha256": sha256_bytes(listing.encode("utf-8")),
        "files": entries,
    }


def _prepare_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_output = output_dir.resolve()
    marker = output_dir / OUTPUT_MARKER_NAME
    project_root = Path(__file__).resolve().parents[2]
    if resolved_output == project_root or (resolved_output / "src" / "novel_evidence").is_dir():
        raise ValueError("refusing to use the source checkout as an artifact output directory")

    generated_targets = [(output_dir / name).resolve() for name in GENERATED_SUBDIRECTORIES]
    for target in generated_targets:
        if target.parent != resolved_output:
            raise ValueError(f"unsafe generated subdirectory: {target}")

    if marker.exists():
        if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != DEMO_MARKER:
            raise ValueError(f"invalid managed-output marker: {marker}")
    else:
        conflicts = [str(target) for target in generated_targets if target.exists()]
        if conflicts:
            raise ValueError(
                "refusing to clean an unmanaged output directory; generated-name "
                f"conflicts exist: {conflicts}"
            )
        marker.write_text(DEMO_MARKER + "\n", encoding="utf-8", newline="\n")

    for target in generated_targets:
        if target.exists():
            shutil.rmtree(target)


def _split_assignments(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "author_id": story["author_id"],
            "work_id": story["work_id"],
            "document_id": story["document_id"],
            "content_sha256": story["content_sha256"],
            "split": story["split"],
            "split_strategy": story["split_strategy"],
            "dataset_version": DATA_VERSION,
            "demo_marker": DEMO_MARKER,
            "demo": True,
        }
        for story in stories
    ]


def _managed_files(output_dir: Path) -> list[Path]:
    files: list[Path] = []
    marker = output_dir / OUTPUT_MARKER_NAME
    if marker.is_file():
        files.append(marker)
    for name in GENERATED_SUBDIRECTORIES:
        root = output_dir / name
        if root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(set(files))


def _artifact_inventory(
    output_dir: Path,
    record_counts: dict[str, int],
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    excluded = {
        "manifests/release_manifest.json",
        "manifests/checksums.sha256",
    }
    for path in _managed_files(output_dir):
        relative = relative_posix(path, output_dir)
        if relative in excluded:
            continue
        inventory.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "record_count": record_counts.get(relative),
            }
        )
    return inventory


def _write_checksums(output_dir: Path) -> int:
    checksum_path = output_dir / "manifests" / "checksums.sha256"
    paths = [
        path for path in _managed_files(output_dir) if path.resolve() != checksum_path.resolve()
    ]
    content = "".join(
        f"{sha256_file(path)}  {relative_posix(path, output_dir)}\n" for path in paths
    )
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text(content, encoding="utf-8", newline="\n")
    return len(paths)


def verify_checksums(output_dir: Path) -> list[str]:
    checksum_path = output_dir / "manifests" / "checksums.sha256"
    errors: list[str] = []
    for line_number, line in enumerate(
        checksum_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append(f"line_{line_number}:malformed")
            continue
        target = output_dir / Path(relative)
        if not target.is_file():
            errors.append(f"{relative}:missing")
        elif sha256_file(target) != expected:
            errors.append(f"{relative}:checksum_mismatch")
    return errors


def run_demo_pipeline(
    output_dir: Path,
    *,
    near_duplicate_threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    _prepare_output(output_dir)

    raw_records = generate_raw_records()
    rights_accepted, rights_rejected = partition_by_rights(raw_records)
    normalized = normalize_records(rights_accepted)
    canonical, duplicate_rejections = deduplicate(
        normalized, near_threshold=near_duplicate_threshold
    )
    split_stories = assign_splits(canonical)
    assert_no_leakage(split_stories)
    split_check = leakage_report(split_stories)

    story_catalog = build_story_catalog(split_stories)
    sft_samples = build_sft_samples(split_stories)
    sft_train = [sample for sample in sft_samples if sample["split"] == "train"]
    sft_validation = [
        sample for sample in sft_samples if sample["split"] == "validation"
    ]
    preference_train = build_preference_pairs(split_stories)
    evaluation_tasks = build_evaluation_tasks(split_stories, count=30)
    editor_events = build_editor_events(split_stories)
    dataset_isolation = validate_dataset_isolation(
        sft_samples, preference_train, evaluation_tasks
    )
    if dataset_isolation["status"] != "passed":
        raise RuntimeError(f"evaluation leakage: {dataset_isolation}")

    duplicate_counts = Counter(row["rejection_reason"] for row in duplicate_rejections)
    expected = {
        "raw_records": 27,
        "rights_accepted": 25,
        "rights_rejected": 2,
        "canonical_stories": 20,
        "exact_duplicates": 2,
        "near_duplicates": 3,
        "evaluation_tasks": 30,
    }
    actual = {
        "raw_records": len(raw_records),
        "rights_accepted": len(rights_accepted),
        "rights_rejected": len(rights_rejected),
        "canonical_stories": len(canonical),
        "exact_duplicates": duplicate_counts["exact_duplicate"],
        "near_duplicates": duplicate_counts["near_duplicate"],
        "evaluation_tasks": len(evaluation_tasks),
    }
    if actual != expected:
        raise RuntimeError(f"deterministic DEMO count contract failed: {actual} != {expected}")

    record_counts: dict[str, int] = {}

    def jsonl(relative: str, rows: list[dict[str, Any]]) -> None:
        record_counts[relative] = write_jsonl(output_dir / relative, rows)

    jsonl("raw/raw_records.jsonl", raw_records)
    jsonl("processed/rights_accepted.jsonl", rights_accepted)
    jsonl("processed/rights_rejected.jsonl", rights_rejected)
    jsonl("processed/normalized_records.jsonl", normalized)
    jsonl("processed/canonical_stories.jsonl", split_stories)
    jsonl("processed/duplicate_rejections.jsonl", duplicate_rejections)
    jsonl("datasets/story_catalog.jsonl", story_catalog)
    jsonl("datasets/split_assignments.jsonl", _split_assignments(split_stories))
    jsonl("datasets/sft_train.jsonl", sft_train)
    jsonl("datasets/sft_validation.jsonl", sft_validation)
    jsonl("datasets/preference_train.jsonl", preference_train)
    jsonl("datasets/evaluation_isolated.jsonl", evaluation_tasks)
    jsonl("operations/editor_events.jsonl", editor_events)

    write_json(output_dir / "metrics/split_leakage_report.json", split_check)
    write_json(output_dir / "metrics/dataset_isolation_report.json", dataset_isolation)
    metrics = build_quality_metrics(
        raw_records=raw_records,
        rights_accepted=rights_accepted,
        rights_rejected=rights_rejected,
        canonical_stories=split_stories,
        duplicate_rejections=duplicate_rejections,
        sft_train=sft_train,
        sft_validation=sft_validation,
        preference_train=preference_train,
        evaluation_tasks=evaluation_tasks,
        editor_events=editor_events,
        split_leakage=split_check,
        dataset_isolation=dataset_isolation,
    )
    write_json(output_dir / "metrics/quality_metrics.json", metrics)
    write_metric_csvs(output_dir / "metrics", metrics, editor_events)
    overview_path = output_dir / "reports/overview.html"
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(
        render_overview_html(metrics),
        encoding="utf-8",
        newline="\n",
    )

    lineage = {
        "demo": True,
        "demo_marker": DEMO_MARKER,
        "disclaimer": DEMO_DISCLAIMER,
        "run_id": RUN_ID,
        "dataset_version": DATA_VERSION,
        "rights_snapshot_version": RIGHTS_SNAPSHOT_VERSION,
        "training_run_id": TRAINING_RUN_ID,
        "training_run_status": "not_executed_demo_placeholder",
        "model_version": MODEL_VERSION,
        "model_status": "template_baseline_not_trained",
        "eval_version": EVALUATION_VERSION,
        "association": {
            "dataset_to_training_run": "declared_demo_input",
            "training_run_to_model": "no_training_executed",
            "model_to_evaluation": "template_baseline_demo_only",
        },
        "generated_at": GENERATED_AT,
    }
    write_json(output_dir / "manifests/version_lineage.json", lineage)

    inventory = _artifact_inventory(output_dir, record_counts)
    release_manifest = {
        "schema_version": "1.0.0",
        "pipeline_version": PIPELINE_VERSION,
        "source_snapshot": _source_snapshot(),
        "demo": True,
        "demo_marker": DEMO_MARKER,
        "disclaimer": DEMO_DISCLAIMER,
        "release_status": "DEMO_ONLY_NOT_FOR_PRODUCTION",
        "run_id": RUN_ID,
        "generated_at": GENERATED_AT,
        "dataset_version": DATA_VERSION,
        "rights_snapshot_version": RIGHTS_SNAPSHOT_VERSION,
        "training_run_id": TRAINING_RUN_ID,
        "model_version": MODEL_VERSION,
        "eval_version": EVALUATION_VERSION,
        "parameters": {
            "near_duplicate_threshold": near_duplicate_threshold,
            "split_strategy": "author_group_hash_v1",
            "split_ratio": {"train": 0.6, "validation": 0.2, "evaluation": 0.2},
            "evaluation_task_count": 30,
        },
        "counts": actual
        | {
            "sft_train_samples": len(sft_train),
            "sft_validation_samples": len(sft_validation),
            "preference_train_pairs": len(preference_train),
            "editor_events": len(editor_events),
        },
        "stage_lineage": [
            {"stage": 1, "name": "synthetic_ingestion", "output": "raw/raw_records.jsonl"},
            {
                "stage": 2,
                "name": "rights_validation",
                "output": "processed/rights_accepted.jsonl",
            },
            {
                "stage": 3,
                "name": "normalization",
                "output": "processed/normalized_records.jsonl",
            },
            {
                "stage": 4,
                "name": "sha256_and_minhash_lsh_dedup",
                "output": "processed/canonical_stories.jsonl",
            },
            {
                "stage": 5,
                "name": "author_group_split",
                "output": "datasets/split_assignments.jsonl",
            },
            {
                "stage": 6,
                "name": "dataset_derivation",
                "output": "datasets/",
            },
            {
                "stage": 7,
                "name": "quality_and_lineage",
                "output": "metrics/",
            },
        ],
        "validation": {
            "status": metrics["status"],
            "quality_gates": metrics["quality_gates"],
            "contracts": [
                "contracts/raw_record.schema.json",
                "contracts/canonical_story.schema.json",
                "contracts/sft_sample.schema.json",
                "contracts/preference_pair.schema.json",
                "contracts/evaluation_task.schema.json",
                "contracts/release_manifest.schema.json",
            ],
        },
        "files": inventory,
    }
    write_json(output_dir / "manifests/release_manifest.json", release_manifest)
    checksummed_files = _write_checksums(output_dir)
    checksum_errors = verify_checksums(output_dir)
    if checksum_errors:
        raise RuntimeError(f"checksum verification failed: {checksum_errors}")

    return {
        "demo": True,
        "status": "passed",
        "output_dir": str(output_dir.resolve()),
        "run_id": RUN_ID,
        "dataset_version": DATA_VERSION,
        "counts": release_manifest["counts"],
        "checksummed_files": checksummed_files,
        "overview": str(overview_path.resolve()),
        "manifest": str((output_dir / "manifests/release_manifest.json").resolve()),
    }
