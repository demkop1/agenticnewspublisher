import os
import dotenv

dotenv.load_dotenv()

import requests

API_BASE = "https://api.currentsapi.services/v1"

class CurrentsAPIClient:
    def __init__(self, api_key: str = None):
        self.api_key = (
            api_key
            or os.environ.get("CURRENTS_API")
        )
        if not self.api_key:
            raise ValueError("Set CURRENTS_API (env or arg).")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        headers = {"Authorization": self.api_key}
        response = requests.get(f"{API_BASE}/{endpoint}", params=(params or {}), headers=headers, timeout=30)
        payload = response.json()
        if payload.get("status") != "ok":
            raise RuntimeError(f"Currents API error: {payload}")
        return payload

    @staticmethod
    def _normalize_article(a: dict) -> dict:
        """Reshape a Currents article into NewsAPI's article shape (title,
        content, url, source.name, publishedAt, ...) so callers can use
        NewsAPIClient and CurrentsAPIClient interchangeably."""
        return {
            "title": a.get("title", ""),
            "content": a.get("description", ""),
            "url": a.get("url"),
            "source": {"name": a.get("author") or "Currents"},
            "author": a.get("author"),
            "publishedAt": a.get("published"),
            "urlToImage": a.get("image"),
            "language": a.get("language"),
            "category": a.get("category"),
        }

    def get_top_headlines(self, country: str = None, category: str = None,
                           query: str = None, page_size: int = 20) -> list:
        """Fetch the latest news. Returns a list of article dicts.

        Currents' /latest-news endpoint only supports a language filter, so
        country/category/query/page_size are accepted for interface
        compatibility with NewsAPIClient but are otherwise unused.
        """
        articles = self._get("latest-news", {"language": "en"})["news"]
        return [self._normalize_article(a) for a in articles]

    def search(self, query: str, language: str = "en",
               sort_by: str = "publishedAt", page_size: int = 20) -> list:
        """Search all articles matching a query. Returns a list of article dicts."""
        params = {
            "keywords": query,
            "language": language,
        }
        articles = self._get("search", params)["news"]
        return [self._normalize_article(a) for a in articles]


if __name__ == "__main__":
    import os
    import sys
    import datetime
    from dotenv import load_dotenv

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(PROJECT_ROOT)

    news = CurrentsAPIClient()
    # articles = news.get_top_headlines( query="Ukraine" )
    query = """ "Ukraine" AND (Russia OR Russian OR Putin OR Kremlin OR "Russian forces" OR "Russian army") AND ("war in Ukraine" OR invasion OR "Russian invasion" OR counteroffensive OR offensive OR frontline OR missiles OR drones OR Donetsk OR Luhansk OR Kharkiv OR Kyiv OR Mariupol OR Crimea OR sanctions)"""
    articles = news.search( query=query )
    # print(articles[0].keys())
    print(articles[0].get("url"), articles[0].get("source"))
    for a in articles[:5]:
        print(f"- {a['title']} {a['content']} ({a['source']['name']}) - { a['publishedAt'] }")
