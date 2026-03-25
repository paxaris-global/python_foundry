from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def extract_headings(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag_name in ["h1", "h2", "h3"]:
        for tag in soup.find_all(tag_name):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
    return headings[:80]
