# sync_google.py

# Sync memory traces to Google Calendar 

# Authenticate with Google Calendar API 
# Demo Account: calendar.demo.365@gmail.com
# Reach out and send message if you have any questions or feedback on the demo and account

# Using OAuth 2.0 to Access Google APIs 
# https://developers.google.com/identity/protocols/oauth2
# https://datatracker.ietf.org/doc/html/rfc6749

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from schema import validate_memory_trace

# If modifying these SCOPES, delete the token.json file to reauthorize
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    creds = None
    token_path = Path("./calendar/token.json")
    creds_path = Path("./calendar/credentials.json")  # downloaded from Google Cloud Console

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def memory_trace_to_event(trace):
    start = trace["timestamp"]
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=30)
    end = end_dt.isoformat() + "Z"

    summary = f"[{trace['type'].upper()}] {trace['content'][:40]}..."
    description = trace["content"]

    meta = []
    if "task_id" in trace:
        meta.append(f"Task: {trace['task_id']}")
    if "importance" in trace:
        meta.append(f"Importance: {trace['importance']}")
    if "completion_status" in trace:
        meta.append(f"Status: {trace['completion_status']}")
    if "source" in trace:
        meta.append(f"Source: {trace['source']}")

    full_description = description + ("\n\n" + "\n".join(meta) if meta else "")

    return {
        "id": trace.get("linked_event_uid", f"{trace['id']}@memorysystem.ai").replace("@", "_"),  # Google API-safe UID
        "summary": summary,
        "description": full_description,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"},
    }

def sync_memory_file_to_google_calendar(service, memory_json_path: Path):
    with open(memory_json_path) as f:
        session = json.load(f)

    traces = session.get("memory", [])
    synced = 0

    for trace in traces:
        if validate_memory_trace(trace):
            event = memory_trace_to_event(trace)
            try:
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"[✓] Synced: {event['summary']}")
                synced += 1
            except Exception as e:
                print(f"[!] Failed to sync {trace.get('id')}: {e}")

    print(f"\n[✓] {synced} events synced from {memory_json_path.name}")

if __name__ == "__main__":
    service = authenticate_google()
    memory_path = Path("data/conversation/raw/lab_manager_4-12.json")
    sync_memory_file_to_google_calendar(service, memory_path)



# https://developers.google.com/identity/protocols/oauth2


# When running this script you may run into an error regaring the Google verification process 

# cursor-calendar has not completed the Google verification process. The app is currently being tested, and can only be accessed by developer-approved testers. If you think you should have access, contact the developer.
# If you are a developer of cursor-calendar, see error details.
# Error 403: access_denied

# Submit for Brand Verification 
# https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification?hl=en#projects-used-in-dev-test-stage

# The OAuth consent screen brand verification process typically takes 2-3 business days after you submit for verification.

# OAuth App Verification
# https://support.google.com/cloud/answer/13463073?visit_id=638809327007167460-1341605746&rd=1#verification-types

# Submit for Verification 
# https://support.google.com/cloud/answer/13461325?sjid=10551380289315301369-NC

# Enable Calendar API 
# https://console.cloud.google.com/marketplace/product/google/calendar-json.googleapis.com?project=memorysystem-ai

# gcloud services enable calendar-json.googleapis.com

