import base64

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_homepage_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "FRA" in response.text.upper()
    assert 'id="signature-in"' in response.text
    assert 'id="stamp-in"' in response.text
    assert "reviewDate" in response.text
    assert "if(g.issuer||g.issuerAddr||g.issuerPhone)" in response.text


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


def test_report_email_endpoint_sends_to_fixed_recipient(monkeypatch):
    sent = {}
    report_pdf = b"%PDF-1.7\n" + (b"sample pdf content\n" * 10)

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["connection"] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            sent["tls"] = True

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setenv("FRA_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("FRA_SMTP_PORT", "587")
    monkeypatch.setenv("FRA_SMTP_USERNAME", "sender@example.test")
    monkeypatch.setenv("FRA_SMTP_PASSWORD", "test-password")
    monkeypatch.delenv("FRA_SMTP_FROM", raising=False)
    monkeypatch.setattr("app.main.smtplib.SMTP", FakeSMTP)

    response = client.post(
        "/api/report/email",
        json={"report_pdf_base64": base64.b64encode(report_pdf).decode("ascii")},
    )

    assert response.status_code == 200
    assert response.json()["recipient"] == "Avrumi@jlsafety.co.uk"
    assert sent["message"]["To"] == "Avrumi@jlsafety.co.uk"
    attachment = next(sent["message"].iter_attachments())
    assert attachment.get_filename() == "Fire Risk Assessment.pdf"
    assert attachment.get_content_type() == "application/pdf"
    assert attachment.get_payload(decode=True) == report_pdf
    assert sent["tls"] is True
    assert client.get("/api/report/email/status").json() == {"configured": True}


def test_report_email_endpoint_requires_smtp_configuration(monkeypatch):
    for key in (
        "FRA_SMTP_HOST",
        "FRA_SMTP_FROM",
        "FRA_SMTP_USERNAME",
        "FRA_SMTP_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)

    response = client.post(
        "/api/report/email",
        json={
            "report_pdf_base64": base64.b64encode(b"%PDF-1.7\n" + (b"content\n" * 20)).decode("ascii")
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Report email is not configured yet."
    assert client.get("/api/report/email/status").json() == {"configured": False}
