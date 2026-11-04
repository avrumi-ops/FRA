import base64
import binascii
import os
import re
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="FRA Builder",
    description="Fire Risk Assessment Builder for regulatory fire safety reports",
    version="0.1.0",
)

ROOT = Path(__file__).resolve().parent.parent
REPORT_RECIPIENT = "Avrumi@jlsafety.co.uk"
EMAIL_WINDOW_SECONDS = 60 * 60
EMAIL_LIMIT_PER_IP = 3
EMAIL_LIMIT_GLOBAL = 20
_email_lock = threading.Lock()
_email_send_times: dict[str, list[float]] = {}


class FireRiskInput(BaseModel):
    account_id: str = Field(..., min_length=3, max_length=50)
    amount: float = Field(..., gt=0)
    country: str = Field(..., min_length=2, max_length=3)
    history: int = Field(..., ge=0, le=12)
    alerts: int = Field(..., ge=0, le=20)


class ReportEmailInput(BaseModel):
    report_pdf_base64: str = Field(..., min_length=100, max_length=11_000_000)
    report_name: str = Field(default="Fire Risk Assessment.pdf", max_length=120)


def _check_email_rate_limit(client_host: str) -> None:
    now = time.monotonic()
    cutoff = now - EMAIL_WINDOW_SECONDS
    with _email_lock:
        active = {
            host: [sent_at for sent_at in times if sent_at > cutoff]
            for host, times in _email_send_times.items()
        }
        active = {host: times for host, times in active.items() if times}
        all_sends = [sent_at for times in active.values() for sent_at in times]
        ip_sends = active.get(client_host, [])
        if len(ip_sends) >= EMAIL_LIMIT_PER_IP or len(all_sends) >= EMAIL_LIMIT_GLOBAL:
            _email_send_times.clear()
            _email_send_times.update(active)
            raise HTTPException(status_code=429, detail="Please wait before sending another report.")
        active.setdefault(client_host, []).append(now)
        _email_send_times.clear()
        _email_send_times.update(active)


def _email_is_configured() -> bool:
    host = os.getenv("FRA_SMTP_HOST")
    username = os.getenv("FRA_SMTP_USERNAME")
    password = os.getenv("FRA_SMTP_PASSWORD")
    sender = os.getenv("FRA_SMTP_FROM") or username
    try:
        port = int(os.getenv("FRA_SMTP_PORT", "587"))
    except ValueError:
        return False
    return bool(host and sender and bool(username) == bool(password) and 1 <= port <= 65535)


def _send_report_email(report_pdf: bytes, report_name: str) -> None:
    host = os.getenv("FRA_SMTP_HOST")
    username = os.getenv("FRA_SMTP_USERNAME")
    password = os.getenv("FRA_SMTP_PASSWORD")
    sender = os.getenv("FRA_SMTP_FROM") or username
    if not _email_is_configured():
        raise HTTPException(status_code=503, detail="Report email is not configured yet.")

    port = int(os.getenv("FRA_SMTP_PORT", "587"))
    filename = re.sub(r"[^A-Za-z0-9._ -]", "", Path(report_name).name).strip()[:100]
    if not filename.lower().endswith(".pdf"):
        filename = "Fire Risk Assessment.pdf"
    message = EmailMessage()
    message["Subject"] = "FRA Builder report submitted"
    message["From"] = sender
    message["To"] = REPORT_RECIPIENT
    message.set_content("A fire risk assessment report was submitted using FRA Builder. The report is attached as a PDF.")
    message.add_attachment(
        report_pdf,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                if username:
                    server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=context)
                if username:
                    server.login(username, password)
                server.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise HTTPException(status_code=502, detail="The report could not be emailed. Please try again later.") from None


@app.get("/")
def landing_page():
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/api/summary")
def summary():
    return JSONResponse(
        {
            "total_cases": 128,
            "risk_score": 64,
            "status": "watchlist",
            "high_risk_cases": 18,
            "critical_cases": 6,
        }
    )


@app.post("/api/report/email")
def email_report(payload: ReportEmailInput, request: Request):
    try:
        report_pdf = base64.b64decode(payload.report_pdf_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="The report PDF is invalid.") from None
    if len(report_pdf) > 8_000_000 or not report_pdf.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="The report PDF is invalid or too large.")
    _check_email_rate_limit(request.client.host if request.client else "unknown")
    _send_report_email(report_pdf, payload.report_name)
    return {"status": "sent", "recipient": REPORT_RECIPIENT}


@app.get("/api/report/email/status")
def report_email_status():
    return {"configured": _email_is_configured()}


@app.post("/api/assess")
def assess_case(payload: FireRiskInput):
    score = int(
        min(
            100,
            15
            + (payload.amount / 40)
            + (payload.alerts * 12)
            + (payload.history * 4)
            + (18 if payload.country.upper() in {"CN", "RU", "IR", "KP", "BY", "UA"} else 8 if payload.country.upper() == "US" else 12),
        )
    )

    if score < 35:
        risk_level = "Low"
        recommendation = "Proceed with standard review."
    elif score < 55:
        risk_level = "Moderate"
        recommendation = "Escalate for manual review of recent activity."
    elif score < 75:
        risk_level = "High"
        recommendation = "Freeze the transaction pending verification."
    else:
        risk_level = "Critical"
        recommendation = "Immediately block and notify compliance."

    return {
        "account_id": payload.account_id,
        "country": payload.country.upper(),
        "score": score,
        "risk_level": risk_level,
        "recommendation": recommendation,
    }
