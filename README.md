# Local Recon Orchestrator

FastAPI-powered UI for running your favorite reconnaissance tools locally and seeing
live output from one place. A dedicated Swagger UI is available at `/swagger`.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> for the UI or <http://localhost:8000/swagger> for Swagger.

## Notes

- The API launches the binaries configured in `app/main.py` with sensible defaults per
  tool (e.g., `nmap -sV -T4 <target>`, `dirsearch -u <target>`). Each tool advertises
  whether a target is required, the default arguments applied, and a hint for the
  target format in the UI.
- `/tools` returns availability, default arguments, and target requirements; the UI
  renders those as chips, disables running missing binaries, and blocks execution when
  a required target is empty.
- If a binary is missing, `/run/{tool}` returns `400` with a helpful message and the UI
  disables the Run button for that tool.
- Output is streamed via server-sent events; the UI uses `EventSource` to render lines
  as they arrive.
