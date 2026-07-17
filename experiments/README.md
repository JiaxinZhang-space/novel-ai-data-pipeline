# 实验证据目录

本目录提供基线、消融和盲测的可复用报告模板，以及一组明确标注为 `DEMO` 的合成结果。

## 使用规则

1. `templates/` 中只保存空白协议和报告结构，不预填项目成果。
2. `demo/` 中的数字完全是合成示例，只用于演示字段、图表和计算口径。
3. 真实实验应输出到 `artifacts/experiments/`，并由 Release Manifest 固定数据、模型、评测、代码和随机种子版本。
4. 不得把 `demo/` 的胜率、评分、编辑耗时或样本量写入简历。
5. 比较实验必须一次只改变声明的变量；不能同时更换模型、提示词、采样参数和数据集后归因于其中一个因素。

## 推荐真实产物

```text
artifacts/experiments/
├─ baseline_results.csv
├─ ablation_results.csv
├─ blind_evaluation_results.csv
├─ baseline_blind_experiment_manifest.json
├─ ablation_experiment_manifest.json
└─ reports/
   ├─ baseline_report.md
   ├─ ablation_report.md
   └─ blind_evaluation_report.md
```

## DEMO 文件说明

| 文件 | 用途 |
|---|---|
| `demo/baseline_results_demo.csv` | 演示基线与候选系统对比字段 |
| `demo/ablation_results_demo.csv` | 演示一次移除一个组件的消融结果 |
| `demo/blind_evaluation_demo.csv` | 演示盲化候选、偏好、平局和弃权记录 |
| `demo/baseline_blind_experiment_manifest_demo.json` | 关联可对账的基线汇总和盲测明细 |
| `demo/ablation_experiment_manifest_demo.json` | 独立记录消融变体及结果文件哈希 |
| `demo/baseline_report_demo.md` | 已填充的基线报告示例 |
| `demo/ablation_report_demo.md` | 已填充的消融报告示例 |
| `demo/blind_evaluation_report_demo.md` | 已填充的盲测报告示例 |
