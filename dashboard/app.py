"""Streamlit dashboard for the novel AI evidence pack.

The dashboard never invents missing metrics. It reads generated artifacts when
available and shows explicit recovery guidance when files are absent or invalid.
Repository DEMO experiment samples are opt-in and remain visibly labelled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import plotly.express as px
import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_ROOT = REPO_ROOT / "artifacts"
DEMO_EXPERIMENT_ROOT = REPO_ROOT / "experiments" / "demo"

QUALITY_CANDIDATES = (
    "metrics/quality_metrics.json",
    "reports/quality_metrics.json",
    "quality_metrics.json",
)
FUNNEL_CANDIDATES = ("metrics/pipeline_funnel.csv",)
SPLIT_COUNT_CANDIDATES = ("metrics/split_counts.csv",)
RELEASE_CANDIDATES = (
    "manifests/release_manifest.json",
    "release_manifest.json",
)
OVERVIEW_REPORT_CANDIDATES = ("reports/overview.html",)
DATA_MANIFEST_CANDIDATES = (
    "manifests/data_manifest.json",
    "manifests/dataset_manifest.json",
)
MODEL_MANIFEST_CANDIDATES = ("manifests/model_manifest.json",)
EVALUATION_MANIFEST_CANDIDATES = (
    "manifests/evaluation_manifest.json",
    "manifests/eval_manifest.json",
)
EXPERIMENT_MANIFEST_CANDIDATES = (
    "experiments/experiment_manifest.json",
    "experiments/baseline_blind_experiment_manifest.json",
    "experiments/ablation_experiment_manifest.json",
)

BASELINE_CANDIDATES = (
    "experiments/baseline_results.csv",
    "experiments/baseline_results.json",
)
ABLATION_CANDIDATES = (
    "experiments/ablation_results.csv",
    "experiments/ablation_results.json",
)
BLIND_CANDIDATES = (
    "experiments/blind_evaluation_results.csv",
    "experiments/blind_evaluation_results.json",
    "experiments/blind_evaluation.csv",
)
EDITOR_EVENT_CANDIDATES = (
    "metrics/editor_efficiency.csv",
    "metrics/editor_time.csv",
    "operations/editor_events.jsonl",
    "datasets/editor_events.csv",
    "datasets/editor_events.json",
    "datasets/editor_events.jsonl",
)

DEMO_MARKER = "DEMO_SYNTHETIC_NOT_REAL_WORLD_EVIDENCE"


st.set_page_config(
    page_title="Novel AI Evidence Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
      --surface: #ffffff;
      --surface-muted: #f8fafc;
      --border: #cbd5e1;
      --text: #0f172a;
      --muted: #475569;
      --primary: #1d4ed8;
      --demo-bg: #fff7ed;
      --demo-border: #c2410c;
      --demo-text: #7c2d12;
    }
    .block-container {
      max-width: 1440px;
      padding-top: 2rem;
      padding-bottom: 3rem;
    }
    .evidence-banner {
      border: 2px solid var(--demo-border);
      background: var(--demo-bg);
      color: var(--demo-text);
      border-radius: 10px;
      padding: 14px 16px;
      margin: 8px 0 20px 0;
      font-weight: 650;
      line-height: 1.55;
    }
    .neutral-banner {
      border: 1px solid var(--border);
      background: var(--surface-muted);
      color: var(--text);
      border-radius: 10px;
      padding: 14px 16px;
      margin: 8px 0 20px 0;
      line-height: 1.55;
    }
    .status-label {
      display: inline-block;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 9px;
      margin-right: 6px;
      font-size: 0.82rem;
      font-weight: 650;
      background: var(--surface-muted);
      color: var(--text);
    }
    div[data-testid="stMetric"] {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
      background: var(--surface);
    }
    div[data-testid="stMetricValue"] {
      font-variant-numeric: tabular-nums;
    }
    .small-note {
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.55;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def resolve_user_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    resolved = path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        raise ValueError(
            "For public-demo safety, the dashboard only reads paths inside the repository."
        )
    return resolved


def locate_file(root: Path, candidates: Iterable[str]) -> Path | None:
    for relative_path in candidates:
        candidate = root / relative_path
        if candidate.is_file():
            return candidate

    if not root.is_dir():
        return None

    target_names = {Path(candidate).name for candidate in candidates}
    for name in sorted(target_names):
        matches = sorted(root.rglob(name))
        if matches:
            return matches[0]
    return None


def read_json_file(path: Path | None) -> tuple[Any | None, str | None]:
    if path is None:
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"{path}: {exc}"


def read_table_file(path: Path | None) -> tuple[pd.DataFrame | None, str | None]:
    if path is None:
        return None, None
    try:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path), None
        if suffix == ".jsonl":
            rows = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            return pd.DataFrame(rows), None
        if suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, list):
                return pd.DataFrame(value), None
            if isinstance(value, dict):
                rows = value.get("rows") or value.get("results") or value.get("records")
                if isinstance(rows, list):
                    return pd.DataFrame(rows), None
                return pd.json_normalize(value), None
            return None, f"{path}: JSON 顶层必须是对象或数组"
        return None, f"{path}: 不支持的表格格式 {suffix}"
    except (OSError, UnicodeError, json.JSONDecodeError, pd.errors.ParserError) as exc:
        return None, f"{path}: {exc}"


def search_key(value: Any, keys: Iterable[str]) -> Any:
    wanted = tuple(keys)
    queue = [value]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            for key in wanted:
                if key in current and current[key] is not None:
                    return current[key]
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return None


def nested_value(value: Any, *paths: str) -> Any:
    for path in paths:
        current = value
        found = True
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                found = False
                break
            current = current[key]
        if found and current is not None:
            return current
    return None


def number_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().rstrip("%"))
        except ValueError:
            return None
    return None


def format_count(value: Any) -> str:
    number = number_value(value)
    if number is None:
        return "缺失"
    return f"{int(number):,}" if number.is_integer() else f"{number:,.2f}"


def format_rate(value: Any) -> str:
    number = number_value(value)
    if number is None:
        return "缺失"
    if number > 1:
        number /= 100
    return f"{number:.1%}"


def contains_demo_marker(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("demo") is True:
            return True
        status = str(value.get("evidence_status", value.get("status", ""))).upper()
        if status == "DEMO":
            return True
        if DEMO_MARKER in str(value.get("demo_marker", "")):
            return True
        return any(contains_demo_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_demo_marker(item) for item in value)
    return DEMO_MARKER in str(value)


def dataframe_is_demo(frame: pd.DataFrame | None) -> bool:
    if frame is None or frame.empty:
        return False
    status_columns = [
        column
        for column in ("evidence_status", "status", "demo", "demo_marker", "disclaimer")
        if column in frame.columns
    ]
    for column in status_columns:
        values = frame[column].astype(str).str.upper()
        if values.str.contains("DEMO", regex=False).any() or values.eq("TRUE").any():
            return True
    return False


def mapping_to_frame(mapping: Any, key_name: str, value_name: str) -> pd.DataFrame:
    if not isinstance(mapping, dict):
        return pd.DataFrame(columns=[key_name, value_name])
    rows = []
    for key, value in mapping.items():
        if isinstance(value, dict):
            numeric = search_key(value, ("count", "records", "value"))
        else:
            numeric = value
        if number_value(numeric) is not None:
            rows.append({key_name: str(key), value_name: number_value(numeric)})
    return pd.DataFrame(rows)


def build_funnel(metrics: Any) -> pd.DataFrame:
    explicit = nested_value(
        metrics,
        "pipeline_counts",
        "funnel",
        "data_funnel",
        "quality.pipeline_counts",
    )
    if isinstance(explicit, dict):
        frame = mapping_to_frame(explicit, "阶段", "记录数")
        if not frame.empty:
            return frame
    if isinstance(explicit, list):
        rows = []
        for item in explicit:
            if not isinstance(item, dict):
                continue
            stage = search_key(item, ("stage", "name", "label"))
            count = search_key(item, ("count", "records", "value"))
            if stage is not None and number_value(count) is not None:
                rows.append({"阶段": str(stage), "记录数": number_value(count)})
        if rows:
            return pd.DataFrame(rows)

    aliases = (
        ("原始输入", ("input_count", "raw_count", "raw_record_count", "raw_records")),
        (
            "版权门通过",
            (
                "rights_accepted_count",
                "rights_pass_count",
                "eligible_record_count",
                "rights_accepted_records",
            ),
        ),
        ("规范化后", ("normalized_count", "normalized_record_count")),
        (
            "精确去重后",
            ("after_exact_dedup_count", "exact_dedup_output_count"),
        ),
        (
            "近似去重后",
            ("after_near_dedup_count", "near_dedup_output_count"),
        ),
        (
            "最终作品",
            (
                "output_count",
                "final_count",
                "accepted_work_count",
                "canonical_stories",
            ),
        ),
    )
    rows = []
    for label, keys in aliases:
        value = search_key(metrics, keys)
        if number_value(value) is not None:
            rows.append({"阶段": label, "记录数": number_value(value)})
    return pd.DataFrame(rows)


def build_filter_reasons(metrics: Any) -> pd.DataFrame:
    reasons = nested_value(
        metrics,
        "filter_reason_counts",
        "quality.filter_reason_counts",
        "rejections.by_reason",
    )
    explicit = mapping_to_frame(reasons, "过滤原因", "记录数")
    if not explicit.empty:
        return explicit

    aliases = (
        ("版权未通过", ("rights_rejected_records", "rights_rejected_count")),
        ("精确重复", ("exact_duplicate_records", "exact_duplicate_count")),
        ("近似重复", ("near_duplicate_records", "near_duplicate_count")),
    )
    rows = []
    for label, keys in aliases:
        value = search_key(metrics, keys)
        if number_value(value) is not None:
            rows.append({"过滤原因": label, "记录数": number_value(value)})
    return pd.DataFrame(rows)


def build_split_counts(metrics: Any) -> pd.DataFrame:
    splits = nested_value(
        metrics,
        "split_statistics",
        "split_counts",
        "split_distribution",
        "datasets.split_statistics",
    )
    return mapping_to_frame(splits, "数据切分", "记录数")


def normalize_funnel_table(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["阶段", "记录数"])
    if {"stage", "records"}.issubset(frame.columns):
        result = frame.rename(columns={"stage": "阶段", "records": "记录数"}).copy()
        result["记录数"] = pd.to_numeric(result["记录数"], errors="coerce")
        return result.dropna(subset=["记录数"])
    if {"阶段", "记录数"}.issubset(frame.columns):
        result = frame.copy()
        result["记录数"] = pd.to_numeric(result["记录数"], errors="coerce")
        return result.dropna(subset=["记录数"])
    return pd.DataFrame(columns=["阶段", "记录数"])


def normalize_split_table(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["数据切分", "记录数"])
    if {"split", "stories"}.issubset(frame.columns):
        result = frame.rename(columns={"split": "数据切分", "stories": "记录数"}).copy()
        result["记录数"] = pd.to_numeric(result["记录数"], errors="coerce")
        return result.dropna(subset=["记录数"])
    if {"数据切分", "记录数"}.issubset(frame.columns):
        result = frame.copy()
        result["记录数"] = pd.to_numeric(result["记录数"], errors="coerce")
        return result.dropna(subset=["记录数"])
    return pd.DataFrame(columns=["数据切分", "记录数"])


def editor_summary_from_events(
    events: pd.DataFrame | None,
) -> tuple[pd.DataFrame, dict[str, float | None]]:
    if events is None or events.empty:
        return pd.DataFrame(), {}

    frame = events.copy()
    if "event_type" in frame.columns:
        completed = frame["event_type"].astype(str).str.contains(
            "completed|submitted", case=False, regex=True
        )
        frame = frame.loc[completed].copy()

    baseline_column = next(
        (
            column
            for column in (
                "baseline_estimate_minutes",
                "baseline_minutes",
                "before_minutes",
            )
            if column in frame.columns
        ),
        None,
    )
    assisted_column = next(
        (
            column
            for column in (
                "duration_minutes",
                "assisted_minutes",
                "after_minutes",
                "active_edit_minutes",
            )
            if column in frame.columns
        ),
        None,
    )
    if assisted_column is None and "active_edit_seconds" in frame.columns:
        frame["active_edit_minutes"] = pd.to_numeric(
            frame["active_edit_seconds"], errors="coerce"
        ) / 60
        assisted_column = "active_edit_minutes"

    if baseline_column is None or assisted_column is None:
        return frame, {}

    frame[baseline_column] = pd.to_numeric(frame[baseline_column], errors="coerce")
    frame[assisted_column] = pd.to_numeric(frame[assisted_column], errors="coerce")
    valid = frame[[baseline_column, assisted_column]].dropna()
    if valid.empty:
        return frame, {}

    baseline_median = float(valid[baseline_column].median())
    assisted_median = float(valid[assisted_column].median())
    reduction = (
        (baseline_median - assisted_median) / baseline_median
        if baseline_median > 0
        else None
    )
    return frame, {
        "baseline_median": baseline_median,
        "assisted_median": assisted_median,
        "reduction": reduction,
        "session_count": float(len(valid)),
        "baseline_column": baseline_column,
        "assisted_column": assisted_column,
    }


def table_download(frame: pd.DataFrame, file_name: str, key: str) -> None:
    st.download_button(
        "导出当前表格 CSV",
        data=frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=file_name,
        mime="text/csv",
        key=key,
    )


def missing_artifact_panel(title: str, candidates: Iterable[str]) -> None:
    st.error(f"未找到{title}。看板不会用推测值补齐该区域。")
    st.markdown("预期候选路径：")
    st.code("\n".join(f"artifacts/{path}" for path in candidates), language="text")
    st.markdown("先在仓库根目录运行：")
    st.code(
        "python .\\scripts\\run_demo.py --output-dir .\\artifacts\n"
        "streamlit run .\\dashboard\\app.py",
        language="powershell",
    )


def show_read_error(error: str | None) -> None:
    if error:
        st.error(f"文件存在但读取失败：{error}")


def candidate_metric(metrics: Any, keys: Iterable[str], rate: bool = False) -> str:
    value = search_key(metrics, keys)
    return format_rate(value) if rate else format_count(value)


def experiment_source(
    artifacts_root: Path,
    candidates: Iterable[str],
    demo_name: str,
    allow_demo: bool,
) -> tuple[pd.DataFrame | None, Path | None, str | None, bool]:
    path = locate_file(artifacts_root, candidates)
    using_demo = False
    if path is None and allow_demo:
        demo_path = DEMO_EXPERIMENT_ROOT / demo_name
        if demo_path.is_file():
            path = demo_path
            using_demo = True
    frame, error = read_table_file(path)
    using_demo = using_demo or dataframe_is_demo(frame)
    return frame, path, error, using_demo


st.title("小说 AI 数据工程证据看板")
st.caption("读取运行产物、实验记录和版本关系；缺失数据不会被自动编造。")

with st.sidebar:
    st.header("数据源")
    artifacts_input = st.text_input(
        "Artifacts 目录",
        value=str(DEFAULT_ARTIFACTS_ROOT),
        help="仅允许仓库内部目录；相对路径按仓库根目录解析。",
    )
    try:
        artifacts_root = resolve_user_path(artifacts_input)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    allow_demo_experiments = st.checkbox(
        "实验产物缺失时显示 DEMO 样例",
        value=False,
        help="只影响实验页。样例始终显示 DEMO 警告，不能作为项目成果。",
    )
    if st.button("重新读取", use_container_width=True):
        st.rerun()
    st.divider()
    st.markdown("**当前读取目录**")
    st.code(str(artifacts_root), language="text")
    st.markdown(
        '<p class="small-note">正式面试材料应固定一次运行的目录或 Release Manifest，'
        "避免看板随临时文件变化。</p>",
        unsafe_allow_html=True,
    )


quality_path = locate_file(artifacts_root, QUALITY_CANDIDATES)
funnel_path = locate_file(artifacts_root, FUNNEL_CANDIDATES)
split_count_path = locate_file(artifacts_root, SPLIT_COUNT_CANDIDATES)
release_path = locate_file(artifacts_root, RELEASE_CANDIDATES)
overview_report_path = locate_file(artifacts_root, OVERVIEW_REPORT_CANDIDATES)
data_manifest_path = locate_file(artifacts_root, DATA_MANIFEST_CANDIDATES)
model_manifest_path = locate_file(artifacts_root, MODEL_MANIFEST_CANDIDATES)
evaluation_manifest_path = locate_file(artifacts_root, EVALUATION_MANIFEST_CANDIDATES)
experiment_manifest_path = locate_file(artifacts_root, EXPERIMENT_MANIFEST_CANDIDATES)
editor_path = locate_file(artifacts_root, EDITOR_EVENT_CANDIDATES)

quality_metrics, quality_error = read_json_file(quality_path)
pipeline_funnel, funnel_error = read_table_file(funnel_path)
split_counts, split_count_error = read_table_file(split_count_path)
release_manifest, release_error = read_json_file(release_path)
data_manifest, data_manifest_error = read_json_file(data_manifest_path)
model_manifest, model_manifest_error = read_json_file(model_manifest_path)
evaluation_manifest, evaluation_manifest_error = read_json_file(evaluation_manifest_path)
experiment_manifest, experiment_manifest_error = read_json_file(experiment_manifest_path)
editor_events, editor_error = read_table_file(editor_path)

loaded_documents = [
    document
    for document in (
        quality_metrics,
        release_manifest,
        data_manifest,
        model_manifest,
        evaluation_manifest,
        experiment_manifest,
    )
    if document is not None
]
demo_detected = any(contains_demo_marker(document) for document in loaded_documents)
demo_detected = demo_detected or dataframe_is_demo(editor_events)

if demo_detected:
    st.markdown(
        '<div class="evidence-banner"><span class="status-label">DEMO</span>'
        "当前产物包含合成故事、模拟编辑事件或模板模型标识。"
        "本看板只证明工程流程可以运行，不证明真实版权、模型效果、用户、发布或收入。</div>",
        unsafe_allow_html=True,
    )
elif loaded_documents:
    st.markdown(
        '<div class="neutral-banner"><span class="status-label">UNVERIFIED</span>'
        "已读取产物，但界面无法替代人工复核。请通过 Manifest 哈希、原始凭证和复核签字确认后，"
        "再引用为真实项目成果。</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="neutral-banner"><span class="status-label">NO ARTIFACTS</span>'
        "尚未读取到运行产物。下方会列出预期文件和生成命令。</div>",
        unsafe_allow_html=True,
    )


overview_tab, quality_tab, experiment_tab, editor_tab, lineage_tab = st.tabs(
    ["运行概览", "数据质量", "实验评估", "编辑效率", "版本血缘"]
)

with overview_tab:
    st.subheader("运行状态")
    expected_rows = [
        {
            "产物": "质量指标",
            "重要性": "必需",
            "状态": "已找到" if quality_path else "缺失",
            "路径": str(quality_path) if quality_path else "artifacts/metrics/quality_metrics.json",
        },
        {
            "产物": "处理漏斗",
            "重要性": "推荐",
            "状态": "已找到" if funnel_path else "缺失",
            "路径": str(funnel_path)
            if funnel_path
            else "artifacts/metrics/pipeline_funnel.csv",
        },
        {
            "产物": "发布关联 Manifest",
            "重要性": "必需",
            "状态": "已找到" if release_path else "缺失",
            "路径": (
                str(release_path)
                if release_path
                else "artifacts/manifests/release_manifest.json"
            ),
        },
        {
            "产物": "数据 Manifest",
            "重要性": "推荐",
            "状态": "已找到" if data_manifest_path else "缺失",
            "路径": str(data_manifest_path)
            if data_manifest_path
            else "artifacts/manifests/data_manifest.json",
        },
        {
            "产物": "编辑事件或效率表",
            "重要性": "推荐",
            "状态": "已找到" if editor_path else "缺失",
            "路径": str(editor_path)
            if editor_path
            else "artifacts/operations/editor_events.jsonl",
        },
        {
            "产物": "离线 HTML 概览",
            "重要性": "推荐",
            "状态": "已找到" if overview_report_path else "缺失",
            "路径": str(overview_report_path)
            if overview_report_path
            else "artifacts/reports/overview.html",
        },
    ]
    expected_frame = pd.DataFrame(expected_rows)
    st.dataframe(expected_frame, use_container_width=True, hide_index=True)

    if overview_report_path:
        try:
            st.download_button(
                "下载离线 HTML 概览",
                data=overview_report_path.read_bytes(),
                file_name="novel_ai_evidence_overview.html",
                mime="text/html",
                key="download-offline-overview",
            )
        except OSError as exc:
            st.error(f"离线 HTML 已找到但读取失败：{overview_report_path}: {exc}")

    if not artifacts_root.exists():
        st.error(f"Artifacts 目录不存在：{artifacts_root}")

    if quality_metrics is None:
        show_read_error(quality_error)
        missing_artifact_panel("质量指标 JSON", QUALITY_CANDIDATES)
    else:
        input_count = candidate_metric(
            quality_metrics,
            ("input_count", "raw_count", "raw_record_count", "raw_records"),
        )
        output_count = candidate_metric(
            quality_metrics,
            (
                "output_count",
                "final_count",
                "accepted_work_count",
                "canonical_stories",
            ),
        )
        retention_rate = candidate_metric(
            quality_metrics,
            ("retention_rate", "canonical_retention_from_raw"),
            rate=True,
        )
        final_status = search_key(
            quality_metrics,
            ("final_status", "quality_gate_status", "gate_status", "status"),
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("输入记录", input_count)
        col2.metric("最终作品", output_count)
        col3.metric("保留率", retention_rate)
        col4.metric("质量门状态", str(final_status or "缺失"))

        show_read_error(funnel_error)
        funnel_frame = normalize_funnel_table(pipeline_funnel)
        if funnel_frame.empty:
            funnel_frame = build_funnel(quality_metrics)
        if not funnel_frame.empty:
            st.subheader("数据处理漏斗")
            funnel_frame["记录数"] = pd.to_numeric(funnel_frame["记录数"])
            figure = px.bar(
                funnel_frame,
                x="阶段",
                y="记录数",
                text_auto=True,
                color_discrete_sequence=["#1d4ed8"],
            )
            figure.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title="记录数",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(figure, use_container_width=True)
            with st.expander("查看漏斗数据表"):
                st.dataframe(funnel_frame, use_container_width=True, hide_index=True)
                table_download(funnel_frame, "pipeline_funnel.csv", "download-funnel")
        else:
            st.info("质量 JSON 中没有可识别的漏斗字段；原始 JSON 可在“数据质量”页查看。")

with quality_tab:
    st.subheader("质量门与泄漏检查")
    if quality_metrics is None:
        show_read_error(quality_error)
        missing_artifact_panel("质量指标 JSON", QUALITY_CANDIDATES)
    else:
        exact_duplicates = search_key(
            quality_metrics,
            (
                "exact_duplicate_count",
                "exact_duplicates_removed",
                "exact_duplicate_records",
            ),
        )
        near_duplicates = search_key(
            quality_metrics,
            (
                "near_duplicate_count",
                "near_duplicates_removed",
                "near_duplicate_records",
            ),
        )
        author_overlap = search_key(
            quality_metrics,
            ("author_id_cross_split_count", "author_overlap_count"),
        )
        work_overlap = search_key(
            quality_metrics,
            ("work_id_cross_split_count", "work_overlap_count"),
        )
        evaluation_author_overlap = search_key(
            quality_metrics,
            (
                "evaluation_training_author_overlap_count",
                "evaluation_author_overlap_count",
            ),
        )
        evaluation_work_overlap = search_key(
            quality_metrics,
            (
                "evaluation_training_work_overlap_count",
                "evaluation_work_overlap_count",
            ),
        )
        content_overlap = search_key(
            quality_metrics,
            ("content_overlap_count", "evaluation_contamination_hit_count"),
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("精确重复", format_count(exact_duplicates))
        col2.metric("近似重复", format_count(near_duplicates))
        col3.metric("作者跨集", format_count(author_overlap))
        col4.metric("作品跨集", format_count(work_overlap))
        col5, col6, col7 = st.columns(3)
        col5.metric("评测-训练作者重叠", format_count(evaluation_author_overlap))
        col6.metric("评测-训练作品重叠", format_count(evaluation_work_overlap))
        col7.metric("内容哈希重叠", format_count(content_overlap))

        left, right = st.columns(2)
        with left:
            st.markdown("#### 过滤原因")
            filter_frame = build_filter_reasons(quality_metrics)
            if filter_frame.empty:
                st.info("没有可识别的 `filter_reason_counts`。")
            else:
                filter_frame = filter_frame.sort_values("记录数", ascending=True)
                figure = px.bar(
                    filter_frame,
                    x="记录数",
                    y="过滤原因",
                    orientation="h",
                    text_auto=True,
                    color_discrete_sequence=["#0f766e"],
                )
                figure.update_layout(
                    showlegend=False,
                    xaxis_title="记录数",
                    yaxis_title=None,
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(figure, use_container_width=True)
                st.dataframe(filter_frame, use_container_width=True, hide_index=True)
        with right:
            st.markdown("#### 切分分布")
            show_read_error(split_count_error)
            split_frame = normalize_split_table(split_counts)
            if split_frame.empty:
                split_frame = build_split_counts(quality_metrics)
            if split_frame.empty:
                st.info("没有可识别的 `split_statistics` 或 `split_counts`。")
            else:
                figure = px.bar(
                    split_frame,
                    x="数据切分",
                    y="记录数",
                    text_auto=True,
                    color_discrete_sequence=["#6d28d9"],
                )
                figure.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title="记录数",
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(figure, use_container_width=True)
                st.dataframe(split_frame, use_container_width=True, hide_index=True)

        with st.expander("查看质量指标原始 JSON"):
            st.caption(str(quality_path))
            st.json(quality_metrics, expanded=False)

with experiment_tab:
    st.subheader("基线、消融与盲测")
    st.caption(
        "Artifacts 中的实验文件优先。只有侧栏主动开启后，缺失区域才显示仓库内 DEMO 样例。"
    )

    baseline_frame, baseline_path, baseline_error, baseline_demo = experiment_source(
        artifacts_root,
        BASELINE_CANDIDATES,
        "baseline_results_demo.csv",
        allow_demo_experiments,
    )
    ablation_frame, ablation_path, ablation_error, ablation_demo = experiment_source(
        artifacts_root,
        ABLATION_CANDIDATES,
        "ablation_results_demo.csv",
        allow_demo_experiments,
    )
    blind_frame, blind_path, blind_error, blind_demo = experiment_source(
        artifacts_root,
        BLIND_CANDIDATES,
        "blind_evaluation_demo.csv",
        allow_demo_experiments,
    )

    for title, frame, path, error, is_demo in (
        ("基线对比", baseline_frame, baseline_path, baseline_error, baseline_demo),
        ("消融实验", ablation_frame, ablation_path, ablation_error, ablation_demo),
        ("盲测明细", blind_frame, blind_path, blind_error, blind_demo),
    ):
        st.markdown(f"### {title}")
        show_read_error(error)
        if frame is None:
            candidates = {
                "基线对比": BASELINE_CANDIDATES,
                "消融实验": ABLATION_CANDIDATES,
                "盲测明细": BLIND_CANDIDATES,
            }[title]
            st.warning(
                f"未找到{title}产物。可生成 artifacts 文件，"
                "或在侧栏主动开启带明显标记的 DEMO 样例。"
            )
            st.code("\n".join(f"artifacts/{item}" for item in candidates), language="text")
            continue

        if is_demo:
            st.warning("DEMO 合成结果：不能用于证明模型效果、编辑效率或简历成果。")
        st.caption(str(path))

        if title == "基线对比" and "mean_rubric_score" in frame.columns:
            chart_frame = frame.copy()
            label_column = next(
                (
                    column
                    for column in ("system_label", "candidate_id", "variant_id")
                    if column in chart_frame.columns
                ),
                None,
            )
            if label_column:
                figure = px.bar(
                    chart_frame,
                    x=label_column,
                    y="mean_rubric_score",
                    text_auto=".2f",
                    color_discrete_sequence=["#1d4ed8"],
                )
                figure.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title="平均量表分",
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(figure, use_container_width=True)

        if title == "消融实验" and "delta_mean_score_vs_full" in frame.columns:
            label_column = "variant_id" if "variant_id" in frame.columns else frame.columns[0]
            figure = px.bar(
                frame,
                x=label_column,
                y="delta_mean_score_vs_full",
                text_auto=".2f",
                color_discrete_sequence=["#6d28d9"],
            )
            figure.add_hline(y=0, line_color="#334155", line_width=1)
            figure.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title="相对完整系统分数变化",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(figure, use_container_width=True)

        if title == "盲测明细" and "preference" in frame.columns:
            winner_labels = []
            for _, row in frame.iterrows():
                preference = str(row.get("preference", "")).strip()
                if preference.upper() == "A":
                    winner_labels.append(str(row.get("candidate_a", "A")))
                elif preference.upper() == "B":
                    winner_labels.append(str(row.get("candidate_b", "B")))
                elif preference.lower() == "tie":
                    winner_labels.append("tie")
                else:
                    winner_labels.append("abstain")
            result_frame = (
                pd.Series(winner_labels, name="结果")
                .value_counts(dropna=False)
                .rename_axis("结果")
                .reset_index(name="数量")
            )
            figure = px.bar(
                result_frame,
                x="结果",
                y="数量",
                text_auto=True,
                color_discrete_sequence=["#0f766e"],
            )
            figure.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title="数量",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(figure, use_container_width=True)
            st.dataframe(result_frame, use_container_width=True, hide_index=True)

        with st.expander(f"查看{title}数据表"):
            st.dataframe(frame, use_container_width=True, hide_index=True)
            safe_name = title.replace(" ", "_")
            table_download(frame, f"{safe_name}.csv", f"download-{title}")

with editor_tab:
    st.subheader("编辑效率与事件口径")
    show_read_error(editor_error)
    editor_frame, editor_summary = editor_summary_from_events(editor_events)

    if editor_events is None:
        metric_editor_summary = nested_value(
            quality_metrics,
            "editor_efficiency",
            "editor_time",
            "metrics.editor_efficiency",
        )
        if isinstance(metric_editor_summary, dict):
            baseline = search_key(
                metric_editor_summary,
                (
                    "baseline_median_minutes",
                    "baseline_minutes",
                    "baseline_mean_minutes",
                ),
            )
            assisted = search_key(
                metric_editor_summary,
                (
                    "assisted_median_minutes",
                    "assisted_minutes",
                    "assisted_mean_minutes",
                ),
            )
            reduction = search_key(
                metric_editor_summary,
                (
                    "time_reduction_rate",
                    "reduction_rate",
                    "synthetic_time_reduction_rate",
                ),
            )
            col1, col2, col3 = st.columns(3)
            col1.metric("基线耗时中位数", f"{format_count(baseline)} 分钟")
            col2.metric("辅助后耗时中位数", f"{format_count(assisted)} 分钟")
            col3.metric("耗时变化", format_rate(reduction))
            st.info("当前展示质量 JSON 中的汇总值；没有加载可逐条复核的编辑事件表。")
        else:
            missing_artifact_panel("编辑事件或效率表", EDITOR_EVENT_CANDIDATES)
    elif editor_summary:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "有效编辑会话",
            format_count(editor_summary.get("session_count")),
        )
        col2.metric(
            "基线耗时中位数",
            f"{editor_summary['baseline_median']:.1f} 分钟",
        )
        col3.metric(
            "辅助后耗时中位数",
            f"{editor_summary['assisted_median']:.1f} 分钟",
        )
        col4.metric(
            "耗时变化",
            format_rate(editor_summary.get("reduction")),
        )

        baseline_column = str(editor_summary["baseline_column"])
        assisted_column = str(editor_summary["assisted_column"])
        plot_frame = editor_frame[[baseline_column, assisted_column]].rename(
            columns={
                baseline_column: "基线估计",
                assisted_column: "辅助后",
            }
        )
        long_frame = plot_frame.melt(
            var_name="工作方式",
            value_name="分钟",
        ).dropna()
        figure = px.box(
            long_frame,
            x="工作方式",
            y="分钟",
            points="all",
            color="工作方式",
            color_discrete_sequence=["#64748b", "#1d4ed8"],
        )
        figure.update_layout(
            xaxis_title=None,
            yaxis_title="分钟",
            legend_title=None,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(figure, use_container_width=True)
        st.caption(
            "耗时减少不等同于质量提升；必须同时报告通过率、返工率、任务复杂度和统计周期。"
        )
        with st.expander("查看编辑事件"):
            st.caption(str(editor_path))
            st.dataframe(editor_frame, use_container_width=True, hide_index=True)
            table_download(editor_frame, "editor_events.csv", "download-editor-events")
    else:
        st.warning(
            "已加载编辑事件文件，但没有同时识别出基线耗时和辅助后耗时列。"
            "请参照 dashboard/README.md 的字段约定。"
        )
        st.caption(str(editor_path))
        st.dataframe(editor_frame, use_container_width=True, hide_index=True)

with lineage_tab:
    st.subheader("数据、模型、评测与实验版本")
    show_read_error(release_error)
    show_read_error(data_manifest_error)
    show_read_error(model_manifest_error)
    show_read_error(evaluation_manifest_error)
    show_read_error(experiment_manifest_error)

    if release_manifest is None:
        missing_artifact_panel("Release Manifest", RELEASE_CANDIDATES)
    else:
        release_id = nested_value(release_manifest, "release_id", "run_id")
        data_version = nested_value(
            release_manifest,
            "data.version",
            "dataset.version",
            "data_version",
            "dataset_version",
        ) or search_key(data_manifest, ("dataset_version", "data_version"))
        model_version = nested_value(
            release_manifest,
            "model.version",
            "model_version",
        ) or search_key(model_manifest, ("model_version",))
        rights_snapshot_version = nested_value(
            release_manifest,
            "rights_snapshot.version",
            "rights_snapshot_version",
        )
        training_run_id = nested_value(
            release_manifest,
            "training_run_id",
        )
        evaluation_version = nested_value(
            release_manifest,
            "evaluation.version",
            "eval.version",
            "evaluation_version",
            "eval_version",
        ) or search_key(
            evaluation_manifest,
            ("evaluation_version", "eval_version"),
        )
        code_commit = nested_value(
            release_manifest,
            "code_commit",
            "code.commit",
        )
        source_snapshot = nested_value(
            release_manifest,
            "source_snapshot.sha256",
        )
        pipeline_version = nested_value(release_manifest, "pipeline_version")

        version_rows = [
            {"资产": "发布运行", "版本": release_id or "缺失", "要求": "必需"},
            {"资产": "管道", "版本": pipeline_version or "缺失", "要求": "必需"},
            {"资产": "权利快照", "版本": rights_snapshot_version or "缺失", "要求": "必需"},
            {"资产": "数据", "版本": data_version or "缺失", "要求": "必需"},
            {"资产": "训练运行", "版本": training_run_id or "缺失", "要求": "必需"},
            {"资产": "模型", "版本": model_version or "缺失", "要求": "必需"},
            {"资产": "评测", "版本": evaluation_version or "缺失", "要求": "必需"},
        ]
        code_version = code_commit or source_snapshot
        if code_version is not None:
            version_rows.append(
                {"资产": "代码", "版本": code_version, "要求": "必需"}
            )
        version_frame = pd.DataFrame(version_rows)
        st.dataframe(version_frame, use_container_width=True, hide_index=True)

        missing_versions = version_frame.loc[
            version_frame["版本"].eq("缺失") & version_frame["要求"].eq("必需"),
            "资产",
        ].tolist()
        if missing_versions:
            st.warning(
                "Release Manifest 尚未完整关联以下资产："
                + "、".join(missing_versions)
                + "。"
            )
        else:
            st.info(
                "版本关系字段已齐全；是否可信仍需校验每个子 Manifest 和文件 SHA-256。"
            )

        with st.expander("查看 Release Manifest 原始 JSON"):
            st.caption(str(release_path))
            st.json(release_manifest, expanded=False)

    manifest_rows = []
    for name, path, document in (
        ("数据 Manifest", data_manifest_path, data_manifest),
        ("模型 Manifest", model_manifest_path, model_manifest),
        ("评测 Manifest", evaluation_manifest_path, evaluation_manifest),
        ("实验 Manifest", experiment_manifest_path, experiment_manifest),
    ):
        status = (
            search_key(document, ("evidence_status", "status"))
            if document is not None
            else "缺失"
        )
        manifest_rows.append(
            {
                "Manifest": name,
                "状态": status or "未标注",
                "路径": str(path) if path else "缺失",
            }
        )
    st.markdown("### 子 Manifest 清单")
    st.dataframe(pd.DataFrame(manifest_rows), use_container_width=True, hide_index=True)
