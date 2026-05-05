"""
═══════════════════════════════════════════════════════════════
HuggingFace API Client — Async HTTP wrapper with retry logic
═══════════════════════════════════════════════════════════════
Handles cold-start delays, rate limits, and error recovery.
All HuggingFace model calls go through this single client.
"""

import asyncio
import hashlib
import json
from typing import Any

import httpx
from cachetools import TTLCache
from loguru import logger

from app.config import get_settings


class HFClientError(Exception):
    """Raised when HuggingFace API call fails after all retries."""
    pass


class HFClient:
    """
    Production-grade HuggingFace Inference API client.
    
    Features:
    - Automatic retry on 503 (model loading / cold start)
    - TTL cache for identical requests
    - Async HTTP for non-blocking calls
    - Detailed logging for debugging
    """

    def __init__(self):
        self._settings = get_settings()
        self._cache = TTLCache(maxsize=200, ttl=self._settings.cache_ttl)
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init async HTTP client (reused across requests)."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self._settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    def _cache_key(self, model_id: str, payload: dict) -> str:
        """Generate a deterministic cache key from model + payload."""
        raw = f"{model_id}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def call(
        self,
        model_id: str,
        payload: dict[str, Any],
        use_cache: bool = True,
    ) -> Any:
        """
        Call a HuggingFace model with automatic retry and caching.
        
        Args:
            model_id: HuggingFace model ID (e.g., 'facebook/bart-large-cnn')
            payload: Request payload (model-specific)
            use_cache: Whether to use response caching
            
        Returns:
            Parsed JSON response from the model
            
        Raises:
            HFClientError: If all retries are exhausted
        """
        # Check cache first
        if use_cache:
            cache_key = self._cache_key(model_id, payload)
            if cache_key in self._cache:
                logger.debug(f"Cache HIT for {model_id}")
                return self._cache[cache_key]

        url = f"{self._settings.hf_base_url}/{model_id}"
        client = await self._get_client()
        max_retries = self._settings.max_retries
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[HF] Calling {model_id} (attempt {attempt}/{max_retries})")
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    # Cache successful responses
                    if use_cache:
                        self._cache[cache_key] = result
                    logger.info(f"[HF] ✓ {model_id} responded successfully")
                    return result

                elif response.status_code == 503:
                    # Model is loading (cold start)
                    body = response.json()
                    wait_time = body.get("estimated_time", 20)
                    logger.warning(
                        f"[HF] {model_id} is loading. "
                        f"Waiting {wait_time:.0f}s (attempt {attempt}/{max_retries})"
                    )
                    await asyncio.sleep(min(wait_time, 60))  # Cap at 60s
                    continue

                elif response.status_code == 429:
                    # Rate limited
                    wait_time = 10 * attempt  # Exponential backoff
                    logger.warning(f"[HF] Rate limited. Waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                elif response.status_code == 422:
                    # Invalid input — don't retry, it won't help
                    error_detail = response.text
                    logger.error(f"[HF] Invalid input for {model_id}: {error_detail}")
                    raise HFClientError(f"Invalid input: {error_detail}")

                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"[HF] {model_id} error: {last_error}")

            except httpx.TimeoutException:
                last_error = "Request timed out (120s)"
                logger.warning(f"[HF] {model_id} timeout (attempt {attempt})")
            except httpx.ConnectError:
                last_error = "Connection failed"
                logger.warning(f"[HF] {model_id} connection error (attempt {attempt})")
            except HFClientError:
                raise  # Don't retry validation errors
            except Exception as e:
                last_error = str(e)
                logger.error(f"[HF] {model_id} unexpected error: {e}")

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)

        raise HFClientError(
            f"Failed to call {model_id} after {max_retries} attempts. Last error: {last_error}"
        )

    async def call_text_generation(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 2000,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        """
        Call text generation using the OpenAI-compatible chat completions API.
        This is the new HuggingFace Inference Providers endpoint.
        Returns the generated text string.
        """
        # Use the chat completions endpoint instead of the old /models/ endpoint
        chat_url = self._settings.hf_chat_url
        client = await self._get_client()
        max_retries = self._settings.max_retries
        last_error = None

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_new_tokens,
            "temperature": temperature,
        }

        # Cache check
        if use_cache:
            cache_key = self._cache_key(model_id, payload)
            if cache_key in self._cache:
                logger.debug(f"Cache HIT for chat {model_id}")
                return self._cache[cache_key]

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[HF Chat] Calling {model_id} (attempt {attempt}/{max_retries})")
                response = await client.post(chat_url, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    text = result["choices"][0]["message"]["content"]
                    # Cache successful response
                    if use_cache:
                        self._cache[cache_key] = text
                    logger.info(f"[HF Chat] ✓ {model_id} responded successfully")
                    return text

                elif response.status_code == 503:
                    body = response.json()
                    wait_time = body.get("estimated_time", 20)
                    logger.warning(
                        f"[HF Chat] {model_id} is loading. "
                        f"Waiting {wait_time:.0f}s (attempt {attempt}/{max_retries})"
                    )
                    await asyncio.sleep(min(wait_time, 60))
                    continue

                elif response.status_code == 429:
                    wait_time = 10 * attempt
                    logger.warning(f"[HF Chat] Rate limited. Waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                elif response.status_code == 422:
                    error_detail = response.text
                    logger.error(f"[HF Chat] Invalid input for {model_id}: {error_detail}")
                    raise HFClientError(f"Invalid input: {error_detail}")

                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"[HF Chat] {model_id} error: {last_error}")

            except httpx.TimeoutException:
                last_error = "Request timed out (120s)"
                logger.warning(f"[HF Chat] {model_id} timeout (attempt {attempt})")
            except httpx.ConnectError:
                last_error = "Connection failed"
                logger.warning(f"[HF Chat] {model_id} connection error (attempt {attempt})")
            except HFClientError:
                raise
            except Exception as e:
                last_error = str(e)
                logger.error(f"[HF Chat] {model_id} unexpected error: {e}")

            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)

        raise HFClientError(
            f"Failed to call {model_id} after {max_retries} attempts. Last error: {last_error}"
        )

    async def close(self):
        """Close the HTTP client connection pool."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            logger.info("[HF] HTTP client closed")


# ── Singleton instance ──
hf_client = HFClient()

