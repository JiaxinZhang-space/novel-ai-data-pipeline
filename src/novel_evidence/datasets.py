"""Derive SFT, preference, isolated evaluation, and editor-event datasets."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .constants import DATA_VERSION, DEMO_MARKER, EVALUATION_VERSION


def _paragraphs(story: dict[str, Any]) -> list[str]:
    return [part.strip() for part in story["normalized_text"].split("\n") if part.strip()]


def build_story_catalog(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "story_id": story["work_id"],
            "work_id": story["work_id"],
            "author_id": story["author_id"],
            "title": story["title"],
            "genre": story["genre"],
            "language": story["language"],
            "split": story["split"],
            "content_sha256": story["content_sha256"],
            "source_record_id": story["record_id"],
            "source_id": story["source_id"],
            "document_id": story["document_id"],
            "rights_record_id": story["rights_record_id"],
            "rights_contract_id": story["rights"]["contract_id"],
            "dataset_version": DATA_VERSION,
            "character_count": len(story["normalized_text"]),
            "demo_marker": DEMO_MARKER,
            "demo": True,
        }
        for story in stories
    ]


def build_sft_samples(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for story in stories:
        if story["split"] == "evaluation":
            continue
        parts = _paragraphs(story)
        tasks = [
            (
                "brief_to_opening",
                f"请为“大女主现实向短篇”写一个克制但有悬念的开场。标题：{story['title']}",
                parts[0],
            ),
            (
                "evidence_driven_escalation",
                f"围绕作品《{story['title']}》续写一段依靠证据推进、避免主角突然开挂的冲突升级。",
                parts[1],
            ),
            (
                "resolution_with_cost",
                f"为《{story['title']}》写一个主角获胜但承担现实代价的结局，保持人物行动逻辑一致。",
                parts[-1],
            ),
        ]
        for task_index, (task_type, instruction, response) in enumerate(tasks, start=1):
            samples.append(
                {
                    "sample_id": f"SFT-{story['work_id']}-{task_index:02d}",
                    "task_type": task_type,
                    "instruction": instruction,
                    "input": {
                        "genre": story["genre"],
                        "title": story["title"],
                        "author_group": story["author_id"],
                    },
                    "response": response,
                    "source_work_id": story["work_id"],
                    "source_author_id": story["author_id"],
                    "work_id": story["work_id"],
                    "author_id": story["author_id"],
                    "source_id": story["source_id"],
                    "document_id": story["document_id"],
                    "rights_record_id": story["rights_record_id"],
                    "content_sha256": story["content_sha256"],
                    "dataset_version": DATA_VERSION,
                    "shard_id": f"sft-{story['split']}-00000",
                    "split": story["split"],
                    "data_status": "synthetic_editor_approved_demo",
                    "demo_marker": DEMO_MARKER,
                    "demo": True,
                }
            )
    return samples


def build_preference_pairs(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for story in stories:
        if story["split"] != "train":
            continue
        parts = _paragraphs(story)
        prompts = [
            f"续写《{story['title']}》的调查转折，要求线索可以复核。",
            f"改写《{story['title']}》的收束段，要求胜利伴随现实代价。",
        ]
        chosen = [parts[2], parts[-1]]
        rejected = [
            "她突然获得所有人的支持，反派当场认错，一切问题在几分钟内彻底解决。",
            "她毫无代价地赢得财富、名声与爱情，从此再也没有遇到任何困难。",
        ]
        reasons = [
            ["证据链完整", "人物行动连续", "避免无依据反转"],
            ["结局有代价", "主题闭合", "避免爽点替代因果"],
        ]
        for index in range(2):
            pairs.append(
                {
                    "pair_id": f"PREF-{story['work_id']}-{index + 1:02d}",
                    "sample_id": f"PREF-{story['work_id']}-{index + 1:02d}",
                    "prompt": prompts[index],
                    "chosen": chosen[index],
                    "rejected": rejected[index],
                    "preference_reasons": reasons[index],
                    "source_work_id": story["work_id"],
                    "source_author_id": story["author_id"],
                    "work_id": story["work_id"],
                    "author_id": story["author_id"],
                    "source_id": story["source_id"],
                    "document_id": story["document_id"],
                    "rights_record_id": story["rights_record_id"],
                    "content_sha256": story["content_sha256"],
                    "dataset_version": DATA_VERSION,
                    "shard_id": "preference-train-00000",
                    "split": "train",
                    "label_source": "deterministic_synthetic_editor_rubric_demo",
                    "demo_marker": DEMO_MARKER,
                    "demo": True,
                }
            )
    return pairs


def build_evaluation_tasks(stories: list[dict[str, Any]], count: int = 30) -> list[dict[str, Any]]:
    evaluation_stories = [story for story in stories if story["split"] == "evaluation"]
    if not evaluation_stories:
        raise ValueError("evaluation split must contain at least one story")
    task_types = [
        "opening_quality",
        "character_consistency",
        "evidence_chain",
        "conflict_escalation",
        "costly_resolution",
    ]
    tasks: list[dict[str, Any]] = []
    for index in range(count):
        story = evaluation_stories[index % len(evaluation_stories)]
        parts = _paragraphs(story)
        task_type = task_types[index % len(task_types)]
        reference = parts[index % len(parts)]
        tasks.append(
            {
                "eval_id": f"EVAL-{index + 1:03d}",
                "sample_id": f"EVAL-{index + 1:03d}",
                "task_type": task_type,
                "prompt": (
                    f"根据标题《{story['title']}》完成{task_type}任务。"
                    "答案应保持现实因果、女性主体性和证据可复核性。"
                ),
                "context": {
                    "genre": story["genre"],
                    "title": story["title"],
                    "prohibited_shortcuts": ["突然开挂", "反派无条件认错", "无代价胜利"],
                },
                "reference_answer": reference,
                "rubric": {
                    "dimensions": [
                        "causal_coherence",
                        "character_agency",
                        "evidence_grounding",
                        "style_control",
                    ],
                    "score_range": [1, 5],
                    "pass_score": 16,
                },
                "source_work_id": story["work_id"],
                "source_author_id": story["author_id"],
                "work_id": story["work_id"],
                "author_id": story["author_id"],
                "source_id": story["source_id"],
                "document_id": story["document_id"],
                "rights_record_id": story["rights_record_id"],
                "content_sha256": story["content_sha256"],
                "dataset_version": DATA_VERSION,
                "eval_version": EVALUATION_VERSION,
                "shard_id": "evaluation-isolated-00000",
                "split": "evaluation",
                "isolation_assertion": "author_and_work_absent_from_sft_and_preference",
                "demo_marker": DEMO_MARKER,
                "demo": True,
            }
        )
    return tasks


def build_editor_events(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    origin = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)
    for index, story in enumerate(stories):
        baseline_minutes = 72 + (index % 5) * 6
        assisted_minutes = 39 + (index % 4) * 4
        started_at = origin + timedelta(days=index, minutes=index * 3)
        completed_at = started_at + timedelta(minutes=assisted_minutes)
        session_id = f"DEMO-EDIT-{index + 1:03d}"
        events.extend(
            [
                {
                    "event_id": f"{session_id}-START",
                    "session_id": session_id,
                    "event_type": "editing_session_started",
                    "occurred_at": started_at.isoformat().replace("+00:00", "Z"),
                    "editor_id": "DEMO-EDITOR-01",
                    "work_id": story["work_id"],
                    "author_id": story["author_id"],
                    "source_id": story["source_id"],
                    "content_sha256": story["content_sha256"],
                    "document_id": story["document_id"],
                    "rights_record_id": story["rights_record_id"],
                    "dataset_version": DATA_VERSION,
                    "split": story["split"],
                    "demo_marker": DEMO_MARKER,
                    "demo": True,
                },
                {
                    "event_id": f"{session_id}-END",
                    "session_id": session_id,
                    "event_type": "editing_session_completed",
                    "occurred_at": completed_at.isoformat().replace("+00:00", "Z"),
                    "editor_id": "DEMO-EDITOR-01",
                    "work_id": story["work_id"],
                    "author_id": story["author_id"],
                    "source_id": story["source_id"],
                    "content_sha256": story["content_sha256"],
                    "document_id": story["document_id"],
                    "rights_record_id": story["rights_record_id"],
                    "dataset_version": DATA_VERSION,
                    "split": story["split"],
                    "duration_minutes": assisted_minutes,
                    "baseline_estimate_minutes": baseline_minutes,
                    "revision_count": 1 + index % 3,
                    "outcome": "approved_for_demo_dataset",
                    "demo_marker": DEMO_MARKER,
                    "demo": True,
                },
            ]
        )
    return events


def validate_dataset_isolation(
    sft_samples: list[dict[str, Any]],
    preference_pairs: list[dict[str, Any]],
    evaluation_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    training_authors = {
        sample["source_author_id"] for sample in sft_samples
    } | {pair["source_author_id"] for pair in preference_pairs}
    training_works = {
        sample["source_work_id"] for sample in sft_samples
    } | {pair["source_work_id"] for pair in preference_pairs}
    evaluation_authors = {task["source_author_id"] for task in evaluation_tasks}
    evaluation_works = {task["source_work_id"] for task in evaluation_tasks}
    author_overlap = sorted(training_authors & evaluation_authors)
    work_overlap = sorted(training_works & evaluation_works)
    return {
        "demo": True,
        "status": "passed" if not author_overlap and not work_overlap else "failed",
        "training_author_count": len(training_authors),
        "evaluation_author_count": len(evaluation_authors),
        "training_work_count": len(training_works),
        "evaluation_work_count": len(evaluation_works),
        "author_overlap": author_overlap,
        "work_overlap": work_overlap,
    }
