# modules/generate_markdown_preview.py

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

def parse_ics_datetime(dt_str: str) -> str:
    """Convert ICS datetime to ISO 8601."""
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def import_ics(filepath: str) -> List[Dict]:
    """Import events from .ics into list of memory traces."""
    with open(filepath, "r") as f:
        content = f.read()

    events = []
    for block in content.split("BEGIN:VEVENT")[1:]:
        lines = block.strip().splitlines()
        trace = {"type": "calendar_event"}
        for line in lines:
            if line.startswith("SUMMARY:"):
                trace["title"] = line[8:].strip()
            elif line.startswith("DESCRIPTION:"):
                trace["content"] = line[12:].strip()
            elif line.startswith("DTSTART:"):
                trace["timestamp"] = parse_ics_datetime(line[8:].strip())
            elif line.startswith("DTEND:"):
                trace["end"] = parse_ics_datetime(line[6:].strip())
            elif line.startswith("UID:"):
                trace["id"] = line[4:].strip()
            elif line.startswith("LOCATION:"):
                trace["location"] = line[9:].strip()

        if "timestamp" in trace and "end" in trace:
            start = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(trace["end"].replace("Z", "+00:00"))
            trace["duration_minutes"] = int((end - start).total_seconds() / 60)

        events.append(trace)

    return events

def traces_to_markdown_table(traces: List[Dict]) -> str:
    """Format memory traces into a Markdown table."""
    headers = ["Event Title", "Date", "Start Time", "Duration (min)", "Location", "Notes"]
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    rows = []
    for trace in traces:
        title = trace.get("title", "Untitled")
        timestamp = trace.get("timestamp", "")
        date = timestamp.split("T")[0] if "T" in timestamp else ""
        start_time = timestamp.split("T")[1].replace("Z", "") if "T" in timestamp else ""
        duration = str(trace.get("duration_minutes", ""))
        location = trace.get("location", "")
        notes = trace.get("content", "").strip().replace("\n", " ")

        row = f"| {title} | {date} | {start_time} | {duration} | {location} | {notes} |"
        rows.append(row)

    return "\n".join([header_line, separator_line] + rows)

def generate_markdown_from_ics(ics_path: str, output_dir: str) -> None:
    """Main entrypoint: generate .md preview from .ics."""
    traces = import_ics(ics_path)
    markdown_content = traces_to_markdown_table(traces)

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    base_name = Path(ics_path).stem
    output_path = output_dir_path / f"{base_name}_preview.md"

    output_path.write_text(markdown_content)
    print(f"Markdown preview generated: {output_path}")

if __name__ == "__main__":
    ics_path = "/Users/derekrosenzweig/Documents/GitHub/chronologue/data/summary/raw_ics/wetlab_sample.ics"
    output_dir = "/Users/derekrosenzweig/Documents/GitHub/chronologue/data/summary/markdown/"
    
    generate_markdown_from_ics(ics_path, output_dir)
