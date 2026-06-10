import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"

LOG_SCHEMA = {
    "type": "object",
    "properties": {
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "count": {"type": "integer"},
                    "first_seen": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["type", "count", "first_seen", "message"]
            }
        },
        "affected_services": {
            "type": "array",
            "items": {"type": "string"}
        },
        "anomalies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "severity": {"type": "string"},
                    "timestamp": {"type": "string"}
                },
                "required": ["description", "severity", "timestamp"]
            }
        }
    },
    "required": ["errors", "affected_services", "anomalies"]
}

def call_ollama_json(prompt: str, schema: dict, model: str = MODEL) -> dict:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0}
            },
            timeout=120,
        )
        raw = response.json().get("response", "{}")
        return json.loads(raw)
    except Exception:
        return {"errors": [], "affected_services": [], "anomalies": []}

class LogAgent:
    def run(self, log_text: str) -> dict:
        prompt = (
            "You are a log analysis agent.\n"
            "Extract only facts from the raw logs.\n"
            "Return valid JSON matching the provided schema.\n"
            "Rules:\n"
            "- Group repeated errors into one entry when possible.\n"
            "- Count approximate frequency from the provided logs only.\n"
            "- List only services explicitly present in the logs.\n"
            "- Severity must be one of: low, medium, high.\n"
            "- If a timestamp is unavailable, use 'Unknown'.\n"
            "- Do not invent root cause conclusions.\n\n"
            "Raw logs:\n"
            f"{log_text}\n"
        )
        result = call_ollama_json(prompt, LOG_SCHEMA)
        if not isinstance(result, dict):
            return {"errors": [], "affected_services": [], "anomalies": []}
        result.setdefault("errors", [])
        result.setdefault("affected_services", [])
        result.setdefault("anomalies", [])
        return result
