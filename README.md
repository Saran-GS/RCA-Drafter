# RCA Agent — Multi-Agent Root Cause Analysis

> Convert fragmented incident evidence into a structured, actionable RCA report in seconds.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=flat-square&logo=flask)
![Ollama](https://img.shields.io/badge/Ollama-phi3:mini-purple?style=flat-square)


---

## What is RCA Agent?

Production incidents leave teams with evidence scattered across Slack threads, log dumps, and recent deploys. **RCA Agent** pulls that evidence together — incident timeline, error logs, and git diff — runs it through a multi-agent analysis pipeline, and produces a consistent, structured RCA report ready for review and documentation.

No cloud API keys. No rate limits. Runs entirely on your machine using a local model via Ollama.

---

## Demo

Demo Video Link: https://drive.google.com/drive/folders/10tN7ORRwezA6pg4srtc4-4J63xLNGadk?usp=sharing

📹 [Watch the demo video](./Video/)

---

## Features

| Feature | Description |
|---|---|
| 🔐 Secure login | Controlled access with a simple authentication flow |
| 📋 Incident form | Paste or upload timeline, logs, and git diff |
| 🤖 Multi-agent pipeline | Four specialized agents analyze different dimensions of the incident |
| 📄 Structured RCA output | Markdown report following a consistent, reviewable template |
| 🗂️ Report history | Browse, retrieve, and delete past reports |
| ⬇️ Export | Download any report as a Markdown file |

---

## How it Works

```
User Input (timeline + logs + git diff)
         │
         ▼
  ┌──────────────────────────────────────────┐
  │           Coordinator (Flask)            │
  │                                          │
  │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
  │  │Timeline │  │   Log    │  │  Diff  │  │
  │  │  Agent  │  │  Agent   │  │ Agent  │  │
  │  └────┬────┘  └────┬─────┘  └───┬────┘  │
  │       └────────────┴────────────┘        │
  │                    │                     │
  │             ┌──────▼──────┐              │
  │             │  Synthesis  │              │
  │             │    Step     │              │
  │             └──────┬──────┘              │
  └────────────────────┼────────────────────┘
                       │
                       ▼
              Structured RCA Report (Markdown)
```

### Agent Roles

| Agent | Responsibility |
|---|---|
| **Timeline Agent** | Extracts ordered events and chronology from the incident timeline |
| **Log Agent** | Identifies recurring errors, anomalies, and affected services |
| **Diff Agent** | Reviews recent code changes and flags risky or likely-culprit modifications |
| **Synthesis Step** | Combines all agent findings into the final structured RCA report |

### Report Sections

Every generated report includes:

1. Incident Summary
2. Timeline
3. Root Cause
4. Contributing Factors
5. Impact Assessment
6. Resolution Steps Taken
7. Action Items
8. Prevention Measures
9. Lessons Learned

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| Frontend | HTML, CSS, JavaScript |
| AI Runtime | [Ollama](https://ollama.com) |
| Model | `phi3:mini` (local, no API key needed) |
| Report Format | Markdown |
| Storage | JSON files |

### Why local AI?

- **Privacy** — incident data never leaves your machine
- **No limits** — no rate limits or API quotas
- **Offline-friendly** — works in air-gapped or demo environments

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- [Ollama](https://ollama.com/download) installed and running
- Git
- A modern browser

### 1 — Pull the model

```bash
ollama pull phi3:mini
```

### 2 — Clone and install

```bash
git clone <your-repo-url>
cd Project
pip install -r requirements.txt
```

### 3 — Run

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Usage

1. Open the app and sign in
2. Paste your incident **timeline**, **error logs**, and **git diff** into the form
3. Click **Run Analysis** — the agent pipeline processes your input
4. Review the generated RCA report
5. Export or save the report for your team

---

## Repository Structure

```
.
├── Document/        # Project report, AI usage note, setup docs, architecture, test cases
├── Project/         # Application source — Flask app, templates, static assets, reports
│   ├── app.py
│   ├── agents/
│   ├── templates/
│   ├── static/
│   └── reports/
├── Resume/          # Team member resumes (PDF)
├── team details/           # Team details and contribution breakdown
├── Video/           # Demo video or link file
└── README.md
```

---

## AI Assistance Notes

AI tools were used throughout development for code generation, prompt design, and report drafting. Key observations:

- **Effective for:** structuring unstructured incident data, extracting patterns from logs, consistent report formatting
- **Watch out for:** over-inferring root causes when evidence is incomplete — always have a human review the final report before sharing

Prompts used during development are documented in [`Document/PROMPTS.md`](./Document/).

---

## Future Improvements

- [ ] Stronger authentication and session management
- [ ] Confidence scoring per agent finding
- [ ] PDF and DOCX export formats
- [ ] Richer dashboard with incident severity scoring
- [ ] Validation layer to cross-check agent conclusions


