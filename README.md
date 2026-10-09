# Azure Foundry Quick Start

[English](README.en.md) | **中文**

Microsoft Foundry 与 Azure OpenAI 的学习资料，以及 Claude on Foundry Workshop 的双语研究指南与整合实操示例。文档解释架构与边界，[实操目录](workshops/claude-foundry/README.md) 提供本地 Agent、Foundry IQ 和 Hosted Responses 的共享实现与运行配置；不是已完成云端验收的部署项目。

## 从哪里开始

| 目标 | 文档 | 语言与状态 |
| --- | --- | --- |
| 在本仓库运行三条 Workshop 路径 | [Claude 实操中文入口](workshops/claude-foundry/README.md) / [English](workshops/claude-foundry/README.en.md) | 2026-10-09 整合；离线检查与云端步骤分开 |
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

研究指南中的 clone/运行命令针对固定上游版本。要运行已整合的实现，请转到
[本仓库实操路径](workshops/claude-foundry/README.md)：先离线预览与配置检查，再按审批选择真实服务调用；
不要把上游文件名、环境变量或原始 YAML 与本目录混用。

## 研究基线与使用边界

研究来源为 Shilpa Jain 的 [Claude-on-foundry-handsonworkshop](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/README.md)，固定提交 `4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e`（2026-09-16；2026-10-09 复查仍为 main HEAD）。研究文档为原创综合整理；实操代码按 MIT 授权改编，保留完整 [许可证](workshops/claude-foundry/LICENSE)、[来源与变更声明](workshops/claude-foundry/NOTICE.md)。未复制上游环境值、作者服务地址或整库；FAQ 为新写的虚构教学数据。

**实操整合仅做本地验证；未部署 Azure、调用模型或外部 MCP、上传数据，也没有云端成功验证结果。** 研究指南保留 2026-09-29 的历史核对范围；实操说明明确区分离线检查与读者后续云端操作。本地运行也可能调用收费云服务。商店 MCP 必须显式配置为自有或明确获准的只读服务，不使用作者的默认地址。

Claude 有独立的订阅、Marketplace、模型版本、区域与身份限制，不能直接沿用 AOAI 通用说明。官方能力会变化，指南区分固定源码、当前文档与未验证建议；维护者应在发布或部署前审阅。新增双语内容由 AI 辅助整理，既有中文手册不在本次全文翻译范围内。
