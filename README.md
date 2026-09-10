# NewsAgent

An agentic news pipeline built on [LangGraph](https://github.com/langchain-ai/langgraph) that searches for news matching a user's stated interests, extracts and deduplicates discrete events from the coverage, and picks which of those events are worth writing up — as a step toward auto-publishing curated news via API.

> **Status:** actively evolving. The search → extract → dedupe → store pipeline runs end to end; the publishing side (picking events, retrieving supporting context, and writing the final article) is in progress. See [Status & roadmap](#status--roadmap).

## How it works

The graph is composed of two LangGraph subgraphs, each a mix of LLM-driven agents and deterministic steps:

```mermaid
flowchart TD
    START((START)) --> search_worker

    subgraph search_graph["search_graph — find, extract, store"]
        search_worker["search_worker<br/>LLM builds a CurrentsAPI query<br/>from the user profile"] --> fetch_articles_worker["fetch_articles_worker<br/>fetch matching articles"]
        fetch_articles_worker --> criticize{"criticize<br/>LLM checks relevance &amp; redundancy"}
        criticize -- revise --> search_worker
        criticize -- approve --> create_events["create_events<br/>LLM extracts structured events<br/>per article"]
        create_events --> deduplicate["deduplicate<br/>TF-IDF similarity clustering,<br/>highest-confidence event wins"]
        deduplicate --> store_articles_worker["store_articles_worker<br/>chunk + embed articles (pgvector),<br/>upsert events (Postgres)"]
    end

    store_articles_worker --> event_picker

    subgraph publisher_graph["publisher_graph — pick & write"]
        event_picker["event_picker<br/>LLM selects which events<br/>are worth publishing"] --> fetch_rag["fetch_rag<br/>LLM-generated query retrieves<br/>supporting article context"]
        fetch_rag --> generate_article["generate_article<br/>🚧 write the final article"]
    end

    generate_article --> END((END))
```

Everything shares one `NewsState` (`agent/state.py`) as it flows through the graph, and every LLM call is grounded in a single user profile (`user_profile.txt` or `USER_PROFILE`) so the whole pipeline stays personalized to what that user actually wants to read.

## Features

- **Query generation & self-critique** — an LLM drafts a boolean search query from the user profile, a second LLM pass critiques it for relevance and redundancy against what's already been published, and the query gets revised (up to a configurable retry cap) before articles are ever fetched.
- **Structured event extraction** — each fetched article is passed through a structured-output LLM call that pulls out discrete events (description, type, date, actors, confidence) rather than treating the whole article as one blob.
- **Similarity-based deduplication** — near-duplicate events (e.g. the same event reported by two sources) are clustered via TF-IDF cosine similarity and collapsed down to the single highest-confidence version.
- **Two storage backends, chosen deliberately per use case**:
  - Articles are chunked (`RecursiveCharacterTextSplitter`) and embedded into Postgres via `pgvector`/`langchain-postgres`, for semantic retrieval later.
  - Events are stored as plain rows (`id`, `content`, `metadata JSONB`) via raw `psycopg`, upserted by a stable id — no embeddings needed for structured event data.
- **Idempotent upserts everywhere** — articles, article chunks, and events are all keyed by deterministic ids, so re-running the pipeline updates existing rows instead of duplicating them.
- **Swappable news sources** — `news_client/` ships both a NewsAPI client and a Currents API client behind the same interface.

## Tech stack

- [LangGraph](https://github.com/langchain-ai/langgraph) for orchestration, [LangChain](https://github.com/langchain-ai/langchain) + OpenAI for the LLM/embedding calls
- [Postgres](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector) (via `langchain-postgres` for articles, raw `psycopg` for events)
- [Currents API](https://currentsapi.services/) / [NewsAPI](https://newsapi.org/) as news sources
- scikit-learn (TF-IDF + cosine similarity) for dedup

## Getting started

### Prerequisites

- Python 3.11+
- Docker (for the local Postgres/pgvector instance)
- An OpenAI API key, and an API key from [Currents API](https://currentsapi.services/) and/or [NewsAPI](https://newsapi.org/)

### Setup

```bash
git clone <this-repo>
cd agenticnewspublisher
pip install -r requirements.txt
```

Create a `.env` file in the project root:

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | LLM calls and embeddings |
| `CURRENTS_API` | Yes* | Currents API key (currently the active news source) |
| `NEWS_API` | Yes* | NewsAPI key (alternative client, not currently wired into the graph) |
| `DATABASE_URL` | Yes | Postgres connection string, e.g. `postgresql+psycopg://news:news@localhost:5432/news` |
| `USER_PROFILE` or `USER_PROFILE_FILEPATH` | Yes (one of them) | The reader's interests/preferences, in plain text — drives every prompt in the pipeline |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` | No | Optional [LangSmith](https://smith.langchain.com/) tracing |

\* only whichever news client you're actually using needs a valid key.

Start a local pgvector-enabled Postgres:

```bash
docker compose up -d
```

> **Troubleshooting:** if you have a native/Homebrew Postgres already listening on `5432`, macOS may route `127.0.0.1:5432` to that instance instead of the container — which doesn't have the `news` role and fails with `role "news" does not exist`. Either stop the native instance or remap the container's port in `docker-compose.yml` (and update `DATABASE_URL` to match).

### Run it

This project is a [LangGraph](https://langchain-ai.github.io/langgraph/) app (see `langgraph.json`). Run it locally with:

```bash
pip install langgraph-cli
langgraph dev
```

which serves the graph defined in `agent/graph.py` through LangGraph's local API/Studio server.

## Project structure

```
agent/
  graph.py              # top-level graph: search_graph -> publisher_graph
  state.py              # shared NewsState
  config.py             # user profile loading, thresholds, id namespaces, splitter config
  prompts.py             # every prompt used by the pipeline
  structured_outputs.py # pydantic schemas for structured LLM outputs
  subgraph/
    search_graph.py     # search -> fetch -> critique -> extract events -> dedupe -> store
    publisher_graph.py  # pick events -> retrieve context (RAG) -> generate article
news_client/
  newsapi_client.py     # NewsAPI client
  current_api.py        # Currents API client (same article shape as NewsAPI's)
storage/
  articles_vectorstore.py # pgvector-backed article store (chunking, dedup, similarity search)
  events_store.py          # plain Postgres/psycopg event store
docker-compose.yml       # local pgvector-enabled Postgres for development
user_profile.txt         # example/default user profile
```

## Status & roadmap

- [x] Query generation with self-critique loop
- [x] Article fetching (Currents API)
- [x] Structured event extraction per article
- [x] Event deduplication (TF-IDF similarity clustering)
- [x] Article + event storage (pgvector and Postgres)
- [x] Event selection for publishing
- [x] RAG query generation & retrieval of supporting article context
- [ ] Final article generation from retrieved context
- [ ] Publishing the generated article through an API.
