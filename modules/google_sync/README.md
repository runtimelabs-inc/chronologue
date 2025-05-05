### Google Calendar Sync 


This module enables syncing memory traces (.json) or calendar events (.ics) directly to Google Calendar using the Google Calendar API and OAuth 2.0.


1. Setup

Ensure the following files exist:

- calendar/credentials.json – your OAuth client credentials from the Google Cloud Console

- calendar/token.json – generated automatically on first authentication


2. Running the Sync 

```bash
python modules/google_sync/sync_google.py --file <path_to_file>
```

Generate Calendar Example: 

```bash 
python modules/google_sync/sync_google.py --file data/conversation/raw/lab_manager_4-12.json
```

Retrieve Calendar Example: 

```bash
python modules/google_sync/sync_google.py --file data/conversation/processed/lab_manager_4-12.ics
```


Supported input formats:

- .json – memory trace JSON file with a top-level "memory" key

- .ics – iCalendar (.ics) file with valid VEVENT entries

3. Module Structure

google_sync/

auth.py – Google OAuth authentication

json_sync.py – Sync logic for JSON files

ics_sync.py – Sync logic for ICS files

event_utils.py – Utility for formatting memory traces as calendar events

sync_google.py – CLI entrypoint for syncing

4. OAuth Notes

If you encounter a 403 access_denied error, make sure:

You're listed as a test user in your OAuth consent screen

Your app is in testing mode (or has completed brand verification)

You’ve enabled the Google Calendar API in your project