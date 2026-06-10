from .timeline_agent import TimelineAgent
from .log_agent import LogAgent
from .diff_agent import DiffAgent
from .rca_agent import RCAAgent

def run_pipeline(timeline_text: str, log_text: str, diff_text: str) -> str:
    timeline_result = TimelineAgent().run(timeline_text)
    log_result      = LogAgent().run(log_text)
    diff_result     = DiffAgent().run(diff_text)
    rca_markdown    = RCAAgent().run(timeline_result, log_result, diff_result)
    return rca_markdown

def stream_pipeline(timeline_text: str, log_text: str, diff_text: str):
    yield "status", "Analyzing timeline..."
    timeline_result = TimelineAgent().run(timeline_text)
    yield "status", "Scanning logs..."
    log_result = LogAgent().run(log_text)
    yield "status", "Reviewing diff..."
    diff_result = DiffAgent().run(diff_text)
    yield "status", "Generating RCA..."
    for token, done in RCAAgent().stream(timeline_result, log_result, diff_result):
        yield "token", token
        if done:
            yield "done", ""
            break
