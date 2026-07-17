# Manifest 模板

这些 JSON 文件用于把数据、模型、评测、实验和发布版本关联起来。

## 规则

- 模板中的 `null` 必须由实际运行程序填充，不能手工猜测。
- 实验Manifest中的`evidence_status`在运行并复核前保持`TEMPLATE_NOT_RUN`。
- 每个正式版本必须不可变；内容变化时创建新版本，不覆盖旧文件。
- 文件清单保存相对路径、字节数、记录数和 SHA-256。
- Release Manifest与`contracts/release_manifest.schema.json`使用同一组顶层字段；
  `validation`和`files`用于关联校验结果及不可变制品。
- 真实凭证只保存脱敏引用，不把合同、用户身份或流水原件提交到公开仓库。

## 推荐生成顺序

```text
data_manifest
  ├─> model_manifest
  └─> evaluation_manifest

data + model + evaluation
  └─> experiment_manifest
        └─> release_manifest
```

## 状态建议

状态枚举按对象类型使用，不应把不同层级的状态混在同一字段中：

| 适用域 | 字段 | 允许状态 | 含义 |
|---|---|---|---|
| 空白实验模板 | `evidence_status` | `TEMPLATE_NOT_RUN` | 尚未执行 |
| 合成实验 | `evidence_status` | `DEMO` | 只验证格式和流程 |
| 真实实验复核 | `evidence_status` | `UNVERIFIED/VERIFIED/REVOKED` | 未核验、已核验或已失效 |
| DEMO发布Manifest | `release_status` | `DEMO_ONLY_NOT_FOR_PRODUCTION` | 与真实发布隔离 |
| 真实发布流程 | `release_status` | `CANDIDATE/VERIFIED/REVOKED` | 候选、已批准或撤回 |
| 对外证据副本 | `record_status` | `TEMPLATE/DEMO/UNVERIFIED/VERIFIED/REDACTED_VERIFIED/REVOKED` | 证据与脱敏状态 |

`demo: true`和`demo_marker`是合成产物的永久标识，不因实验完成或格式校验通过而移除。
