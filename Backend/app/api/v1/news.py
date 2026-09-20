from fastapi import APIRouter, HTTPException, Query
import uuid
from typing import List, Dict, Any
from pydantic import RootModel

from app.ingestion.providers.gnews import GNewsProvider
from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.client import GroqClient

logger = get_logger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


class NewsCategoriesResponse(RootModel[Dict[str, str]]):
    """Pydantic schema mapping article indices to Groq AI categories."""
    pass


@router.get("/top")
async def get_top_news(
    category: str | None = Query(default=None, description="Category filter, e.g. SPORTS, TECH, BUSINESS, POLITICS, SCIENCE, ENVIRONMENT, INDIA, WORLD, ALL")
) -> List[Dict[str, Any]]:
    """
    Fetches latest top news via GNewsProvider matching optional category filter (e.g. SPORTS, BUSINESS, TECH),
    then uses Groq LLM to intelligently categorize and tag each article.
    """
    cat_clean = (category or "ALL").strip().upper()
    
    # Map category to specific live news query
    if cat_clean == "SPORTS":
        query = "sports news"
    elif cat_clean == "TECH":
        query = "technology news"
    elif cat_clean == "BUSINESS":
        query = "business finance news"
    elif cat_clean == "POLITICS":
        query = "politics government news"
    elif cat_clean == "SCIENCE":
        query = "science news"
    elif cat_clean == "ENVIRONMENT":
        query = "environment climate news"
    elif cat_clean == "INDIA":
        query = "india news"
    elif cat_clean == "WORLD":
        query = "world news"
    else:
        query = "latest news"

    provider = GNewsProvider(query=query)
    
    try:
        raw_docs = await provider.fetch_latest(limit=10)
    except Exception as e:
        logger.error("top_news_fetch_failed", category=cat_clean, query=query, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        
    articles_data: List[Dict[str, Any]] = []
    groq_prompt_lines: List[str] = []

    default_category = cat_clean if cat_clean != "ALL" else "WORLD"

    for i, doc in enumerate(raw_docs):
        date_str = "TODAY"
        if doc.published_at:
            try:
                date_str = doc.published_at.strftime("%d %b %Y, %I:%M %p").upper()
            except Exception:
                pass
                
        doc_id = str(uuid.uuid4())
        title = doc.title or "Untitled"
        excerpt = (doc.content or "")[:200] + ("..." if len(doc.content or "") > 200 else "")
        
        articles_data.append({
            "id": doc_id,
            "category": default_category,
            "date": date_str,
            "title": title,
            "excerpt": excerpt,
            "source": doc.source_name or "GNews",
            "link": doc.url or f"/investigate/{doc_id}",
            "imageUrl": "https://images.openai.com/static-rsc-4/yfR8vPBESFSSsvbi4mJU8PpZgnAh1CdFgAaDsyiK0VYy768KbX4OoQP-w-0xufTt6Q6uhwalI-yd6Nfwyl5EAtSar0qSaDhDJkiiVWCKGyXaK0VJCvLW280Pyowk7T0kAGbhD-vsoJ2yvJp6pEH1956xStkPz5N2zYjMu5ZE__LOaJTBU9aotfXFMMYuknFy?purpose=fullsize" if i == 0 else None,
            "isMain": i == 0
        })
        groq_prompt_lines.append(f"{i}. Title: {title} | Excerpt: {excerpt}")

    # Use Groq LLM for news categorization if query was generic or ALL
    settings = get_settings()
    if settings.groq_api_key and groq_prompt_lines:
        try:
            client = GroqClient(
                api_key=settings.groq_api_key,
                default_model=settings.groq_model,
                fast_model=settings.groq_fast_model,
                timeout=10.0,
            )
            sys_prompt = (
                "You are an expert news classifier. Respond in JSON format. "
                "Return a JSON object mapping each article index string to its exact category. "
                "Valid categories: WORLD, TECH, BUSINESS, POLITICS, SPORTS, SCIENCE, ENVIRONMENT, INDIA."
            )
            user_prompt = f"Target preferred topic: {cat_clean}\nClassify these news articles:\n" + "\n".join(groq_prompt_lines)
            
            categories_res = await client.generate_structured(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                response_schema=NewsCategoriesResponse,
                model=settings.groq_fast_model,
                prompt_version="news_category_v1",
            )
            
            groq_cats = categories_res.root or {}
            valid_cats = {"WORLD", "TECH", "BUSINESS", "POLITICS", "SPORTS", "SCIENCE", "ENVIRONMENT", "INDIA"}
            
            for idx_str, cat in groq_cats.items():
                try:
                    idx = int(idx_str)
                    clean_cat = str(cat).strip().upper()
                    if 0 <= idx < len(articles_data) and clean_cat in valid_cats:
                        articles_data[idx]["category"] = clean_cat
                except Exception:
                    pass
            logger.info("groq_news_categorization_success", category=cat_clean, count=len(groq_cats))
        except Exception as exc:
            logger.warning("groq_news_categorization_failed", error=str(exc))

    return articles_data
