from datetime import datetime
from typing import List, Dict
import re
import json
from pathlib import Path
from chronologue_modules.schema import validate_memory_trace  # Adjust as needed

def parse_ics_datetime(dt_str: str) -> str:
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def parse_ics_event(ics_text: str) -> Dict:
    raw = {}

    for line in ics_text.splitlines():
        if line.startswith("SUMMARY:"):
            raw["title"] = line[len("SUMMARY:"):].strip()
        elif line.startswith("DESCRIPTION:"):
            raw["content"] = line[len("DESCRIPTION:"):].strip()
        elif line.startswith("DTSTART:"):
            raw["timestamp"] = parse_ics_datetime(line[len("DTSTART:"):])
        elif line.startswith("DTEND:"):
            raw["end"] = parse_ics_datetime(line[len("DTEND:"):])
        elif line.startswith("UID:"):
            raw["id"] = line[len("UID:"):].strip()
        elif line.startswith("LOCATION:"):
            raw["location"] = line[len("LOCATION:"):].strip()

    if "timestamp" in raw and "end" in raw:
        try:
            start = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(raw["end"].replace("Z", "+00:00"))
            raw["duration_minutes"] = int((end - start).total_seconds() // 60)
        except Exception as e:
            print(f"[!] Failed to infer duration: {e}")

    raw["type"] = "calendar_event"
    return {k: v for k, v in raw.items() if v is not None}

def import_ics(filepath: str) -> List[Dict]:
    print(f"→ Reading iCalendar file: {filepath}")
    with open(filepath, "r") as f:
        content = f.read()

    events = []
    for match in re.finditer(r"BEGIN:VEVENT(.*?)END:VEVENT", content, re.DOTALL):
        event_block = match.group(1)
        trace = parse_ics_event(event_block)
        if validate_memory_trace(trace):
            events.append(trace)
            print(f"→ Parsed: {trace.get('title', 'Untitled')}")
        else:
            print(f"[!] Invalid event skipped: {trace.get('id', 'unknown')}")
    return events

def save_events_to_json(events: List[Dict], output_path: str) -> None:
    with open(output_path, 'w') as f:
        json.dump({"memory": events}, f, indent=4)
    print(f"→ Saved {len(events)} event(s) to {output_path}")

def import_ics_from_directory(input_dir: Path, output_dir: Path) -> None:
    for ics_file in input_dir.glob("*.ics"):
        events = import_ics(str(ics_file))
        output_path = output_dir / (ics_file.stem + ".json")
        save_events_to_json(events, output_path)

if __name__ == "__main__":
    input_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/calendar/raw")
    output_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/calendar/processed")
    import_ics_from_directory(input_dir, output_dir)
