## Article storage (Postgres)

Extracted news articles can be persisted as embeddings in Postgres (via
[pgvector](https://github.com/pgvector/pgvector) and `langchain-postgres`),
deduplicated by article URL so re-fetched articles upsert instead of
duplicating and are skipped before re-embedding.

1. Start a local pgvector-enabled Postgres: `docker compose up -d`
2. Set `DATABASE_URL` in `.env` (defaults to the docker-compose credentials,
   e.g. `postgresql+psycopg://news:news@localhost:5432/news`)

If `DATABASE_URL` is unset, the graph skips Postgres storage and only keeps
articles in memory for the run, as before.
