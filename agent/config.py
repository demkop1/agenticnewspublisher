from typing import Literal
import warnings
import os

from langgraph.graph import END

import dotenv
dotenv.load_dotenv()

if not os.environ['USER_PROFILE']:
    if os.environ['USER_PROFILE_FILEPATH']:
        with open(os.environ['USER_PROFILE_FILEPATH'], 'r') as f:
            USER_PROFILE = f.read()
    else:
        USER_PROFILE = None
        warnings.warn("Specify either USER_PROFILE or USER_PROFILE_FILEPATH in your environment!")
else:
    USER_PROFILE = os.environ['USER_PROFILE']

AGENT_DESCRIPTIONS: dict[str, str] = {
    "search_worker": "Generates the next API search query from the user's profile and preferences.",
    # "fetch_articles_worker": "Fetches top headlines and matching articles from NewsAPI for the current search query.",
    # "store_articles_worker": "Persists fetched articles as embeddings in Postgres, deduplicated by URL.",
    END: "When everything seems okay and an article is published, the end of execution is called"
}

AGENT_NAMES = list(AGENT_DESCRIPTIONS.keys())

MAX_CRITIQUE_ATTEMPTS = 3