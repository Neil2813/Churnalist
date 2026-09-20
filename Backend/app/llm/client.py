"""
Groq LLM client wrapper.

Single entry point for all LLM calls in DRIFT. Provides:
- Structured JSON output via Pydantic schema validation
- Centralized retry with exponential backoff
- Concurrency semaphore
- Prompt versioning
- Token usage logging
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMQuotaExceededError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 4
RETRY_DELAYS = [1.0, 2.0, 4.0, 8.0]


class GroqClient:
    """
    Application-level wrapper around the Groq SDK.

    All agents must use this class — never import the Groq SDK directly.
    This centralises retry logic, token tracking, and test mocking.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str | None = None,
        fast_model: str | None = None,
        timeout: float = 60.0,
        max_concurrent: int = 4,
    ) -> None:
        from app.core.config import get_settings
        s = get_settings()
        self.api_key = api_key or s.groq_api_key
        self.default_model = default_model or s.groq_model
        self.fast_model = fast_model or s.groq_fast_model
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client = None

    async def generate_json(
        self,
        *,
        prompt: str,
        system_prompt: str = "Return strict JSON.",
        temperature: float = 0.0,
        model: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Call Groq and parse raw JSON output."""
        use_model = model or self.default_model
        raw = await self._call(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model=use_model,
            temperature=temperature,
            timeout=self.timeout,
        )
        clean_raw = raw.strip()
        first_brace = clean_raw.find("{")
        last_brace = clean_raw.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            clean_raw = clean_raw[first_brace:last_brace + 1]
        return json.loads(clean_raw)

    def _get_client(self):
        if self._client is None:
            from groq import AsyncGroq  # type: ignore
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
        timeout: float | None = None,
        prompt_version: str = "v1",
    ) -> T:
        """
        Call Groq and parse the response into a validated Pydantic model.

        Four-level validation:
          1. Transport: HTTP success
          2. JSON: valid JSON in response
          3. Schema: Pydantic model validation
          4. Evidence: caller is responsible for domain validation
        """
        use_model = model or self.default_model
        use_timeout = timeout or self.timeout

        for attempt in range(MAX_RETRIES):
            try:
                async with self._semaphore:
                    raw = await self._call(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        model=use_model,
                        temperature=temperature,
                        timeout=use_timeout,
                    )

                # Level 2: JSON validation
                clean_raw = raw.strip()
                first_brace = clean_raw.find("{")
                last_brace = clean_raw.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_candidate = clean_raw[first_brace:last_brace + 1]
                else:
                    json_candidate = clean_raw

                try:
                    parsed_dict = json.loads(json_candidate)
                except json.JSONDecodeError:
                    try:
                        parsed_dict = json.loads(clean_raw)
                    except json.JSONDecodeError as e:
                        raise LLMInvalidResponseError(
                            f"LLM returned non-JSON content: {e}",
                            details={"raw_response": raw[:500]},
                        )

                # Level 3: Schema validation
                try:
                    result = response_schema.model_validate(parsed_dict)
                except Exception as e:
                    raise LLMSchemaValidationError(
                        f"LLM response failed schema validation: {e}",
                        details={"schema": response_schema.__name__, "parsed": parsed_dict},
                    )

                logger.info(
                    "llm_call_success",
                    model=use_model,
                    prompt_version=prompt_version,
                    schema=response_schema.__name__,
                    attempt=attempt + 1,
                )
                return result

            except (LLMInvalidResponseError, LLMSchemaValidationError):
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning("llm_retry", attempt=attempt + 1, delay=delay)
                    await asyncio.sleep(delay)
                    continue
                raise

            except Exception as e:
                err_str = str(e).lower()
                if "rate" in err_str or "429" in err_str:
                    if attempt < MAX_RETRIES - 1:
                        import re
                        match = re.search(r"try again in (\d+(?:\.\d+)?)s", str(e), re.IGNORECASE)
                        wait_sec = float(match.group(1)) + 0.5 if match else (2.0 * (attempt + 1))
                        logger.warning("llm_rate_limit_retry", attempt=attempt + 1, wait_sec=wait_sec, error=str(e))
                        await asyncio.sleep(wait_sec)
                        continue
                    raise LLMQuotaExceededError(f"Groq rate limit exceeded: {e}")
                if "timeout" in err_str or "timed out" in err_str:
                    raise LLMTimeoutError(f"Groq call timed out: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    await asyncio.sleep(delay)
                    continue
                raise LLMInvalidResponseError(f"Groq call failed after {MAX_RETRIES} retries: {e}")

        raise LLMInvalidResponseError("Exhausted all retries")  # should not reach here

    async def _call(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        timeout: float,
    ) -> str:
        """Raw Groq API call — returns the assistant message content string."""
        client = self._get_client()
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            ),
            timeout=timeout,
        )
        content = response.choices[0].message.content or ""
        logger.debug(
            "llm_raw_response",
            model=model,
            tokens_in=response.usage.prompt_tokens if response.usage else None,
            tokens_out=response.usage.completion_tokens if response.usage else None,
        )
        return content
