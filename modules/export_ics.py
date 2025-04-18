import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from schema import validate_memory_trace

def generate_uid(title: str, date_str: str) -> str:
    # Simplify UID format to match gold standard
    base = title.lower().replace(" ", "_").replace("/", "_").replace("°", "").replace("#", "")
    return f"{base}-{date_str}@memorysystem.ai"

def datetime_to_ics(dt: str) -> str:
    return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")

def generate_ics_string(trace: dict) -> str:
    start_iso = trace["timestamp"]
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=15)

    start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end = end_dt.strftime("%Y%m%dT%H%M%SZ")

    # Summary: first 40 characters
    summary = trace["content"][:40] + ("..." if len(trace["content"]) > 40 else "")

    # Hardcoded chat link for now (to be replaced by real integration)
    chat_url = trace.get("chat_url", "https://chat.openai.com/share/example-link")

    # Full description + link
    full_description = f"{trace['content']}\\nChat log: {chat_url}"

    # Escape special characters for ICS format
    summary = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    full_description = full_description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    # Timestamp and UID
    dtstamp = "20250401T080000Z"
    uid = trace.get("linked_event_uid") or generate_uid(trace["task_id"], start[:8])
    location = trace.get("location", "")

    return f"""
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{start}
DTEND:{end}
SUMMARY:{summary}
DESCRIPTION:{full_description}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT"""


def write_consolidated_ics(events: list[str], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Match gold standard format
    calendar_header = "BEGIN:VCALENDAR\rVERSION:2.0\rPRODID:-//CalendarMemorySystem//EN\r"
    calendar_footer = "\rEND:VCALENDAR"
    
    # Join events without additional line breaks
    events_block = "".join(events)
    
    calendar_block = calendar_header + events_block + calendar_footer
    
    with open(output_path, "w", newline='\r\n') as f:
        f.write(calendar_block)
    print(f"→ Saved consolidated calendar: {output_path.name}")

def convert_json_folder_to_ics(input_dir: Path, output_dir: Path):
    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        print(f"[!] No JSON files found in {input_dir}")
        return

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        traces = data.get("memory", [])
        vevents = []
        for trace in traces:
            if validate_memory_trace(trace):
                try:
                    vevents.append(generate_ics_string(trace))
                except KeyError as e:
                    print(f"[!] Skipping trace {trace.get('id')} due to missing key: {e}")

        if vevents:
            output_filename = json_file.stem + ".ics"
            output_path = output_dir / output_filename
            write_consolidated_ics(vevents, output_path)
        else:
            print(f"[!] No valid memory traces found in {json_file.name}")

def test_ics_format():
    # Sample memory trace similar to gold standard
    sample_trace = {
        "id": "test-001",
        "type": "observation",
        "timestamp": "2024-04-07T09:00:00Z",
        "content": "Temperature in incubator #3 drifted 1.5°C above target during morning run.",
        "task_id": "lab_ops",
        "location": "wetlab_sync"
    }
    
    # Generate ICS string
    ics_string = generate_ics_string(sample_trace)
    
    # Expected format based on gold standard
    expected_format = """BEGIN:VEVENT
UID:lab_ops-20240407@memorysystem.ai
DTSTAMP:20250401T080000Z
DTSTART:20240407T090000Z
DTEND:20240407T091500Z
SUMMARY:Temperature in incubator #3 drifted 1.5°C above target during morning run.
DESCRIPTION:Temperature in incubator #3 drifted 1.5°C above target during morning run.
LOCATION:wetlab_sync
STATUS:CONFIRMED
END:VEVENT"""
    
    # Compare the generated string with expected format
    print("Generated ICS string:")
    print(ics_string)
    print("\nExpected format:")
    print(expected_format)
    
    # Write to file for visual comparison
    test_output = Path("test_output.ics")
    write_consolidated_ics([ics_string], test_output)
    print(f"\nWritten to {test_output} for comparison with gold standard")

if __name__ == "__main__":
    test_ics_format()
    # Original main code
    input_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/raw")
    output_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/processed")
    convert_json_folder_to_ics(input_dir, output_dir)