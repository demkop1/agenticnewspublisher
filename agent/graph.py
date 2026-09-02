import os
from typing import Literal
from agent.config import AGENT_NAMES

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from news_client.newsapi_client import NewsAPIClient
import re
from agent.prompts import *
from langchain_core.messages import SystemMessage, HumanMessage
from agent.structured_outputs import OrchestratorDecision

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agent.state import NewsState
from storage.postgres_store import get_default_store

llm = ChatOpenAI(model="gpt-5-mini")
embeddings_model = OpenAIEmbeddings()

newsapi_client = NewsAPIClient()

def orchestrator_node(state: NewsState) -> Command[AGENT_NAMES]:
    # if not state.get("search_query"):
    #     return Command(goto="search_worker")
    structured_llm = llm.with_structured_output(OrchestratorDecision)
    messages = [
        ORCHESTRATOR_SYSTEM_PROMPT_TEMPLATE.format(**{
            "search_query": state.get("search_query", ""),
            "current_articles": state.get("top_headlines")
        }),
        *[HumanMessage(a) for a in state.get("published_articles", [])],
        ORCHESTRATOR_SYSTEM_PROMPT2
    ]
    response = structured_llm.invoke(messages)

    update = {}
    if response.agent_prompt:
        update["agent_chats"] = {response.next_agent: [HumanMessage(response.agent_prompt)]}

    return Command(goto=response.next_agent, update=update)


def search_worker(state: NewsState) -> NewsState:
    chat_history = state.get("agent_chats", {}).get("search_worker", [])
    messages = [SEARCH_SYSTEM_PROMPT, *[m for m in chat_history]]

    response = llm.invoke(messages)
    search_query = re.findall(STRING_EXTRACTOR, response.content)[-1]

    return {"search_query": search_query, "agent_chats": {"search_worker": [AIMessage(search_query)]}}


def fetch_articles_worker(state: NewsState) -> NewsState:
    def _article_to_document(a):
        doc_content = a['title'] + "\n" + a['content']
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
            "articles": articles,
            "articles_fetched": True,
        }


def store_articles_worker(state: NewsState) -> NewsState:
    store = get_default_store(embeddings=embeddings_model)
    stored_ids = store.upsert_articles(state["top_headlines"] + state["articles"])

    return {"stored_article_ids": stored_ids, "articles_stored": True}


builder = StateGraph(NewsState)

builder.add_node(
    "orchestrator",
    orchestrator_node,
    destinations=("search_worker", END),
)
builder.add_node("search_worker", search_worker)
builder.add_node("fetch_articles_worker", fetch_articles_worker)
builder.add_node("store_articles_worker", store_articles_worker)

builder.add_edge(START, "orchestrator")

builder.add_edge("search_worker", "fetch_articles_worker")
builder.add_edge("fetch_articles_worker", "store_articles_worker")
builder.add_edge("store_articles_worker", "orchestrator")

graph = builder.compile()
