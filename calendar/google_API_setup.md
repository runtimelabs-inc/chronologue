### Setting Up Google Calendar API Credentials 

Here is a sguide to walk through creating OAuth 2.0 credentials to enable access to the Google Calendar API for the script `modules/sync_google.py`. 


**Step 1: Create a Google Cloud Project**

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Click the project dropdown in the top left. 
3. Select "New Project" and give it a name. 
4. Click "Create" and wait for the project to initialize. 


**Step 2: Enable the Calendar API**

1. In the Google Cloud Console, select your new project. 
2. Navigate to: APIs and Services --> Library 
3. Search for "Google Calendar API" 
4. Click "Enable" 

**Step 3: Create OAuth 2.0 Credentials**

1. Go to APIs & Services --> Credentials 
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted to configure the consent screen:

- Choose "External" and click "Create"

- Fill in the App name, User support email, and Developer contact information

- Click "Save and Continue" through all other steps (you can skip scopes and test users)

4. On the "Create OAuth client ID" page:

- Application type: Desktop App

- Name: Calendar Sync Local

- Click "Create"


**Step 4: Download Your credentials.json File** 

1. After creation, a dialog will show your new OAuth client.

2. Click "Download JSON" and save it to:

`calendar/credentials.json`

3. Make sure file is included in .gitignore to avoid committing it to version control.

**Step 5: Run the Script** 

1. Once set up, test the OAuth flow:

`python sync_google.py`

- A browser window will open to authenticate your Google account.

- After you authorize access, a file token.json will be created automatically.

- Subsequent runs will reuse this token unless revoked or expired.



