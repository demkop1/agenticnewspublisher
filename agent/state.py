from typing import TypedDict, Literal, Annotated
from agent.config import USER_PROFILE, AGENT_NAMES
import operator

from langchain_core.documents import Document


def merge_agent_prompts(
    existing: dict[str, list[str]], update: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Reducer for orchestrator_prompts: appends each agent's new messages to
    its existing chat history instead of overwriting the whole dict, so a
    node only needs to return the delta (the message(s) for the agent it's
    dispatching to), not the full accumulated history."""
    merged = {**existing}
    for agent, new_messages in update.items():
        merged[agent] = merged.get(agent, []) + new_messages
    return merged


class NewsState(TypedDict):
    # user_profile: str = USER_PROFILE if USER_PROFILE else None
    search_query: str
    top_headlines: list[Document] = []
    articles: list[Document] = []
    stored_article_ids: list[str] = []

    #Orchestrator
    next_agent: AGENT_NAMES
    agent_chats: Annotated[dict[str, list], merge_agent_prompts] = {}
    # published_articles: Annotated[dict[str, list[str]], ], = []