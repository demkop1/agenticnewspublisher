import os
from typing import Literal
from agent.config import AGENT_NAMES

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from news_client.newsapi_client import NewsAPIClient
from news_client.current_api import CurrentsAPIClient

import re
from agent.prompts import *
from langchain_core.messages import SystemMessage, HumanMessage

from agent.subgraph.search_graph import search_graph

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agent.state import NewsState
from storage.postgres_store import get_default_store

llm = ChatOpenAI(model="gpt-5-mini")
embeddings_model = OpenAIEmbeddings()
currentsapi_client = CurrentsAPIClient()


builder = StateGraph(NewsState)

builder.add_node("search_graph", search_graph)

builder.add_edge(START, "search_graph")
builder.add_edge("search_graph", END)

graph = builder.compile()
