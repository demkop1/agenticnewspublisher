import os
import dotenv

dotenv.load_dotenv()

import requests

API_BASE = "https://newsapi.org/v2"


class NewsAPIClient:
    def __init__(self, api_key: str = None):
        self.api_key = (
            api_key
            or os.environ.get("NEWS_API")
        )
        if not self.api_key:
            raise ValueError("Set NEWS_API (env or arg).")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = {**(params or {}), "apiKey": self.api_key}
        response = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=30)
        payload = response.json()
        if payload.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {payload.get('message')}")
        return payload

    def get_top_headlines(self, country: str = None, category: str = None,
                           query: str = None, page_size: int = 20) -> list:
        """Fetch top headlines. Returns a list of article dicts."""
        params = {"pageSize": page_size}
        if country:
            params["country"] = country
        if category:
            params["category"] = category
        if query:
            params["q"] = query
        return self._get("top-headlines", params)["articles"]

    def search(self, query: str, language: str = "en",
               sort_by: str = "publishedAt", page_size: int = 20) -> list:
        """Search all articles matching a query. Returns a list of article dicts."""
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
        }
        return self._get("everything", params)["articles"]


if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(PROJECT_ROOT)
    # print(os.environ)
    news = NewsAPIClient()
    articles = news.get_top_headlines(query="Ukraine")
    print(articles[0].keys())
    for a in articles[:5]:
        print(f"- {a['title']} ({a['source']['name']})")
