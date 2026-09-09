import os
import datetime
import uuid
from typing import Literal
from agent.config import AGENT_NAMES, MAX_CRITIQUE_ATTEMPTS, EVENT_ID_NAMESPACE, DUPLICATE_SIMILARITY_THRESHOLD

import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from news_client.newsapi_client import NewsAPIClient
from news_client.current_api import CurrentsAPIClient

import re
from agent.prompts import *
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.structured_outputs import SchedulerDecision, QueryCritique, Event, EventsExtraction

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agent.state import NewsState
from storage.articles_vectorstore import get_news_store

llm = ChatOpenAI(model="gpt-5-mini")
embeddings_model = OpenAIEmbeddings()

currentsapi_client = CurrentsAPIClient()

builder = StateGraph(NewsState)

builder.add_edge(START, END)

publisher_graph = builder.compile()
