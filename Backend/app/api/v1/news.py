from fastapi import APIRouter, HTTPException
import uuid
from typing import List, Dict, Any
from app.ingestion.providers.gnews import GNewsProvider
import httpx
from datetime import datetime

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/top")
async def get_top_news() -> List[Dict[str, Any]]:
    """
    Fetches the top news using the GNewsProvider (which falls back to RSS if API key is not present).
    Transforms the data into a format expected by the frontend.
    """
    provider = GNewsProvider(query="latest news")
    
    try:
        raw_docs = await provider.fetch_latest(limit=6)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    articles = []
    for i, doc in enumerate(raw_docs):
        # Format the date if available
        date_str = "TODAY"
        if doc.published_at:
            try:
                date_str = doc.published_at.strftime("%d %b %Y, %I:%M %p").upper()
            except Exception:
                pass
                
        # Assign category randomly or just use a default
        categories = ["WORLD", "POLITICS", "BUSINESS", "TECH", "SCIENCE"]
        category = categories[i % len(categories)]
        
        # We need an id, fallback to uuid if not present
        doc_id = str(uuid.uuid4())
        
        articles.append({
            "id": doc_id,
            "category": category,
            "date": date_str,
            "title": doc.title or "Untitled",
            "excerpt": (doc.content or "")[:200] + ("..." if len(doc.content or "") > 200 else ""),
            "source": doc.source_name or "GNews",
            "link": f"/investigate/{doc_id}",
            "imageUrl": "https://images.openai.com/static-rsc-4/yfR8vPBESFSSsvbi4mJU8PpZgnAh1CdFgAaDsyiK0VYy768KbX4OoQP-w-0xufTt6Q6uhwalI-yd6Nfwyl5EAtSar0qSaDhDJkiiVWCKGyXaK0VJCvLW280Pyowk7T0kAGbhD-vsoJ2yvJp6pEH1956xStkPz5N2zYjMu5ZE__LOaJTBU9aotfXFMMYuknFy?purpose=fullsize" if i == 0 else None,
            "isMain": i == 0
        })
        
    return articles
