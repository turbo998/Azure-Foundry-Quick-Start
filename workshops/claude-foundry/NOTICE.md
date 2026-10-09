# Source and adaptation / 来源与改编

Adapted from Shilpa Jain's
[Claude-on-foundry-handsonworkshop](https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/tree/4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e),
commit `4326fb9c76cdac1f1b6e7444151e32fa99ec2e6e`, checked on 2026-10-09.
Copyright (c) 2026 Shilpa Jain. The upstream [MIT license](LICENSE) is retained
in full; it applies to the adapted workshop, not a relicensing of the rest
of this repository.

本目录基于上游 `agent.py`、`FoundryIQ/agent_IQ.py`、
`FoundryIQ/ingest_foundry_iq.py` 和 Hosted Agent 的实现思路改编，不是整库镜像。
保留三条学习路径，共用 Agent 与配置，采用当前 provider 导入，固定直接依赖，
增加离线测试、失败检查和打包排除。原环境文件、外部服务地址、重复依赖、
缺失的调试配置不随本目录分发。FAQ 为本仓库新写的虚构教学数据，
不代表上游商店政策或真实业务。

The adapted code shares configuration and agent construction, requires an
explicit approved MCP URL, uses application-owned instructions instead of remote
prompts, and sends no automatic greeting. Ingestion resolves its FAQ relative to
the script, aligns resource names with the agent, and stops on upload failure.
Hosted configuration uses application-prefixed model settings and an `env` map.
The sample FAQ is newly written synthetic training data, not upstream store policy.

The license grants no access to the author's MCP service. These are learning
samples, not production approval or evidence of successful Azure execution.
