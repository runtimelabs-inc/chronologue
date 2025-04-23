from mcp.server.fastmcp import FastMCP
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# === Configuration ===
SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_PATH = Path("data/conversation/raw")
GOOGLE_CALENDAR_ID = "primary"

mcp = FastMCP("GoogleCalendarMCP")

# === Auth Setup ===
def authenticate_google():
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", "calendar/token.json"))
    creds_path = Path(os.getenv("GOOGLE_OAUTH_PATH", "calendar/credentials.json"))

    if not token_path.exists():
        raise RuntimeError("Google Calendar not authenticated. Run `auth_google_calendar.py` first.")

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("calendar", "v3", credentials=creds)

# === ICS Utility ===
def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("\u00b0", "").replace("#", "")
    return f"{base}-{date_str}@memorysystem.ai"

def generate_ics_string(trace: dict) -> str:
    start_dt = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=15)

    start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end = end_dt.strftime("%Y%m%dT%H%M%SZ")
    summary = trace["content"][:40] + ("..." if len(trace["content"]) > 40 else "")
    description = trace.get("content", "")
    chat_url = trace.get("chat_url", "https://chat.openai.com/share/example-link")
    full_description = f"{description}\\nChat log: {chat_url}"

    summary = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    full_description = full_description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    uid = trace.get("linked_event_uid") or generate_uid(trace["task_id"], start[:8])
    location = trace.get("location", "")
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{start}
DTEND:{end}
SUMMARY:{summary}
DESCRIPTION:{full_description}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT"""

# === Tools ===
@mcp.tool()
def convert_trace_to_ics(trace: dict) -> str:
    return generate_ics_string(trace)

@mcp.tool()
def sync_traces_to_google(traces: list[dict]) -> str:
    service = authenticate_google()
    synced = 0

    for trace in traces:
        try:
            start_dt = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(minutes=15)

            payload = {
                "summary": trace["content"][:40],
                "description": trace.get("content", ""),
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
                "location": trace.get("location", ""),
            }

            service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=payload).execute()
            synced += 1
        except Exception as e:
            print(f"[!] Failed to sync event: {e}")

    return f"Synced {synced} events to Google Calendar"

@mcp.tool()
def load_memory_file(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(path) as f:
        data = json.load(f)
    return data.get("memory", [])

# === Resources ===
@mcp.resource("calendar://pending_goals")
def pending_goals() -> list[dict]:
    traces = []
    for json_file in BASE_PATH.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        for trace in data.get("memory", []):
            if trace.get("type") == "goal" and trace.get("completion_status") == "pending":
                traces.append(trace)
    return traces

@mcp.resource("calendar://week_summary/{iso_week}")
def week_summary(iso_week: str) -> dict:
    year, week = iso_week.split("-W")
    traces = []
    for json_file in BASE_PATH.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        for trace in data.get("memory", []):
            if "timestamp" in trace:
                dt = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
                if dt.isocalendar().year == int(year) and dt.isocalendar().week == int(week):
                    traces.append(trace)
    return {"iso_week": iso_week, "count": len(traces), "traces": traces}

@mcp.resource("calendar://trace_by_id/{trace_id}")
def trace_by_id(trace_id: str) -> dict:
    for json_file in BASE_PATH.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        for trace in data.get("memory", []):
            if trace.get("id") == trace_id:
                return trace
    raise ValueError(f"No trace found with id: {trace_id}")