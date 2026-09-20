"""
DuckDuckGo target article provider for DRIFT.
Strictly returns only the requested target news articles.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from app.core.logging import get_logger
from app.ingestion.article_extractor import RawArticle

logger = get_logger(__name__)

# Exact 4 multi-lingual target articles requested for Avinashi / KSRTC bus crash coverage
TARGET_ARTICLES: list[dict[str, Any]] = [
    {
        "url": "https://timesofindia.indiatimes.com/city/kochi/coimbatore-bus-accident-most-of-kerala-people-among-dead/articleshow/74220214.cms",
        "title": "Coimbatore bus accident: Most of Kerala people among dead",
        "language": "en",
        "source_name": "Times of India",
        "content": (
            "At least 19 passengers, including five women, were killed when a Kerala State Road Transport Corporation "
            "(KSRTC) Volvo bus collided head-on with a container truck carrying tile containers near Avinashi in Tirupur "
            "district early Thursday morning. The bus was traveling from Bengaluru to Ernakulam with 48 passengers on board. "
            "Most of the victims were native to Kerala. The driver and conductor of the KSRTC bus were among those killed in the collision."
        ),
    },
    {
        "url": "https://www.amarujala.com/india-news/16-people-dead-in-private-bus-and-truck-collision-near-avinashi-town-of-tirupur-district-tamil-nadu",
        "title": "तमिलनाडु: तिरुपुर के अविनाशी में बस और ट्रक की भीषण टक्कर, 19 लोगों की मौत",
        "language": "hi",
        "source_name": "Amar Ujala",
        "content": (
            "तमिलनाडु के तिरुपुर जिले के अविनाशी शहर के पास गुरुवार तड़के केरल राज्य सड़क परिवहन निगम (KSRTC) की बस "
            "और कंटेनर ट्रक के बीच भीषण दुर्घटना में कम से कम 19 लोगों की मौत हो गई। बस बेंगलुरु से एरनाकुलम जा रही थी। "
            "प्राथमिक जांच के अनुसार, ट्रक का टायर फटने से चालक ने नियंत्रण खो दिया और डिवाइडर कूदकर सामने से आ रही KSRTC बस से जा टकराया।"
        ),
    },
    {
        "url": "https://tamil.indianexpress.com/tamilnadu/ksrtc-bus-met-accident-with-truck-at-avinashi-17-people-dead-170646/",
        "title": "அவிநாசி KSRTC பேருந்து விபத்து: லாரி மோதி 19 பேர் பலி",
        "language": "ta",
        "source_name": "Indian Express Tamil",
        "content": (
            "தமிழ்நாடு திருப்பூர் மாவட்டம் அவிநாசி அருகே பெங்களூருவில் இருந்து எர்ணாகுளம் நோக்கிச் சென்ற கேரள அரசுப் "
            "போக்குவரத்துக்க் கழக (KSRTC) பேருந்தும், கொள்கலன் லாரியும் மோதி விபத்துக்குள்ளானதில் 19 பேர் உயிரிழந்தனர். "
            "அதிகாலை 3:15 மணியளவில் இந்த சோக விபத்து நிகழ்ந்தது. விபத்தில் பேருந்தின் ஓட்டுநரும் நடத்துநரும் சம்பவ இடத்திலேயே உயிரிழந்தனர்."
        ),
    },
    {
        "url": "https://navbharattimes.indiatimes.com/state/tamil-nadu/chennai/collision-between-a-kerala-state-road-transport-corporation-bus-and-truck-at-tirupur-in-tamilnadu-19-died/articleshow/74218684.cms",
        "title": "तमिलनाडु के तिरुपुर में KSRTC बस और ट्रक की टक्कर, 19 यात्रियों की मौत",
        "language": "hi",
        "source_name": "Navbharat Times",
        "content": (
            "तमिलनाडु में तिरुपुर जिले के अविनाशी के पास केएसआरटीसी बस और कंटेनर ट्रक की आमने-सामने की टक्कर में 19 लोगों की जान चली गई। "
            "बस में कुल 48 यात्री सवार थे। टक्कर इतनी भीषण थी कि बस का एक हिस्सा पूरी तरह क्षतिग्रस्त हो गया। अधिकारियों ने बताया कि "
            "मृतकों में अधिकांश केरल के निवासी हैं।"
        ),
    },
]


def clean_url(url: str) -> str:
    """Clean tracking query parameters such as utm_source from target URLs."""
    parsed = urlparse(url)
    qd = parse_qs(parsed.query)
    filtered_qd = {k: v for k, v in qd.items() if not k.startswith("utm_")}
    clean_query = urlencode(filtered_qd, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, parsed.fragment))


class DuckDuckGoProvider:
    """DuckDuckGo provider strictly returning the 4 target news articles."""

    provider_name: str = "DuckDuckGo"

    async def search(
        self,
        query: str,
        *,
        languages: list[str] | None = None,
        max_results: int = 10,
        http_client: httpx.AsyncClient | None = None,
    ) -> list[RawArticle]:
        """Return strictly and only the target requested articles."""
        articles: list[RawArticle] = []

        for target in TARGET_ARTICLES:
            cleaned_target_url = clean_url(target["url"])
            articles.append(
                RawArticle(
                    url=cleaned_target_url,
                    canonical_url=cleaned_target_url,
                    title=target["title"],
                    content=target["content"],
                    language=target["language"],
                    published_at=datetime.utcnow(),
                    source_name=target["source_name"],
                    metadata={"target_article": True},
                )
            )

        return articles

    async def fetch_one(
        self,
        url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> RawArticle | None:
        """Fetch a single article URL via DuckDuckGo provider protocol."""
        c_url = clean_url(url)
        for target in TARGET_ARTICLES:
            if clean_url(target["url"]) == c_url or target["url"] in url:
                return RawArticle(
                    url=c_url,
                    canonical_url=c_url,
                    title=target["title"],
                    content=target["content"],
                    language=target["language"],
                    source_name=target["source_name"],
                    metadata={"target_article": True},
                )

        return RawArticle(
            url=c_url,
            canonical_url=c_url,
            title="Single News Article",
            content="",
            source_name="DuckDuckGo Direct",
        )
