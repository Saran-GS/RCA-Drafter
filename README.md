# RCA Agent — Multi-Agent Root Cause Analysis

RCA Agent is an AI-assisted incident analysis system that converts raw operational evidence into a structured Root Cause Analysis (RCA) report. The application accepts incident timelines, error logs, and code diffs, processes them through a multi-agent analysis pipeline, and produces a consistent Markdown report for investigation, review, and documentation. [1][2]

## Overview

Production incidents often leave teams with fragmented evidence spread across notes, logs, and recent code changes. RCA Agent addresses this by providing a workflow that collects these inputs, analyzes them through specialized agents, and generates a readable RCA report with sections such as incident summary, timeline, root cause, contributing factors, impact, resolution steps, and action items. [1][3]

## Features

- Secure login flow for controlled access to the application.  
- Dashboard for submitting timeline data, logs, and git diffs.  
- Multi-agent analysis pipeline with specialized roles for timeline parsing, log analysis, and diff review.  
- AI-generated RCA report in Markdown format.  
- Stored report history with retrieval and deletion support.  
- Export option for downloading the generated RCA report. [2][4]

## Architecture

The system uses a browser-based frontend and a Flask backend. The frontend handles authentication and user input, while the backend orchestrates the RCA pipeline, communicates with the local model service, stores generated reports, and returns the final analysis to the user. [2][5]

### Multi-Agent Flow

1. **Timeline Agent** extracts incident events and ordering from the timeline input.  
2. **Log Agent** identifies recurring errors, anomalies, and affected services from raw logs.  
3. **Diff Agent** reviews recent code changes and highlights risky modifications.  
4. **Synthesis Step** combines all agent outputs into a final Markdown RCA report.  

This architecture keeps responsibilities separated and makes the pipeline easier to maintain, test, and extend. [4][1]

## Technology Stack

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, JavaScript  
- **AI Runtime:** Ollama  
- **Model:** `phi3:mini`  
- **Report Format:** Markdown  
- **Storage:** JSON report files [1][3]

## Why Local AI

The project uses a local model instead of a cloud API. This improves privacy for incident data, reduces reliance on internet connectivity and third-party API limits, and makes the system easier to demonstrate in offline or controlled environments. [1][2]

## Repository Structure

```text
.
├── Document/        # Project reports, AI usage note, setup docs, test cases
├── Project/         # Application source code, templates, static assets, reports
├── Resume/          # Resume or profile documents
├── Team1/           # Team member information and contribution details
├── Video/           # Demo video or video link files
└── README.md
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or later  
- Ollama installed locally  
- Git  
- A compatible browser [1][3]

### Model Setup

Pull the local model:

```bash
ollama pull phi3:mini
```

### Installation

From the project root:

```bash
cd Project
pip install -r requirements.txt
```

### Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Usage

1. Open the login page.  
2. Sign in with valid credentials.  
3. Enter one or more of the following: timeline, logs, and code diff.  
4. Run the analysis.  
5. Review the generated RCA report.  
6. Export or revisit saved reports as needed. [1][2]

## Example Output

A generated RCA report typically contains:

- Incident Summary  
- Timeline  
- Root Cause  
- Contributing Factors  
- Impact Assessment  
- Resolution Steps Taken  
- Action Items  
- Prevention Measures  
- Lessons Learned

## AI Assistance Notes

AI was used to support analysis, extraction, and report drafting. It is effective for organizing unstructured incident data, but final RCA outputs should still be reviewed by a human because language models may over-infer causes when evidence is incomplete. [4][3]

## Documentation

Additional supporting material can be placed in the `Document/` folder, such as:

- Project overview  
- Setup instructions  
- AI usage note  
- Test cases  
- Architecture diagram  
- Demo script [1][2]

## Future Improvements

- Add stronger authentication and session handling.  
- Improve prompt grounding for more reliable factual output.  
- Add richer report visualizations and severity scoring.  
- Extend the multi-agent pipeline with validation or confidence scoring.  
- Support additional export formats such as PDF or DOCX. [5][4]

## Maintainers

Project repository maintained by the development team for the RCA Agent submission.

## License

Add the appropriate license for your repository if needed.