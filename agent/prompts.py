import dotenv
dotenv.load_dotenv()
import os

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

