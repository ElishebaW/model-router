import pytest
from unittest.mock import patch
from app.config import settings
from app.router import inspect_route, ModelRouter
from app.schemas import RouteRequest
from app.services.google_service import GoogleServiceError
from app.services.hf_service import HuggingFaceServiceError


def test_inspect_route_short_words():
    # 4 words, 22 chars -> < 10 words -> HuggingFace
    inspection = inspect_route("Hello world this test")
    assert inspection.primary_route == "huggingface"
    assert inspection.word_count == 4
    assert inspection.model_name == settings.HUGGINGFACE_MODEL
    assert "Word count" in inspection.reason


def test_inspect_route_short_chars():
    # 1 word, 3 chars -> < 10 chars -> HuggingFace
    inspection = inspect_route("Hi!")
    assert inspection.primary_route == "huggingface"
    assert inspection.word_count == 1
    assert inspection.char_count == 3
    assert inspection.model_name == settings.HUGGINGFACE_MODEL


def test_inspect_route_long_prompt():
    # 12 words, 82 chars -> >= 10 words & >= 10 chars -> Google API
    prompt = "This is a detailed prompt that contains more than ten words for testing static routing."
    inspection = inspect_route(prompt)
    assert inspection.primary_route == "google"
    assert inspection.word_count >= 10
    assert inspection.char_count >= 10
    assert inspection.model_name == settings.GOOGLE_MODEL


def test_validation_empty_prompt():
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        RouteRequest(prompt="   ")


def test_validation_oversized_prompt():
    huge_prompt = "a" * 10001
    with pytest.raises(ValueError, match="Prompt exceeds maximum length"):
        RouteRequest(prompt=huge_prompt)


@patch("app.services.google_service.GoogleService.generate")
def test_router_google_primary_success(mock_google_gen):
    mock_google_gen.return_value = ("Google response output", 0)
    router = ModelRouter()
    prompt = "Explain artificial intelligence and its implications on modern enterprise software development."
    req = RouteRequest(prompt=prompt)
    res = router.process_request(req)

    assert res.status == "success"
    assert res.metadata.primary_target == "google"
    assert res.metadata.final_provider == "google"
    assert res.metadata.fallback_activated is False


@patch("app.services.hf_service.HuggingFaceService.generate")
@patch("app.services.google_service.GoogleService.generate")
def test_router_failover_google_to_hf(mock_google_gen, mock_hf_gen):
    mock_google_gen.side_effect = GoogleServiceError("Failed after 3 attempts: Simulated Google API failure")
    mock_hf_gen.return_value = ("HuggingFace failover response output", 0)

    router = ModelRouter()
    prompt = "Explain artificial intelligence and its implications on modern enterprise software development."
    req = RouteRequest(prompt=prompt, simulate_google_failure=True)
    res = router.process_request(req)

    assert res.status == "degraded_fallback"
    assert res.metadata.primary_target == "google"
    assert res.metadata.final_provider == "huggingface"
    assert res.metadata.fallback_activated is True
    assert "Simulated Google API failure" in res.metadata.fallback_reason


@patch("app.services.google_service.GoogleService.generate")
@patch("app.services.hf_service.HuggingFaceService.generate")
def test_router_failover_hf_to_google(mock_hf_gen, mock_google_gen):
    mock_hf_gen.side_effect = HuggingFaceServiceError("Failed after 3 attempts: Simulated Hugging Face API failure")
    mock_google_gen.return_value = ("Google failover response output", 0)

    router = ModelRouter()
    prompt = "Short prompt" # routes to HF by default (< 10 words)
    req = RouteRequest(prompt=prompt, simulate_hf_failure=True)
    res = router.process_request(req)

    assert res.status == "degraded_fallback"
    assert res.metadata.primary_target == "huggingface"
    assert res.metadata.final_provider == "google"
    assert res.metadata.fallback_activated is True


@patch("app.services.hf_service.HuggingFaceService.generate")
@patch("app.services.google_service.GoogleService.generate")
def test_router_degraded_error_when_both_fail(mock_google_gen, mock_hf_gen):
    mock_google_gen.side_effect = GoogleServiceError("Google API simulated error")
    mock_hf_gen.side_effect = HuggingFaceServiceError("HF API simulated error")

    router = ModelRouter()
    prompt = "Explain artificial intelligence and its implications on modern enterprise software development."
    req = RouteRequest(
        prompt=prompt,
        simulate_google_failure=True,
        simulate_hf_failure=True
    )
    res = router.process_request(req)

    assert res.status == "degraded_error"
    assert res.metadata.final_provider == "none"
    assert "⚠️ Model Routing Error" in res.generated_text
    assert res.error_details is not None
