"""Quality metrics, CSV exports, and a dependency-free offline HTML overview."""

from __future__ import annotations

import csv
import html
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from .constants import DEMO_DISCLAIMER, DEMO_MARKER, GENERATED_AT


def build_quality_metrics(
    *,
    raw_records: list[dict[str, Any]],
    rights_accepted: list[dict[str, Any]],
    rights_rejected: list[dict[str, Any]],
    canonical_stories: list[dict[str, Any]],
    duplicate_rejections: list[dict[str, Any]],
    sft_train: list[dict[str, Any]],
    sft_validation: list[dict[str, Any]],
    preference_train: list[dict[str, Any]],
    evaluation_tasks: list[dict[str, Any]],
    editor_events: list[dict[str, Any]],
    split_leakage: dict[str, Any],
    dataset_isolation: dict[str, Any],
) -> dict[str, Any]:
    duplicate_reasons = Counter(row["rejection_reason"] for row in duplicate_rejections)
    split_counts = Counter(story["split"] for story in canonical_stories)
    completed_sessions = [
        event for event in editor_events if event["event_type"] == "editing_session_completed"
    ]
    assisted = [event["duration_minutes"] for event in completed_sessions]
    baseline = [event["baseline_estimate_minutes"] for event in completed_sessions]
    assisted_mean = mean(assisted)
    baseline_mean = mean(baseline)
    time_reduction = (baseline_mean - assisted_mean) / baseline_mean
    raw_count = len(raw_records)
    accepted_count = len(rights_accepted)
    canonical_count = len(canonical_stories)

    return {
        "demo": True,
        "demo_marker": DEMO_MARKER,
        "disclaimer": DEMO_DISCLAIMER,
        "generated_at": GENERATED_AT,
        "status": (
            "passed"
            if canonical_count == 20
            and len(evaluation_tasks) == 30
            and split_leakage["status"] == "passed"
            and dataset_isolation["status"] == "passed"
            else "failed"
        ),
        "data_volume": {
            "raw_records": raw_count,
            "rights_accepted_records": accepted_count,
            "rights_rejected_records": len(rights_rejected),
            "canonical_stories": canonical_count,
            "sft_train_samples": len(sft_train),
            "sft_validation_samples": len(sft_validation),
            "preference_train_pairs": len(preference_train),
            "isolated_evaluation_tasks": len(evaluation_tasks),
            "editor_events": len(editor_events),
        },
        "retention": {
            "rights_acceptance_rate": round(accepted_count / raw_count, 6),
            "canonical_retention_from_raw": round(canonical_count / raw_count, 6),
            "canonical_retention_after_rights": round(canonical_count / accepted_count, 6),
        },
        "duplicates": {
            "exact_duplicate_records": duplicate_reasons["exact_duplicate"],
            "near_duplicate_records": duplicate_reasons["near_duplicate"],
            "total_duplicate_records": len(duplicate_rejections),
            "duplicate_rate_after_rights": round(
                len(duplicate_rejections) / accepted_count, 6
            ),
        },
        "split_distribution": dict(sorted(split_counts.items())),
        "leakage": {
            "split_leakage_status": split_leakage["status"],
            "dataset_isolation_status": dataset_isolation["status"],
            "author_overlap_count": split_leakage["overlap_counts"]["author_id"],
            "work_overlap_count": split_leakage["overlap_counts"]["work_id"],
            "content_overlap_count": split_leakage["overlap_counts"]["content_sha256"],
            "evaluation_training_author_overlap_count": len(
                dataset_isolation["author_overlap"]
            ),
            "evaluation_training_work_overlap_count": len(
                dataset_isolation["work_overlap"]
            ),
        },
        "editor_time": {
            "session_count": len(completed_sessions),
            "baseline_mean_minutes": round(baseline_mean, 2),
            "assisted_mean_minutes": round(assisted_mean, 2),
            "synthetic_time_reduction_rate": round(time_reduction, 6),
            "metric_warning": "Synthetic DEMO event data; not a measured productivity claim.",
        },
        "quality_gates": {
            "expected_canonical_story_count": canonical_count == 20,
            "expected_evaluation_task_count": len(evaluation_tasks) == 30,
            "author_work_content_leakage_zero": split_leakage["status"] == "passed",
            "evaluation_isolated_from_training": dataset_isolation["status"] == "passed",
            "all_records_marked_demo": all(row.get("demo") is True for row in raw_records),
        },
    }


def write_metric_csvs(
    metrics_dir: Path,
    metrics: dict[str, Any],
    editor_events: list[dict[str, Any]],
) -> None:
    metrics_dir.mkdir(parents=True, exist_ok=True)
    volume = metrics["data_volume"]
    stages = [
        ("raw_records", volume["raw_records"]),
        ("rights_accepted_records", volume["rights_accepted_records"]),
        ("canonical_stories", volume["canonical_stories"]),
    ]
    with (metrics_dir / "pipeline_funnel.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "stage",
                "records",
                "retention_from_previous",
                "retention_from_raw",
                "demo",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        previous = stages[0][1]
        raw = stages[0][1]
        for stage, records in stages:
            writer.writerow(
                {
                    "stage": stage,
                    "records": records,
                    "retention_from_previous": f"{records / previous:.6f}",
                    "retention_from_raw": f"{records / raw:.6f}",
                    "demo": "true",
                }
            )
            previous = records

    with (metrics_dir / "split_counts.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "stories", "demo"],
            lineterminator="\n",
        )
        writer.writeheader()
        for split, stories in sorted(metrics["split_distribution"].items()):
            writer.writerow({"split": split, "stories": stories, "demo": "true"})

    with (metrics_dir / "editor_time.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "session_id",
            "work_id",
            "split",
            "baseline_estimate_minutes",
            "duration_minutes",
            "revision_count",
            "demo",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for event in editor_events:
            if event["event_type"] != "editing_session_completed":
                continue
            writer.writerow({field: event.get(field) for field in fields})


def render_overview_html(metrics: dict[str, Any]) -> str:
    volume = metrics["data_volume"]
    duplicates = metrics["duplicates"]
    leakage = metrics["leakage"]
    editor = metrics["editor_time"]

    cards = [
        ("原始记录", volume["raw_records"]),
        ("最终唯一故事", volume["canonical_stories"]),
        ("SFT样本", volume["sft_train_samples"] + volume["sft_validation_samples"]),
        ("偏好对", volume["preference_train_pairs"]),
        ("隔离评测任务", volume["isolated_evaluation_tasks"]),
        ("重复记录", duplicates["total_duplicate_records"]),
    ]
    card_html = "".join(
        f'<section class="card"><strong>{html.escape(str(value))}</strong>'
        f"<span>{html.escape(label)}</span></section>"
        for label, value in cards
    )
    split_rows = "".join(
        f"<tr><td>{html.escape(split)}</td><td>{count}</td></tr>"
        for split, count in sorted(metrics["split_distribution"].items())
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DEMO 小说AI数据证据包概览</title>
  <style>
    :root {{ color-scheme: light; --ink:#17202a; --muted:#5d6d7e; --bg:#f4f6f7; --accent:#6c3483; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:15px/1.6 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif; color:var(--ink); background:var(--bg); }}
    header {{ padding:28px max(24px,6vw); color:white; background:linear-gradient(120deg,#4a235a,#1f618d); }}
    header h1 {{ margin:0 0 8px; }}
    .warning {{ margin:20px max(24px,6vw); padding:14px 18px; border:2px solid #b03a2e; background:#fdedec; color:#78281f; font-weight:700; }}
    main {{ max-width:1100px; margin:auto; padding:0 24px 48px; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:12px; }}
    .card {{ padding:18px; border-radius:12px; background:white; box-shadow:0 2px 12px #17202a18; }}
    .card strong {{ display:block; font-size:28px; color:var(--accent); }}
    .card span {{ color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; margin-top:18px; }}
    article {{ padding:20px; border-radius:12px; background:white; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:8px; text-align:left; border-bottom:1px solid #d5d8dc; }}
    code {{ background:#f2f3f4; padding:2px 5px; border-radius:4px; }}
  </style>
</head>
<body>
<header><h1>小说 AI 数据证据包 V0.1</h1><div>离线概览 · {GENERATED_AT} · {DEMO_MARKER}</div></header>
<div class="warning">{html.escape(DEMO_DISCLAIMER)}</div>
<main>
  <div class="cards">{card_html}</div>
  <div class="grid">
    <article><h2>数据切分</h2><table><tr><th>Split</th><th>故事数</th></tr>{split_rows}</table></article>
    <article><h2>泄漏门禁</h2>
      <p>作者重叠：<strong>{leakage["author_overlap_count"]}</strong></p>
      <p>作品重叠：<strong>{leakage["work_overlap_count"]}</strong></p>
      <p>内容哈希重叠：<strong>{leakage["content_overlap_count"]}</strong></p>
      <p>评测隔离：<strong>{html.escape(leakage["dataset_isolation_status"])}</strong></p>
    </article>
    <article><h2>编辑耗时（模拟）</h2>
      <p>基线均值：{editor["baseline_mean_minutes"]} 分钟</p>
      <p>辅助后均值：{editor["assisted_mean_minutes"]} 分钟</p>
      <p>模拟降幅：{editor["synthetic_time_reduction_rate"]:.1%}</p>
      <small>{html.escape(editor["metric_warning"])}</small>
    </article>
    <article><h2>重复治理</h2>
      <p>SHA精确重复：{duplicates["exact_duplicate_records"]}</p>
      <p>MinHash+LSH近重复：{duplicates["near_duplicate_records"]}</p>
      <p>授权后重复率：{duplicates["duplicate_rate_after_rights"]:.1%}</p>
    </article>
  </div>
</main>
</body>
</html>
"""
