# Claude on Foundry hands-on

[中文](README.md) | [Repository home](../../README.en.md) | [Full research guide](../../claude-on-foundry-workshop-guide.en.md)

The upstream learning paths share one implementation here: local Claude + store MCP,
then Foundry IQ, then Hosted Responses. See [NOTICE](NOTICE.md) and [LICENSE](LICENSE)
for the pinned source, adaptations, and retained MIT notice. The existing research
guide covers architecture, eligibility, identity, and historical source issues.
**Use this page to run the integrated samples**, rather than the upstream commands.

> **Boundaries:** Offline preview, configuration checks and unit tests do not call Azure.
> Starting the agent/host connects to remote MCP; user questions can trigger billable
> model/tool calls. `ingest.py --apply` creates/updates Search objects and uploads the FAQ.
> No Azure deployment, model invocation or data upload was performed. Cloud identity,
> retrieval, hosting and downstream compatibility remain untested.

## Paths and files

| Path | Entry point | Requirements and limits |
| --- | --- | --- |
| Local tool agent | `agent.py` | Your own Claude deployment and approved store MCP; upstream supplies no store server |
| Foundry IQ | `ingest.py`, `agent.py --iq` | Text fields, semantic configuration, knowledge source and KB; no vector RAG or per-user ACL |
| Hosted agent | `hosted.py`, `azure.yaml` | Shares the IQ agent; external Responses, internal Claude Messages |
| Shared configuration | `config.py`, `.env.example` | `.env` is resolved in this directory; process settings win; missing required values fail |
| Offline data | [data/store-faq.md](data/store-faq.md) | Newly written fictional FAQ; no live stock, orders or customer records |

## 1. Environment

From the repository root, use these PowerShell commands. Python **3.13** is recommended
to match the hosted runtime. Offline logic was checked on Windows ARM64 Python 3.12;
SDK checks use the already installed Windows x64 Python 3.14. ARM64 installation lacked a
prebuilt `cryptography` wheel and the MSVC linker, so an x64 environment is used instead,
without weakening TLS or installing system build tools. Python 3.13 remote builds remain untested.
Provider/hosting packages are pinned
prereleases. Direct dependencies are pinned, not the entire transitive dependency graph.

```powershell
Set-Location .\workshops\claude-foundry
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m pip check
Copy-Item .\.env.example .\.env
```

Supply only your own values, never upstream environment files or the author's service URL.

| Variable | Requirement |
| --- | --- |
| `APP_CLAUDE_DEPLOYMENT` | Actual Claude deployment name, not catalog model ID, project or agent name |
| `APP_CLAUDE_API_KEY` | Matching resource key; this teaching implementation is key-only, **not for Entra-only models** |
| `APP_CLAUDE_BASE_URL` | `https://<resource>.services.ai.azure.com/anthropic`, not a project or full `/v1/messages` URL |
| `CUPCAKE_MCP_URL` | Explicit approved Streamable HTTP MCP URL; no third-party default |
| `AZURE_SEARCH_ENDPOINT` | Required for IQ/host: `https://<service>.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Required for IQ/host MCP: Search admin key, not an ordinary query key |
| `KNOWLEDGE_BASE_NAME` | Shared by ingestion/agent; default `quickstart-cupcake-kb` |
| `SEARCH_INDEX_NAME` / `KNOWLEDGE_SOURCE_NAME` | Ingestion; defaults `quickstart-cupcake-index` / `quickstart-cupcake-source` |

Use only an owned or explicitly approved MCP service that **exposes read-only tools at
the server**. The backend is not included. The agent does not fetch remote instructions
or banners. Its read-only prompt is not an authorization control: do not connect
production services exposing order, cancellation or refund tools.
HTTPS is required except for local development on `http://localhost`, `127.0.0.1` or `[::1]`.
Store MCP OAuth/token injection is not implemented; authenticated services need an
appropriate adaptation. Never embed credentials in URLs.

Check the [prerequisite matrix](../../claude-on-foundry-workshop-guide.en.md#prerequisites)
and current [official Claude guidance](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude)
for Marketplace, subscription, region and identity requirements.

## 2. Local Claude + MCP

```powershell
.\.venv\Scripts\python.exe .\agent.py --check-config
```

This validates structure, not credentials, resource ownership, MCP tools, networking or model support.
Only after preparing approved services, run:

```powershell
.\.venv\Scripts\python.exe .\agent.py
```

There is no automatic `hello`. Ask read-only stock/order-status questions; the loop
reuses one session. Type `exit` / `quit` to stop. The agent context releases tools on
exit, failure and cancellation. Model/tool errors propagate rather than masquerading as success.

## 3. Foundry IQ: offline first, optional upload

The preview requires no Azure account, keys or third-party Python packages. The default
FAQ is resolved relative to the script, independent of the working directory.

```powershell
python .\ingest.py
python -m unittest discover -s .\tests -p test_workshop.py -v
```

Expect **5 chunks**, including the document preamble. This default does not load `.env`
or send requests. Use `--document <path>` for your own approved Markdown.

Only after data, budget and experiment-resource approval, install ingestion dependencies and upload:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-ingest.txt
.\.venv\Scripts\python.exe .\ingest.py --apply
.\.venv\Scripts\python.exe .\agent.py --iq --check-config
.\.venv\Scripts\python.exe .\agent.py --iq
```

Creation and KB MCP share API `2026-04-01`, with `azure-search-documents==12.0.0`.
There are no embeddings, vector fields or KB LLM. Without a Search key, ingestion uses
`DefaultAzureCredential` with Search Service Contributor and Search Index Data Contributor.
The agent MCP remains key-only; ingestion's Entra fallback does not make the application keyless.
The service must support semantic/KB capabilities. SDK construction/schema checks do not
establish service compatibility. See [official Search KB guidance](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base).

`--apply` uses `create_or_update_*`: **existing same-name objects can be overwritten**.
Use dedicated experiment objects. Every upload result must succeed or source/KB updates stop.
An existing index or partial uploads are not rolled back. Stable chunk IDs are overwritten
on reruns, but obsolete IDs are not removed; use a fresh experiment index after shortening the FAQ.
Verify policy questions use KB and stock questions use store MCP through actual traces and sources.

## 4. Hosted Responses: review before deployment

`azure.yaml` points to this directory, starts `hosted.py`, declares `python_3_13` and
`remote_build`, and restores `requirements.txt`. No Dockerfile is needed.
Custom settings use `APP_CLAUDE_*`, not reserved platform `FOUNDRY_*` variables.
The pinned hosting version owns one agent instance, enters its context on the first request
and cleans it up at shutdown. `history_source="agent"` uses agent session history persisted
by the host's session store, not the local chat loop's session. This version does not support
the request-level factory shown in newer documentation. Store/Search tools use application
identity, not per-user authentication isolation; do not use this as a multi-tenant production service.

```powershell
.\.venv\Scripts\python.exe .\hosted.py --check-config
```

After preparing downstream services, you can start the real host locally
(it still uses billable cloud dependencies):

```powershell
.\.venv\Scripts\python.exe .\hosted.py
```

Before using azd's local client, follow [local running guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/run-hosted-agent-locally)
to configure the azd environment, port and `env`. Neither `azd ai agent run` nor
`invoke --local` is offline. This YAML defines the agent only, **not a self-contained
resource provisioning template**; it does not create the model, Search or store backend.
Before publishing, follow [source deployment guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent-code)
to bind your approved Foundry project, confirm tenant/subscription/project and extension
versions, and configure all seven YAML runtime variables in that azd environment.
A local `.env` alone is insufficient. Inject secrets through an approved secret/connection
workflow, not YAML literals or Git.

`.agentignore` excludes `.env*`, `.azure`, virtual environments, logs, tests and ingestion
data, retaining LICENSE and NOTICE. Git exclusions are not ZIP exclusions: inspect the
actual package with the selected azd version before publishing. azd was not installed/run
and platform packaging or cloud hosting was not verified.
See the [official YAML reference](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/azure-yaml-reference).

## Validation and cleanup

Offline tests cover required settings/endpoints, names, chunking, upload failures, no
automatic greeting, session reuse, exit/failure/cancellation and configuration-only entrypoints.
SDK imports, object construction and YAML checks send no requests. Inference, MCP authentication,
KB retrieval, Python 3.13 remote builds, hosted sessions and deployment packages require cloud checks.
After installing both requirements files, run `.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v`
for all local tests, including SDK contract checks.
**All 23 local tests passed**, with no dependency conflicts reported by `pip check`.
Checking 115 relative links/anchors found no new errors; one inherited AOAI manual
contents-anchor issue was left unchanged. SDK experimental/prerelease and Python 3.14
deprecation warnings are not test failures or a production-stability guarantee.

Stopping local processes does not stop Search/model/hosting charges. Inventory actual dedicated
resources and follow the [operations/cleanup guide](../../claude-on-foundry-workshop-guide.en.md#operations);
never delete shared resources by sample name. The historical PDF was not regenerated.
