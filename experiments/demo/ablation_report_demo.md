# 消融实验报告（DEMO）

> 证据状态：`DEMO`  
> 复核状态：`DEMO_NOT_REVIEWED`  
> 下列分数完全合成，只用于演示单变量消融报告结构。

## 1. 实验标识

| 字段 | DEMO值 |
|---|---|
| 实验运行 | `DEMO-ABLATION-001` |
| 数据版本 | `novel-demo-data-v0.1.0` |
| 评测版本 | `novel-gold-demo-v0.1.0` |
| 模型引用 | `template-candidate-demo-v0.1.0` |
| 实验Manifest | `ablation_experiment_manifest_demo.json` |
| 每个变体任务数 | 30 |

## 2. 变量控制

本示例假定评测任务、基础模型引用、提示模板、生成参数和量表不变，每个变体只移除或替换一个数据/工作流组件。

该假定只存在于DEMO元数据中，并没有真实训练或推理运行可以验证。

## 3. DEMO结果

| 变体 | 唯一声明差异 | 平均量表分 | 通过率 | 相对完整系统 |
|---|---|---:|---:|---:|
| `full_demo` | 无 | 3.80 | 70% | 0.00 |
| `no_near_dedup` | 移除近重复过滤 | 3.51 | 60% | -0.29 |
| `no_editor_diff` | 移除编辑修改样本 | 3.42 | 57% | -0.38 |
| `synthetic_only` | 只保留合成样本 | 3.28 | 50% | -0.52 |
| `no_story_bible` | 移除结构化故事上下文 | 3.36 | 53% | -0.44 |

## 4. DEMO解释

在这组虚构数字中，`synthetic_only`相对完整系统下降最大，为`-0.52`。这只演示如何定位值得进一步验证的组件，不能证明真实项目中合成数据一定有相同影响。

没有重复运行、方差、置信区间或真实错误样例，因此不能对组件贡献作因果判断。

## 5. 可复核引用

- 原始表：`ablation_results_demo.csv`
- Manifest：`ablation_experiment_manifest_demo.json`
- Manifest记录原始表的记录数和SHA-256。

## 6. DEMO决策

`REPEAT_WITH_REAL_RUNS`：真实项目应使用多个随机种子重复训练或生成，报告均值、离散程度、成本与失败案例后再决定组件取舍。

