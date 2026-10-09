import asyncio
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent
import config
import hosted
import ingest

MODEL_ENV = {
    "APP_CLAUDE_DEPLOYMENT": "test-deployment",
    "APP_CLAUDE_API_KEY": "synthetic-model-key",
    "APP_CLAUDE_BASE_URL": "https://test.services.ai.azure.com/anthropic",
    "CUPCAKE_MCP_URL": "https://mcp.example/mcp",
}
SEARCH_ENV = {
    "AZURE_SEARCH_ENDPOINT": "https://test.search.windows.net",
    "AZURE_SEARCH_API_KEY": "synthetic-search-key",
    "KNOWLEDGE_BASE_NAME": "test-kb",
    "SEARCH_INDEX_NAME": "test-index",
    "KNOWLEDGE_SOURCE_NAME": "test-source",
}


class ConfigTests(unittest.TestCase):
    def test_local_does_not_require_search(self):
        with patch.dict(os.environ, MODEL_ENV, clear=True):
            settings = config.AgentSettings.from_environment(iq=False)
        self.assertIsNone(settings.search)
        self.assertNotIn("synthetic-model-key", repr(settings))

    def test_iq_uses_shared_names_and_version(self):
        with patch.dict(os.environ, MODEL_ENV | SEARCH_ENV, clear=True):
            settings = config.AgentSettings.from_environment(iq=True)
        self.assertEqual(
            settings.search.mcp_url,
            "https://test.search.windows.net/knowledgebases/test-kb/mcp?api-version=2026-04-01",
        )
        self.assertNotIn("synthetic-search-key", repr(settings))

    def test_no_author_mcp_fallback(self):
        env = MODEL_ENV.copy()
        del env["CUPCAKE_MCP_URL"]
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "CUPCAKE_MCP_URL"):
                config.AgentSettings.from_environment(iq=False)

    def test_rejects_empty_required_values(self):
        for name in MODEL_ENV:
            with self.subTest(name=name), patch.dict(
                os.environ, MODEL_ENV | {name: " "}, clear=True
            ):
                with self.assertRaisesRegex(ValueError, name):
                    config.AgentSettings.from_environment(iq=False)

    def test_rejects_wrong_model_endpoint(self):
        for path in ("/api/projects/test", "/anthropic/v1/messages", "/models/anthropic"):
            with self.subTest(path=path), patch.dict(
                os.environ,
                MODEL_ENV | {"APP_CLAUDE_BASE_URL": f"https://test.example{path}"},
                clear=True,
            ):
                with self.assertRaisesRegex(ValueError, "/anthropic"):
                    config.AgentSettings.from_environment(iq=False)

    def test_rejects_unsafe_mcp_url(self):
        for url in (
            "http://remote.example/mcp",
            "https://user:secret@mcp.example/mcp",
            "https://mcp.example/mcp?key=secret",
            "https://mcp.example/mcp#fragment",
        ):
            with self.subTest(url=url), patch.dict(
                os.environ, MODEL_ENV | {"CUPCAKE_MCP_URL": url}, clear=True
            ):
                with self.assertRaisesRegex(ValueError, "CUPCAKE_MCP_URL"):
                    config.AgentSettings.from_environment(iq=False)

    def test_allows_local_mcp_for_owned_development_server(self):
        with patch.dict(
            os.environ, MODEL_ENV | {"CUPCAKE_MCP_URL": "http://localhost:8000/mcp"}, clear=True
        ):
            self.assertEqual(
                config.AgentSettings.from_environment(iq=False).store_mcp_url,
                "http://localhost:8000/mcp",
            )

    def test_search_key_optional_only_for_ingestion(self):
        env = SEARCH_ENV.copy()
        del env["AZURE_SEARCH_API_KEY"]
        with patch.dict(os.environ, env, clear=True):
            self.assertIsNone(config.SearchSettings.from_environment(require_key=False).api_key)
            with self.assertRaisesRegex(ValueError, "AZURE_SEARCH_API_KEY"):
                config.SearchSettings.from_environment(require_key=True)

    def test_rejects_bad_resource_names(self):
        for name in ("", "Uppercase", "space name", "x/mcp?y=z", "-leading", "x--y"):
            with self.subTest(name=name), patch.dict(
                os.environ, SEARCH_ENV | {"KNOWLEDGE_BASE_NAME": name}, clear=True
            ):
                with self.assertRaisesRegex(ValueError, "KNOWLEDGE_BASE_NAME"):
                    config.SearchSettings.from_environment(require_key=False)


class IngestionTests(unittest.TestCase):
    def test_synthetic_faq_shape(self):
        chunks = ingest.chunk_document(ingest.DEFAULT_DOCUMENT)
        self.assertEqual(len(chunks), 5)
        self.assertEqual([c["id"] for c in chunks], ["0", "1", "2", "3", "4"])
        self.assertEqual(chunks[3]["title"], "Returns")
        self.assertTrue(all(set(c) == {"id", "title", "category", "content"} for c in chunks))

    def test_blank_document_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.md"
            path.write_text(" \n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty"):
                ingest.chunk_document(path)

    def test_preview_does_not_load_credentials_or_apply(self):
        with (
            patch.object(sys, "argv", ["ingest.py"]),
            patch.object(ingest, "load_environment") as load,
            patch.object(ingest, "apply_ingestion") as apply,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            ingest.main()
        load.assert_not_called()
        apply.assert_not_called()
        self.assertIn("Offline preview only", output.getvalue())

    def test_upload_rejects_partial_missing_or_duplicate_results(self):
        chunks = ingest.chunk_document(ingest.DEFAULT_DOCUMENT)
        good = [SimpleNamespace(key=c["id"], succeeded=True) for c in chunks]
        for results in (
            good[:-1],
            good[:-1] + [SimpleNamespace(key="4", succeeded=False)],
            good[:-1] + [good[0]],
        ):
            with self.subTest(results=results):
                client = Mock()
                client.upload_documents.return_value = results
                with self.assertRaisesRegex(RuntimeError, "upload incomplete"):
                    ingest.upload_documents(client, chunks)

    def test_upload_accepts_complete_results(self):
        chunks = ingest.chunk_document(ingest.DEFAULT_DOCUMENT)
        client = Mock()
        client.upload_documents.return_value = [
            SimpleNamespace(key=c["id"], succeeded=True) for c in chunks
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            ingest.upload_documents(client, chunks)
        client.upload_documents.assert_called_once_with(documents=chunks)


class AgentTests(unittest.TestCase):
    def test_check_config_never_constructs_agent(self):
        for module, argv in (
            (agent, ["agent.py", "--check-config", "--iq"]),
            (hosted, ["hosted.py", "--check-config"]),
        ):
            with (
                self.subTest(module=module.__name__),
                patch.dict(os.environ, MODEL_ENV | SEARCH_ENV, clear=True),
                patch.object(module, "load_environment"),
                patch.object(module, "create_agent") as create,
                patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                module.main()
                create.assert_not_called()

    def test_chat_closes_on_exit_error_and_cancellation(self):
        with patch.dict(os.environ, MODEL_ENV, clear=True):
            settings = config.AgentSettings.from_environment(iq=False)
        for failure in (None, RuntimeError("model unavailable"), asyncio.CancelledError()):
            with self.subTest(failure=failure):
                fake = AsyncMock()
                fake.__aenter__.return_value = fake
                fake.create_session = Mock(return_value=object())
                fake.run.side_effect = failure
                inputs = ["quit"] if failure is None else ["what is in stock?"]
                with (
                    patch.object(agent, "create_agent", return_value=fake),
                    patch("builtins.input", side_effect=inputs),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    if failure is None:
                        asyncio.run(agent.chat(settings))
                        fake.run.assert_not_called()
                    else:
                        with self.assertRaises(type(failure)):
                            asyncio.run(agent.chat(settings))
                fake.__aexit__.assert_awaited_once()

    def test_chat_reuses_session_without_automatic_greeting(self):
        with patch.dict(os.environ, MODEL_ENV, clear=True):
            settings = config.AgentSettings.from_environment(iq=False)
        fake = AsyncMock()
        fake.__aenter__.return_value = fake
        session = object()
        fake.create_session = Mock(return_value=session)
        fake.run.return_value = SimpleNamespace(text="test reply")
        with (
            patch.object(agent, "create_agent", return_value=fake),
            patch("builtins.input", side_effect=["", "first", "second", "exit"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            asyncio.run(agent.chat(settings))
        self.assertEqual(fake.run.await_count, 2)
        for call in fake.run.await_args_list:
            self.assertIs(call.kwargs["session"], session)


if __name__ == "__main__":
    unittest.main()
