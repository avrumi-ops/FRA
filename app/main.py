from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="FRA Builder",
    description="Fire Risk Assessment Builder for regulatory fire safety reports",
    version="0.1.0",
)

ROOT = Path(__file__).resolve().parent.parent


class FireRiskInput(BaseModel):
    account_id: str = Field(..., min_length=3, max_length=50)
    amount: float = Field(..., gt=0)
    country: str = Field(..., min_length=2, max_length=3)
    history: int = Field(..., ge=0, le=12)
    alerts: int = Field(..., ge=0, le=20)


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
