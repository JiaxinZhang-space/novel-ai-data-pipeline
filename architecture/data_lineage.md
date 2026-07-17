# 数据血缘与撤回路径

> 状态：`DEMO`  
> 血缘结构可用于真实项目；文档中的标识符仅为示例，不是实际业务证据。

## 1. 主血缘图

```mermaid
flowchart TD
    R["rights_record_id<br/>版权判断与授权范围"]
    W["work_id / author_id<br/>作品与作者隔离单元"]
    D["document_id + content_sha256<br/>规范化文档"]
    S["sample_id / pair_id / eval_task_id<br/>派生样本"]
    DV["dataset_version + shard_id<br/>不可变数据版本"]
    TR["training_run_id<br/>训练配置、代码、随机种子"]
    MV["model_version + artifact_sha256<br/>模型制品"]
    EV["eval_version + rubric_version<br/>冻结评测资产"]
    ER["experiment_run_id<br/>基线、消融、盲测"]
    PR["publication_event_id / evidence_ref<br/>脱敏外部证据"]

    R --> W --> D --> S --> DV --> TR --> MV
    EV --> ER
    MV --> ER
    DV --> ER
    MV --> PR
```

## 2. 版本关系

```mermaid
erDiagram
    RIGHTS_RECORD ||--o{ WORK : authorizes
    WORK ||--o{ DOCUMENT : produces
    DOCUMENT ||--o{ SAMPLE : derives
    DATASET_VERSION ||--o{ SAMPLE : contains
    DATASET_VERSION ||--o{ TRAINING_RUN : consumed_by
    TRAINING_RUN ||--|| MODEL_VERSION : produces
    EVALUATION_VERSION ||--o{ EXPERIMENT_RUN : evaluates
    MODEL_VERSION ||--o{ EXPERIMENT_RUN : candidate_in
    RELEASE_MANIFEST }o--|| DATASET_VERSION : pins
    RELEASE_MANIFEST }o--|| MODEL_VERSION : pins
    RELEASE_MANIFEST }o--|| EVALUATION_VERSION : pins
```

## 3. 权利撤回影响分析

```mermaid
flowchart LR
    A["收到撤回或授权到期事件"]
    B["冻结 rights_record_id"]
    C["查询 work / document / sample 索引"]
    D["定位数据分片和数据版本"]
    E["定位训练运行和模型版本"]
    F{"是否已进入模型或发布？"}
    G["隔离数据并发布删除报告"]
    H["风险评估：回滚、重训或停用"]
    I["更新 Release Manifest 与证据索引"]

    A --> B --> C --> D --> E --> F
    F -- "否" --> G --> I
    F -- "是" --> H --> G
```

## 4. 每条血缘边的最低证据

| 血缘边 | 最低机器可读证据 |
|---|---|
| 权利记录 → 作品 | 版权台账中的 `rights_record_id`、`work_id`、用途范围和有效期 |
| 作品 → 文档 | 处理运行 ID、源文件哈希、规范化内容哈希 |
| 文档 → 样本 | 样本中的来源作品 ID、生成规则版本和父内容哈希 |
| 样本 → 数据版本 | 数据 Manifest 中的分片路径、计数和 SHA-256 |
| 数据版本 → 训练运行 | 模型 Manifest 中冻结的数据版本和配置哈希 |
| 训练运行 → 模型版本 | 训练运行 ID、模型制品 URI 和 SHA-256 |
| 模型 + 评测 → 实验 | 实验 Manifest、随机种子、候选盲化映射和结果文件哈希 |
| 模型 → 发布证据 | 脱敏事件引用和受控证据库中的原始凭证 |

## 5. 不接受的“伪血缘”

- 只在 README 中写“使用了某数据”，没有可校验的 Manifest。
- 只保存文件名，不保存内容哈希。
- 覆盖旧模型或旧数据后继续沿用原版本号。
- 由人工记忆回答某作品是否进入训练。
- 用 DEMO 标识符替代真实合同、发布或收入凭证。

