# Azure Foundry Quick Start

**English** | [中文](README.md)

Learning materials for Microsoft Foundry and Azure OpenAI, plus bilingual research and integrated Claude on Foundry Workshop samples. Documentation explains architecture and boundaries; the [hands-on directory](workshops/claude-foundry/README.en.md) supplies a shared implementation and configuration for local agents, Foundry IQ and Hosted Responses. Cloud deployment acceptance has not been established.

## Where to start

| Goal | Document | Language and status |
| --- | --- | --- |
| Run the three workshop paths in this repository | [Claude hands-on English entry](workshops/claude-foundry/README.en.md) / [中文](workshops/claude-foundry/README.md) | Integrated 2026-10-09; offline checks separated from cloud steps |
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

The research guide's clone/run commands target pinned upstream source. Use the
[integrated hands-on path](workshops/claude-foundry/README.en.md) for this repository:
start with offline preview/configuration checks, then explicitly opt into approved
service calls. Do not mix upstream filenames, settings or YAML with this implementation.

## Research baseline and usage boundaries

The source is Shilpa Jain's [Claude-on-foundry-handsonworkshop](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e/README.md), pinned to `4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e` (2026-09-16; still main HEAD on 2026-10-09). Research documents are original synthesis; hands-on code is adapted under MIT with the full [license](workshops/claude-foundry/LICENSE) and [source/change notice](workshops/claude-foundry/NOTICE.md). Upstream environment values, the author's service URL and the entire repository are not copied; the FAQ is newly written fictional training data.

**The hands-on integration was checked locally only; no Azure resources were deployed, models or external MCP servers called, or data uploaded, and no successful cloud verification results are supplied.** The research guide retains its historical 2026-09-29 review scope; hands-on instructions separate offline checks from later cloud operations. Local execution can still call billable services. Store MCP must be explicitly configured as an owned or approved read-only service, never the author's default URL.

Claude has separate subscription, Marketplace, model-version, region, and identity restrictions; general AOAI guidance does not automatically apply. Official capabilities change, so the guides distinguish pinned source, current documentation, and unverified proposals. Maintainers should review them before publication or deployment. The new bilingual content was prepared with AI assistance; translating the entire existing Chinese manual is outside this work's scope.
