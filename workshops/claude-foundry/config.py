"""Shared configuration for the adapted Claude on Foundry workshop."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

WORKSHOP_ROOT = Path(__file__).resolve().parent
SEARCH_API_VERSION = "2026-04-01"
SEMANTIC_CONFIG_NAME = "cupcake-semantic"


def load_environment() -> None:
    from dotenv import load_dotenv

    load_dotenv(WORKSHOP_ROOT / ".env", override=False)


def require_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def endpoint(name: str, *, local_mcp: bool = False) -> str:
    value = require_setting(name).rstrip("/")
    parsed = urlsplit(value)
    local_http = (
        local_mcp
        and parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    )
    if (
        (parsed.scheme != "https" and not local_http)
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or parsed.query
    ):
        raise ValueError(f"{name} must be an HTTPS URL without credentials, query or fragment")
    if name == "APP_CLAUDE_BASE_URL" and parsed.path != "/anthropic":
        raise ValueError(f"{name} must end in /anthropic, not a project or Messages URL")
    if name == "AZURE_SEARCH_ENDPOINT" and parsed.path:
        raise ValueError(f"{name} must be the Search service URL without a path")
    return value


def resource_name(setting: str, default: str) -> str:
    value = os.getenv(setting, default).strip()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?", value):
        raise ValueError(f"{setting} must be 1-128 lowercase letters, digits or hyphens")
    if "--" in value:
        raise ValueError(f"{setting} must not contain consecutive hyphens")
    return value


@dataclass(frozen=True)
class SearchSettings:
    endpoint: str
    api_key: str | None = field(repr=False)
    index_name: str
    source_name: str
    kb_name: str

    @classmethod
    def from_environment(cls, *, require_key: bool) -> "SearchSettings":
        return cls(
            endpoint=endpoint("AZURE_SEARCH_ENDPOINT"),
            api_key=(
                require_setting("AZURE_SEARCH_API_KEY")
                if require_key
                else os.getenv("AZURE_SEARCH_API_KEY", "").strip() or None
            ),
            index_name=resource_name("SEARCH_INDEX_NAME", "quickstart-cupcake-index"),
            source_name=resource_name("KNOWLEDGE_SOURCE_NAME", "quickstart-cupcake-source"),
            kb_name=resource_name("KNOWLEDGE_BASE_NAME", "quickstart-cupcake-kb"),
        )

    @property
    def mcp_url(self) -> str:
        return (
            f"{self.endpoint}/knowledgebases/{self.kb_name}/mcp"
            f"?api-version={SEARCH_API_VERSION}"
        )


@dataclass(frozen=True)
class AgentSettings:
    deployment: str
    api_key: str = field(repr=False)
    base_url: str
    store_mcp_url: str
    search: SearchSettings | None

    @classmethod
    def from_environment(cls, *, iq: bool) -> "AgentSettings":
        return cls(
            deployment=require_setting("APP_CLAUDE_DEPLOYMENT"),
            api_key=require_setting("APP_CLAUDE_API_KEY"),
            base_url=endpoint("APP_CLAUDE_BASE_URL"),
            store_mcp_url=endpoint("CUPCAKE_MCP_URL", local_mcp=True),
            search=SearchSettings.from_environment(require_key=True) if iq else None,
        )
