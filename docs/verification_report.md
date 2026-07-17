# V0.1 验证报告

> 数据来源：`SYNTHETIC_DEMO`  
> 构建状态：`PASS`  
> 对外声明状态：`DEMO_ONLY`  
> 验证日期：`2026-07-17`

这里的 PASS 仅表示公开样例代码、合成数据、数据契约和文件关系通过检查，不表示真实模型效果、用户使用、发布或收入已经发生。

## 验证环境

- Python：3.12.13
- 核心管道依赖：仅 Python 标准库
- 运行入口：`scripts/run_demo.py`
- 数据版本：`novel-demo-data-v0.1.0`
- 评测版本：`novel-gold-demo-v0.1.0`
- 模型状态：`template_baseline_not_trained`
- 源码版本：Release Manifest 中的跨平台规范化源码快照 SHA-256

## 结果

| 检查 | 结果 |
|---|---|
| 从受管输出目录重新生成全部 artifacts | PASS |
| 重复运行得到相同产物 | PASS |
| 运行产物 SHA-256 自校验 | PASS，23 个文件 |
| 规范化源码快照与文件级哈希 | PASS |
| 单元、契约、端到端与发布安全测试 | PASS，17 / 17 |
| 公开仓库安全检查 | PASS |
| 实际产物逐条通过 JSON Schema 子集校验 | PASS |
| 非法 required / const / enum / pattern / type 负向测试 | PASS |
| 作者、作品、正文哈希跨 split 泄漏 | 0 / 0 / 0 |
| 训练数据与隔离评测作者、作品重叠 | 0 / 0 |
| JSON、JSONL、CSV 和 Markdown 格式检查 | PASS |
| 生成文本跨平台固定 LF | PASS |
| 基线汇总与盲测明细对账 | PASS：候选 6 胜、基线 4 胜、平局 1、弃权 1 |
| 实验 Manifest 与结果文件 SHA-256 对账 | PASS |
| Python 源码编译检查 | PASS |

实验结果完全是 DEMO 对账样例，不代表运行过模型。

## 固定合成回归计数

```text
原始记录                 27
权利通过 / 拒绝          25 / 2
精确重复 / 近似重复       2 / 3
最终唯一作品              20
SFT 训练 / 验证           36 / 12
偏好对                    24
隔离评测任务              30
编辑事件                  40
```

这些数字是确定性合成数据的回归契约，不能写成真实项目产量。

## 安全验证

- 输出目录必须包含专属托管标记，管道才允许清理之前生成的子目录；
- 将源码仓库本身作为输出目录会被拒绝；
- 已存在用户文件但没有托管标记的目录会被拒绝；
- PowerShell 入口在任一子命令失败时立即失败，不再出现“管道失败但脚本返回 0”；
- 权利未授权和已经过期的记录在正文派生前被阻断；
- 公开安全门会检查常见密钥、个人标识、本机用户路径、私有目录、归档文件和缺少 `demo=true` 的运行产物。

该安全门是轻量防线，不能替代法律、隐私、安全和人工代码审查。

## 质量契约实现边界

`governance/data_quality_contract.yaml` 是部分落地的目标规范，不是通用规则引擎。当前已执行的子集与尚未实现的 PII、通用主键唯一性、跨集合近重复、完整可追踪率量化及审批流，已在 Dataset Card 和质量契约中分开标注。

## 尚未完成

- Streamlit 辅助函数和源码已通过测试/编译，但未安装可选依赖进行浏览器级验收；
- 未执行模型训练、真实盲测、生产 PII 检测或线上发布；
- GitHub Actions 需要在首次推送后确认 Python 3.10 / 3.12 两个任务均通过。

## 复现命令

```powershell
python scripts/run_demo.py --output-dir artifacts
python -m unittest discover -s tests -v
python scripts/check_public_repo.py
python -m compileall -q src scripts tests dashboard
```
