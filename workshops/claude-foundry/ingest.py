"""Adapted text/semantic Search ingestion. Offline by default; --apply writes to Azure."""

import argparse
import re
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from config import (
    SEARCH_API_VERSION,
    SEMANTIC_CONFIG_NAME,
    WORKSHOP_ROOT,
    SearchSettings,
    load_environment,
)

DEFAULT_DOCUMENT = WORKSHOP_ROOT / "data" / "store-faq.md"

if TYPE_CHECKING:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes.models import (
        KnowledgeBase,
        SearchIndex,
        SearchIndexKnowledgeSource,
    )


class Chunk(TypedDict):
    id: str
    title: str
    category: str
    content: str


def chunk_document(path: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    chunks: list[Chunk] = []
    for part in re.split(r"\n(?=## )", text):
        body = part.strip()
        if not body:
            continue
        title = body.splitlines()[0].lstrip("# ").strip()
        chunks.append(
            {"id": str(len(chunks)), "title": title, "category": title, "content": body}
        )
    if not chunks:
        raise ValueError("The FAQ document is empty; no Search objects were changed")
    return chunks


def build_definitions(
    settings: SearchSettings,
) -> "tuple[SearchIndex, SearchIndexKnowledgeSource, KnowledgeBase]":
    from azure.search.documents.indexes.models import (
        KnowledgeBase,
        KnowledgeSourceReference,
        SearchableField,
        SearchFieldDataType,
        SearchIndex,
        SearchIndexFieldReference,
        SearchIndexKnowledgeSource,
        SearchIndexKnowledgeSourceParameters,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        SimpleField,
    )

    index = SearchIndex(
        name=settings.index_name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(
                name="category", type=SearchFieldDataType.String, filterable=True, facetable=True
            ),
            SearchableField(name="content", type=SearchFieldDataType.String),
        ],
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name=SEMANTIC_CONFIG_NAME,
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="title"),
                        keywords_fields=[SemanticField(field_name="category")],
                        content_fields=[SemanticField(field_name="content")],
                    ),
                )
            ]
        ),
    )
    source = SearchIndexKnowledgeSource(
        name=settings.source_name,
        description="Fictional cupcake store workshop FAQ.",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=settings.index_name,
            semantic_configuration_name=SEMANTIC_CONFIG_NAME,
            source_data_fields=[
                SearchIndexFieldReference(name=name)
                for name in ("id", "title", "category", "content")
            ],
            search_fields=[SearchIndexFieldReference(name="content")],
        ),
    )
    kb = KnowledgeBase(
        name=settings.kb_name,
        knowledge_sources=[KnowledgeSourceReference(name=settings.source_name)],
    )
    return index, source, kb


def upload_documents(client: "SearchClient", chunks: list[Chunk]) -> None:
    results = client.upload_documents(documents=chunks)
    expected = {chunk["id"] for chunk in chunks}
    succeeded = {result.key for result in results if result.succeeded}
    failed = [result.key for result in results if not result.succeeded]
    if failed or succeeded != expected or len(results) != len(chunks):
        raise RuntimeError(
            f"Search upload incomplete: {len(succeeded)}/{len(chunks)} succeeded; "
            f"failed document IDs: {', '.join(failed) or 'missing results'}. "
            "Knowledge source and KB were not updated."
        )
    print(f"Uploaded {len(chunks)}/{len(chunks)} chunks.")


def apply_ingestion(settings: SearchSettings, chunks: list[Chunk]) -> None:
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient

    index, source, kb = build_definitions(settings)
    credential = (
        AzureKeyCredential(settings.api_key) if settings.api_key else DefaultAzureCredential()
    )
    try:
        with (
            SearchIndexClient(
                endpoint=settings.endpoint, credential=credential, api_version=SEARCH_API_VERSION
            ) as index_client,
            SearchClient(
                endpoint=settings.endpoint,
                index_name=settings.index_name,
                credential=credential,
                api_version=SEARCH_API_VERSION,
            ) as search_client,
        ):
            index_client.create_or_update_index(index)
            upload_documents(search_client, chunks)
            index_client.create_or_update_knowledge_source(source)
            index_client.create_or_update_knowledge_base(kb)
    finally:
        if isinstance(credential, DefaultAzureCredential):
            credential.close()
    print("Search objects updated. KB retrieval still requires a separate cloud check.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", type=Path, default=DEFAULT_DOCUMENT)
    parser.add_argument(
        "--apply", action="store_true", help="Create/update Search objects and upload FAQ data"
    )
    args = parser.parse_args()
    chunks = chunk_document(args.document)
    print(f"Prepared {len(chunks)} chunks.")
    if not args.apply:
        print("Offline preview only. No credentials loaded and no Azure requests sent.")
        for chunk in chunks:
            print(f"{chunk['id']}: {chunk['title']}")
        return
    load_environment()
    settings = SearchSettings.from_environment(require_key=False)
    apply_ingestion(settings, chunks)


if __name__ == "__main__":
    main()
