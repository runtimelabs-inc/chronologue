# python modules/calendar_io/sync_google_ics.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pathlib import Path
from datetime import datetime
import pytz
import json
import re

from schema import validate_memory_trace 

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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

def event_to_trace(event):
    trace = {
        "type": "calendar_event",
        "timestamp": event["start"]["dateTime"],
        "end": event["end"]["dateTime"],
        "title": event.get("summary", "Untitled Event"),
        "content": event.get("description", ""),
        "id": event.get("id"),
        "location": event.get("location", "")
    }

    try:
        start = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(trace["end"].replace("Z", "+00:00"))
        trace["duration_minutes"] = int((end - start).total_seconds() // 60)
    except Exception as e:
        print(f"[!] Failed to parse duration: {e}")

    return {k: v for k, v in trace.items() if v}

def fetch_and_export_events(service, output_path: Path, calendar_id="primary"):
    print("→ Fetching events from Google Calendar...")

    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId=calendar_id, timeMin=now,
        maxResults=100, singleEvents=True, orderBy="startTime").execute()

    events = events_result.get("items", [])
    traces = []

    for event in events:
        trace = event_to_trace(event)
        if validate_memory_trace(trace):
            traces.append(trace)
            print(f"[✓] Parsed: {trace.get('title')}")
        else:
            print(f"[!] Invalid event skipped: {event.get('id')}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"memory": traces}, f, indent=4)

    print(f"\n→ Saved {len(traces)} trace(s) to {output_path}")

if __name__ == "__main__":
    output_path = Path("data/calendar/processed/google_events.json")
    service = authenticate_google()
    fetch_and_export_events(service, output_path)
