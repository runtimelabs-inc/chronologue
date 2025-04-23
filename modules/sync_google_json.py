from ics import Calendar
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

from schema import validate_memory_trace

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    token_path = Path("./calendar/token.json")
    creds_path = Path("./calendar/credentials.json")

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def generate_uid(title: str, date_str: str) -> str:
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

    summary = trace["content"][:40] + ("..." if len(trace["content"]) > 40 else "")
    chat_url = trace.get("chat_url", "https://chat.openai.com/share/example-link")
    full_description = f"{trace['content']}\\nChat log: {chat_url}"

    summary = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    full_description = full_description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

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

def parse_ics_and_sync(ics_path: Path, service):
    with open(ics_path, "r") as f:
        calendar = Calendar(f.read())

    synced = 0
    for event in calendar.events:
        try:
            payload = {
                "summary": event.name or "Untitled Event",
                "description": event.description or "",
                "start": {
                    "dateTime": event.begin.astimezone(pytz.UTC).isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": event.end.astimezone(pytz.UTC).isoformat(),
                    "timeZone": "UTC"
                }
            }
            service.events().insert(calendarId="primary", body=payload).execute()
            print(f"[✓] Synced: {payload['summary']}")
            synced += 1
        except Exception as e:
            print(f"[!] Failed to sync event: {e}")

    print(f"\n[✓] {synced} events synced from {ics_path.name}")

if __name__ == "__main__":
    input_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/raw")
    output_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/processed")
    
    # Convert JSON to ICS
    convert_json_folder_to_ics(input_dir, output_dir)
    
    # Authenticate with Google Calendar
    service = authenticate_google()
    
    # Sync each ICS file with Google Calendar
    for ics_file in output_dir.glob("*.ics"):
        parse_ics_and_sync(ics_file, service)