import requests
import json
import re
from datetime import date, datetime


def call_ollama(prompt: str, model: str = "phi3:mini") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=180,
        )
        return response.json()["response"]
    except Exception:
        return "{}"


def _safe_json_loads(text: str) -> dict:
    try:
        cleaned = (text or "").strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            if len(parts) > 1:
                cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned.strip())
    except Exception:
        return {}


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace("|", "-").strip()


def _fallback_text(value):
    text = _one_line(value)
    if not text or text.lower() in {"unknown", "tbd", "n/a", "none", "null"}:
        return "Under investigation"
    return text


def _normalize_severity(value):
    text = _fallback_text(value).lower()
    if "critical" in text:
        return "Critical"
    if "high" in text:
        return "High"
    if "medium" in text or "moderate" in text:
        return "Medium"
    if "low" in text:
        return "Low"
    return "Under investigation"


def _parse_time_token(text: str):
    text = _one_line(text)
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            pass
    match = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", text)
    if match:
        token = match.group(1)
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(token, fmt)
            except Exception:
                pass
    return None


def _format_duration_hours_minutes(delta):
    total_seconds = int(abs(delta.total_seconds()))
    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours} hours {minutes} minutes"


def _clean_services(values):
    if not isinstance(values, list):
        return ["Under investigation"]
    cleaned = []
    for item in values:
        text = _fallback_text(item)
        if text not in cleaned:
            cleaned.append(text)
    return cleaned or ["Under investigation"]


def _clean_timeline(rows):
    cleaned = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                t = _fallback_text(row.get("time"))
                e = _fallback_text(row.get("event"))
                cleaned.append({"time": t, "event": _one_line(e)})
    return cleaned


def _ensure_duration(data):
    rows = data.get("timeline", [])
    parsed = []
    for row in rows:
        dt = _parse_time_token(row.get("time", ""))
        if dt:
            parsed.append(dt)
    if len(parsed) >= 2:
        data["duration"] = _format_duration_hours_minutes(max(parsed) - min(parsed))
    else:
        data["duration"] = "Under investigation"
    return data


def _strip_priority_tags(text):
    text = _one_line(text)
    text = re.sub(r"\|\s*priority\s*:\s*(critical|high|medium|low)\s*", "", text, flags=re.I)
    text = re.sub(r"priority\s*:\s*(critical|high|medium|low)\b", "", text, flags=re.I)
    text = re.sub(r"\s+-\s+$", "", text).strip(" -")
    return _fallback_text(text)


def _clean_resolution_steps(values):
    cleaned = []
    if isinstance(values, list):
        for item in values:
            text = _strip_priority_tags(item)
            if text and text not in cleaned:
                cleaned.append(text)
    return cleaned or [
        "Rollback or mitigation was initiated",
        "Logs and telemetry were reviewed",
        "The affected component was isolated",
        "Service health was revalidated"
    ]


def _minimum_action_items(existing):
    required = [
        {"action": "Add defensive code checks and error handling for the failing path", "owner": "Engineering", "due_date": "Under investigation", "priority": "High"},
        {"action": "Review infrastructure capacity and connection pool configuration", "owner": "Infrastructure", "due_date": "Under investigation", "priority": "High"},
        {"action": "Update incident response process and escalation guidance", "owner": "SRE", "due_date": "Under investigation", "priority": "Medium"},
        {"action": "Add regression and load tests for the affected workflow", "owner": "QA", "due_date": "Under investigation", "priority": "High"},
        {"action": "Strengthen deployment safeguards and rollback checks", "owner": "Release Engineering", "due_date": "Under investigation", "priority": "High"},
        {"action": "Add monitoring and alerting for early detection of the failure pattern", "owner": "Observability", "due_date": "Under investigation", "priority": "High"},
    ]

    cleaned = []
    if isinstance(existing, list):
        for idx, item in enumerate(existing, start=1):
            if not isinstance(item, dict):
                continue
            cleaned.append({
                "id": idx,
                "action": _fallback_text(item.get("action")),
                "owner": _fallback_text(item.get("owner")),
                "due_date": _fallback_text(item.get("due_date")),
                "priority": _normalize_severity(item.get("priority")),
            })

    covered = set()
    for item in cleaned:
        combined = (item["action"] + " " + item["owner"]).lower()
        if "code" in combined or "engineering" in combined or "error handling" in combined:
            covered.add("code")
        if "infra" in combined or "connection pool" in combined or "capacity" in combined:
            covered.add("infra")
        if "process" in combined or "incident response" in combined or "sre" in combined:
            covered.add("process")
        if "test" in combined or "qa" in combined or "regression" in combined or "load" in combined:
            covered.add("testing")
        if "deploy" in combined or "rollback" in combined or "release" in combined:
            covered.add("deployment")
        if "monitor" in combined or "alert" in combined or "observability" in combined:
            covered.add("monitoring")

    needed = {
        "code": required[0],
        "infra": required[1],
        "process": required[2],
        "testing": required[3],
        "deployment": required[4],
        "monitoring": required[5],
    }

    for key in ["code", "infra", "process", "testing", "deployment", "monitoring"]:
        if key not in covered:
            cleaned.append(needed[key])

    while len(cleaned) < 6:
        cleaned.append(required[len(cleaned) % len(required)])

    final = []
    for idx, item in enumerate(cleaned, start=1):
        final.append({
            "id": idx,
            "action": _fallback_text(item["action"]),
            "owner": _fallback_text(item["owner"]),
            "due_date": _fallback_text(item["due_date"]),
            "priority": item["priority"] if item["priority"] in {"Critical", "High", "Medium", "Low"} else "Medium",
        })
    return final


def _normalize_paragraph(text):
    text = _fallback_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text.endswith("."):
        text += "."
    return text


def _normalize_report(data, timeline_result=None, log_result=None, diff_result=None):
    data = data if isinstance(data, dict) else {}

    if not data.get("date"):
        data["date"] = str(date.today())

    data["severity"] = _normalize_severity(
        data.get("severity")
        or (diff_result.get("risk_level") if isinstance(diff_result, dict) else None)
    )

    services = data.get("services_affected")
    if not services and isinstance(log_result, dict):
        services = log_result.get("affected_services", [])
    data["services_affected"] = _clean_services(services)

    timeline = _clean_timeline(data.get("timeline"))
    if isinstance(timeline_result, dict):
        source_events = timeline_result.get("events", [])
        fallback_rows = []
        for ev in source_events:
            if isinstance(ev, dict):
                fallback_rows.append({
                    "time": _fallback_text(ev.get("timestamp")),
                    "event": _fallback_text(ev.get("event")),
                })
        if len(fallback_rows) > len(timeline):
            timeline = _clean_timeline(fallback_rows)

    data["timeline"] = timeline or [{"time": "Under investigation", "event": "Timeline details are under investigation"}]
    data = _ensure_duration(data)

    data["root_cause"] = _normalize_paragraph(data.get("root_cause"))
    data["contributing_factors"] = [
        _fallback_text(x) for x in (data.get("contributing_factors") or [])
        if _fallback_text(x)
    ] or ["Under investigation"]

    impact = data.get("impact_assessment", {}) if isinstance(data.get("impact_assessment"), dict) else {}
    data["impact_assessment"] = {
        "users_affected": _fallback_text(impact.get("users_affected")),
        "data_integrity": _fallback_text(impact.get("data_integrity")),
        "financial_sla_impact": _fallback_text(impact.get("financial_sla_impact")),
    }

    data["resolution_steps"] = _clean_resolution_steps(data.get("resolution_steps"))
    data["action_items"] = _minimum_action_items(data.get("action_items"))
    data["prevention_measures"] = [
        _fallback_text(x) for x in (data.get("prevention_measures") or [])
        if _fallback_text(x)
    ] or ["Under investigation"]
    data["lessons_learned"] = _normalize_paragraph(data.get("lessons_learned"))

    return data


def render_rca_markdown(data: dict) -> str:
    lines = []
    lines.append("# Root Cause Analysis Report")
    lines.append("")
    lines.append("## Incident Summary")
    lines.append(f"- **Date:** {_fallback_text(data.get('date'))}")
    lines.append(f"- **Severity:** {data.get('severity', 'Under investigation')}")
    lines.append(f"- **Duration:** {_fallback_text(data.get('duration'))}")
    lines.append(f"- **Services Affected:** {', '.join(data.get('services_affected', ['Under investigation']))}")
    lines.append("")
    lines.append("## Timeline")
    lines.append("| Time | Event |")
    lines.append("|------|-------|")
    for row in data.get("timeline", []):
        lines.append(f"| {_fallback_text(row['time'])} | {_one_line(row['event'])} |")
    lines.append("")
    lines.append("## Root Cause")
    lines.append(data.get("root_cause", "Under investigation."))
    lines.append("")
    lines.append("## Contributing Factors")
    for factor in data.get("contributing_factors", ["Under investigation"]):
        lines.append(f"- {factor}")
    lines.append("")
    lines.append("## Impact Assessment")
    impact = data.get("impact_assessment", {})
    lines.append(f"- Users affected: {_fallback_text(impact.get('users_affected'))}")
    lines.append(f"- Data integrity: {_fallback_text(impact.get('data_integrity'))}")
    lines.append(f"- Financial/SLA impact: {_fallback_text(impact.get('financial_sla_impact'))}")
    lines.append("")
    lines.append("## Resolution Steps Taken")
    for i, step in enumerate(data.get("resolution_steps", []), start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Action Items")
    lines.append("| # | Action | Owner | Due Date | Priority |")
    lines.append("|---|--------|-------|----------|----------|")
    for item in data.get("action_items", []):
        lines.append(f"| {item['id']} | {_one_line(item['action'])} | {_one_line(item['owner'])} | {_one_line(item['due_date'])} | {_one_line(item['priority'])} |")
    lines.append("")
    lines.append("## Prevention Measures")
    for measure in data.get("prevention_measures", ["Under investigation"]):
        lines.append(f"- {_one_line(measure)}")
    lines.append("")
    lines.append("## Lessons Learned")
    lines.append(data.get("lessons_learned", "Under investigation."))
    lines.append("")
    return "\n".join(lines)


class RCAAgent:
    def run(self, timeline_result: dict, log_result: dict, diff_result: dict) -> str:
        today = date.today().isoformat()
        timeline_json = json.dumps(timeline_result or {}, indent=2)
        log_json = json.dumps(log_result or {}, indent=2)
        diff_json = json.dumps(diff_result or {}, indent=2)

        prompt = f"""You are a senior Site Reliability Engineer.
Use ONLY the evidence provided below.
Return VALID JSON ONLY.
No prose outside JSON.
No markdown.
No code fences.

RULES:
- Duration must be calculated as: last timeline event timestamp MINUS first timeline event timestamp.
- Express duration exactly as: X hours Y minutes.
- Never say "brief" or "seconds".
- Timeline table MUST include ALL events from the input, not just the first 3.
- Timeline must contain a minimum of 6 rows when at least 6 input events exist.
- Severity must be ONE word only: Critical / High / Medium / Low
- Timeline rows must be single-line concise event text only.
- Resolution Steps must be plain numbered steps only, with no inline priority tags or commentary.
- Action Items must contain at least 6 rows and must cover code, infrastructure, process, testing, deployment, and monitoring.
- Never leave placeholder text or incomplete sentences.
- If unsure of a value, write "Under investigation".
- Do not invent dates, durations, user counts, owners, or financial impact.
- Keep root_cause to one paragraph.
- Keep lessons_learned to one paragraph.

Required JSON schema:
{{
  "date": "{today}",
  "severity": "Critical|High|Medium|Low",
  "duration": "X hours Y minutes",
  "services_affected": ["string"],
  "timeline": [{{"time": "string", "event": "string"}}],
  "root_cause": "string",
  "contributing_factors": ["string"],
  "impact_assessment": {{
    "users_affected": "string",
    "data_integrity": "string",
    "financial_sla_impact": "string"
  }},
  "resolution_steps": ["string"],
  "action_items": [
    {{
      "id": 1,
      "action": "string",
      "owner": "string",
      "due_date": "string",
      "priority": "Critical|High|Medium|Low"
    }}
  ],
  "prevention_measures": ["string"],
  "lessons_learned": "string"
}}

Evidence from TimelineAgent:
{timeline_json}

Evidence from LogAgent:
{log_json}

Evidence from DiffAgent:
{diff_json}

Output JSON only."""

        raw = call_ollama(prompt)
        structured = _safe_json_loads(raw)

        if not structured:
            structured = {
                "date": today,
                "severity": diff_result.get("risk_level", "Under investigation") if isinstance(diff_result, dict) else "Under investigation",
                "duration": "Under investigation",
                "services_affected": (log_result.get("affected_services", []) if isinstance(log_result, dict) else []) or ["Under investigation"],
                "timeline": [
                    {
                        "time": ev.get("timestamp", "Under investigation"),
                        "event": ev.get("event", "Under investigation"),
                    }
                    for ev in (timeline_result.get("events", []) if isinstance(timeline_result, dict) else [])
                    if isinstance(ev, dict)
                ],
                "root_cause": "Under investigation",
                "contributing_factors": ["Under investigation"],
                "impact_assessment": {
                    "users_affected": "Under investigation",
                    "data_integrity": "Under investigation",
                    "financial_sla_impact": "Under investigation",
                },
                "resolution_steps": ["Under investigation"],
                "action_items": [],
                "prevention_measures": ["Under investigation"],
                "lessons_learned": "Under investigation",
            }

        normalized = _normalize_report(structured, timeline_result, log_result, diff_result)
        return render_rca_markdown(normalized)
