# Azure Foundry & Azure OpenAI 配置手册

> 面向新客户的端到端配置指南 — 涵盖 AOAI 申请开通、Foundry 配置、模型部署、Agent Service、最佳实践
>
> 版本 2.0 — 2026 年 7 月（对齐 Microsoft Foundry 2026-06/07 最新发布）

> **2026-09-29 Claude 定向补充：**本次仅澄清 Claude 的订阅、认证与 API 边界，并增加 [Claude Workshop 完整中文指南](claude-on-foundry-workshop-guide.md) / [Full English guide](claude-on-foundry-workshop-guide.en.md)。其他章节仍为既有历史内容，未全面重审；[PDF](azure-foundry-aoai-guide.pdf) 保留为 2026 年 7 月历史快照，不与本次 Markdown 修改同步。仓库入口：[中文](README.md) / [English](README.en.md)。

---

## 更新说明（v2.0 vs v1.0）

| 变化 | 说明 |
|------|------|
| 品牌 | "Azure AI Studio" 已彻底更名为 **Microsoft Foundry**；门户仍为 `ai.azure.com` |
| 模型 | 新增 GPT-5.6（sol/terra/luna）、GPT-5.5、GPT-5.1~5.4 系列、`gpt-chat-latest`、Grok 4.3、DeepSeek V4、**Claude 模型现已登陆 Foundry** |
| Agent Service | 新增 **Skills / Toolboxes（预览）**、**Routines 自动化（预览）**、**Memory 记忆（预览）**、Trace Replay、Agent Optimizer |
| 网络安全 | **Managed VNET 已 GA**（原生托管网络隔离，无需自建 VNet） |
| 配额 | **Global/Data Zone 配额管理已 GA**，新增 Model Capacities API、Usages API |
| 成本 | 新增 **Project-level 成本归因** |
| 门户体验 | 门户内可直接开通 Pay-As-You-Go，免跳转 Azure Portal |
| 出版渠道 | Microsoft 365 Copilot / Teams 发布 agent 打通 |

---

## 目录

1. [概述：Microsoft Foundry 与 Azure OpenAI](#1-概述microsoft-foundry-与-azure-openai)
2. [前提条件与准备工作](#2-前提条件与准备工作)
3. [申请开通 Azure OpenAI 服务](#3-申请开通-azure-openai-服务)
4. [创建 Foundry 资源](#4-创建-foundry-资源)
5. [部署模型](#5-部署模型)
6. [认证与访问控制](#6-认证与访问控制)
7. [快速验证：调用 API（含 Sample 代码）](#7-快速验证调用-api含-sample-代码)
8. [Foundry Agent Service：Skills / Toolbox / Memory / Routines](#8-foundry-agent-service skills--toolbox--memory--routines)
9. [配额与限制（2026 新模型）](#9-配额与限制2026-新模型)
10. [网络安全：Managed VNET（GA）](#10-网络安全managed-vnetga)
11. [成本管理：Project-level 归因](#11-成本管理project-level-归因)
12. [工具（Tools）最佳实践与 FAQ](#12-工具tools最佳实践与-faq)
13. [常见问题排查](#13-常见问题排查)
14. [附录：推荐区域与模型可用性](#14-附录推荐区域与模型可用性)

---

## 1. 概述：Microsoft Foundry 与 Azure OpenAI

**Microsoft Foundry**（原 Azure AI Studio / Azure AI Foundry）是微软统一的企业级 AI 应用与 Agent 工厂，集成：

- **Foundry Models**：Azure OpenAI 系列 + 合作伙伴/社区模型（Grok、DeepSeek、Claude、Cohere、Mistral、Llama、Kimi 等）
- **Foundry Agent Service**：托管 Agent 运行时、工具、Skills/Toolbox、Routines、Memory
- **Foundry Local**：设备端模型运行（含 Vision、语音、ARM64 支持）
- **Observability**：Tracing、Trace Replay、Evaluation（含基于生产 Trace 的评测）

**Azure OpenAI Service (AOAI)** 现作为 Foundry 的核心模型供给方，模型阵容已扩展至 GPT-5.6 / GPT-5.5 系列、Sora 2 视频生成、gpt-image-2 等。

### 核心优势

| 特性 | 说明 |
|------|------|
| 企业安全 | 数据不用于训练；支持 Managed VNET（GA）、Private Endpoint、CMK |
| 合规认证 | SOC 2、ISO 27001、HIPAA、GDPR 等 |
| 全球部署 | 30+ 区域，支持 Global / Data Zone（OSS 模型公开预览）部署 |
| 统一计费 + 归因 | EA/CSP/PAYG 统一计费，新增 Project 级成本归因 |
| 内容安全 | 内置 Content Safety，可自定义策略 |
| Agent 化 | Skills/Toolbox/Memory/Routines 让 Agent 具备可复用能力与自动化触发 |

> **Claude 能力边界：**本表为既有平台概述，不代表所有 Claude 模型/托管版本都支持相同的网络、内容安全、合规、部署类型或工具能力。应按具体模型卡与 [Claude 官方说明](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude) 分别核对；应用使用 Agent Framework 也不等于已经部署到 Foundry Agent Service。

---

## 2. 前提条件与准备工作

1. **Azure 订阅**（PAYG / EA / CSP 均可）；也可在 Foundry 门户内**直接开通 PAYG**，无需先跳 Azure Portal
2. **Azure 账户** — Contributor / Owner 权限
3. **AOAI 访问权限** — 部分模型（如 `computer-use-preview`、`grok-4`、GPT-5 RFT）为受限访问，需单独申请
4. **浏览器** — Edge / Chrome

> 💡 CSP 客户联系合作伙伴协助开通；EA 客户通过 EA Portal 管理订阅。

> **Claude 不适用上述订阅泛化说明：**截至 2026-09-29，[Claude 官方部署页](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude) 明确列出 CSP 订阅等不支持情形，并另有付费方式、账单地区、Marketplace 订阅权限和部署区域要求。请先核对 [Claude 专项前置条件](claude-on-foundry-workshop-guide.md#prerequisites)，不要用 AOAI 开通或权限说明代替 Claude 准入检查。

---

## 3. 申请开通 Azure OpenAI 服务

1. 访问 `https://aka.ms/oai/access`，企业 Azure AD 账户登录，填写申请表单
2. 个人邮箱（@outlook.com 等）通常无法通过；审批 1–5 工作日
3. 部分**受限访问模型**（Gated）额外单独申请：
   - `computer-use-preview` → `https://aka.ms/oai/cuaaccess`
   - `grok-4` / `grok-code-fast-1` → `https://aka.ms/xai/grok-4`
   - GPT-5 Reinforcement Fine-Tuning（Gated GA）→ 联系微软客户经理

### 加速审批技巧
- 场景描述具体（"智能客服""文档摘要"等）
- 说明合规要求（GDPR、数据不出境）
- 提供公司官网链接；如有 TAM/CSA 可协助加速

---

## 4. 创建 Foundry 资源

### 4.1 通过 Foundry / Azure Portal 创建

1. 登录 `https://ai.azure.com`（或 `portal.azure.com` 搜索 "Microsoft Foundry"）
2. **"+ Create"** → 填写 Subscription / Resource Group / Region / Name / Pricing Tier (S0)
3. **Network** 选项卡三种模式：
   - All networks（开发测试）
   - Selected networks（生产推荐，指定 IP/VNet）
   - **Managed VNET（GA，2026-05）**：无需自建 VNet，由 Foundry 托管网络边界，二选一隔离模式：
     - `allow_internet_outbound`：托管隔离但允许广泛出站
     - `allow_only_approved_outbound`：仅允许经批准的出站（Service Tag / Private Endpoint / FQDN）
   - Disabled（仅 Private Endpoint，最高安全级别）

> ⚠️ **Managed VNET 是创建时的架构决策**，事后不可禁用或从自建 VNet 转换；FQDN 出站规则会创建托管 Azure Firewall（产生额外防火墙费用，Managed VNET 本身免费）。

### 4.2 通过 Azure CLI 创建

```bash
az login
az group create --name rg-aoai-prod --location eastus2
az cognitiveservices account create \
  --name mycompany-foundry-prod \
  --resource-group rg-aoai-prod \
  --kind OpenAI \
  --sku S0 \
  --location eastus2
```

---

## 5. 部署模型

### 5.1 通过 Foundry Portal 部署

`ai.azure.com` → 选择项目 → **Model catalog / Deployments** → **+ Deploy model**

### 5.2 主要可用模型（2026-07 更新）

| 模型系列 | 部署名称示例 | 类型 | 说明 |
|------|-------------|------|------|
| **GPT-5.6**（NEW） | `gpt-5.6-sol` / `-terra` / `-luna` | Chat/Reasoning | 2026-07-09 发布，Preview，100万+ token 上下文 |
| **gpt-chat-latest**（NEW） | `gpt-chat-latest` | Chat | 持续更新的"最新对话模型"别名（即 GPT-5.5 Instant） |
| **GPT-5.5** | `gpt-5.5` | Chat/Reasoning | 部分配额 Tier 需申请（Tier 5/6 默认有配额） |
| GPT-5.4 / 5.3 / 5.2 / 5.1 | `gpt-5.4`, `gpt-5.1-codex-max` 等 | Chat/Codex/Reasoning | Codex 系列针对 Codex CLI/VS Code 优化 |
| GPT-5 / gpt-oss | `gpt-5`, `gpt-oss-120b`, `gpt-oss-20b` | Chat/开源推理 | gpt-oss 需 Foundry 项目部署 |
| GPT-4.1 系列 | `gpt-4.1`, `-mini`, `-nano` | Chat（多模态） | 已知问题：工具定义超 300K token 会报错 |
| GPT-Image-2 / gpt-image-1.5 | `gpt-image-2` | Image | 图像生成/编辑 |
| Sora 2（NEW） | `sora-2` | Video | 视频生成 |
| o3 / o4-mini / codex-mini | — | Reasoning | 数学/代码推理 |
| text-embedding-3-large | — | Embedding | 文本向量化 |
| Whisper / gpt-4o-transcribe | — | Speech-to-Text | |
| **Grok 4.3**（NEW，xAI） | `grok-4.3` | Chat | Chat Completions API（非 Responses API），高 agentic 能力，注意越狱风险评级更高 |
| **DeepSeek V4 / V4-Pro / V4-Flash**（NEW） | — | Chat（推理） | 开源模型，100万 token 输入 |
| **Kimi K2.6 / K2.7-Code**（Moonshot AI，NEW） | — | Chat（推理，多模态） | |
| **Claude 模型** | 使用实际部署名 | Messages API | 按具体模型/托管版本核对可用性，参考 [部署指南](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude) |

> **Claude 调用与编排：**模型客户端使用 `https://<resource>.services.ai.azure.com/anthropic` 作为 base URL，Messages 请求路径为 `/anthropic/v1/messages`，`model` 填实际部署名。不要套用本手册的 OpenAI Chat Completions / Responses 示例，也不要仅凭模型可部署就推断 Model Router 支持。Hosted Agent 可以对外提供 Responses 协议，同时在内部调用 Claude Messages；这是不同层次。三条路径、版本差异与未实测适配建议见 [Claude Workshop 指南](claude-on-foundry-workshop-guide.md#architecture)。

### 5.3 部署配置参数

| 参数 | 建议 |
|------|------|
| Deployment type | Standard（起步）/ Provisioned PTU（高流量生产）/ Global Standard（跨区域） |
| **Data Zone Standard**（公开预览，OSS 模型） | 地理范围内托管路由，兼顾数据驻留与运维便捷性；⚠️ Preview 阶段勿直接用于生产，先验证可用性/配额/内容过滤/回退策略 |

### 5.4 CLI 部署示例

```bash
# 部署 GPT-5.5
az cognitiveservices account deployment create \
  --name mycompany-foundry-prod \
  --resource-group rg-aoai-prod \
  --deployment-name gpt-5.5 \
  --model-name gpt-5.5 \
  --model-version "2026-04-24" \
  --model-format OpenAI \
  --sku-capacity 80 \
  --sku-name GlobalStandard

# 部署开源推理模型 gpt-oss-120b（需 Foundry 项目）
az cognitiveservices account deployment create \
  --name "Foundry-project-resource" \
  --resource-group rg-aoai-prod \
  --deployment-name gpt-oss-120b \
  --model-name gpt-oss-120b \
  --model-version "1" \
  --model-format OpenAI-OSS \
  --sku-capacity 10 \
  --sku-name GlobalStandard
```

---

## 6. 认证与访问控制

三种方式不变：**API Key**、**Microsoft Entra ID（推荐生产）**、**Managed Identity（VM/AKS/App Service）**。

| IAM 角色 | 权限 |
|----------|------|
| Cognitive Services OpenAI User | 调用 API ✅ |
| Cognitive Services OpenAI Contributor | 调用 API + 管理部署 |
| Cognitive Services Contributor | 管理资源（不含数据面，**不能**调用 API） |

> **Claude 身份补充：**上表不能直接作为 Claude 的 RBAC 配置表。Claude 官方 Entra 示例使用 `https://ai.azure.com/.default`，排障页列出 **Cognitive Services User**；模型部署、Marketplace 订阅与推理权限需分开核对。部分模型仅支持 Entra ID，不能假定 API key 始终可用。详见 [Claude 身份矩阵](claude-on-foundry-workshop-guide.md#prerequisites)。托管 Agent identity 也不会自动替换应用中显式配置的模型/Search keys。

Managed Identity 示例（参考 SA 团队既有最佳实践 skill `azure-foundry-managed-identity`）：

```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://mycompany-foundry-prod.openai.azure.com/",
    azure_ad_token_provider=DefaultAzureCredential(),
    api_version="2025-04-01-preview"
)
response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[{"role": "user", "content": "你好"}]
)
```

> ⚠️ 安全提醒：任何交付给客户的代码示例，**切勿硬编码 API Key**；生产环境优先 Managed Identity / Entra ID。IAM 角色传播有 5–10 分钟延迟属正常现象。

---

## 7. 快速验证：调用 API（含 Sample 代码）

### 7.1 Chat Completion（GPT-5.5，Responses API 推荐路径）

```python
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://mycompany-foundry-prod.openai.azure.com/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-04-01-preview"
)

response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "请介绍 Microsoft Foundry 2026 年的核心新功能。"}
    ],
    temperature=0.7,
    max_tokens=1000
)
print(response.choices[0].message.content)
```

### 7.2 调用 Grok 4.3（第三方模型，注意 API 路径不同）

Grok 使用 Chat Completions API 路径，需去掉 `/chat/completions` 后缀再构造 base_url：

```python
import os
from openai import OpenAI

endpoint = os.environ["FOUNDRY_ENDPOINT"]  # 形如 .../openai/v1/chat/completions

client = OpenAI(
    api_key=os.environ["FOUNDRY_API_KEY"],
    base_url=endpoint.removesuffix("/chat/completions"),
)

response = client.chat.completions.create(
    model="grok-4.3",
    messages=[
        {"role": "system", "content": "You are Grok, a highly intelligent, helpful AI assistant."},
        {"role": "user", "content": "用一句话说明为何要在生产前评估 Agent 工具调用。"},
    ],
    temperature=0.2,
    max_tokens=80,
)
print(response.choices[0].message.content)
```

### 7.3 Image Generation（GPT-Image-2）

```python
response = client.images.generate(
    model="gpt-image-2",
    prompt="一只穿着宇航服的猫在月球上散步，赛博朋克风格",
    n=1,
    size="1024x1024",
    quality="high"
)
print(response.data[0].url)
```

### 7.4 Embedding

```python
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Microsoft Foundry 是微软的统一 AI 平台"
)
print(f"向量维度: {len(response.data[0].embedding)}")
```

### 7.5 Foundry Local 本地推理（含 Vision，1.1+ 新特性）

```python
import base64, io
from openai import OpenAI
from PIL import Image
from foundry_local_sdk import Configuration, FoundryLocalManager

config = Configuration(app_name="demo")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

model = manager.catalog.get_model("qwen3-vl-2b-instruct")
if not model.is_cached:
    model.download()

model.load()
manager.start_web_service()
client = OpenAI(base_url=manager.urls[0].rstrip("/") + "/v1", api_key="notneeded")

image = Image.open("screenshot.jpg")
image.thumbnail((512, 512))
buf = io.BytesIO(); image.save(buf, format="JPEG")
image_b64 = base64.b64encode(buf.getvalue()).decode()

resp = client.responses.create(
    model=model.id,
    input="placeholder",
    extra_body={"input": [{
        "type": "message", "role": "user",
        "content": [
            {"type": "input_text", "text": "描述这张截图，指出对开发者有用的信息。"},
            {"type": "input_image", "image_data": image_b64, "media_type": "image/jpeg"},
        ],
    }]},
)
print(resp.output_text)
```

> 💡 适合无需上云、对数据敏感的截图/文档分析场景（如客户现场演示，不希望截图离开本地设备）。

### 7.6 在 Foundry Playground 测试

`https://ai.azure.com` → 选择部署模型 → Chat Playground → 调整参数、查看结果。

---

## 8. Foundry Agent Service：Skills / Toolbox / Memory / Routines

2026 年最重要的 Agent 开发范式升级：**Skills（可复用指令）+ Toolbox（工具集合，暴露为 MCP 端点）+ Prompt Agent**，全部走原生 Foundry Agent Service（无需 Microsoft Agent Framework）。

```python
import os
from pathlib import Path
from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
credential = DefaultAzureCredential()

with AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project_client, \
     project_client.get_openai_client() as openai_client:

    # 1. 注册可复用 Skill
    skill = project_client.beta.skills.create(
        "customer-onboarding-skill",
        inline_content=models.SkillInlineContent(
            description="客户上云 onboarding 流程指导",
            instructions=Path("skills/onboarding/SKILL.md").read_text(),
        ),
        default=True,
    )

    # 2. 组装 Toolbox（工具 + Skill），开启 tool search
    toolbox = project_client.beta.toolboxes.create_version(
        "onboarding-toolbox",
        description="客户 onboarding 工具箱",
        tools=[
            models.WebSearchTool(type="web_search", name="doc_search", search_context_size="low"),
            models.ToolboxSearchPreviewTool(type="toolbox_search_preview", name="tool_search"),
        ],
        skills=[models.ToolboxSkillReference(type="skill_reference", name=skill.name, version=skill.version)],
    )

    # 3. 通过 MCP 端点把 Toolbox 挂给 Prompt Agent
    token = credential.get_token("https://ai.azure.com/.default").token
    mcp_url = f"{endpoint.rstrip('/')}/toolboxes/onboarding-toolbox/versions/{toolbox.version}/mcp?api-version=v1"

    agent = project_client.agents.create_version(
        "onboarding-agent",
        definition=models.PromptAgentDefinition(
            kind="prompt",
            model="gpt-5.4",
            instructions="你是客户 onboarding 顾问，先用 tool_search 再调用工具。",
            reasoning=models.Reasoning(effort="high"),
            tools=[models.MCPTool(
                server_label="onboarding_toolbox", server_url=mcp_url,
                authorization=token, headers={"Foundry-Features": "Toolboxes=V1Preview"},
                require_approval="never",
            )],
        ),
    )
```

**其他 2026 新能力（均为 Preview，评估后再上生产）：**

| 能力 | 用途 | 注意事项 |
|------|------|----------|
| **Memory（记忆）** | Agent 跨会话记住用户偏好/上下文 | 参考 STATE-Bench 先验证"记忆是否真的提升效果"，避免为了用而用 |
| **Routines（自动化）** | 触发式自动执行 Agent 任务 | 适合定时/事件驱动的运营型 Agent |
| **Trace Replay** | 复盘 Agent 历史交互 | 排障与评测数据集构建的关键入口 |
| **Agent Optimizer** | 基于生产 Trace 自动优化托管 Agent | 需先接入 Tracing |
| **发布到 M365 Copilot / Teams** | 把 Foundry Agent 直接发布为企业协作入口 | 支持虚拟网络内发布，适合合规客户 |

---

## 9. 配额与限制（2026 新模型）

| 模型 | 默认 TPM | 默认 RPM | 可申请提升 |
|------|---------|---------|-----------|
| GPT-5.5 | 需 Tier 5/6 默认有配额，其余需申请 | — | ✅ |
| GPT-5.4 / 5.1 | 80K | 480 | ✅ |
| GPT-4.1 | 80K | 480 | ✅ |
| GPT-4o | 150K | 900 | ✅ |
| GPT-Image-2 | — | 10 images/min | ✅ |
| text-embedding-3-large | 350K | 2100 | ✅ |

### 配额管理已 GA（Global / Data Zone Standard）

- **Model Capacities API** — 查询"这个模型现在能在哪部署"
- **Usages API** — 查询已消耗配额
- 429 排查看响应头：`x-ratelimit-limit-tokens`、`x-ratelimit-remaining-*`、`retry-after-ms`
- ⚠️ **配额 ≠ 计费 token**：限流按请求时估算的最大处理 token（含 `max_tokens`）计算，RPM 按分钟内短窗口执行 —— 若应用把 `max_tokens` 设得过大或突发调用，即使 Azure Monitor 用量图表看起来不高也可能被限流

### Tier 等级（不变）

| Tier | 解锁条件 | 配额倍数 |
|------|---------|---------|
| Tier 1 | 默认 | 1x |
| Tier 2 | 累计消费 $500+ | 2x |
| Tier 3 | 累计消费 $2,000+ | 4x |
| Tier 4–6 | 更高消费/企业协议 | 8x–32x |

---

## 10. 网络安全：Managed VNET（GA）

已于 2026-05 GA，详见第 4.1 节。关键要点再强调：

- 托管私有终结点可让 Agent 访问 Azure Storage / Cosmos DB / Key Vault / AI Search，而无需应用团队自行设计子网
- 两种出站模式二选一，**创建时决定，不可事后切换**
- FQDN 规则会创建**托管 Azure Firewall（单独计费）**
- **Private Search + Private Agent 工具**在新版 Foundry 门户路径已支持；RAG 架构建议把 Search 连接纳入网络隔离设计，而非当作应用层细节
- 工具兼容性：MCP / Azure AI Search / OpenAPI / Azure Functions / A2A 可走 VNET 路径；部分工具仍走公网或暂不支持隔离环境，上线前逐一核实

---

## 11. 成本管理：Project-level 归因

- 新增 Project 级别成本视图，解决"这笔 AI 账单是哪个项目产生的"
- 建议与 **Azure Cost Management** 搭配使用而非替代：Foundry 侧看模型/项目维度，Azure Cost Management 侧看 Search/Storage/Key Vault/App Insights/Private Link/VM/Marketplace 等完整账单
- 落地建议：为共享 Foundry 环境（chatbot 原型 + 评测 + 微调实验 + 生产 Agent 混跑）设置项目级预算与异常告警

---

## 12. 工具（Tools）最佳实践与 FAQ

> 来源：Microsoft Foundry 官方 *Tool best practices*（2026-07 更新）

### 配置与验证
- 在工具目录（Tool Catalog）中配置工具与连接
- 通过 **Run Trace** 确认 Agent 是否调用了工具、输入输出是什么

### 提升工具调用可靠性
- 用 `tool_choice` 做确定性控制：`auto`（模型自行决定）/ `required`（强制调用）/ `none`（禁止调用）
- Agent instructions 里明确写清楚**每个工具是干什么的**；多个工具功能重叠时加决策规则，例如："内部内容优先用 File Search，其次才用 Web Search"

### 安全使用工具（务必遵守）
- **工具输出视为不可信输入**，关键值使用前先校验
- 只传递完成任务所必需的信息
- **绝不在 Prompt 中包含密钥/Token/凭证**
- 避免在 Trace 或应用日志中记录密钥
- 接入第三方 MCP 服务器前，review Tool Catalog 的安全说明；需要集中路由与策略管控时用 **AI Gateway 工具治理（预览）**

### FAQ

**Q: 如何确认工具被调用了？**
A: 查看 Run Trace，确认调用及输入输出。

**Q: 如何让工具调用更可靠？**
A: 先写清楚工具说明；需要确定性行为用 `tool_choice=required`。

**Q: Foundry 报"工具不支持"，但文档表里显示支持？**
A: 工具可用性需要**模型**和**区域**两张表同时为 `Yes`；任一为 `No` 即不可用。同时确认模型确实部署在目标项目/区域（如 Code Interpreter 在 `southcentralus`/`spaincentral` 不可用，与模型无关）。

---

## 13. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 创建资源找不到 OpenAI 选项 | 订阅未开通 AOAI | 提交申请 `aka.ms/oai/access` |
| 部署模型提示区域不可用 | 所选区域不支持该模型 | 更换区域（East US 2 / Sweden Central） |
| API 返回 401 | Key 错误或 IAM 角色不足 | 确认分配 Cognitive Services OpenAI User 角色 |
| API 返回 429 | 超出 TPM/RPM，或 `max_tokens` 设置过大触发估算限流 | 降低请求频率/申请提升配额/检查响应头 `x-ratelimit-*` |
| API 返回 404 | 部署名/api-version 错误 | 核对 deployment name 与 api-version |
| Content Filter 拒绝请求 | 内容安全触发 | 调整 prompt 或自定义 Content Filter 策略 |
| Managed Identity 返回 401 | IAM 角色传播延迟 | 等待 5–10 分钟重试 |
| GPT-Image-2 / Sora 返回空结果 | 区域不支持或配额为 0 | 确认区域支持且已分配对应配额 |
| GPT-4.1 系列超长 tool 定义报错 | 已知问题：工具定义超 300K token（未到 1M 上下文上限）即报错 | 精简 function/tool description 长度 |
| Grok 模型调用报错路径不对 | Grok 走 Chat Completions API 路径，非 Responses API | 用 `endpoint.removesuffix("/chat/completions")` 构造 base_url，见 7.2 |
| Toolbox/MCP 工具在隔离网络下不可用 | 部分工具仍为公网访问，未适配 VNET 隔离 | 上线前逐工具核实 VNET 兼容性 |

---

## 14. 附录：推荐区域与模型可用性

### 14.1 推荐区域

| 区域 | GPT-4.1 | GPT-4o | GPT-5.5/5.6 | GPT-Image-2 | Embedding |
|------|---------|--------|---------|-------------|-----------|
| East US 2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sweden Central | ✅ | ✅ | ✅ | ✅ | ✅ |
| West US 3 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Japan East | ✅ | ✅ | — | — | ✅ |
| UK South | ✅ | ✅ | — | ✅ | ✅ |

> ⚠️ 具体新模型（GPT-5.6、Grok 4.3、DeepSeek V4、Claude on Foundry）区域可用性变化很快，**务必在部署前用 [Region availability 官方页](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability) 或 Model Capacities API 现查**，本表仅供参考、不作为承诺依据。

### 14.2 重要链接

| 资源 | 链接 |
|------|------|
| Microsoft Foundry 门户 | https://ai.azure.com |
| Azure Portal | https://portal.azure.com |
| AOAI 申请 | https://aka.ms/oai/access |
| What's New（月度更新） | https://learn.microsoft.com/azure/foundry/whats-new-foundry |
| Foundry Blog | https://devblogs.microsoft.com/foundry/ |
| 模型列表（Azure 直销） | https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure |
| 区域可用性 | https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability |
| Tool 最佳实践 | https://learn.microsoft.com/azure/foundry/agents/concepts/tool-best-practice |
| 定价信息 | https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/ |
| 配额与限制 | https://learn.microsoft.com/azure/ai-services/openai/quotas-limits |
| Managed VNET 配置 | https://learn.microsoft.com/azure/foundry/how-to/managed-virtual-network |
| Claude Workshop 三路径指南 | [中文](claude-on-foundry-workshop-guide.md) / [English](claude-on-foundry-workshop-guide.en.md) |

---

*Microsoft Foundry & Azure OpenAI 配置手册 v2.0 — 2026 年 7 月*
*如有疑问，请联系您的微软客户经理或提交 Azure 支持工单*
*⚠️ 免责声明：本文档所列 2026 年新功能/新模型信息基于公开发布内容整理，部分能力仍为 Preview 阶段，具体可用性、区域、配额请以 Azure 官方文档及门户实时信息为准，上生产前务必自行核实。*
