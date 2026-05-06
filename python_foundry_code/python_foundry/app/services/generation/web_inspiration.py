import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class WebInspirationFetcher:
    """
    Fetches and analyzes top real websites for a given intent using a search API and scraping.
    """
    def __init__(self, search_api_key: str = None, search_engine_id: str = None):
        self.search_api_key = search_api_key
        self.search_engine_id = search_engine_id

    def search_web(self, query: str, num_results: int = 2) -> List[str]:
        """
        Uses Google Custom Search API to get top website URLs for the query.
        """
        if not self.search_api_key or not self.search_engine_id:
            raise ValueError("Search API key and engine ID must be set.")
        url = (
            f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.search_api_key}"
            f"&cx={self.search_engine_id}&num={num_results}"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        return [item['link'] for item in data.get('items', [])]

    def fetch_and_parse(self, url: str) -> Dict:
        """
        Fetches and parses a website, returning its main structure and text content.
        """
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract main sections, nav, and visible text
        nav = soup.find('nav')
        main = soup.find('main') or soup.body
        title = soup.title.string if soup.title else ''
        return {
            'url': url,
            'title': title,
            'nav': nav.get_text(separator=' | ', strip=True) if nav else '',
            'main': main.get_text(separator='\n', strip=True) if main else '',
        }

    def get_inspirations(self, query: str) -> List[Dict]:
        urls = self.search_web(query)
        return [self.fetch_and_parse(url) for url in urls]
