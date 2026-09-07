import os
from typing import Literal
from agent.config import AGENT_NAMES, MAX_CRITIQUE_ATTEMPTS

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from news_client.newsapi_client import NewsAPIClient
from news_client.current_api import CurrentsAPIClient

import re
from agent.prompts import *
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.structured_outputs import SchedulerDecision, QueryCritique

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agent.state import NewsState
from storage.postgres_store import get_default_store

llm = ChatOpenAI(model="gpt-5-mini")
embeddings_model = OpenAIEmbeddings()

currentsapi_client = CurrentsAPIClient()

# def scheduler(state: NewsState) -> Command[AGENT_NAMES]:
#     structured_llm = llm.with_structured_output(SchedulerDecision)
#     chat_history = state.get("agent_chats", {}).get("scheduler", [])

#     messages = [
#         SCHEDULER_SYSTEM_PROMPT,

#         *[m for m in chat_history],
#         SCHEDULER_PROMPT_TEMPLATE.format(
#             search_query=state.get("search_query"),
#             articles=state.get("articles"),
#             published_articles=state.get("published_articles")
#         )
#     ]
#     response: SchedulerDecision = structured_llm.invoke(messages)

#     update = {}
#     if response.agent_prompt:
#         update["agent_chats"] = {
#             "scheduler": [messages[-1], AIMessage(f"Agent: {response.next_agent} Prompt: {response.agent_prompt}")],
#             response.next_agent: [HumanMessage(response.agent_prompt)]
#         }

#     return Command(goto=response.next_agent, update=update)


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
    
    articles = [
        _article_to_document(a) for a in currentsapi_client.search(search_query)
    ]

    return {
            "articles": articles,
            "articles_fetched": True,
        }


def store_articles_worker(state: NewsState) -> NewsState:
    store = get_default_store(embeddings=embeddings_model)
    stored_ids = store.upsert_articles(state["articles"])

    return {"stored_article_ids": stored_ids, "articles_stored": True}

def _format_articles(articles: list[Document]) -> str:
    if not articles:
        return "(none)"
    return "\n\n".join(
        f"- {a.page_content}\n  url: {a.metadata.get('url')}" for a in articles
    )

def criticize(state: NewsState) -> Command[Literal["search_worker", END]]:
    structured_llm = llm.with_structured_output(QueryCritique)

    articles = state.get("articles", [])
    published_articles = state.get("published_articles", [])
    published_urls = {a.metadata.get("url") for a in published_articles}
    duplicate_count = sum(1 for a in articles if a.metadata.get("url") in published_urls)

    messages = [
        CRITIC_SYSTEM_PROMPT,
        CRITIC_PROMPT_TEMPLATE.format(
            search_query=state.get("search_query"),
            num_fetched=len(articles),
            articles=_format_articles(articles),
            published_articles=_format_articles(published_articles),
        ),
    ]

    critique: QueryCritique = structured_llm.invoke(messages)
    attempts = state.get("critique_attempts", 0) + 1

    if critique.verdict == "approve" or attempts >= MAX_CRITIQUE_ATTEMPTS or not critique.revised_query:
        return Command(goto=END, update={"critique_attempts": attempts})

    return Command(
        goto="search_worker",
        update={
            "critique_attempts": attempts,
            "agent_chats": {
                "search_worker": [
                    HumanMessage(
                        f"Critic feedback: {critique.feedback}\n"
                        f"Suggested query: {critique.revised_query}"
                    )
                ]
            },
        },
    )

builder = StateGraph(NewsState)

# builder.add_node(
#     "scheduler",
#     scheduler,
#     destinations=("search_worker", END),
# )

builder.add_node("search_worker", search_worker)
builder.add_node("fetch_articles_worker", fetch_articles_worker)
builder.add_node("store_articles_worker", store_articles_worker)
builder.add_node("criticize", criticize, destinations=("search_worker", END))

builder.add_edge(START, "search_worker")
builder.add_edge("search_worker", "fetch_articles_worker")
builder.add_edge("fetch_articles_worker", "store_articles_worker")
builder.add_edge("store_articles_worker", "criticize")

search_graph = builder.compile()
