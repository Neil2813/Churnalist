"""Unit tests for app.ingestion components."""
import pytest
from app.ingestion.html_cleaner import clean_html_content
from app.ingestion.normalizer import normalize_article_text


def test_clean_html_content():
    html = """
    <html>
      <head><script>alert('xss');</script></head>
      <body>
        <nav>Menu links</nav>
        <p>Major News Story Headline</p>
        <p>This is the first paragraph of the article body.</p>
        <p>This is the second paragraph with details.</p>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    cleaned = clean_html_content(html)
    assert "Major News Story Headline" in cleaned.extracted_text
    assert "first paragraph" in cleaned.extracted_text
    assert "<script>" not in cleaned.extracted_text




def test_normalize_article_text():
    raw_text = "  This   is  a   test sentence with   irregular    spaces.  "
    norm = normalize_article_text(raw_text)
    assert norm == "This is a test sentence with irregular spaces."
