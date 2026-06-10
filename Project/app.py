import io
import os
import json
import uuid
from datetime import datetime

import requests
from flask import Flask, request, jsonify, render_template, send_file, Response, stream_with_context

from agents.orchestrator import run_pipeline

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3:mini"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return jsonify({"ollama": "ok", "model": MODEL})
        return jsonify({"ollama": "unreachable", "model": MODEL}), 503
    except Exception:
        return jsonify({"ollama": "unreachable", "model": MODEL}), 503


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    timeline = (data.get("timeline") or "").strip()
    logs = (data.get("logs") or "").strip()
    diff = (data.get("diff") or "").strip()

    if not any([timeline, logs, diff]):
        return jsonify({"status": "error", "rca_markdown": "At least one field must be provided."}), 400

    try:
        rca_markdown = run_pipeline(timeline, logs, diff)

        report_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        preview = (rca_markdown or "").replace("\n", " ")[:180]

        report = {
            "id": report_id,
            "created_at": created_at,
            "timeline": timeline,
            "logs": logs,
            "diff": diff,
            "preview": preview,
            "rca_markdown": rca_markdown
        }

        with open(os.path.join(REPORTS_DIR, f"{report_id}.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return jsonify({
            "status": "ok",
            "rca_markdown": rca_markdown,
            "report_id": report_id
        })
    except Exception as e:
        return jsonify({"status": "error", "rca_markdown": f"Pipeline error: {str(e)}"}), 500


@app.route("/export", methods=["POST"])
def export():
    data = request.get_json(silent=True) or {}
    content = data.get("rca_markdown", "")
    if not content:
        return jsonify({"error": "No rca_markdown provided"}), 400

    buffer = io.BytesIO(content.encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="rca_report.md",
        mimetype="text/markdown"
    )


@app.route("/reports", methods=["GET"])
def list_reports():
    reports = []
    for name in sorted(os.listdir(REPORTS_DIR), reverse=True):
        if not name.endswith(".json"):
            continue
        path = os.path.join(REPORTS_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            reports.append({
                "id": data.get("id"),
                "created_at": data.get("created_at"),
                "preview": data.get("preview", "")
            })
        except Exception:
            continue
    return jsonify({"status": "ok", "reports": reports})


@app.route("/reports/<report_id>", methods=["GET"])
def get_report(report_id):
    path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    if not os.path.exists(path):
        return jsonify({"status": "error", "message": "Report not found"}), 404

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify({"status": "ok", "report": data})


@app.route("/reports/<report_id>", methods=["DELETE"])
def delete_report(report_id):
    path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    if not os.path.exists(path):
        return jsonify({"status": "error", "message": "Report not found"}), 404
    try:
        os.remove(path)
        return jsonify({"status": "ok", "message": "Report deleted", "report_id": report_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/analyze-stream", methods=["POST"])
def analyze_stream():
    data = request.get_json(silent=True) or {}
    timeline = (data.get("timeline") or "").strip()
    logs = (data.get("logs") or "").strip()
    diff = (data.get("diff") or "").strip()

    if not any([timeline, logs, diff]):
        return jsonify({"status": "error", "message": "At least one field must be provided."}), 400

    def call_ollama_json(prompt: str):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=180
            )
            text = response.json().get("response", "{}").strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) > 1:
                    text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception:
            return {}

    def stream():
        try:
            yield json.dumps({"type":"status","message":"Analyzing timeline..."}) + "\n"

            timeline_prompt = f"""You are a precise incident timeline parser.
Analyze the following raw incident timeline text and extract structured events.

IMPORTANT: Respond with VALID JSON ONLY. No prose, no explanation, just raw JSON.

Output format:
{{
  "events": [
    {{"timestamp": "HH:MM or ISO string", "event": "description of what happened"}}
  ],
  "incident_start": "timestamp string",
  "incident_end": "timestamp string"
}}

Sort events chronologically. If timestamps are missing, infer from context.
If incident_end cannot be determined, use "unknown".

Timeline text:
{timeline}

JSON output:"""
            timeline_result = call_ollama_json(timeline_prompt)

            yield json.dumps({"type":"status","message":"Scanning logs..."}) + "\n"

            log_prompt = f"""You are an expert log analysis agent.
Analyze the following error logs and identify patterns, anomalies, and affected services.

IMPORTANT: Respond with VALID JSON ONLY. No prose, no explanation, just raw JSON.

Output format:
{{
  "errors": [
    {{"type": "error type", "count": 1, "first_seen": "timestamp", "message": "sample message"}}
  ],
  "affected_services": ["service1", "service2"],
  "anomalies": [
    {{"description": "what was anomalous", "severity": "low|medium|high", "timestamp": "when"}}
  ]
}}

Error logs:
{logs}

JSON output:"""
            log_result = call_ollama_json(log_prompt)

            yield json.dumps({"type":"status","message":"Reviewing diff..."}) + "\n"

            diff_prompt = f"""You are a code review and risk assessment agent.
Analyze the following git diff and identify risky changes that could cause incidents.

IMPORTANT: Respond with VALID JSON ONLY. No prose, no explanation, just raw JSON.

Output format:
{{
  "risky_changes": [
    {{
      "file": "filename",
      "change_type": "deletion|config|dependency|logic|other",
      "description": "why this is risky",
      "lines": "line numbers if relevant"
    }}
  ],
  "risk_level": "low|medium|high",
  "changed_files": ["file1", "file2"]
}}

Git diff:
{diff}

JSON output:"""
            diff_result = call_ollama_json(diff_prompt)

            yield json.dumps({"type":"status","message":"Generating RCA..."}) + "\n"

            rca_prompt = f"""You are a senior Site Reliability Engineer writing a formal Root Cause Analysis report.
Using the structured data from three analysis agents below, produce a complete RCA document in Markdown.

TIMELINE AGENT OUTPUT:
{json.dumps(timeline_result, indent=2)}

LOG AGENT OUTPUT:
{json.dumps(log_result, indent=2)}

DIFF AGENT OUTPUT:
{json.dumps(diff_result, indent=2)}

Produce the RCA report using this structure:

# Root Cause Analysis Report

## Incident Summary
- **Date:**
- **Severity:**
- **Duration:**
- **Services Affected:**

## Timeline
| Time | Event |
|------|-------|

## Root Cause
[Single clear paragraph explaining the root cause]

## Contributing Factors
- Factor 1
- Factor 2

## Impact Assessment
- Users affected:
- Data integrity:
- Financial/SLA impact:

## Resolution Steps Taken
1. Step 1
2. Step 2

## Action Items
| # | Action | Owner | Due Date | Priority |
|---|--------|-------|----------|----------|

## Prevention Measures
- Measure 1
- Measure 2

## Lessons Learned
[Paragraph]

Output ONLY markdown."""

            final_markdown = ""
            try:
                response = requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": MODEL, "prompt": rca_prompt, "stream": True},
                    stream=True,
                    timeout=300
                )
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        token = chunk.get("response", "")
                        if token:
                            final_markdown += token
                            yield json.dumps({"type":"chunk","content":token}) + "\n"
                    except Exception:
                        continue
            except Exception as e:
                yield json.dumps({"type":"error","message":str(e)}) + "\n"
                return

            report_id = str(uuid.uuid4())[:8]
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            preview = final_markdown.replace("\n", " ")[:180]

            report = {
                "id": report_id,
                "created_at": created_at,
                "timeline": timeline,
                "logs": logs,
                "diff": diff,
                "preview": preview,
                "rca_markdown": final_markdown
            }

            try:
                with open(os.path.join(REPORTS_DIR, f"{report_id}.json"), "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            yield json.dumps({"type":"done","report_id":report_id}) + "\n"
        except Exception as e:
            yield json.dumps({"type":"error","message":str(e)}) + "\n"

    return Response(stream_with_context(stream()), mimetype="application/x-ndjson")

if __name__ == "__main__":
    app.run(debug=True, port=5000)




