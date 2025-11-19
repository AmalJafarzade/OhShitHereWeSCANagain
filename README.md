# Local Recon Orchestrator

FastAPI-powered UI for running your favorite reconnaissance tools locally and seeing
live output from one place. Swagger UI is available at `/docs`.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> for the UI or <http://localhost:8000/docs> for Swagger.

## Notes

- The API simply launches the binaries configured in `app/main.py`. Ensure each tool
  is installed and available in `PATH`.
- Output is streamed via server-sent events; the UI uses `EventSource` to render lines
  as they arrive.
