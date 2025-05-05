from ics import Calendar
from datetime import datetime
import pytz

def sync_ics_file(service, ics_path):
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
