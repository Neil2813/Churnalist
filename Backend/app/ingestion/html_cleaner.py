"""HTML cleaning and structured text extraction module."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup
try:
    from selectolax.parser import HTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HTMLParser = None
    HAS_SELECTOLAX = False

from app.core.logging import get_logger

logger = get_logger(__name__)



@dataclass
class CleanedHTMLResult:
    """Extracted text and metadata from an HTML document."""
    title: str | None
    text: str
    author: str | None
    published_date_str: str | None
    canonical_url: str | None
    metadata: dict[str, Any]


class HTMLCleaner:
    """
    Cleans raw web HTML and extracts body text, titles, and metadata.
    Uses selectolax for high performance, falling back to BeautifulSoup if selectolax encounters issues.
    """

    # Unwanted HTML tags to strip
    STRIP_TAGS = {
        "script", "style", "nav", "footer", "header", "aside", "form",
        "iframe", "noscript", "svg", "button", "input", "select", "textarea"
    }

    # Classes/IDs commonly associated with boilerplate/ads
    BOILERPLATE_PATTERN = re.compile(
        r"(comment|sidebar|advertisement|banner|social-share|related-posts|cookie|footer|nav|popup|widget)",
        re.IGNORECASE
    )

    def extract(self, html_content: str, fallback_url: str | None = None) -> CleanedHTMLResult:
        """Extract structured text and metadata from raw HTML string."""
        if not html_content or not html_content.strip():
            return CleanedHTMLResult(
                title=None,
                text="",
                author=None,
                published_date_str=None,
                canonical_url=fallback_url,
                metadata={}
            )

        if HAS_SELECTOLAX:
            try:
                return self._extract_selectolax(html_content, fallback_url)
            except Exception as exc:
                logger.warning("selectolax_extraction_failed_falling_back_to_bs4", error=str(exc))
        return self._extract_bs4(html_content, fallback_url)


    def _extract_selectolax(self, html_content: str, fallback_url: str | None = None) -> CleanedHTMLResult:
        tree = HTMLParser(html_content)

        # 1. Canonical URL
        canonical_url = fallback_url
        canonical_tag = tree.css_first("link[rel='canonical']")
        if canonical_tag and canonical_tag.attributes.get("href"):
            canonical_url = canonical_tag.attributes.get("href")

        # 2. Title extraction
        title = None
        og_title = tree.css_first("meta[property='og:title']") or tree.css_first("meta[name='twitter:title']")
        if og_title and og_title.attributes.get("content"):
            title = og_title.attributes.get("content")
        elif tree.css_first("title"):
            title = tree.css_first("title").text(strip=True)

        # 3. Author extraction
        author = None
        author_tag = tree.css_first("meta[name='author']") or tree.css_first("meta[property='article:author']")
        if author_tag and author_tag.attributes.get("content"):
            author = author_tag.attributes.get("content")

        # 4. Published date string
        published_date_str = None
        date_tag = (
            tree.css_first("meta[property='article:published_time']")
            or tree.css_first("meta[name='publication_date']")
            or tree.css_first("meta[name='date']")
        )
        if date_tag and date_tag.attributes.get("content"):
            published_date_str = date_tag.attributes.get("content")

        # 5. Remove unwanted tags
        for tag_name in self.STRIP_TAGS:
            for node in tree.css(tag_name):
                node.decompose()

        # 6. Extract main content paragraphs
        paragraphs: list[str] = []
        # Prefer main/article tags if present
        container = tree.css_first("article") or tree.css_first("main") or tree.body

        if container:
            for node in container.css("p"):
                # Check for boilerplate class/id
                node_cls = node.attributes.get("class", "")
                node_id = node.attributes.get("id", "")
                if self.BOILERPLATE_PATTERN.search(node_cls) or self.BOILERPLATE_PATTERN.search(node_id):
                    continue

                p_text = node.text(strip=True)
                if p_text and len(p_text.split()) > 3:  # Skip trivial snippets
                    paragraphs.append(p_text)

        full_text = "\n\n".join(paragraphs)

        return CleanedHTMLResult(
            title=title.strip() if title else None,
            text=full_text,
            author=author.strip() if author else None,
            published_date_str=published_date_str,
            canonical_url=canonical_url,
            metadata={"paragraph_count": len(paragraphs)}
        )

    def _extract_bs4(self, html_content: str, fallback_url: str | None = None) -> CleanedHTMLResult:
        soup = BeautifulSoup(html_content, "lxml")

        # Canonical URL
        canonical_url = fallback_url
        link_canon = soup.find("link", rel="canonical")
        if link_canon and link_canon.get("href"):
            canonical_url = str(link_canon["href"])

        # Title
        title = None
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if meta_title and meta_title.get("content"):
            title = str(meta_title["content"])
        elif soup.title:
            title = soup.title.get_text(strip=True)

        # Author
        author = None
        meta_author = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if meta_author and meta_author.get("content"):
            author = str(meta_author["content"])

        # Date
        published_date_str = None
        meta_date = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "date"})
        if meta_date and meta_date.get("content"):
            published_date_str = str(meta_date["content"])

        # Strip unwanted elements
        for element in soup(self.STRIP_TAGS):
            element.decompose()

        paragraphs: list[str] = []
        container = soup.find("article") or soup.find("main") or soup.body

        if container:
            for p in container.find_all("p"):
                p_text = p.get_text(strip=True)
                if p_text and len(p_text.split()) > 3:
                    paragraphs.append(p_text)

        full_text = "\n\n".join(paragraphs)

        return CleanedHTMLResult(
            title=title.strip() if title else None,
            text=full_text,
            author=author.strip() if author else None,
            published_date_str=published_date_str,
            canonical_url=canonical_url,
            metadata={"paragraph_count": len(paragraphs)}
        )


def clean_html_content(html: str, url: str | None = None):
    """Module-level helper function to clean HTML using HTMLCleaner."""
    cleaner = HTMLCleaner()
    res = cleaner.extract(html, fallback_url=url)
    # Expose helper attributes extracted_text and cleaned_html for test compatibility
    res.extracted_text = res.text
    res.cleaned_html = html
    return res

