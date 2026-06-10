import markdown
from pathlib import Path


def render_markdown_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])


def save_markdown_file(md_text: str, output_path: str = "rca_report.md") -> str:
    path = Path(output_path)
    path.write_text(md_text, encoding="utf-8")
    return str(path.resolve())
