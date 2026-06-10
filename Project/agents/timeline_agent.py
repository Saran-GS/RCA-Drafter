import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"

TIMELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "event": {"type": "string"}
                },
                "required": ["timestamp", "event"]
            }
        },
        "incident_start": {"type": "string"},
        "incident_end": {"type": "string"}
    },
    "required": ["events", "incident_start", "incident_end"]
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
        return {"events": [], "incident_start": "Unknown", "incident_end": "Unknown"}

class TimelineAgent:
    def run(self, timeline_text: str) -> dict:
        prompt = (
            "You are an incident timeline extraction agent.\n"
            "Extract only facts from the raw timeline.\n"
            "Return valid JSON matching the provided schema.\n"
            "Rules:\n"
            "- Sort events chronologically.\n"
            "- Do not invent timestamps.\n"
            "- If a timestamp is missing, use 'Unknown'.\n"
            "- If incident start/end cannot be determined, use 'Unknown'.\n"
            "- Keep event descriptions concise and factual.\n\n"
            "Raw timeline:\n"
            f"{timeline_text}\n"
        )
        result = call_ollama_json(prompt, TIMELINE_SCHEMA)
        if not isinstance(result, dict):
            return {"events": [], "incident_start": "Unknown", "incident_end": "Unknown"}
        result.setdefault("events", [])
        result.setdefault("incident_start", "Unknown")
        result.setdefault("incident_end", "Unknown")
        return result
