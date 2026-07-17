# 数据字典

> 状态：`DEMO / 目标 Schema`  
> 时间字段采用 ISO 8601 并包含时区；哈希统一为小写十六进制 SHA-256；布尔值统一为 `true/false`。

## 1. 跨表标识符

| 字段 | 类型 | 必填 | 定义 |
|---|---|---:|---|
| `rights_record_id` | string | 是 | 一次独立权利判断的不可变标识 |
| `source_id` | string | 是 | 来源批次或来源对象标识 |
| `author_id` | string | 是 | 不可逆化名；真实身份只存在受控证据库 |
| `work_id` | string | 是 | 完整作品标识；切分和去重的基本隔离单位 |
| `document_id` | string | 是 | 某作品在某处理阶段的文档实例 |
| `sample_id` | string | 条件必填 | 各任务样本的通用关联键；SFT 主键，偏好和评测均携带 |
| `pair_id` | string | 偏好必填 | 偏好训练对主键 |
| `eval_id` | string | 评测必填 | 评测任务主键 |
| `dataset_version` | string | 是 | 不可变数据集版本；当前为 `novel-demo-data-v0.1.0` |
| `shard_id` | string | 是 | 数据版本内的物理分片标识 |
| `training_run_id` | string | 训练时 | 一次可复现训练运行 |
| `model_version` | string | 模型时 | 可部署或归档的模型制品版本 |
| `eval_version` | string | 评测时 | 固定任务集、裁判规则和代码版本 |
| `content_sha256` | string(64) | 是 | 规范化文本的内容哈希 |

## 2. `rights_ledger`

| 字段 | 类型 | 必填 | 定义 |
|---|---|---:|---|
| `record_status` | enum | 是 | 本 DEMO 台账固定为 `DEMO`；真实台账另行定义审核状态，不复用对外证据状态 |
| `rights_record_id` | string | 是 | 权利判断主键 |
| `source_id` / `work_id` / `author_id` | string | 是 | 来源、作品、作者化名 |
| `rightsholder_type` | enum | 是 | 团队作者、委托作者、第三方权利人等 |
| `source_type` | enum | 是 | 原创、委托、公版、采购、正式授权 |
| `acquisition_method` | string | 是 | 获取路径，不等同权利基础 |
| `rights_basis` | string | 是 | 合同、转让、许可或公版复核结论 |
| `license_or_contract_id` | string | 是 | 只保存脱敏编号 |
| `*_allowed` | boolean | 是 | 训练、评测、生成、发布、商业衍生、原文再分发分别判断 |
| `territory` | string | 是 | 授权地域 |
| `valid_from` / `valid_until` | date | 是 | 使用期限；永久许可也应使用明确枚举而非留空 |
| `revocable` | boolean | 是 | 是否存在撤回机制 |
| `withdrawal_status` | enum | 是 | `not_requested/requested/effective/rejected/disputed` |
| `withdrawal_requested_at` / `withdrawal_effective_at` | datetime | 条件必填 | 撤回时必填 |
| `source_file_sha256` | string(64) | 是 | 原始文件哈希 |
| `normalized_content_sha256` | string(64) | 是 | 规范化正文哈希 |
| `evidence_file_sha256` | string(64) | 是 | 授权证据哈希 |
| `evidence_ref` | string | 是 | 受控证据库引用 |
| `dataset_versions` / `shard_ids` | list[string] | 派生后 | 被哪些数据制品消费 |
| `training_run_ids` / `model_versions` | list[string] | 训练后 | 被哪些训练和模型消费 |
| `reviewer_id` / `reviewed_at` | string/datetime | 是 | 权利复核记录 |

生产系统中的列表字段建议拆成关联表；CSV 演示中仅为提高可读性。

## 3. `removal_ledger`

| 字段 | 类型 | 必填 | 定义 |
|---|---|---:|---|
| `removal_request_id` | string | 是 | 撤回/删除事件主键 |
| `rights_record_id` / `work_id` | string | 是 | 受影响权利与作品 |
| `request_reason` / `request_channel` | string | 是 | 原因与可核验渠道 |
| `requested_at` / `effective_deadline` | datetime | 是 | 受理与完成时限 |
| `source_file_sha256` / `normalized_content_sha256` | string(64) | 是 | 用于反向定位 |
| `impacted_dataset_versions` / `impacted_shard_ids` | list[string] | 是 | 受影响数据制品 |
| `impacted_sample_index_ref` | string | 是 | 受影响样本清单的受控引用 |
| `impacted_training_run_ids` / `impacted_model_versions` | list[string] | 是 | 模型影响范围 |
| `source_action` / `dataset_action` / `model_action` | enum/string | 是 | 各层补救措施 |
| `verification_query_ref` / `verification_result` | string | 是 | 删除后验证 |
| `status` | enum | 是 | `received/in_progress/blocked/completed/rejected` |
| `evidence_ref` / `approved_by` | string | 是 | 执行证据和批准人 |

## 4. `works.jsonl`

一行对应一个规范化作品文档。

| 字段 | 类型 | 必填 | 约束/说明 |
|---|---|---:|---|
| `document_id` | string | 是 | 唯一 |
| `work_id` | string | 是 | 必须存在于权利台账 |
| `author_id` | string | 是 | 用于作者级隔离 |
| `rights_record_id` | string | 是 | 必须为有效授权状态 |
| `source_id` | string | 是 | 来源批次 |
| `source_file_sha256` | string | 是 | 原始文件哈希 |
| `content_sha256` | string | 是 | 规范化正文哈希 |
| `title_redacted` | string | 是 | 可公开展示的脱敏标题 |
| `genre` | string | 是 | 受控词表 |
| `language` | string | 是 | BCP-47，如 `zh-CN` |
| `text` | string | 是 | 仅存在于访问受控的数据区 |
| `char_count` | integer | 是 | 大于 0 |
| `processing_version` | string | 是 | 清洗代码/规则版本 |
| `split` | enum | 是 | 当前机器 Schema 为 `train/validation/evaluation`；作品只会进入其中一个分组 |
| `created_at` | datetime | 是 | 记录生成时间 |

## 5. `sft.jsonl`

| 字段 | 类型 | 必填 | 约束/说明 |
|---|---|---:|---|
| `sample_id` | string | 是 | 唯一 |
| `task_type` | enum | 是 | `brief_to_bible/bible_to_beats/beat_to_scene/rewrite/...` |
| `instruction` | string | 是 | 用户任务 |
| `input` | object/string | 是 | 结构化上下文 |
| `response` | string | 是 | 监督答案；实际 Schema 不使用 `output` |
| `source_work_id` / `source_author_id` | string | 是 | 数据来源的作品与作者 |
| `work_id` / `author_id` | string | 是 | 当前样本的作品与作者隔离键 |
| `source_id` / `document_id` | string | 是 | 来源和规范化文档 |
| `rights_record_id` | string | 是 | 可反查权利 |
| `content_sha256` | string(64) | 是 | 规范化样本内容哈希 |
| `dataset_version` | string | 是 | 数据版本 |
| `shard_id` | string | 是 | 物理分片 |
| `split` | enum | 是 | `train/validation` |
| `demo` | boolean | 是 | DEMO 制品恒为 `true` |
| `editor_id` / `acceptance_tier` / `label_version` | string | 否 | 可选审核元数据，不是当前必填 Schema |

## 6. `preferences.jsonl`（训练对）

| 字段 | 类型 | 必填 | 约束/说明 |
|---|---|---:|---|
| `pair_id` | string | 是 | 唯一 |
| `sample_id` | string | 是 | 训练对关联键 |
| `prompt` | string/object | 是 | 比较任务输入 |
| `chosen` / `rejected` | string | 是 | 已裁决的优选与劣选答案 |
| `preference_reasons` | array[string] | 是 | 至少一个分维度原因 |
| `source_work_id` / `source_author_id` | string | 是 | 来源作品与作者 |
| `work_id` / `author_id` | string | 是 | 当前样本隔离键 |
| `source_id` / `document_id` | string | 是 | 来源和文档 |
| `rights_record_id` / `content_sha256` | string | 是 | 权利与内容追踪 |
| `dataset_version` / `shard_id` | string | 是 | 数据版本和分片 |
| `split` | enum | 是 | 当前 Schema 固定为 `train` |
| `demo` | boolean | 是 | DEMO 制品恒为 `true` |

盲测原始标注使用独立事件结构，保留 `candidate_a/candidate_b/preference/tie/abstain`、随机位置和标注员信息；裁决完成后才转换为本表的 `chosen/rejected` 训练对，二者不得混为一个 Schema。

## 7. `eval_tasks.jsonl`

| 字段 | 类型 | 必填 | 约束/说明 |
|---|---|---:|---|
| `eval_id` | string | 是 | 评测任务主键 |
| `sample_id` | string | 是 | 跨制品关联键 |
| `eval_version` | string | 是 | 不可变评测版本 |
| `task_type` | string | 是 | 与能力维度映射 |
| `prompt` | object/string | 是 | 固定输入 |
| `reference_answer` | object/string | 是 | 仅裁判可见的参考答案 |
| `rubric` | object/array | 是 | 当前任务评分规则 |
| `source_work_id` / `source_author_id` | string | 是 | 来源作品与作者 |
| `work_id` / `author_id` | string | 是 | 当前评测隔离键 |
| `source_id` / `document_id` | string | 是 | 来源和文档 |
| `rights_record_id` / `content_sha256` | string | 是 | 权利与内容追踪 |
| `dataset_version` / `shard_id` | string | 是 | 数据版本和分片 |
| `split` | enum | 是 | 当前 Schema 固定为 `evaluation` |
| `isolation_assertion` | object/string | 是 | 与训练、验证数据隔离的声明 |
| `demo` | boolean | 是 | DEMO 制品恒为 `true` |

## 8. `edit_events.jsonl`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `edit_event_id` | string | 是 | 唯一 |
| `draft_id` | string | 是 | 被编辑草稿 |
| `model_version` | string | 是 | 草稿来源模型 |
| `dataset_version` | string | 是 | 模型所用数据版本 |
| `editor_id` | string | 是 | 化名 |
| `started_at` / `submitted_at` | datetime | 是 | 服务端事件时间 |
| `active_edit_seconds` | integer | 是 | 排除长时间无操作 |
| `before_sha256` / `after_sha256` | string | 是 | 修改前后哈希 |
| `edit_distance_chars` | integer | 是 | 字符级修改量 |
| `decision` | enum | 是 | `accept/minor_edit/major_edit/reject` |
| `reason_codes` | array[string] | 是 | 拒绝或修改原因 |

## 9. 反馈与商业事件

真实业务表只保存必要字段，展示层仅输出汇总和脱敏引用。

| 表 | 主键 | 核心字段 |
|---|---|---|
| `publication_events` | `publication_event_id` | `draft_id, channel_code, published_at, evidence_ref, status` |
| `usage_events` | `usage_event_id` | `actor_pseudonym, action, occurred_at, duration_ms, model_version` |
| `revenue_events` | `revenue_event_id` | `contract_ref, currency, gross_minor_units, refund_minor_units, occurred_at, evidence_ref` |

金额使用最小货币单位整数；“净收入”必须由书面口径计算，不能把流水、合同额或平台预估收益直接当净收入。

## 10. 权利反查关系

```text
rights_record_id
  → work_id
  → document_id + content_sha256
  → `sample_id` / `pair_id + sample_id` / `eval_id + sample_id`
  → dataset_version + shard_id
  → training_run_id
  → model_version
  → eval_version / publication_event_id
```

每条边必须有机器可读 manifest 或索引支撑，不接受只靠人工记忆的关联。
