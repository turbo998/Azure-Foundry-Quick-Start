# Azure Foundry & Azure OpenAI 配置手册

> 面向新客户的端到端配置指南 — 涵盖 AOAI 申请开通、Foundry 配置、模型部署
>
> 版本 1.0 — 2026 年 4 月

---

## 目录

1. [概述：Azure Foundry 与 Azure OpenAI](#1-概述azure-foundry-与-azure-openai)
2. [前提条件与准备工作](#2-前提条件与准备工作)
3. [申请开通 Azure OpenAI 服务](#3-申请开通-azure-openai-服务)
4. [创建 Azure Foundry 资源](#4-创建-azure-foundry-资源)
5. [部署 OpenAI 模型](#5-部署-openai-模型)
6. [认证与访问控制](#6-认证与访问控制)
7. [快速验证：调用 API](#7-快速验证调用-api)
8. [配额与限制](#8-配额与限制)
9. [常见问题排查](#9-常见问题排查)
10. [附录：推荐区域与模型可用性](#10-附录推荐区域与模型可用性)

---

## 1. 概述：Azure Foundry 与 Azure OpenAI

**Azure AI Foundry**（原 Azure AI Studio）是微软统一的 AI 开发平台，集成了 Azure OpenAI、开源模型目录、AI 搜索、评估工具等能力，为企业提供一站式 AI 开发与部署体验。

**Azure OpenAI Service (AOAI)** 是 Azure 上的托管 OpenAI 服务，提供 GPT-4o、GPT-4.1、GPT-5.5、GPT-Image-2、DALL·E、Whisper 等模型，兼具企业级安全、合规与可扩展性。

### 核心优势

| 特性 | 说明 |
|------|------|
| 企业安全 | 数据不会用于训练模型；支持 VNet、Private Endpoint、CMK 加密 |
| 合规认证 | SOC 2、ISO 27001、HIPAA、GDPR 等 |
| 全球部署 | 30+ 区域可用，支持就近部署降低延迟 |
| 统一计费 | 通过 Azure 订阅统一管理，支持 EA / CSP / PAYG |
| 内容安全 | 内置 Content Safety 过滤，可自定义策略 |

---

## 2. 前提条件与准备工作

在开始之前，请确认以下条件已满足：

1. **Azure 订阅** — 需要一个有效的 Azure 订阅（PAYG / EA / CSP 均可）
2. **Azure 账户** — 拥有订阅的 Contributor 或 Owner 权限
3. **AOAI 访问权限** — Azure OpenAI 需要申请开通（见第 3 章）
4. **浏览器** — 推荐使用 Edge 或 Chrome 访问 Azure Portal

> 💡 **提示：** 如果您是 CSP 客户，请联系您的 CSP 合作伙伴协助开通订阅和 AOAI 权限。EA 客户可通过 EA Portal 管理订阅。

---

## 3. 申请开通 Azure OpenAI 服务

Azure OpenAI 目前需要通过申请审批才能使用。

### 3.1 申请入口

1. 访问申请页面：`https://aka.ms/oai/access`
2. 使用您的 **企业 Azure AD 账户**（工作或学校账户）登录
3. 填写申请表单

### 3.2 申请表单关键字段

| 字段 | 说明 | 建议 |
|------|------|------|
| Subscription ID | 要开通 AOAI 的订阅 ID | 在 Azure Portal → Subscriptions 中获取 |
| Company Name | 公司名称 | 填写正式注册名称 |
| Use Case Description | 使用场景描述 | 详细描述业务场景，提高审批通过率 |
| Expected Models | 计划使用的模型 | 选择 GPT-4 / GPT-4o / DALL·E 等 |
| Responsible AI Contact | 负责人邮箱 | 确保为有效的企业邮箱 |

> ⚠️ **注意：** 个人账户（@outlook.com / @hotmail.com）通常无法通过审批。请使用企业 Azure AD 账户申请。审批通常需要 **1-5 个工作日**。

### 3.3 加速审批技巧

- 使用场景描述要具体、详细（如"智能客服"、"文档摘要"等）
- 说明数据处理合规要求（如 GDPR、数据不出境等）
- 提供公司官网链接
- 如有微软客户经理（TAM/CSA），可请其协助加速

---

## 4. 创建 Azure Foundry 资源

### 4.1 通过 Azure Portal 创建

1. 登录 `https://portal.azure.com`
2. 搜索 **"Azure AI Foundry"**（或 "Azure OpenAI"）
3. 点击 **"+ Create"**
4. 填写基本信息：

| 配置项 | 说明 |
|--------|------|
| Subscription | 选择已开通 AOAI 的订阅 |
| Resource Group | 选择已有或新建资源组 |
| Region | 推荐 **East US 2**、**Sweden Central**、**West US 3**（模型可用性最全） |
| Name | 全局唯一名称，如 `mycompany-aoai-prod` |
| Pricing Tier | 选择 **Standard S0** |

5. **Network** 选项卡：选择网络访问方式
   - **All networks** — 公网可访问（开发测试用）
   - **Selected networks** — 指定 IP / VNet（推荐生产环境）
   - **Disabled** — 仅 Private Endpoint 访问（最高安全级别）
6. 点击 **"Review + Create"** → **"Create"**

### 4.2 通过 Azure CLI 创建

```bash
# 登录
az login

# 创建资源组
az group create --name rg-aoai-prod --location eastus2

# 创建 Azure OpenAI 资源
az cognitiveservices account create \
  --name mycompany-aoai-prod \
  --resource-group rg-aoai-prod \
  --kind OpenAI \
  --sku S0 \
  --location eastus2
```

---

## 5. 部署 OpenAI 模型

资源创建完成后，需要为每个模型创建**部署（Deployment）**。

### 5.1 通过 Azure AI Foundry Portal 部署

1. 访问 `https://ai.azure.com`
2. 选择您的 Foundry 资源/项目
3. 左侧菜单 → **"Model catalog"** 或 **"Deployments"**
4. 点击 **"+ Deploy model"**
5. 选择模型并配置部署参数

### 5.2 主要可用模型

| 模型 | 部署名称示例 | 类型 | 用途 |
|------|-------------|------|------|
| GPT-4.1 | `gpt-4.1` | Chat | 高性能对话与推理 |
| GPT-4.1 mini | `gpt-4.1-mini` | Chat | 性价比优选 |
| GPT-4.1 nano | `gpt-4.1-nano` | Chat | 低延迟轻量任务 |
| GPT-4o | `gpt-4o` | Chat (多模态) | 文本 + 图片理解 |
| **GPT-5.5** | `gpt-5.5` | Chat | 最新一代旗舰模型 |
| **GPT-Image-2** | `gpt-image-2` | Image | 图像生成与编辑 |
| o4-mini | `o4-mini` | Reasoning | 推理任务（数学/代码） |
| text-embedding-3-large | `text-embedding-3-large` | Embedding | 文本向量化 |
| Whisper | `whisper` | Speech | 语音转文字 |
| TTS / TTS-HD | `tts` | Speech | 文字转语音 |

### 5.3 部署配置参数

| 参数 | 说明 | 建议 |
|------|------|------|
| Deployment name | API 调用时使用的名称 | 与模型名保持一致 |
| Model version | 模型版本号 | 选择最新稳定版 |
| Deployment type | Standard / Provisioned / Global | Standard 适合起步 |
| TPM | 每分钟 Token 配额 | 根据业务量设置，可后续调整 |

> 💡 **部署类型说明：**
> - **Standard** — 按需计费，共享容量，适合开发和中低流量场景
> - **Provisioned (PTU)** — 预留吞吐量，固定月费，适合高流量生产环境
> - **Global Standard** — 跨区域动态路由，更高可用性

### 5.4 通过 CLI 部署模型

```bash
# 部署 GPT-4.1
az cognitiveservices account deployment create \
  --name mycompany-aoai-prod \
  --resource-group rg-aoai-prod \
  --deployment-name gpt-4.1 \
  --model-name gpt-4.1 \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-capacity 80 \
  --sku-name Standard

# 部署 GPT-Image-2
az cognitiveservices account deployment create \
  --name mycompany-aoai-prod \
  --resource-group rg-aoai-prod \
  --deployment-name gpt-image-2 \
  --model-name gpt-image-2 \
  --model-version "2025-04-15" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

---

## 6. 认证与访问控制

Azure OpenAI 支持三种认证方式：

### 6.1 API Key 认证（最简单）

1. Azure Portal → 您的 OpenAI 资源 → **"Keys and Endpoint"**
2. 复制 **KEY 1** 或 **KEY 2** 和 **Endpoint**

```bash
curl https://mycompany-aoai-prod.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2024-12-01-preview \
  -H "Content-Type: application/json" \
  -H "api-key: YOUR_API_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

### 6.2 Microsoft Entra ID（推荐生产环境）

使用 Azure AD Token 认证，更安全，支持 RBAC 精细权限控制。

| IAM 角色 | 权限 |
|----------|------|
| Cognitive Services OpenAI User | 调用 API（Chat / Image / Embedding 等）✅ |
| Cognitive Services OpenAI Contributor | 调用 API + 管理部署 |
| Cognitive Services Contributor | 管理资源配置（不含数据面） |

> ⚠️ **常见误区：** Contributor 角色**不能**调用 API！需要专门的 **Cognitive Services OpenAI User** 角色。

### 6.3 Managed Identity（VM / App Service 场景）

适用于 Azure VM、App Service、AKS 等运行环境，无需管理密钥。

```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://mycompany-aoai-prod.openai.azure.com/",
    azure_ad_token_provider=DefaultAzureCredential(),
    api_version="2024-12-01-preview"
)

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "你好"}]
)
```

---

## 7. 快速验证：调用 API

### 7.1 Chat Completion（GPT-4.1 / GPT-5.5）

```python
import openai

client = openai.AzureOpenAI(
    azure_endpoint="https://mycompany-aoai-prod.openai.azure.com/",
    api_key="YOUR_API_KEY",
    api_version="2024-12-01-preview"
)

response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "请介绍 Azure AI Foundry 的核心功能。"}
    ],
    temperature=0.7,
    max_tokens=1000
)
print(response.choices[0].message.content)
```

### 7.2 Image Generation（GPT-Image-2）

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

### 7.3 Embedding（文本向量化）

```python
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Azure AI Foundry 是微软的统一 AI 平台"
)
print(f"向量维度: {len(response.data[0].embedding)}")
```

### 7.4 在 AI Foundry Playground 测试

如果不想写代码，可以直接在 `https://ai.azure.com` 的 **Playground** 中测试：

1. 选择已部署的模型
2. 在 Chat Playground 输入提示词
3. 调整参数（Temperature、Max Tokens 等）
4. 查看响应结果

---

## 8. 配额与限制

### 8.1 默认配额

| 模型 | 默认 TPM | 默认 RPM | 可申请提升 |
|------|---------|---------|-----------|
| GPT-4.1 | 80K | 480 | ✅ |
| GPT-4o | 150K | 900 | ✅ |
| GPT-5.5 | 80K | 480 | ✅ |
| GPT-Image-2 | — | 10 images/min | ✅ |
| text-embedding-3-large | 350K | 2100 | ✅ |

*TPM = Tokens Per Minute，RPM = Requests Per Minute*

### 8.2 提升配额

1. Azure Portal → 您的 OpenAI 资源 → **"Quotas"**
2. 选择要提升的模型/部署
3. 点击 **"Request Quota Increase"**
4. 或提交支持工单：Azure Portal → **"Help + support"** → **"New support request"**

### 8.3 Tier 等级

| Tier | 解锁条件 | 配额倍数 |
|------|---------|---------|
| Tier 1 | 默认 | 1x |
| Tier 2 | 累计消费 $500+ | 2x |
| Tier 3 | 累计消费 $2,000+ | 4x |
| Tier 4-6 | 更高消费 / 企业协议 | 8x-32x |

---

## 9. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 创建资源时找不到 OpenAI 选项 | 订阅未开通 AOAI | 提交申请：`aka.ms/oai/access` |
| 部署模型时提示区域不可用 | 所选区域不支持该模型 | 更换区域（推荐 East US 2 / Sweden Central） |
| API 返回 401 Unauthorized | API Key 错误或 IAM 角色不足 | 检查 Key / 确认分配了 Cognitive Services OpenAI User 角色 |
| API 返回 429 Too Many Requests | 超出 TPM/RPM 配额 | 降低请求频率或申请提升配额 |
| API 返回 404 Not Found | 部署名称错误或 API 版本不对 | 确认 deployment name 和 api-version 参数 |
| Content Filter 拒绝请求 | 内容安全过滤触发 | 调整 prompt 或自定义 Content Filter 策略 |
| Managed Identity 返回 401 | IAM 角色传播延迟 | 等待 5-10 分钟后重试 |
| GPT-Image-2 返回空结果 | 区域不支持或配额为 0 | 确认区域支持且已分配图像配额 |

---

## 10. 附录：推荐区域与模型可用性

### 10.1 推荐区域

| 区域 | GPT-4.1 | GPT-4o | GPT-5.5 | GPT-Image-2 | Embedding |
|------|---------|--------|---------|-------------|-----------|
| East US 2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sweden Central | ✅ | ✅ | ✅ | ✅ | ✅ |
| West US 3 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Japan East | ✅ | ✅ | — | — | ✅ |
| UK South | ✅ | ✅ | — | ✅ | ✅ |

> 💡 **选区建议：** 如果需要最全模型支持，优先选择 **East US 2** 或 **Sweden Central**。如需中国大陆低延迟，可考虑 **Japan East**（部分模型）。

### 10.2 重要链接

| 资源 | 链接 |
|------|------|
| Azure AI Foundry | https://ai.azure.com |
| Azure Portal | https://portal.azure.com |
| AOAI 申请 | https://aka.ms/oai/access |
| 定价信息 | https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/ |
| 模型可用性 | https://learn.microsoft.com/azure/ai-services/openai/concepts/models |
| API 文档 | https://learn.microsoft.com/azure/ai-services/openai/reference |
| 配额与限制 | https://learn.microsoft.com/azure/ai-services/openai/quotas-limits |

---

*Azure Foundry & Azure OpenAI 配置手册 v1.0 — 2026 年 4 月*
*如有疑问，请联系您的微软客户经理或提交 Azure 支持工单*
