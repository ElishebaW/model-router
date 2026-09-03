import time
import logging
from typing import Tuple, Dict, Any

from app.config import settings
from app.schemas import RouteRequest, RouteResponse, RouteMetadata, RouteInspection
from app.services.google_service import GoogleService, GoogleServiceError
from app.services.hf_service import HuggingFaceService, HuggingFaceServiceError

logger = logging.getLogger(__name__)


def inspect_route(prompt: str) -> RouteInspection:
    """
    Evaluates prompt static metrics and determines primary destination.
    Rule:
    - Less than 10 words OR less than 10 characters -> Hugging Face (Qwen/Qwen2.5-7B-Instruct)
    - 10+ words AND 10+ characters -> Google API (google/gemini-2.5-flash)
    """
    cleaned_prompt = prompt.strip()
    words = cleaned_prompt.split()
    word_count = len(words)
    char_count = len(cleaned_prompt)

    if word_count < settings.WORD_COUNT_THRESHOLD or char_count < settings.CHAR_COUNT_THRESHOLD:
        primary = "huggingface"
        model_name = settings.HUGGINGFACE_MODEL
        reasons = []
        if word_count < settings.WORD_COUNT_THRESHOLD:
            reasons.append(f"Word count ({word_count}) < {settings.WORD_COUNT_THRESHOLD}")
        if char_count < settings.CHAR_COUNT_THRESHOLD:
            reasons.append(f"Char count ({char_count}) < {settings.CHAR_COUNT_THRESHOLD}")
        reason = f"Routed to Hugging Face: {', '.join(reasons)}"
    else:
        primary = "google"
        model_name = settings.GOOGLE_MODEL
        reason = (
            f"Routed to Google API: Word count ({word_count}) >= {settings.WORD_COUNT_THRESHOLD} "
            f"and Char count ({char_count}) >= {settings.CHAR_COUNT_THRESHOLD}"
        )

    return RouteInspection(
        prompt=cleaned_prompt,
        word_count=word_count,
        char_count=char_count,
        primary_route=primary,
        model_name=model_name,
        reason=reason,
    )


class ModelRouter:
    def __init__(self):
        self.google_service = GoogleService()
        self.hf_service = HuggingFaceService()

    def process_request(self, request: RouteRequest) -> RouteResponse:
        start_time = time.perf_counter()
        
        # 1. Determine Static Route
        inspection = inspect_route(request.prompt)
        primary_target = request.force_route or inspection.primary_route
        reason = f"Manual override to {primary_target}" if request.force_route else inspection.reason

        fallback_activated = False
        fallback_reason = None
        final_provider = primary_target
        retries_count = 0
        generated_text = ""
        model_used = settings.GOOGLE_MODEL if primary_target == "google" else settings.HUGGINGFACE_MODEL

        # 2. Attempt Primary Provider Execution
        if primary_target == "google":
            try:
                logger.info("Attempting primary execution via Google API...")
                generated_text, retries_count = self.google_service.generate(
                    prompt=request.prompt,
                    simulate_failure=request.simulate_google_failure
                )
            except GoogleServiceError as g_err:
                logger.warning(f"Primary Google API failed: {g_err}. Activating failover to Hugging Face...")
                fallback_activated = True
                fallback_reason = f"Google API error: {str(g_err)}"
                final_provider = "huggingface"
                model_used = settings.HUGGINGFACE_MODEL

                # 3. Failover Execution to Hugging Face
                try:
                    generated_text, hf_retries = self.hf_service.generate(
                        prompt=request.prompt,
                        simulate_failure=request.simulate_hf_failure
                    )
                    retries_count += hf_retries
                except HuggingFaceServiceError as hf_err:
                    # Both providers failed - Graceful Degradation
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(f"Both Google and HuggingFace services failed. {hf_err}")
                    return RouteResponse(
                        status="degraded_error",
                        generated_text=(
                            "⚠️ Model Routing Error: Both primary (Google API) and fallback "
                            "(HuggingFace API) services encountered failures or rate limits."
                        ),
                        metadata=RouteMetadata(
                            primary_target=primary_target,
                            final_provider="none",
                            model_used="none",
                            reason=reason,
                            fallback_activated=True,
                            fallback_reason=f"Google Error: {g_err} | HF Error: {hf_err}",
                            retries_count=retries_count,
                            latency_ms=round(elapsed_ms, 2),
                            words_count=inspection.word_count,
                            chars_count=inspection.char_count,
                        ),
                        error_details=f"Primary: {g_err} | Failover: {hf_err}"
                    )
        else: # Primary target is Hugging Face
            try:
                logger.info("Attempting primary execution via Hugging Face API...")
                generated_text, retries_count = self.hf_service.generate(
                    prompt=request.prompt,
                    simulate_failure=request.simulate_hf_failure
                )
            except HuggingFaceServiceError as hf_err:
                logger.warning(f"Primary Hugging Face API failed: {hf_err}. Activating failover to Google API...")
                fallback_activated = True
                fallback_reason = f"HuggingFace API error: {str(hf_err)}"
                final_provider = "google"
                model_used = settings.GOOGLE_MODEL

                # Failover to Google API
                try:
                    generated_text, g_retries = self.google_service.generate(
                        prompt=request.prompt,
                        simulate_failure=request.simulate_google_failure
                    )
                    retries_count += g_retries
                except GoogleServiceError as g_err:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(f"Both HuggingFace and Google services failed. {g_err}")
                    return RouteResponse(
                        status="degraded_error",
                        generated_text=(
                            "⚠️ Model Routing Error: Both primary (Hugging Face) and fallback "
                            "(Google API) services encountered failures."
                        ),
                        metadata=RouteMetadata(
                            primary_target=primary_target,
                            final_provider="none",
                            model_used="none",
                            reason=reason,
                            fallback_activated=True,
                            fallback_reason=f"HF Error: {hf_err} | Google Error: {g_err}",
                            retries_count=retries_count,
                            latency_ms=round(elapsed_ms, 2),
                            words_count=inspection.word_count,
                            chars_count=inspection.char_count,
                        ),
                        error_details=f"Primary: {hf_err} | Failover: {g_err}"
                    )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        status_flag = "degraded_fallback" if fallback_activated else "success"

        return RouteResponse(
            status=status_flag,
            generated_text=generated_text,
            metadata=RouteMetadata(
                primary_target=primary_target,
                final_provider=final_provider,
                model_used=model_used,
                reason=reason,
                fallback_activated=fallback_activated,
                fallback_reason=fallback_reason,
                retries_count=retries_count,
                latency_ms=round(elapsed_ms, 2),
                words_count=inspection.word_count,
                chars_count=inspection.char_count,
            )
        )
