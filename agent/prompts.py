from agent.config import AGENT_NAMES
from agent.state import USER_PROFILE

import re
STRING_EXTRACTOR = re.compile(r"\*\*(.*?)\*\*")

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

SEARCH_SYSTEM_PROMPT = SystemMessage(
f"""
You are an AI agent that generates the query to search for the recent news according to the following user profile and his preferences:
{USER_PROFILE}.

Type the query has to be surrounded by ** and be consistent with CurrentsAPI. Additionally you will also be given with directions on how to generate the search query, you have to comply with them.
"""
)

SCHEDULER_SYSTEM_PROMPT = """
You are a search scheduler and your task is to schedule and query the search_worker whenever such a need arises.
These needs can be when the current search query fails to return relevant articles, when broader research is needed, and etc.

You will be provided with the state values, such as the current search query, the top headlines extracted from there, as well as the current articles published so far.
Additionally, you also have to stick to the user's profile: %s.
""" % (USER_PROFILE)

SCHEDULER_PROMPT_TEMPLATE = HumanMessagePromptTemplate.from_template(
"""
search_query: {search_query}
articles: {articles}
published_articles: {published_articles}
"""
)

CRITIC_SYSTEM_PROMPT = SystemMessage(
f"""
You are a critic that reviews a news search query before it is relied on again, checking it
against the following user profile and preferences:
{USER_PROFILE}

You will be given the search query that was just used, the articles it fetched, and the
articles already published to the user's channel.

Judge the query on:
1. Relevance - does it match the topics, entities, and angle the user profile cares about,
   rather than being generic or drifting onto an unrelated topic?
2. Redundancy - do the fetched articles mostly repeat stories, angles, or sources already
   present in published_articles? A query that keeps surfacing what's already been published
   is not doing its job, even if it is topically on point.
3. CurrentsAPI fit - the query is the `keywords` string sent to CurrentsAPI's /search endpoint,
   which supports boolean AND/OR and phrase quoting. Flag queries that are malformed, so broad
   (e.g. a single generic word) that they return noise, or so over-qualified that they likely
   return nothing new.

Decide "approve" if the query is fine as-is, or "revise" if it should change. When you revise,
give a concrete replacement query, surrounded by ** the same way the search worker formats it,
that fixes the specific problem you identified rather than a generic rewrite.
"""
)

CRITIC_PROMPT_TEMPLATE = HumanMessagePromptTemplate.from_template(
"""
search_query: {search_query}

fetched_articles ({num_fetched} total):
{articles}

published_articles (for judging redundancy):
{published_articles}
"""
)

# ORCHESTRATOR_SYSTEM_PROMPT = SystemMessage(
# """
# You are an orchestrator, you have to manage in the most efficient way possible the following agents: %s. 
# You should also take into account the user preferences %s.
# You will be given with the current state values and based on that you have to determine the next agent to execute, as well as should you write prompts to them.
# Consider the following state descriptions:

# search_query - A query that searches for news through CurrentsAPI. Sometimes it may get irrelevant, so you would want to change it.
# fetched_articles - The most recent truncated articles fetched by the search_query.
# top_headlines - The most recent headlines fetched by the search_query.
# published_articles - THe so far published articles.

#  For example:

# USER:
# search_query: None
# fetched_articles: []
# top_headlines: []
# published_articles: [].

# You:
# search_worker
# """ % (AGENT_NAMES, USER_PROFILE)
# )

# ORCHESTRATOR_HUMAN_PROMPT_TEMPLATE = HumanMessagePromptTemplate.from_template(
# """
# search_query: {search_query}
# fetched_articles: {articles}
# top_headlines: {top_headlines}
# published_articles: {published_articles}
# """ 
# )