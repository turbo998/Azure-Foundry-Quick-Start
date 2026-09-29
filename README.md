# Azure Foundry Quick Start

[English](README.en.md) | **中文**

Microsoft Foundry 与 Azure OpenAI 的学习资料，以及 Claude on Foundry Workshop 的独立研究与实操指南。本仓库以**文档**为交付物，不包含可执行 Agent 项目、部署模板或已验证的依赖环境。

## 从哪里开始

| 目标 | 文档 | 语言与状态 |
| --- | --- | --- |
| 学习 Claude + MCP 本地 Agent、Foundry IQ、Hosted Agent 三条路径 | [Claude Workshop 中文指南](claude-on-foundry-workshop-guide.md) | 完整中文；源码与官方资料核对日期 2026-09-29 |
| 阅读相同范围的完整英文说明 | [Claude Workshop English guide](claude-on-foundry-workshop-guide.en.md) | 完整英文对应版，不是摘要 |
| 查阅既有 Foundry / AOAI 配置资料 | [Azure Foundry & Azure OpenAI 配置手册](azure-foundry-aoai-guide.md) | 仅中文；2026 年 7 月 v2.0 基础上增加 Claude 定向澄清与互链，未全面重审其他历史内容 |
| 查看历史离线版本 | [既有 PDF](azure-foundry-aoai-guide.pdf) | **2026 年 7 月历史快照**；本次未修改或重新生成，不与更新后的 Markdown 或新增指南同步 |

## Claude Workshop 阅读路线

先看 [架构与职责](claude-on-foundry-workshop-guide.md#architecture) 和 [准入、端点、身份与版本矩阵](claude-on-foundry-workshop-guide.md#prerequisites)，再按需阅读：

1. [本地 Claude + MCP Agent](claude-on-foundry-workshop-guide.md#local)：应用拥有的 Agent Framework 循环、prompts、tools 与会话。
2. [Foundry IQ](claude-on-foundry-workshop-guide.md#iq)：FAQ 分块、文本索引与语义配置、knowledge source、KB MCP；不是已实现的向量 RAG。
3. [Hosted Agent](claude-on-foundry-workshop-guide.md#hosted)：将编排托管到 Foundry Agent Service，对外 Responses 与内部 Claude Messages 的区别。

运行前必须阅读 [源码问题与未测试适配建议](claude-on-foundry-workshop-guide.md#issues)、[数据边界、费用与清理](claude-on-foundry-workshop-guide.md#operations) 和 [读者检查清单](claude-on-foundry-workshop-guide.md#checklist)。

## 研究基线与使用边界

研究来源为 Shilpa Jain 的 [Claude-on-foundry-handsonworkshop](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/README.md)，固定提交 `4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e`（2026-09-16）。已核对其 [MIT LICENSE](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/LICENSE)；归属与官方参考见 [指南来源](claude-on-foundry-workshop-guide.md#sources)。本文档为原创综合整理，不复制上游应用或环境文件。

**本次没有安装/运行示例、部署 Azure、调用模型或外部 MCP、上传数据，也没有云端成功验证结果。** 指南中的命令、预期观察和迁移建议供读者在获准的独立实验环境自行核验；本地运行也可能调用收费云服务。不要使用作者的默认 MCP 地址发送数据，应替换为自有或明确获准的服务。

Claude 有独立的订阅、Marketplace、模型版本、区域与身份限制，不能直接沿用 AOAI 通用说明。官方能力会变化，指南区分固定源码、当前文档与未验证建议；维护者应在发布或部署前审阅。新增双语内容由 AI 辅助整理，既有中文手册不在本次全文翻译范围内。
