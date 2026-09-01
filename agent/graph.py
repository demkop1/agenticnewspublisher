import os
import warnings

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from news_client.newsapi_client import NewsAPIClient
import re
from agent.prompts import SEARCH_SYSTEM_PROMPT, STRING_EXTRACTOR

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from langgraph.graph import StateGraph, START, END
from agent.state import NewsState
from storage.postgres_store import get_default_store, NewsPostgresStore

llm = ChatOpenAI(model="gpt-5-mini")
embeddings_model = OpenAIEmbeddings()

newsapi_client = NewsAPIClient()

#Nodes
def search_node(state: NewsState) -> NewsState:
    response = llm.invoke([SEARCH_SYSTEM_PROMPT])
    search_query = re.findall(STRING_EXTRACTOR, response.content)[-1]

    return {
        "search_query": search_query
    }

def fetch_store_embed_news(state: NewsState) -> NewsState:
    def _article_to_document(a):
        doc_content =  a['title'] + "\n" + a['content']
        a.pop('title'), a.pop('content')
        return Document(doc_content, metadata=a)
    
    search_query = state["search_query"]
    top_headlines = [
        _article_to_document(a) for a in newsapi_client.get_top_headlines(search_query)
    ]
    articles = [
       _article_to_document(a) for a in newsapi_client.search(search_query)
    ]

    return {
        "top_headlines": top_headlines,
        "articles": articles
    }

def store_articles_in_postgres_node(state: NewsState) -> NewsState:
    if not os.environ.get("DATABASE_URL"):
        warnings.warn("DATABASE_URL is not set; skipping Postgres storage of articles.")
        return {}

    store = get_default_store(embeddings=embeddings_model)
    stored_ids = store.upsert_articles(state["top_headlines"] + state["articles"])

    return {
        "stored_article_ids": stored_ids
    }

builder = StateGraph(NewsState)

builder.add_node("search_node", search_node)
builder.add_node("fetch_and_store_news", fetch_store_embed_news)
builder.add_node("store_articles_in_postgres", store_articles_in_postgres_node)

builder.add_edge(START, "search_node")
builder.add_edge("search_node", "fetch_and_store_news")
builder.add_edge("fetch_and_store_news", "store_articles_in_postgres")
builder.add_edge("store_articles_in_postgres", END)

graph = builder.compile()