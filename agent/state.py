from typing import TypedDict
import warnings
import os

from langchain_core.documents import Document

if not os.environ['USER_PROFILE']:
    if os.environ['USER_PROFILE_FILEPATH']:
        with open(os.environ['USER_PROFILE_FILEPATH'], 'r') as f:
            USER_PROFILE = f.read()
    else:
        USER_PROFILE = None
        warnings.warn("Specify either USER_PROFILE or USER_PROFILE_FILEPATH in your environment!")
else:
    USER_PROFILE = os.environ['USER_PROFILE']

class NewsState(TypedDict):
    user_profile: str = USER_PROFILE if USER_PROFILE else ""
    search_query: str = ""
    top_headlines: list[Document] = []
    articles: list[Document] = []
    stored_article_ids: list[str] = []
    # hot_headlines: list[str] = []
    # telegram_channels: list[str] = []
    # published_news: list[str] = []