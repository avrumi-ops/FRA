# FRA Builder

A fire risk assessment system built with FastAPI. It provides a compliant-style FRA builder with sections for means of escape, emergency lighting, alarms, fire equipment, signage, training, and reporting.

## Features

- Multi-section fire risk questionnaire
- Live report preview and action planning
- Summary risk scoring and assessment API
- Browser-based fire risk assessment workflow

## Run locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open http://localhost:8000.

## API

- GET /api/summary
- POST /api/assess

## Test

```bash
pytest -q
```
