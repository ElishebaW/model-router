import time
import logging
import httpx
from typing import Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

from app.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceServiceError(Exception):
    """Custom exception raised when Hugging Face API fails after all retries."""
    pass


class HuggingFaceService:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.HUGGINGFACE_API_KEY
        self.model = model or settings.HUGGINGFACE_MODEL
        # Hugging Face modern Serverless Router endpoints
        self.chat_url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
        self.direct_url = f"https://router.huggingface.co/models/{self.model}"

    def _call_api_internal(self, prompt: str, simulate_failure: bool = False) -> str:
        if simulate_failure:
            raise HuggingFaceServiceError("Simulated Hugging Face API failure triggered for testing failover.")

        if not self.api_key or "YOUR_HUGGINGFACE_API_KEY" in self.api_key or self.api_key == "YOUR_HUGGINGFACE_API_KEY_HERE":
            # Synthetic output for local demo mode if key not configured yet
            time.sleep(0.2)
            return (
                f"[Hugging Face Demo Mode - {self.model}]\n"
                f"Processed prompt: \"{prompt[:60]}...\"\n"
                f"HuggingFace API key not configured yet. Add HUGGINGFACE_API_KEY in backend/.env for real Qwen2.5 outputs."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Primary: Chat Completions API format on router.huggingface.co
        chat_payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.7
        }

        try:
            with httpx.Client(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(self.chat_url, headers=headers, json=chat_payload)
                
                # If 404 or unsupported format, attempt direct router model endpoint
                if response.status_code == 404:
                    direct_payload = {
                        "inputs": prompt,
                        "parameters": {"max_new_tokens": 512, "temperature": 0.7, "return_full_text": False}
                    }
                    response = client.post(self.direct_url, headers=headers, json=direct_payload)

                # Check for model loading 503 status
                if response.status_code == 503:
                    error_data = response.json() if response.content else {}
                    estimated_time = error_data.get("estimated_time", 10.0)
                    logger.info(f"HF model is loading. Estimated time: {estimated_time}s")
                    raise HuggingFaceServiceError(f"HuggingFace model loading (503). Retrying...")

                if response.status_code != 200:
                    raise HuggingFaceServiceError(
                        f"HF API returned status {response.status_code}: {response.text}"
                    )

                data = response.json()
                
                # Parse OpenAI / Chat Completion format
                if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if content:
                            return content.strip()

                # Parse standard HuggingFace list response format
                if isinstance(data, list) and len(data) > 0:
                    first_elem = data[0]
                    if "generated_text" in first_elem:
                        return first_elem["generated_text"].strip()
                    elif "summary_text" in first_elem:
                        return first_elem["summary_text"].strip()
                elif isinstance(data, dict):
                    if "generated_text" in data:
                        return data["generated_text"].strip()

                return str(data)
        except Exception as e:
            if isinstance(e, HuggingFaceServiceError):
                raise e
            logger.warning(f"HuggingFace API call exception: {e}")
            raise HuggingFaceServiceError(f"HuggingFace API error: {str(e)}") from e

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
