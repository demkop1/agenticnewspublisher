from config import AGENT_NAMES
from agent.state import USER_PROFILE

import re
STRING_EXTRACTOR = re.compile(r"\*\*(.*?)\*\*")

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

SEARCH_SYSTEM_PROMPT = SystemMessage(
f"""
You are an AI agent that generates the query to search for the recent news according to the following user profile and his preferences:
{USER_PROFILE}.

Type the query has to be surrounded by ** and contain at most 100 characters. The query should be consistent with NewsAPI.
"""
)

ORCHESTRATOR_SYSTEM_PROMPT = SystemMessage(
"""
You are an orchestrator, you have to manage in the most efficient way possible the following agents: %s. 
You are given with the following information about the state:
    - search_query: {search_query}
    - current_articles: {current_articles}.
You will also provided with the so-far published articles below (If there are none or you dont see them, ignore it).
""" % (AGENT_NAMES)
)
ORCHESTRATOR_SYSTEM_PROMPT2 = SystemMessage(
"""
Based on the state information and the published articles above, choose the next agent to operate on.
"""
)