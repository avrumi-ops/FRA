from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_homepage_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "FRA" in response.text.upper()


def test_summary_endpoint():
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "risk_score" in data
    assert "status" in data


def test_assessment_endpoint():
    payload = {
        "account_id": "ACC-1001",
        "amount": 1200,
        "country": "US",
        "history": 4,
        "alerts": 1,
    }

    response = client.post("/api/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data
    assert "score" in data
    assert "recommendation" in data
