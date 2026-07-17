# V0.1 公开发布检查表

> 检查快照：`2026-07-17`  
> 范围：独立合成作品集 Demo

## 可运行性

- [x] 在受管目录运行 `scripts/run_demo.py` 成功。
- [x] 核心流程不要求网络、API Key 或外部模型。
- [x] `python -m unittest discover -s tests -v`：17 / 17 PASS。
- [x] 重复运行产生相同业务数据、指标和校验和。
- [x] Windows / Linux 生成文本固定 LF，避免跨平台哈希漂移。
- [x] PowerShell 入口对子命令失败执行 fail-fast。

## 数据与治理

- [x] 生成 20 个唯一合成作品。
- [x] 原始输入包含可验证的精确重复和近重复案例。
- [x] 权利字段不完整或训练用途未授权的记录被阻断。
- [x] 作者、作品和正文哈希跨 split 泄漏数量为 0。
- [x] SFT、偏好和评测数据通过对应 Schema 子集验证。
- [x] 评测任务与训练数据按作者和作品隔离。
- [x] 目标质量契约和当前已实现子集明确分开。

## 证据与真实性

- [x] README 明确标注独立合成 Demo，不是第三方真实项目脱敏副本。
- [x] Dataset Card 明确说明合成数据和适用边界。
- [x] 基线、消融、盲测报告均标注 DEMO。
- [x] 发布、用户、收入文件保持空白模板或显式模拟示例。
- [x] 不包含真实合同、支付流水、平台后台截图或第三方小说正文。
- [x] README 明确禁止把 DEMO 指标写成真实业务成果。
- [x] `PROVENANCE.md` 说明生成器、第三方资产边界和 AI 辅助开发。

## 可追踪性

- [x] 数据版本记录输入、处理配置和输出校验和。
- [x] Release Manifest 包含跨平台规范化源码快照哈希。
- [x] 模型字段明确标记未训练占位状态。
- [x] 评测版本记录题集和盲测协议。
- [x] Release Manifest 关联数据、模型占位版本和评测版本。
- [x] Removal ledger 演示撤回后的影响追踪结构。

## 公开仓库安全

- [x] `.gitignore` 覆盖环境文件、密钥、证书、数据库和归档。
- [x] `scripts/check_public_repo.py` 扫描常见秘密、PII、本机路径和未标记产物。
- [x] Dashboard 只允许读取仓库内部路径。
- [x] GitHub Actions 采用只读 contents 权限。
- [x] CI 已配置 Python 3.10 / 3.12、包入口、测试和 artifacts 字节稳定性检查。

## 展示

- [x] README 首屏给出边界、架构、结果和快速运行路径。
- [x] 架构图使用 GitHub Mermaid flowchart 语法。
- [x] 离线 HTML 概览无需额外服务即可打开。
- [x] `docs/interview_walkthrough.md` 提供 30 秒和 5 分钟讲解。
- [ ] 首次推送后复核 GitHub Mermaid、徽章和 Actions 页面。
- [ ] 安装可选依赖并完成 Streamlit 浏览器级验收。
