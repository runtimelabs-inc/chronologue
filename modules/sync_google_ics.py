from ics import Calendar
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from pathlib import Path
from datetime import datetime
import pytz

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
    ics_path = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/processed/lab_manager_4-12.ics")
    service = authenticate_google()
    parse_ics_and_sync(ics_path, service)
