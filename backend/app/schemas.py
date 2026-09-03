from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class RouteRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="The user input text prompt to be routed and processed.",
        examples=["Explain quantum computing in simple terms."]
    )
    force_route: Optional[Literal["google", "huggingface"]] = Field(
        default=None,
        description="Optional manual override for routing."
    )
    simulate_google_failure: bool = Field(
        default=False,
        description="Simulates Google API error to test automatic Hugging Face failover."
    )
    simulate_hf_failure: bool = Field(
        default=False,
        description="Simulates Hugging Face API error to test failover behavior."
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Prompt cannot be empty or consist only of whitespace.")
        if len(cleaned) > 10000:
            raise ValueError("Prompt exceeds maximum length limit of 10,000 characters.")
        return cleaned


class RouteInspection(BaseModel):
    prompt: str
    word_count: int
    char_count: int
    primary_route: Literal["google", "huggingface"]
    model_name: str
    reason: str


class RouteMetadata(BaseModel):
    primary_target: str
    final_provider: str
    model_used: str
    reason: str
    fallback_activated: bool = False
    fallback_reason: Optional[str] = None
    retries_count: int = 0
    latency_ms: float
    words_count: int
    chars_count: int


class RouteResponse(BaseModel):
    status: Literal["success", "degraded_fallback", "degraded_error"]
    generated_text: str
    metadata: RouteMetadata
    error_details: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    environment: str
    google_key_configured: bool
    hf_key_configured: bool
    google_model: str
    hf_model: str
