from typing import TypedDict, Literal
from config import USER_PROFILE, AGENT_NAMES
import operator

from langchain_core.documents import Document

class NewsState(TypedDict):
    user_profile: str = USER_PROFILE if USER_PROFILE else None
    search_query: str
    top_headlines: list[Document] = []
    articles: list[Document] = []
    stored_article_ids: list[str] = []

    #Orchestrator
    next_agent: AGENT_NAMES
    published_articles: list[Document, operator.add] = []