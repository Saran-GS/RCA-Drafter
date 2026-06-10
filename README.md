# RCA Agent — Multi-Agent Root Cause Analysis

## Setup

```bash
ollama pull phi3:mini
pip install -r requirements.txt
python app.py

# Then open http://localhost:5000
```

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Web UI |
| POST | `/analyze` | `{timeline, logs, diff}` ? `{rca_markdown, status}` |
| POST | `/export` | `{rca_markdown}` ? `rca_report.md` download |
| GET | `/health` | `{"ollama": "ok/unreachable", "model": "phi3:mini"}` |

## Notes
- Ollama must be running on http://localhost:11434 before starting Flask.
- Any textarea can be left empty — pipeline handles missing inputs gracefully.
- Keyboard shortcut: Ctrl+Enter / Cmd+Enter triggers analysis.
