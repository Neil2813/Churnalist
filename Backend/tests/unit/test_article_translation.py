import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.constants import ExtractionStatus, SourceType
from unittest.mock import AsyncMock
from app.core.exceptions import ArticleNotFoundError, TranslationError, UnsupportedLanguageError
from app.db.base import Base
from app.db.models.article import Article, ArticleTranslation
from app.services.translation_service import ArticleTranslationSchema, TranslationService


@pytest_asyncio.fixture
async def db_session():
    """Isolated in-memory SQLite session for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_translate_article_fresh_and_cached(db_session: AsyncSession):
    """Verify first request translates and caches, second request hits cache directly."""
    article = Article(
        id="art_tamil_test_001",
        url="https://example.com/tamil-news-001",
        url_hash="hash_tamil_001",
        title="சென்னையில் புதிய மெட்ரோ ரயில் திட்டம் தொடக்கம்",
        content="சென்னையில் புதிய மெட்ரோ ரயில் பாதை இன்று தொடங்கப்பட்டது. இதில் பல முக்கிய அதிகாரிகள் கலந்து கொண்டனர்.",
        language="ta",
        source_type=SourceType.NEWSROOM,
        extraction_status=ExtractionStatus.FULL,
    )
    db_session.add(article)
    await db_session.commit()

    mock_client = AsyncMock()
    mock_client.api_key = "test_key"
    mock_client.generate_structured.return_value = ArticleTranslationSchema(
        translated_title="New Metro Rail Project Launched in Chennai",
        translated_content="A new metro rail route was inaugurated in Chennai today. Several senior officials attended the event.",
    )

    service = TranslationService(llm_client=mock_client)

    # 1. First call: translate to English (fresh translation)
    res1 = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
    )

    assert res1.article_id == article.id
    assert res1.target_language == "en"
    assert res1.target_language_name == "English"
    assert res1.original_language == "ta"
    assert res1.original_language_name == "Tamil"
    assert res1.original_title == article.title
    assert res1.original_content == article.content
    assert res1.cached is False
    assert res1.translated_content == "A new metro rail route was inaugurated in Chennai today. Several senior officials attended the event."
    # Confirm NO fake bracketed fallback prefix
    assert not res1.translated_title.startswith("[")
    assert not res1.translated_content.startswith("[")
    assert mock_client.generate_structured.await_count == 1

    # 2. Second call: should hit cache without invoking LLM
    res2 = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
    )

    assert res2.cached is True
    assert res2.target_language == "en"
    assert res2.translated_title == res1.translated_title
    assert res2.translated_content == res1.translated_content
    # LLM should not have been called a second time
    assert mock_client.generate_structured.await_count == 1


@pytest.mark.asyncio
async def test_translate_article_to_kannada(db_session: AsyncSession):
    """Verify Kannada round-trip translation produces real Kannada script and no fallback prefix."""
    article = Article(
        id="art_kannada_test_003",
        url="https://example.com/kannada-news-003",
        url_hash="hash_kannada_003",
        title="Breaking: New Public Transport System Launched",
        content="The government announced a major new public transport system in the city today. Over twenty thousand commuters used the service on its first day.",
        language="en",
        source_type=SourceType.NEWSROOM,
        extraction_status=ExtractionStatus.FULL,
    )
    db_session.add(article)
    await db_session.commit()

    mock_client = AsyncMock()
    mock_client.api_key = "test_key"
    mock_client.generate_structured.return_value = ArticleTranslationSchema(
        translated_title="ಬ್ರೇಕಿಂಗ್: ಹೊಸ ಸಾರ್ವಜನಿಕ ಸಾರಿಗೆ ವ್ಯವಸ್ಥೆ ಪ್ರಾರಂಭ",
        translated_content="ಸರ್ಕಾರವು ಇಂದು ನಗರದಲ್ಲಿ ಹೊಸ ಸಾರ್ವಜನಿಕ ಸಾರಿಗೆ ವ್ಯವಸ್ಥೆಯನ್ನು ಘೋಷಿಸಿದೆ. ಮೊದಲ ದಿನವೇ ಇಪ್ಪತ್ತು ಸಾವಿರಕ್ಕೂ ಹೆಚ್ಚು ಪ್ರಯಾಣಿಕರು ಈ ಸೇವೆಯನ್ನು ಬಳಸಿದ್ದಾರೆ.",
    )

    service = TranslationService(llm_client=mock_client)
    res = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="kn",
    )

    assert res.target_language == "kn"
    assert res.target_language_name == "Kannada"
    assert res.cached is False
    assert res.translated_title is not None and len(res.translated_title) > 0
    assert res.translated_content is not None and len(res.translated_content) > 0
    # Must NOT be bracketed fallback
    assert not res.translated_title.startswith("[")
    assert not res.translated_content.startswith("[")
    # Must contain actual Kannada script (Unicode block \u0C80 - \u0CFF)
    kannada_chars = [ch for ch in res.translated_content if '\u0C80' <= ch <= '\u0CFF']
    assert len(kannada_chars) > 10, f"Expected Kannada script characters, got: {res.translated_content}"
    assert mock_client.generate_structured.await_count == 1


@pytest.mark.asyncio
async def test_translation_failure_raises_502(db_session: AsyncSession):
    """Confirm TranslationError with status 502 is raised instead of returning fake fallback."""
    article = Article(
        id="art_fail_test_004",
        url="https://example.com/fail-test-004",
        url_hash="hash_fail_004",
        title="Sample Article",
        content="Sample content that fails translation.",
        language="en",
        source_type=SourceType.NEWSROOM,
        extraction_status=ExtractionStatus.FULL,
    )
    db_session.add(article)
    await db_session.commit()

    mock_failing_client = AsyncMock()
    mock_failing_client.api_key = "fake_key"
    mock_failing_client.generate_structured.side_effect = RuntimeError("Groq upstream connection failed")

    service = TranslationService(llm_client=mock_failing_client)

    with pytest.raises(TranslationError) as exc_info:
        await service.get_or_translate_article(
            db=db_session,
            article_id=article.id,
            target_language="te",
        )

    assert exc_info.value.status_code == 502
    assert "Translation failed" in exc_info.value.message


@pytest.mark.asyncio
async def test_translate_same_language_returns_original(db_session: AsyncSession):
    """When target language matches article language, return original content immediately."""
    article = Article(
        id="art_english_test_002",
        url="https://example.com/english-news-002",
        url_hash="hash_english_002",
        title="Major Infrastructure Project Announced",
        content="Officials announced a new public transit expansion today in the capital.",
        language="en",
        source_type=SourceType.OFFICIAL,
        extraction_status=ExtractionStatus.FULL,
    )
    db_session.add(article)
    await db_session.commit()

    service = TranslationService()
    res = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
    )

    assert res.cached is True
    assert res.target_language == "en"
    assert res.translated_title == article.title
    assert res.translated_content == article.content


@pytest.mark.asyncio
async def test_translate_unsupported_language(db_session: AsyncSession):
    """Reject unsupported language codes with UnsupportedLanguageError."""
    service = TranslationService()
    with pytest.raises(UnsupportedLanguageError):
        await service.get_or_translate_article(
            db=db_session,
            article_id="any-id",
            target_language="klingon",
        )


@pytest.mark.asyncio
async def test_translate_article_not_found(db_session: AsyncSession):
    """Raise ArticleNotFoundError when article_id does not exist."""
    service = TranslationService()
    with pytest.raises(ArticleNotFoundError):
        await service.get_or_translate_article(
            db=db_session,
            article_id="non_existent_article_123",
            target_language="en",
        )


@pytest.mark.asyncio
async def test_translate_article_title_only_and_cache_upgrade(db_session: AsyncSession):
    """Verify title_only translates headline only, caches it, and upgrades when full translation requested."""
    article = Article(
        id="art_bengali_sidebar_001",
        url="https://example.com/bengali-sidebar-001",
        url_hash="hash_bengali_001",
        title="কলকাতায় নতুন বিমানবন্দর টার্মিনাল উদ্বোধন",
        content="কলকাতায় আজ একটি নতুন অত্যাধুনিক বিমানবন্দর টার্মিনাল উদ্বোধন করা হয়েছে। অনুষ্ঠানে বহু বিশিষ্ট ব্যক্তি উপস্থিত ছিলেন।",
        language="bn",
        source_type=SourceType.NEWSROOM,
        extraction_status=ExtractionStatus.FULL,
    )
    db_session.add(article)
    await db_session.commit()

    mock_client = AsyncMock()
    mock_client.api_key = "test_key"
    mock_client.generate_structured.side_effect = [
        # 1st call: title-only
        ArticleTranslationSchema(
            translated_title="New Airport Terminal Inaugurated in Kolkata",
            translated_content="",
        ),
        # 2nd call: full article upgrade
        ArticleTranslationSchema(
            translated_title="New Airport Terminal Inaugurated in Kolkata",
            translated_content="A new modern airport terminal was inaugurated in Kolkata today. Many dignitaries were present at the ceremony.",
        ),
    ]

    service = TranslationService(llm_client=mock_client)

    # 1. Headline-only translation (sidebar card)
    res_title_only = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
        title_only=True,
    )

    assert res_title_only.cached is False
    assert res_title_only.translated_title == "New Airport Terminal Inaugurated in Kolkata"
    assert res_title_only.translated_content == ""
    assert mock_client.generate_structured.await_count == 1

    # Check prompt passed article content (excerpt)
    call_args = mock_client.generate_structured.call_args[1]
    assert article.content[:50] in call_args["user_prompt"]

    # 2. Second title-only call hits cache
    res_title_cache = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
        title_only=True,
    )

    assert res_title_cache.cached is True
    assert res_title_cache.translated_title == "New Airport Terminal Inaugurated in Kolkata"
    assert mock_client.generate_structured.await_count == 1

    # 3. Full article translation request upgrades the cached row
    res_full = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
        title_only=False,
    )

    assert res_full.cached is False
    assert res_full.translated_title == "New Airport Terminal Inaugurated in Kolkata"
    assert "A new modern airport terminal was inaugurated" in res_full.translated_content
    assert mock_client.generate_structured.await_count == 2

    # 4. Subsequent full article call hits cache
    res_full_cached = await service.get_or_translate_article(
        db=db_session,
        article_id=article.id,
        target_language="en",
        title_only=False,
    )

    assert res_full_cached.cached is True
    assert res_full_cached.translated_content == res_full.translated_content
    assert mock_client.generate_structured.await_count == 2
