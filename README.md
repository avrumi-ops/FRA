# FRA Builder

A fire risk assessment system built with FastAPI. It provides a compliant-style FRA builder with sections for means of escape, emergency lighting, alarms, fire equipment, signage, training, and reporting.

## Features

- Multi-section fire risk questionnaire
- Live report preview and action planning
- Blank assessment for each new visitor, with drafts saved in that visitor's browser
- Browser-based fire risk assessment workflow
- N/A responses for all questions, including free-text questions
- Compressed photo evidence for individual questions and the report summary
- Assessor signature image in the report sign-off section
- Editable review date and assessor stamp below the sign-off table
- Generate, download, and share reports as PDF
- Email PDF reports to Avrumi@jlsafety.co.uk

## Report email setup

The report view can share a PDF through the device's share options (including email apps where supported), download it, or send a PDF attachment to the fixed recipient `Avrumi@jlsafety.co.uk`. The direct email button requires SMTP. Configure credentials as environment variables on the server; do not put credentials in the HTML or commit them to the repository:

- `FRA_SMTP_HOST` - SMTP server hostname
- `FRA_SMTP_PORT` - SMTP port; use `587` for STARTTLS or `465` for implicit TLS
- `FRA_SMTP_USERNAME` and `FRA_SMTP_PASSWORD` - SMTP authentication credentials
- `FRA_SMTP_FROM` - verified sender address (defaults to the username)

In Codespaces, store credentials as Codespaces secrets and expose them to the running app process. Restart the app after setting them. The endpoint limits report size and email frequency.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open http://localhost:8000.

## Test

```bash
pytest -q
```
