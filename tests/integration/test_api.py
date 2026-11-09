
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_application_health_endpoint():

    response = client.get("/api/v1/health/")

    assert response.status_code == 200


def test_openapi_documentation_endpoint():

    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert "paths" in data


def test_expected_api_routes_are_registered():

    response = client.get("/openapi.json")

    paths = response.json()["paths"]

    expected_routes = [
        "/api/v1/health/",
        "/api/v1/chat/",
        "/api/v1/documents/upload",
        "/api/v1/documents/search",
        "/api/v1/documents/stats",
        "/api/v1/analysis/csv",
        "/api/v1/reports/generate",
        "/api/v1/reports/",
        "/api/v1/reports/download/{report_id}",
        "/api/v1/audit/",
        "/api/v1/audit/stats",
    ]

    for route in expected_routes:
        assert route in paths, f"Missing API route: {route}"


def test_report_generation_rejects_empty_title():

    response = client.post(
        "/api/v1/reports/generate",
        json={
            "title": "",
            "report_type": "analysis",
            "content": {},
        },
    )

    assert response.status_code == 422


def test_report_download_rejects_unknown_id():

    response = client.get(
        "/api/v1/reports/download/99999999"
    )

    assert response.status_code == 404
