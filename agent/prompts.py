import dotenv
dotenv.load_dotenv()
import os

if not os.environ['USER_PROFILE']:
    if os.environ['USER_PROFILE_FILEPATH']:
        with open(os.environ['USER_PROFILE_FILEPATH'], 'r') as f:
            user_profile = f.read()
    else:
        raise FileNotFoundError("Specify either USER_PROFILE or USER_PROFILE_FILEPATH in your environment!")
else:
    user_profile = os.environ['USER_PROFILE']

import re
STRING_EXTRACTOR = re.compile(r"\*\*(.*?)\*\*")

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate


SEARCH_SYSTEM_PROMPT = SystemMessage(
f"""
You are an AI agent that generates the query to search for the recent news according to the following user profile and his preferences:
{user_profile}.

Type the query surrounded by **.
"""
)

