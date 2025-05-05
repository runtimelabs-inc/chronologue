import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from schema import validate_memory_trace
from openai import OpenAI  

client = OpenAI()


def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("°", "").replace("#", "")
    return f"{base}-{date_str}@memorysystem.ai"


def datetime_to_ics(dt: str) -> str:
    return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")

def resolve_duration_minutes(trace: dict, default: int = 30, strict: bool = False) -> int:
    """
    Resolves duration from a structured JSON trace.
    Returns an integer duration in minutes, or a fallback default.
    Only applies to 'scheduled_event' traces.
    """
    trace_id = trace.get("id", "unknown")
    trace_type = trace.get("type", "")

    if trace_type != "scheduled_event":
        return 15  # Optional: fallback for other types like 'observation' or 'goal'

    duration = trace.get("duration_minutes")
    if duration is None:
        print(f"[!] Missing duration_minutes in trace {trace_id}, using default {default}")
        return default

    if isinstance(duration, int) and 0 < duration <= 1440:
        return duration
    if isinstance(duration, str):
        try:
            val = int(duration)
            if 0 < val <= 1440:
                return val
        except ValueError:
            pass

    print(f"[!] Invalid duration_minutes in trace {trace_id}, using default {default}")
    return default if not strict else 0



def generate_summary_title(content: str, max_chars: int = 40) -> str:
    try:
        response = client.responses.create(
            model="gpt-4.1",
            input=f"Summarize this event in under {max_chars} characters:\n{content}"
        )
        return response.output_text.strip()
    except Exception as e:
        print(f"[!] OpenAI summarization failed: {e}")
        return content[:max_chars] + "..." if len(content) > max_chars else content


def generate_ics_string(trace: dict) -> str:
    start_iso = trace["timestamp"]
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    duration = resolve_duration_minutes(trace)
    end_dt = start_dt + timedelta(minutes=duration)

    start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end = end_dt.strftime("%Y%m%dT%H%M%SZ")

    summary = trace.get("title") or generate_summary_title(trace["content"])

    chat_url = trace.get("chat_url", "https://chat.openai.com/share/example-link")
    full_description = f"{trace['content']}\nChat log: {chat_url}"

    summary = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    full_description = full_description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
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
    calendar_header = "BEGIN:VCALENDAR\rVERSION:2.0\rPRODID:-//CalendarMemorySystem//EN\r"
    calendar_footer = "\rEND:VCALENDAR"
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
    sample_trace = {
        "id": "test-001",
        "type": "observation",
        "timestamp": "2024-04-07T09:00:00Z",
        "content": "Temperature in incubator #3 drifted 1.5°C above target during morning run.",
        "task_id": "lab_ops",
        "location": "wetlab_sync"
    }

    ics_string = generate_ics_string(sample_trace)

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

    print("Generated ICS string:")
    print(ics_string)
    print("\nExpected format:")
    print(expected_format)

    # test_output = Path("test_output.ics")
    # write_consolidated_ics([ics_string], test_output)
    # print(f"\nWritten to {test_output} for comparison with gold standard")


if __name__ == "__main__":
    test_ics_format()
    input_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/raw")
    output_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/processed")
    convert_json_folder_to_ics(input_dir, output_dir)
