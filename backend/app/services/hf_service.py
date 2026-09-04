import time
import logging
from typing import Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)
from huggingface_hub import InferenceClient

from app.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceServiceError(Exception):
    """Custom exception raised when Hugging Face API fails after all retries."""
    pass


class HuggingFaceService:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.HUGGINGFACE_API_KEY
        self.model = model or settings.HUGGINGFACE_MODEL

    def _call_api_internal(self, prompt: str, simulate_failure: bool = False) -> str:
        if simulate_failure:
            raise HuggingFaceServiceError("Simulated Hugging Face API failure triggered for testing failover.")

        if not self.api_key or "YOUR_HUGGINGFACE_API_KEY" in self.api_key or self.api_key == "YOUR_HUGGINGFACE_API_KEY_HERE":
            time.sleep(0.2)
            return (
                f"[Hugging Face Demo Mode - {self.model}]\n"
                f"Processed prompt: \"{prompt[:60]}...\"\n"
                f"HuggingFace API key not configured yet. Add HUGGINGFACE_API_KEY in backend/.env for real outputs."
            )

        try:
            client = InferenceClient(
                provider="hf-inference",
                api_key=self.api_key
            )
            messages = [{"role": "user", "content": prompt}]
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500
            )

            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                if content:
                    return content.strip()

            raise HuggingFaceServiceError("Hugging Face API returned an empty response.")
        except Exception as e:
            if isinstance(e, HuggingFaceServiceError):
                raise e
            logger.warning(f"HuggingFace API call exception: {e}")
            raise HuggingFaceServiceError(f"HF API error: {str(e)}") from e

    def generate(self, prompt: str, simulate_failure: bool = False) -> Tuple[str, int]:
        """
        Invokes HuggingFace API with exponential backoff and random jitter.
        Returns: Tuple[generated_text, retries_count]
        """
        attempt_tracker = {"count": 0}

        @retry(
            wait=wait_random_exponential(
                min=settings.RETRY_MIN_WAIT_SECONDS,
                max=settings.RETRY_MAX_WAIT_SECONDS
            ),
            stop=stop_after_attempt(settings.MAX_RETRIES),
            retry=retry_if_exception_type(HuggingFaceServiceError),
            reraise=True
        )
        def _execute_with_retry():
            attempt_tracker["count"] += 1
            return self._call_api_internal(prompt, simulate_failure=simulate_failure)

        try:
            result_text = _execute_with_retry()
            retries = max(0, attempt_tracker["count"] - 1)
            return result_text, retries
        except HuggingFaceServiceError as err:
            retries = max(0, attempt_tracker["count"] - 1)
            raise HuggingFaceServiceError(f"Failed after {attempt_tracker['count']} attempts: {err}") from err
