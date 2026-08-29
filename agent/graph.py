from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

import re
from agent.prompts import SEARCH_SYSTEM_PROMPT, STRING_EXTRACTOR

from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, START, END
from agent.state import NewsState

llm = ChatOpenAI(model="gpt-5-mini")

#Nodes
def search_node(state: NewsState) -> NewsState:
    response = llm.invoke([SEARCH_SYSTEM_PROMPT])
    search_query = re.findall(STRING_EXTRACTOR, response.content)[-1]

    return {
        "search_query": search_query
    }

builder = StateGraph(NewsState)

builder.add_node("search_node", search_node)

builder.add_edge(START, "search_node")
builder.add_edge("search_node", END)

graph = builder.compile()