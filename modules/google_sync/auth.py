from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google(token_path="calendar/token.json", creds_path="calendar/credentials.json"):
    token_path = Path(token_path)
    creds_path = Path(creds_path)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)
