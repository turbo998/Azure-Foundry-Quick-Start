# Azure Foundry Quick Start

**English** | [中文](README.md)

Learning materials for Microsoft Foundry and Azure OpenAI, plus independent research and practical guidance for the Claude on Foundry Workshop. This repository delivers **documentation**, not an executable agent project, deployment templates, or a validated dependency environment.

## Where to start

| Goal | Document | Language and status |
| --- | --- | --- |
| Learn all three paths: local Claude + MCP agent, Foundry IQ, and hosted agent | [Claude Workshop Chinese guide](claude-on-foundry-workshop-guide.md) | Full Chinese guide; source and official-reference review dated 2026-09-29 |
| Read complete English coverage of the same scope | [Claude Workshop English guide](claude-on-foundry-workshop-guide.en.md) | Full English counterpart, not a summary |
| Consult existing Foundry / AOAI configuration material | [Azure Foundry & Azure OpenAI configuration manual](azure-foundry-aoai-guide.md) | Chinese only; July 2026 v2.0 with targeted Claude clarifications and cross-links, not a comprehensive re-review of other historical content |
| View the historical offline edition | [Existing PDF](azure-foundry-aoai-guide.pdf) | **Historical July 2026 snapshot**; unchanged and not regenerated in this work, and not synchronized with the updated Markdown or new guides |

## Claude Workshop reading path

Start with [architecture and responsibilities](claude-on-foundry-workshop-guide.en.md#architecture) and the [eligibility, endpoint, identity, and version matrices](claude-on-foundry-workshop-guide.en.md#prerequisites), then select a path:

1. [Local Claude + MCP agent](claude-on-foundry-workshop-guide.en.md#local): application-owned Agent Framework loop, prompts, tools, and sessions.
2. [Foundry IQ](claude-on-foundry-workshop-guide.en.md#iq): FAQ chunking, text index and semantic configuration, knowledge source, and KB MCP; not an implemented vector RAG pipeline.
3. [Hosted agent](claude-on-foundry-workshop-guide.en.md#hosted): host orchestration in Foundry Agent Service, distinguishing external Responses from internal Claude Messages.

Before running anything, read [source issues and untested adaptations](claude-on-foundry-workshop-guide.en.md#issues), [data boundaries, costs, and cleanup](claude-on-foundry-workshop-guide.en.md#operations), and the [reader checklist](claude-on-foundry-workshop-guide.en.md#checklist).

## Research baseline and usage boundaries

The source is Shilpa Jain's [Claude-on-foundry-handsonworkshop](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/README.md), pinned to `4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e` (2026-09-16). Its [MIT LICENSE](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/LICENSE) was checked; see [guide sources](claude-on-foundry-workshop-guide.en.md#sources) for attribution and official references. This is an original synthesis, not a copy of upstream applications or environment files.

**This work did not install/run samples, deploy Azure resources, call models or external MCP servers, or upload data, and provides no successful cloud verification results.** Commands, expected observations, and migration proposals are for readers to verify in approved, isolated experiment environments. Local execution can still call billable cloud services. Do not send data to the author's default MCP address; replace it with an owned or explicitly approved service.

Claude has separate subscription, Marketplace, model-version, region, and identity restrictions; general AOAI guidance does not automatically apply. Official capabilities change, so the guides distinguish pinned source, current documentation, and unverified proposals. Maintainers should review them before publication or deployment. The new bilingual content was prepared with AI assistance; translating the entire existing Chinese manual is outside this work's scope.
