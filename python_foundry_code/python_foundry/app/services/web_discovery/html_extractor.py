import trafilatura
from bs4 import BeautifulSoup

from app.utils.html_utils import extract_headings, html_to_text


class HtmlExtractor:
    def extract(self, html: str, url: str) -> dict:
        extracted_text = trafilatura.extract(html) if html else ""
        text = extracted_text or html_to_text(html)

        soup = BeautifulSoup(html, "html.parser")
        title = ""
        if html and soup.title:
            title = soup.title.get_text(strip=True)

        nav_links = []
        for a in soup.select("nav a")[:30]:
            label = a.get_text(strip=True)
            href = a.get("href", "")
            if label:
                nav_links.append({"label": label, "href": href})

        return {
            "url": url,
            "title": title,
            "text": text,
            "headings": extract_headings(html),
            "nav_links": nav_links,
        }
