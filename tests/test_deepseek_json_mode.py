import json
from unittest.mock import patch
from pydantic import BaseModel
from requirement_alignment.ai.provider import OpenAICompatibleProvider

class DemoAnswer(BaseModel):
    name: str

class FakeResponse:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps({"choices":[{"message":{"content":'{"name":"marketing"}'}}]}).encode()

def test_deepseek_json_object_request():
    observed = []
    def stub(request, timeout):
        observed.append(json.loads(request.data))
        return FakeResponse()
    provider = OpenAICompatibleProvider(base_url="https://api.deepseek.com", api_key="fake-test-key", model="deepseek-flash")
    with patch("requirement_alignment.ai.provider.urlopen", stub):
        result = provider.generate_structured("Analyze the brief", "Marketing assistant", DemoAnswer)
    assert result.name == "marketing"
    assert observed[0]["response_format"] == {"type": "json_object"}
    assert "JSON" in observed[0]["messages"][0]["content"]
