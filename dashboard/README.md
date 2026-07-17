# Streamlit 证据看板

看板读取 `artifacts/` 中的运行产物，不会为缺失指标填入推测值。

## 启动

```powershell
python .\scripts\run_demo.py --output-dir .\artifacts
python -m pip install -r .\requirements-dashboard.txt
streamlit run .\dashboard\app.py
```

也可以在侧栏填写仓库内部的另一次运行目录。公开 Demo 会拒绝解析到仓库外部的路径，避免托管看板读取服务器上的任意文件。

## 核心候选路径

看板会先按以下路径读取；文件位于更深目录时，也会按文件名做兼容查找。

```text
artifacts/
├─ metrics/
│  ├─ quality_metrics.json
│  ├─ pipeline_funnel.csv
│  ├─ split_counts.csv
│  ├─ editor_efficiency.csv
│  └─ editor_time.csv
├─ operations/
│  └─ editor_events.jsonl
├─ experiments/
│  ├─ baseline_results.csv
│  ├─ ablation_results.csv
│  ├─ blind_evaluation_results.csv
│  ├─ baseline_blind_experiment_manifest.json
│  └─ ablation_experiment_manifest.json
├─ manifests/
│  ├─ release_manifest.json
│  ├─ data_manifest.json
│  ├─ model_manifest.json
│  └─ evaluation_manifest.json
└─ reports/
   └─ overview.html
```

最低必需文件：

- `artifacts/metrics/quality_metrics.json`
- `artifacts/manifests/release_manifest.json`

## `quality_metrics.json` 兼容字段

当前核心管道输出以下嵌套结构；看板同时兼容早期扁平字段：

```json
{
  "demo": true,
  "demo_marker": "DEMO_SYNTHETIC_NOT_REAL_WORLD_EVIDENCE",
  "status": "passed",
  "data_volume": {
    "raw_records": 27,
    "rights_accepted_records": 25,
    "rights_rejected_records": 2,
    "canonical_stories": 20,
    "isolated_evaluation_tasks": 30
  },
  "retention": {
    "rights_acceptance_rate": 0.925926,
    "canonical_retention_after_rights": 0.8,
    "canonical_retention_from_raw": 0.740741
  },
  "duplicates": {
    "exact_duplicate_records": 2,
    "near_duplicate_records": 3,
    "total_duplicate_records": 5
  },
  "split_distribution": {
    "train": 12,
    "validation": 4,
    "evaluation": 4
  },
  "leakage": {
    "author_overlap_count": 0,
    "work_overlap_count": 0,
    "content_overlap_count": 0,
    "evaluation_training_author_overlap_count": 0,
    "evaluation_training_work_overlap_count": 0
  },
  "editor_time": {
    "baseline_mean_minutes": 84,
    "assisted_mean_minutes": 45,
    "synthetic_time_reduction_rate": 0.464286
  }
}
```

示例只用于解释字段，不能直接复制成运行结果。

## 编辑事件最低字段

看板会筛选 `event_type` 包含 `completed` 或 `submitted` 的记录，并识别：

| 含义 | 兼容列 |
|---|---|
| 基线耗时 | `baseline_estimate_minutes`、`baseline_minutes`、`before_minutes` |
| 辅助后耗时 | `duration_minutes`、`assisted_minutes`、`after_minutes`、`active_edit_minutes` |
| 秒级主动编辑耗时 | `active_edit_seconds`，看板自动除以 60 |

编辑效率必须与质量、返工和任务难度一起解释，不能单独声称生产率提升。

核心DEMO会优先读取`artifacts/metrics/editor_time.csv`作为可视化明细；如果该文件
不存在，也可读取`artifacts/operations/editor_events.jsonl`。运行概览页会识别并提供
`artifacts/reports/overview.html`的下载入口。

## 实验 DEMO 回退

侧栏的“实验产物缺失时显示 DEMO 样例”默认关闭。开启后只会读取：

- `experiments/demo/baseline_results_demo.csv`
- `experiments/demo/ablation_results_demo.csv`
- `experiments/demo/blind_evaluation_demo.csv`

界面会持续显示 DEMO 警告；这些数字不能进入简历。
