"""Offline SDK contract checks; install both requirements files before running."""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent
import config
import ingest
import yaml
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.anthropic import AnthropicFoundryClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

ENV = {
    "APP_CLAUDE_DEPLOYMENT": "test-deployment",
    "APP_CLAUDE_API_KEY": "synthetic-model-key",
    "APP_CLAUDE_BASE_URL": "https://test.services.ai.azure.com/anthropic",
    "CUPCAKE_MCP_URL": "https://mcp.example/mcp",
    "AZURE_SEARCH_ENDPOINT": "https://test.search.windows.net",
    "AZURE_SEARCH_API_KEY": "synthetic-search-key",
    "KNOWLEDGE_BASE_NAME": "test-kb",
    "SEARCH_INDEX_NAME": "test-index",
    "KNOWLEDGE_SOURCE_NAME": "test-source",
}


class SDKTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.settings = config.AgentSettings.from_environment(iq=True)
        self.search = self.settings.search

    def test_actual_agent_construction_without_connections(self):
        with patch.object(MCPStreamableHTTPTool, "connect", side_effect=AssertionError("network")):
            built = agent.create_agent(self.settings)
        self.assertIsInstance(built, Agent)
        self.assertIsInstance(built.client, AnthropicFoundryClient)
        self.assertTrue(hasattr(built, "__aenter__"))
        self.assertTrue(hasattr(built, "__aexit__"))

    def test_host_construction_does_not_connect_tools(self):
        with (
            patch("socket.socket.connect", side_effect=AssertionError("network")),
            patch.object(MCPStreamableHTTPTool, "connect", side_effect=AssertionError("network")),
        ):
            server = ResponsesHostServer(agent.create_agent(self.settings), history_source="agent")
        self.assertIsInstance(server, ResponsesHostServer)

    def test_search_models_have_consistent_names_and_no_vectors(self):
        index, source, kb = ingest.build_definitions(self.search)
        self.assertEqual(index.name, "test-index")
        self.assertEqual(source.search_index_parameters.search_index_name, index.name)
        self.assertEqual(kb.knowledge_sources[0].name, source.name)
        self.assertEqual(kb.name, "test-kb")
        self.assertEqual([field.name for field in index.fields], ["id", "title", "category", "content"])
        self.assertTrue(all(field.vector_search_dimensions is None for field in index.fields))
        self.assertEqual(
            source.search_index_parameters.semantic_configuration_name,
            index.semantic_search.configurations[0].name,
        )
        for model in (index, source, kb):
            self.assertIsInstance(model.as_dict(), dict)

    def test_search_clients_accept_explicit_api_version(self):
        credential = AzureKeyCredential("synthetic-search-key")
        with (
            SearchIndexClient(
                endpoint=self.search.endpoint,
                credential=credential,
                api_version=config.SEARCH_API_VERSION,
            ) as index_client,
            SearchClient(
                endpoint=self.search.endpoint,
                index_name=self.search.index_name,
                credential=credential,
                api_version=config.SEARCH_API_VERSION,
            ) as search_client,
        ):
            self.assertTrue(callable(index_client.create_or_update_knowledge_source))
            self.assertTrue(callable(index_client.create_or_update_knowledge_base))
            self.assertTrue(callable(search_client.upload_documents))

    def test_failed_upload_stops_source_and_kb_creation(self):
        index_client = Mock()
        search_client = Mock()
        search_client.upload_documents.return_value = [
            SimpleNamespace(key="0", succeeded=False)
        ]
        index_context = Mock()
        index_context.__enter__ = Mock(return_value=index_client)
        index_context.__exit__ = Mock(return_value=False)
        search_context = Mock()
        search_context.__enter__ = Mock(return_value=search_client)
        search_context.__exit__ = Mock(return_value=False)
        with (
            patch("azure.search.documents.indexes.SearchIndexClient", return_value=index_context),
            patch("azure.search.documents.SearchClient", return_value=search_context),
        ):
            with self.assertRaisesRegex(RuntimeError, "upload incomplete"):
                ingest.apply_ingestion(self.search, ingest.chunk_document(ingest.DEFAULT_DOCUMENT))
        index_client.create_or_update_index.assert_called_once()
        index_client.create_or_update_knowledge_source.assert_not_called()
        index_client.create_or_update_knowledge_base.assert_not_called()
        index_context.__exit__.assert_called_once()
        search_context.__exit__.assert_called_once()

    def test_yaml_entrypoint_dependencies_and_env_match(self):
        definition = yaml.safe_load((ROOT / "azure.yaml").read_text(encoding="utf-8"))
        service = definition["services"]["cupcake-agent"]
        self.assertEqual(service["host"], "azure.ai.agent")
        self.assertEqual(service["project"], ".")
        self.assertEqual(service["codeConfiguration"]["runtime"], "python_3_13")
        self.assertTrue((ROOT / service["codeConfiguration"]["entryPoint"]).is_file())
        self.assertEqual(service["startupCommand"], "python hosted.py")
        env = service["env"]
        self.assertEqual(set(env), set(ENV) - {"SEARCH_INDEX_NAME", "KNOWLEDGE_SOURCE_NAME"})
        self.assertTrue(all(value == "${" + key + "}" for key, value in env.items()))
        self.assertTrue(all(not key.startswith(("FOUNDRY_", "AGENT_")) for key in env))
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("agent-framework-foundry-hosting==", requirements)
        self.assertIn("agent-framework-anthropic==", requirements)


if __name__ == "__main__":
    unittest.main()
