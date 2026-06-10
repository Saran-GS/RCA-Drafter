import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"

DIFF_SCHEMA = {
    "type": "object",
    "properties": {
        "risky_changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "change_type": {"type": "string"},
                    "description": {"type": "string"},
                    "lines": {"type": "string"}
                },
                "required": ["file", "change_type", "description", "lines"]
            }
        },
        "risk_level": {"type": "string"},
        "changed_files": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["risky_changes", "risk_level", "changed_files"]
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
        return {"risky_changes": [], "risk_level": "Unknown", "changed_files": []}

class DiffAgent:
    def run(self, diff_text: str) -> dict:
        prompt = (
            "You are a git diff risk analysis agent.\n"
            "Extract only evidence-based risky changes from the diff.\n"
            "Return valid JSON matching the provided schema.\n"
            "Rules:\n"
            "- Risk level must be one of: low, medium, high, Unknown.\n"
            "- Flag deletions, config changes, dependency bumps, and critical logic changes.\n"
            "- Do not claim an outage was caused unless the diff clearly suggests risk.\n"
            "- If line numbers are unclear, use 'Unknown'.\n"
            "- changed_files must contain only files present in the diff.\n\n"
            "Raw diff:\n"
            f"{diff_text}\n"
        )
        result = call_ollama_json(prompt, DIFF_SCHEMA)
        if not isinstance(result, dict):
            return {"risky_changes": [], "risk_level": "Unknown", "changed_files": []}
        result.setdefault("risky_changes", [])
        result.setdefault("risk_level", "Unknown")
        result.setdefault("changed_files", [])
        return result
