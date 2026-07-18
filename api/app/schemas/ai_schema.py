from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PromptTemplateOut(BaseModel):
    key: str
    name: str
    purpose: str
    required_variables: list[str]
    optional_variables: list[str]
    default_temperature: float
    default_max_tokens: int | None = None
    expects_json: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIPromptRequest(BaseModel):
    prompt_key: str = "generic_assistant"
    variables: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=16000)
    reasoning: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class AIChatRequest(BaseModel):
    purpose: str = Field(default="custom_chat", max_length=80)
    messages: list[AIMessage]
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=16000)
    reasoning: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AICompletionResponse(BaseModel):
    ai_request_id: UUID
    provider: str
    model: str
    purpose: str
    text: str
    tokens_input: int | None = None
    tokens_output: int | None = None
