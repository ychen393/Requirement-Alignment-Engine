import json
from unittest.mock import patch

import pytest

from requirement_alignment.ai.provider import (
    AIConfigurationError,
    AIResponseError,
    AIResponseValidationError,
    OpenAICompatibleProvider,
)
from requirement_alignment.ai.schemas import RequirementAnalysisDraft


class FakeHTTPResponse:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self.body


def provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://provider.example/v1",
        api_key="secret-value",
        model="test-model",
    )


def test_provider_validates_structured_response() -> None:
    content = RequirementAnalysisDraft(
        confirmed_information=[],
        missing_information=[],
        assumptions=[],
        ambiguities=[],
        risks=[],
    ).model_dump_json()
    response = FakeHTTPResponse({"choices": [{"message": {"content": content}}]})
    with patch("requirement_alignment.ai.provider.urlopen", return_value=response) as mocked:
        result = provider().generate_structured("system", "user", RequirementAnalysisDraft)
    assert result.confirmed_information == []
    request = mocked.call_args.args[0]
    sent = json.loads(request.data)
    assert sent["response_format"]["type"] == "json_schema"
    schema = sent["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert "secret-value" not in json.dumps(sent)


def test_provider_rejects_malformed_structured_output() -> None:
    response = FakeHTTPResponse({"choices": [{"message": {"content": "{}"}}]})
    with patch("requirement_alignment.ai.provider.urlopen", return_value=response):
        with pytest.raises(AIResponseValidationError, match="schema validation"):
            provider().generate_structured("system", "user", RequirementAnalysisDraft)


def test_provider_rejects_empty_model_response() -> None:
    response = FakeHTTPResponse({"choices": [{"message": {"content": ""}}]})
    with patch("requirement_alignment.ai.provider.urlopen", return_value=response):
        with pytest.raises(AIResponseError, match="empty"):
            provider().generate_structured("system", "user", RequirementAnalysisDraft)


def test_missing_ai_configuration_is_clear_and_secret_free(monkeypatch) -> None:
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(AIConfigurationError, match="LLM_BASE_URL") as error:
        OpenAICompatibleProvider.from_env()
    assert "API_KEY" not in str(error.value)
