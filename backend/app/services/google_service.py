import time
import logging
import httpx
from typing import Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleServiceError(Exception):
    """Custom exception raised when Google API fails after all retries."""
    pass


class GoogleService:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        # Normalize model string if prefixed with provider (e.g. google/gemini-2.5-flash -> gemini-2.5-flash)
        model_name = model or settings.GOOGLE_MODEL
        self.model = model_name.replace("google/", "")

    def _call_api_internal(self, prompt: str, simulate_failure: bool = False) -> str:
        if simulate_failure:
            raise GoogleServiceError("Simulated Google API failure triggered for testing failover.")

        if not self.api_key or self.api_key == "YOUR_GOOGLE_API_KEY":
            # Provide an informative synthetic response if key is missing during local demo mode
            time.sleep(0.3)
            return (
                f"[Google API Demo Mode - {self.model}]\n"
                f"Processed prompt: \"{prompt[:60]}...\"\n"
                f"Google API key not set in environment. Set GOOGLE_API_KEY in backend/.env to get real Gemini outputs."
            )

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )
            if response.text:
                return response.text.strip()
            raise GoogleServiceError("Google API returned an empty response.")
        except Exception as e:
            if isinstance(e, GoogleServiceError):
                raise e
            logger.warning(f"Google API call exception: {e}")
            raise GoogleServiceError(f"Google API error: {str(e)}") from e

    def generate(self, prompt: str, simulate_failure: bool = False) -> Tuple[str, int]:
        """
        Invokes Google API with exponential backoff and random jitter.
        Returns: Tuple[generated_text, retries_count]
        """
        attempt_tracker = {"count": 0}

        @retry(
            wait=wait_random_exponential(
                min=settings.RETRY_MIN_WAIT_SECONDS,
                max=settings.RETRY_MAX_WAIT_SECONDS
            ),
            stop=stop_after_attempt(settings.MAX_RETRIES),
            retry=retry_if_exception_type(GoogleServiceError),
            reraise=True
        )
        def _execute_with_retry():
            attempt_tracker["count"] += 1
            return self._call_api_internal(prompt, simulate_failure=simulate_failure)

        try:
            result_text = _execute_with_retry()
            # Retries count is total attempts minus 1
            retries = max(0, attempt_tracker["count"] - 1)
            return result_text, retries
        except GoogleServiceError as err:
            retries = max(0, attempt_tracker["count"] - 1)
            raise GoogleServiceError(f"Failed after {attempt_tracker['count']} attempts: {err}") from err
