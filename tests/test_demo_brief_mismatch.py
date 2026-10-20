from fastapi.testclient import TestClient
from requirement_alignment.api.main import create_app
from requirement_alignment.api.schemas import AppMode

def test_marketing_brief_is_not_replaced_with_benchmark_demo():
    client = TestClient(create_app(mode=AppMode.DEMO))
    response = client.post("/requirements/analyze", json={
        "request": "市场部希望建设 AI 营销文案助手，首先支持小红书文案，五人试用，审核耗时降低30%。",
        "title": "Client Brief",
        "submitted_by": "Consultant",
        "source": "Client brief",
    })
    assert response.status_code == 409
    assert "DEMO" in response.json()["detail"]
