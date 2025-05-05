# sync_mac_calendar.py

# Sync memory traces to macOS Calendar (iCloud-compatible if calendar is synced)

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from schema import validate_memory_trace  # Ensure your schema validation remains the same


def memory_trace_to_applescript(trace, calendar_name="Home"):
    start_dt = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=30)

    # Use long English date format (AppleScript-friendly)
    start_str = start_dt.strftime("%A, %B %-d, %Y at %H:%M:%S")
    end_str = end_dt.strftime("%A, %B %-d, %Y at %H:%M:%S")

    def sanitize(text):
        return text.replace('"', "'").replace("\n", " ").strip()

    summary = sanitize(f"[{trace['type'].upper()}] {trace['content'][:40]}...")
    description = sanitize(trace["content"])

    meta = []
    if "task_id" in trace:
        meta.append(f"Task: {trace['task_id']}")
    if "importance" in trace:
        meta.append(f"Importance: {trace['importance']}")
    if "completion_status" in trace:
        meta.append(f"Status: {trace['completion_status']}")
    if "source" in trace:
        meta.append(f"Source: {trace['source']}")

    full_description = sanitize(description + ("\n\n" + "\n".join(meta) if meta else ""))

    script = f'''
tell application "Calendar"
    tell calendar "{calendar_name}"
        make new event with properties {{
            summary: "{summary}",
            description: "{full_description}",
            start date:date "{start_str}",
            end date:date "{end_str}"
        }}
    end tell
end tell
'''
    return script


def create_event(trace, calendar_name="Home"):
    applescript = memory_trace_to_applescript(trace, calendar_name)
    subprocess.run(["osascript", "-e", applescript], check=True)

def sync_memory_file_to_mac_calendar(memory_json_path: Path, calendar_name="Home"):
    with open(memory_json_path) as f:
        session = json.load(f)

    traces = session.get("memory", [])
    synced = 0

    for trace in traces:
        if validate_memory_trace(trace):
            try:
                create_event(trace, calendar_name)
                print(f"[✓] Synced: {trace['content'][:40]}...")
                synced += 1
            except subprocess.CalledProcessError as e:
                print(f"[!] Failed to sync {trace.get('id')}: {e}")

    print(f"\n[✓] {synced} events synced from {memory_json_path.name}")

if __name__ == "__main__":
    memory_path = Path("data/conversation/raw/lab_manager_4-12.json")
    sync_memory_file_to_mac_calendar(memory_path)

