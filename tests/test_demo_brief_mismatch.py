import pytest
from fastapi import HTTPException
from requirement_alignment.api.main import create_app
from requirement_alignment.api.schemas import AppMode, AnalyzeRequest


def test_marketing_brief_is_not_replaced_by_benchmark_fixture():
    app = create_app(mode=AppMode.DEMO)
    route = next(route for route in app.routes if getattr(route, "path", "") == "/requirements/analyze")
    payload = AnalyzeRequest(
        request="市场部要建立 AI 营销文案助手，先支持小红书，五名同事试用，平均审核耗时降低30%。",
        title="Client Brief",
        submitted_by="Consultant",
        source="Client brief",
    )
    with pytest.raises(HTTPException) as exc:
        route.endpoint(payload)
    assert exc.value.status_code == 409
