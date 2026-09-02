import os
import uuid
from typing import Iterable, Optional

import dotenv

dotenv.load_dotenv()

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector

# Fixed namespace so the same article URL always maps to the same row id,
# across processes and restarts.
_ID_NAMESPACE = uuid.UUID("f0b3d9d0-6e1a-4b8b-9b0a-2f5c7a1e9d3c")

DEFAULT_COLLECTION_NAME = os.environ.get("POSTGRES_NEWS_COLLECTION", "news_articles")


def _connection_string() -> str:
    connection = os.environ.get("DATABASE_URL")
    if not connection:
        raise ValueError(
            "Set DATABASE_URL to a Postgres connection string, e.g. "
            "postgresql+psycopg://user:password@localhost:5432/news"
        )
    return connection


def article_id(document: Document) -> str:
    key = document.metadata.get("url") or document.page_content
    return str(uuid.uuid5(_ID_NAMESPACE, key))


class NewsPostgresStore:
    """Persists extracted news articles as embeddings in Postgres via pgvector.

    Storage is deduplicated by article URL: documents already present are
    skipped before embedding (so they are never re-sent to the embeddings
    API) and re-storing a known article upserts its row instead of
    duplicating it.
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        connection: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        if embeddings is None:
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings()

        self.store = PGVector(
            embeddings=embeddings,
            connection=connection or _connection_string(),
            collection_name=collection_name,
            use_jsonb=True,
        )

    def upsert_articles(self, documents: Iterable[Document]) -> list[str]:
        """Store articles that aren't already in the database.

        Returns the ids (existing and newly stored) for every article passed
        in, in order.
        """
        documents = list(documents)
        if not documents:
            return []

        ids = [article_id(d) for d in documents]
        existing_ids = {d.id for d in self.store.get_by_ids(ids)}

        new_docs, new_ids, seen = [], [], set()
        for doc, doc_id in zip(documents, ids):
            if doc_id in existing_ids or doc_id in seen:
                continue
            seen.add(doc_id)
            new_docs.append(doc)
            new_ids.append(doc_id)

        if new_docs:
            self.store.add_documents(new_docs, ids=new_ids)

        return ids

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self.store.similarity_search(query, k=k)


_default_store: Optional[NewsPostgresStore] = None


def get_default_store(embeddings: Optional[Embeddings] = None) -> NewsPostgresStore:
    """Lazily-created, process-wide store so the graph reuses one connection pool."""
    global _default_store
    if _default_store is None:
        _default_store = NewsPostgresStore(embeddings=embeddings)
    return _default_store
