# Claude on Foundry 实操

[English](README.en.md) | [仓库首页](../../README.md) | [完整研究指南](../../claude-on-foundry-workshop-guide.md)

本目录把上游三条路径整合为一个共享实现，避免重复复制 Agent 与环境文件：
本地 Claude + 商店 MCP → 加入 Foundry IQ → Hosted Responses。
上游版本、改编差异与 MIT 声明见 [NOTICE](NOTICE.md) 和 [LICENSE](LICENSE)。
现有研究指南继续解释架构、准入、身份与历史源码问题；**运行本仓库示例以本页为准**。

> **边界：**离线预览、配置检查和单元测试不调用 Azure。启动 Agent/host 会连接远程 MCP；
> 输入问题后可产生收费模型/工具调用。`ingest.py --apply` 会创建/更新 Search 对象并上传 FAQ。
> 未部署 Azure、调用模型或上传数据；云端身份、检索、托管与下游兼容性均未实测。

## 学习路径与文件

| 路径 | 入口 | 依赖和限制 |
| --- | --- | --- |
| 本地工具 Agent | `agent.py` | 自有 Claude 部署与获准商店 MCP；上游没有商店服务端 |
| Foundry IQ | `ingest.py`，`agent.py --iq` | 文本字段、语义配置、knowledge source 与 KB；不是向量 RAG，无逐用户 ACL |
| Hosted Agent | `hosted.py`，`azure.yaml` | 共用 IQ Agent，提供 Responses 协议；内部 Claude 仍使用 Messages |
| 共用配置 | `config.py`，`.env.example` | 本地 `.env` 固定在此目录，进程环境优先；必需值缺失立即报错 |
| 离线教学数据 | [data/store-faq.md](data/store-faq.md) | 新写的虚构 FAQ；不含真实库存、订单或客户记录 |

## 1. 准备环境

以下 PowerShell 命令从仓库根目录进入实操目录。建议 Python **3.13**（与托管 runtime 一致）；
离线逻辑在 Windows ARM64 Python 3.12 验证；SDK 验证使用本机已有的 Windows x64 Python 3.14。
ARM64 安装时 `cryptography` 缺少预编译 wheel 且本机缺少 MSVC linker，因此改用 x64 环境，
未降低 TLS 校验或安装系统级编译工具。Python 3.13 远程构建仍未验证。
Framework provider/hosting 包为固定的 prerelease；固定的是直接依赖，不是全部传递依赖锁文件。

```powershell
Set-Location .\workshops\claude-foundry
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m pip check
Copy-Item .\.env.example .\.env
```

只填自己的配置，不复制上游环境值或作者服务地址。

| 变量 | 要求 |
| --- | --- |
| `APP_CLAUDE_DEPLOYMENT` | 实际 Claude 部署名，不是模型目录 ID、项目名或 Agent 名 |
| `APP_CLAUDE_API_KEY` | 对应资源的 key；本教学实现只支持 key，**不能用于 Entra-only 模型** |
| `APP_CLAUDE_BASE_URL` | `https://<resource>.services.ai.azure.com/anthropic`；不是项目端点或完整 `/v1/messages` URL |
| `CUPCAKE_MCP_URL` | 显式指定获准的 Streamable HTTP MCP URL；无第三方默认值 |
| `AZURE_SEARCH_ENDPOINT` | IQ/host 必需：`https://<service>.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | IQ/host MCP 客户端必需，使用 Search admin key；不是普通 query key |
| `KNOWLEDGE_BASE_NAME` | ingestion 与 Agent 共用，默认 `quickstart-cupcake-kb` |
| `SEARCH_INDEX_NAME` / `KNOWLEDGE_SOURCE_NAME` | ingestion 使用，默认 `quickstart-cupcake-index` / `quickstart-cupcake-source` |

商店 MCP 必须由你拥有或明确获准使用，并且在服务端**只暴露只读工具**。
本示例不分发其后端，也不自动获取远程 instructions/banner。
系统提示中的“只读”不是授权控制；不要连接会暴露下单、取消或退款工具的生产服务。
支持 HTTPS；仅本地开发允许 `http://localhost` / `127.0.0.1` / `[::1]`。
未实现商店 MCP 的 OAuth/token 注入；需要认证的服务须自行适配，不要在 URL 中放凭据。

Claude Marketplace、订阅、区域与身份要求见 [前置条件矩阵](../../claude-on-foundry-workshop-guide.md#prerequisites)；
运行前重新核对 [Claude 官方说明](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude)。

## 2. 本地 Claude + MCP

```powershell
.\.venv\Scripts\python.exe .\agent.py --check-config
```

这只检查配置结构，不验证密钥、资源归属、MCP 工具、网络或模型支持。
准备获准服务后，才执行：

```powershell
.\.venv\Scripts\python.exe .\agent.py
```

不会自动发送 `hello`。问只读库存/订单状态问题；同一交互循环复用一个 session，
输入 `exit` / `quit` 退出。Agent 上下文负责退出、异常与取消时回收工具连接。
模型/工具错误向调用者显式传播，不假装回答成功。

## 3. Foundry IQ：先离线，后选择性上传

离线预览无需 Azure、key 或第三方 Python 包，从任意工作目录均可定位默认 FAQ：

```powershell
python .\ingest.py
python -m unittest discover -s .\tests -p test_workshop.py -v
```

预期输出 **5 个分块**，包括文档前言；默认操作不读取 `.env`，不发送网络请求。
用 `--document <path>` 选择自己的获准 Markdown。

只有完成数据审查、预算和实验资源审批后才安装 ingestion 依赖并上传：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-ingest.txt
.\.venv\Scripts\python.exe .\ingest.py --apply
.\.venv\Scripts\python.exe .\agent.py --iq --check-config
.\.venv\Scripts\python.exe .\agent.py --iq
```

创建端与 KB MCP 共用 `2026-04-01` API，使用 `azure-search-documents==12.0.0`；
不配置 embeddings、向量字段或 KB LLM。ingestion 无 Search key 时使用
`DefaultAzureCredential`，需要 Search Service Contributor 和 Search Index Data Contributor；
Agent MCP 仍是 key-only，不能把 ingestion 的 Entra fallback 理解为整个应用已无密钥。
服务须支持语义/KB 能力；schema 与 SDK 构造验证不等于服务实测。
参见 [Search KB 官方说明](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base)。

`--apply` 使用 `create_or_update_*`；**同名对象可能被覆盖**。只用专用实验对象。
每个上传结果都必须成功，否则停止，不再更新 source/KB；已创建的索引或部分文档不会自动回滚。
重复上传用稳定分块 ID 覆盖，但不清除旧的多余 ID；FAQ 缩短后应使用新实验索引，避免陈旧检索结果。
验证“退货政策”走 KB、“库存”走商店 MCP，以实际调用记录和来源为准。

## 4. Hosted Responses：先核对，再部署

`azure.yaml` 的源码项目为本目录，入口 `hosted.py`，runtime 为 `python_3_13`，
`remote_build` 从 `requirements.txt` 恢复依赖。无需额外 Dockerfile。
配置使用 `APP_CLAUDE_*`，不覆盖平台保留的 `FOUNDRY_*`。
固定 hosting 版本使用一个 Agent 实例，由 host 在首次请求时进入其上下文并在关闭时清理。
`history_source="agent"` 使用 Agent 的会话历史，由 host 的 session store 持久化；
不复用本地交互循环的 session。该版本不支持新版文档中的请求级 factory。
商店/Search 工具使用应用级身份，不实现逐用户认证隔离；不要用于多租户生产服务。

```powershell
.\.venv\Scripts\python.exe .\hosted.py --check-config
```

完成下游准备后，可在本地启动真实 host（仍会调用收费云服务）：

```powershell
.\.venv\Scripts\python.exe .\hosted.py
```

使用当前扩展的本地客户端前，按 [本地运行说明](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/run-hosted-agent-locally)
配置正确 azd 环境、启动端口和 `env`；`azd ai agent run` / `invoke --local` 并不离线。
本目录 YAML 只描述 Agent，**不是自包含资源 provision 模板**；不创建模型、Search 或商店后端。
发布前按 [源码部署说明](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent-code)
关联自己已批准的 Foundry 项目、核对当前租户/订阅/项目和 azd 扩展版本，
并将 YAML 中七个运行时变量配置到该 azd 环境。不要仅因本地 `.env` 已填就直接部署。
密钥通过获准 secret/connection 流程注入，不要写进 YAML 或提交到 Git。

`.agentignore` 排除 `.env*`、`.azure`、虚拟环境、日志、测试与 ingestion 数据；
MIT LICENSE 与 NOTICE 保留在包内。Git 忽略不等于打包排除，发布前须检查所选 azd 实际 ZIP 清单。
本次未安装/运行 azd，也未验证平台打包或云端 host。当前 YAML 规范见
[官方参考](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/azure-yaml-reference)。

## 验证范围与清理

离线测试覆盖必需配置/端点、资源命名、FAQ 分块、上传失败、无自动问候、会话复用、
退出/异常/取消，以及配置检查不构造 Agent。SDK 导入、对象构造和 YAML 检查不发网络请求。
安装两份 requirements 后可用 `.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v` 运行包含 SDK 契约检查的完整本地测试。
本次 **23 项本地测试通过**，`pip check` 无依赖冲突；115 个相对链接/锚点检查无新增错误。
历史 AOAI 手册已有一处目录锚点问题，未在本次无关整合中修改。
SDK 输出 prerelease/实验特性与 Python 3.14 弃用警告；不代表失败，也不构成生产稳定性保证。
成功推理、MCP 认证、KB 检索、Python 3.13 远程构建、托管会话和部署包都需要读者后续云端验证。

停止本机进程不会停止 Search/模型/托管费用。按 [运维与清理指南](../../claude-on-foundry-workshop-guide.md#operations)
盘点实际创建的专用资源后处理，不使用示例名称盲删共享对象。既有 PDF 不随本次整合重新生成。
