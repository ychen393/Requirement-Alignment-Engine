"""Minimal structured-output provider and one OpenAI-compatible implementation."""

import json
import os
import socket
from typing import Protocol, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError

ResponseT = TypeVar("ResponseT", bound=BaseModel)


def _strict_json_schema(value):
    """Normalize Pydantic JSON Schema for strict structured-output providers."""
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {
        key: _strict_json_schema(item)
        for key, item in value.items()
        if key != "default"
    }
    if "properties" in result:
        result["additionalProperties"] = False
        result["required"] = list(result["properties"])
    return result


class AIProviderError(RuntimeError):
    """Safe base error for provider failures."""


class AIConfigurationError(AIProviderError):
    pass


class AITimeoutError(AIProviderError):
    pass


class AIResponseError(AIProviderError):
    pass


class AIResponseValidationError(AIResponseError):
    pass


class LLMProvider(Protocol):
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT: ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30,
    ) -> None:
        if not base_url.strip():
            raise AIConfigurationError("LLM_BASE_URL is required in AI mode")
        if not api_key.strip():
            raise AIConfigurationError("LLM_API_KEY is required in AI mode")
        if not model.strip():
            raise AIConfigurationError("LLM_MODEL is required in AI mode")
        if timeout_seconds <= 0:
            raise AIConfigurationError("LLM_TIMEOUT_SECONDS must be positive")
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        raw_timeout = os.getenv("LLM_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(raw_timeout)
        except ValueError as exc:
            raise AIConfigurationError("LLM_TIMEOUT_SECONDS must be numeric") from exc
        return cls(
            base_url=os.getenv("LLM_BASE_URL", ""),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", ""),
            timeout_seconds=timeout,
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": _strict_json_schema(response_model.model_json_schema()),
                },
            },
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except (TimeoutError, socket.timeout) as exc:
            raise AITimeoutError("The language model request timed out") from exc
        except HTTPError as exc:
            raise AIProviderError(f"The language model provider returned HTTP {exc.code}") from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise AITimeoutError("The language model request timed out") from exc
            raise AIProviderError("The language model provider could not be reached") from exc

        try:
            envelope = json.loads(body)
            content = envelope["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise AIResponseError("The provider returned an invalid response envelope") from exc
        if not isinstance(content, str) or not content.strip():
            raise AIResponseError("The provider returned an empty structured response")
        try:
            return response_model.model_validate_json(content)
        except ValidationError as exc:
            raise AIResponseValidationError("The provider response failed schema validation") from exc
