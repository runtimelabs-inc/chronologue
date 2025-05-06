# streamlit run modules/tempo/streamlit-command.py
# Derek Rosenzweig, 2025-05-06 

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ics import Calendar
from openai import OpenAI
import re
from zoneinfo import ZoneInfo
import json

st.set_page_config(page_title="Chronologue Scheduler", layout="wide")
client = OpenAI()

# --- Tempo Token Generator ---
def generate_tempo_tokens(row):
    tokens = []
    start_dt = datetime.fromisoformat(row['Date'] + 'T' + row['Start Time 24H'])
    end_dt = start_dt + pd.to_timedelta(row['Duration (min)'], unit='m')
    duration = int((end_dt - start_dt).total_seconds() / 60)

    tokens.append(f"<tempo:{start_dt.strftime('%Y-%m-%dT%H:%MZ')}>")
    tokens.append(f"<tempo:{start_dt.strftime('%A')}>")

    if start_dt.hour < 12:
        tokens.append("<tempo:Morning>")
    elif start_dt.hour < 17:
        tokens.append("<tempo:Afternoon>")
    else:
        tokens.append("<tempo:Evening>")

    tokens.append(f"<tempo:duration-{duration}min>")
    if 'meeting' in row['Event Title'].lower():
        tokens.append("<tempo:meeting>")
    if 'urgent' in row['Notes'].lower():
        tokens.append("<tempo:urgent>")

    return tokens

# --- Utility: UID Generator ---
def generate_uid(title: str, date: str) -> str:
    base = re.sub(r'\W+', '_', title.lower())
    return f"{base}-{date}-{datetime.utcnow().strftime('%H%M%S')}"

# --- Utility: Correct Hallucinated Dates ---
def correct_to_nearest_weekday(weekday_str: str) -> str:
    today = datetime.now().date()
    days = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6}
    target = days.get(weekday_str, today.weekday())
    delta = (target - today.weekday()) % 7
    return (today + timedelta(days=delta)).isoformat()

# --- ICS Import Utility ---
def import_ics_to_dataframe(ics_text):
    events = []
    for block in ics_text.split("BEGIN:VEVENT")[1:]:
        lines = block.strip().splitlines()
        trace = {}
        for line in lines:
            if line.startswith("SUMMARY:"):
                trace["Event Title"] = line[8:].strip()
            elif line.startswith("DESCRIPTION:"):
                trace["Notes"] = line[12:].strip()
            elif line.startswith("DTSTART:"):
                start_dt = datetime.strptime(line[8:].strip(), "%Y%m%dT%H%M%SZ")
                trace["Date"] = start_dt.date().isoformat()
                trace["Start Time"] = start_dt.strftime("%I:%M %p").lstrip("0")
                trace["Start Time 24H"] = start_dt.strftime("%H:%M")
                trace["Day"] = start_dt.strftime("%A")
            elif line.startswith("DTEND:"):
                end_dt = datetime.strptime(line[6:].strip(), "%Y%m%dT%H%M%SZ")
                trace["End Time"] = end_dt.strftime("%I:%M %p").lstrip("0")
            elif line.startswith("UID:"):
                trace["UID"] = line[4:].strip()
            elif line.startswith("LOCATION:"):
                trace["Location"] = line[9:].strip()
        if "Date" in trace and "Start Time" in trace and "End Time" in trace:
            trace["Duration (min)"] = int((end_dt - start_dt).total_seconds() / 60)
        events.append(trace)
    return pd.DataFrame(events)

# --- Time Parsing Utility ---
def parse_time_string(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p")
    except ValueError:
        return datetime.strptime(time_str.strip(), "%H:%M")

# --- Function Schema for Command Execution ---
calendar_tool = {
    "type": "function",
    "function": {
        "name": "calendar_update",
        "description": "Modify calendar with add/edit/delete actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "edit", "delete"]},
                "event": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "location": {"type": "string"},
                        "notes": {"type": "string"}
                    },
                    "required": ["title", "date", "start_time", "duration_minutes"]
                }
            },
            "required": ["action", "event"]
        }
    }
}

# --- Apply Command to DataFrame ---
def apply_command(df, command):
    action = command["action"]
    event = command["event"]
    
    # Correct invalid date if model uses hallucinated 2023-12-13
    if "2023" in event["date"]:
        parsed_day = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        event["date"] = correct_to_nearest_weekday(parsed_day)

    if action == "add":
        start_dt = parse_time_string(event["start_time"])
        start_24h = start_dt.strftime("%H:%M")
        standard_time = start_dt.strftime("%I:%M %p").lstrip("0")
        day = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        end_dt = (start_dt + timedelta(minutes=event["duration_minutes"])).strftime("%I:%M %p")
        uid = generate_uid(event["title"], event["date"])
        new_row = {
            "Date": event["date"],
            "Day": day,
            "Start Time": standard_time,
            "Start Time 24H": start_24h,
            "End Time": end_dt,
            "Duration (min)": event["duration_minutes"],
            "Event Title": event["title"],
            "Location": event.get("location", ""),
            "Notes": event.get("notes", ""),
            "UID": uid
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    elif action == "delete":
        df = df[~((df["Event Title"].str.lower() == event["title"].lower()) & (df["Date"] == event["date"]))]

    elif action == "edit":
        mask = (df["Event Title"].str.lower() == event["title"].lower()) & (df["Date"] == event["date"])
        df.loc[mask, "Start Time"] = event["start_time"]
        df.loc[mask, "Duration (min)"] = event["duration_minutes"]
        df.loc[mask, "Location"] = event.get("location", "")
        df.loc[mask, "Notes"] = event.get("notes", "")
        df.loc[mask, "Start Time 24H"] = parse_time_string(event["start_time"]).strftime("%H:%M")
        df.loc[mask, "End Time"] = (parse_time_string(event["start_time"]) + timedelta(minutes=event["duration_minutes"])).strftime("%I:%M %p")

    # Sort the DataFrame by 'Date' to ensure chronological order
    df = df.sort_values(by='Date').reset_index(drop=True)
    return df

# --- Load Default ICS File ---
if "calendar_df" not in st.session_state:
    try:
        with open('modules/tempo/example_schedule.ics', 'r') as default_file:
            default_ics_text = default_file.read()
            st.session_state['calendar_df'] = import_ics_to_dataframe(default_ics_text)
    except FileNotFoundError:
        st.session_state['calendar_df'] = pd.DataFrame()
        st.error("Default calendar file not found.")

# --- UI Section ---
st.title("Chronologue Tempo Token Scheduler")

uploaded_file = st.file_uploader("Upload your Calendar (.ics)", type=["ics"])
if uploaded_file:
    ics_text = uploaded_file.getvalue().decode()
    st.session_state['calendar_df'] = import_ics_to_dataframe(ics_text)

df = st.session_state['calendar_df']

# Display current UID reference (most recent event)
if not df.empty and "UID" in df.columns:
    last_uid = df["UID"].iloc[-1]
    st.markdown(f"**Last Event UID Reference:** `{last_uid}`")
else:
    last_uid = None

# --- Command Input ---
st.subheader("Command Your Calendar")
user_command = st.text_input("Describe an action", "Add a 30-minute meeting with Jamie on Wednesday at 2 PM")

if st.button("Update Calendar"):
    try:
        messages = [
            {"role": "system", "content": f"You are modifying a calendar. The most recent event had UID: {last_uid}." if last_uid else "You are modifying a calendar."},
            {"role": "user", "content": user_command}
        ]
        result = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=[calendar_tool],
            tool_choice="auto"
        )
        tool_call = result.choices[0].message.tool_calls[0]
        parsed = json.loads(tool_call.function.arguments)

        before_count = len(df)
        updated_df = apply_command(df.copy(), parsed)
        after_count = len(updated_df)

        st.session_state['calendar_df'] = updated_df
        df = updated_df  # immediate UI reflection

        if parsed["action"] == "add":
            if after_count == before_count + 1:
                st.success(f"✅ Event added. Calendar now has {after_count} events.")
            else:
                st.warning("⚠️ Tried to add event, but row count did not increase.")
        else:
            st.success(f"✅ Calendar updated via '{parsed['action']}' command.")
    except Exception as e:
        st.error(f"⚠️ Failed to update calendar: {e}")

# --- Calendar Display ---
if not df.empty:
    desired_order = ["Date", "Day", "Start Time", "End Time", "Duration (min)", "Event Title", "Location", "Notes", "UID"]
    ordered_cols = [col for col in desired_order if col in df.columns]
    st.dataframe(df[ordered_cols], use_container_width=True)

    now_pt = datetime.now(ZoneInfo("America/Los_Angeles"))
    st.markdown(f"**Current Time (Pacific):** {now_pt.strftime('%A, %B %d %Y – %I:%M %p')} PT")

def update_event(df, title, new_date, new_time):
    # Locate the event
    mask = df['Event Title'].str.lower() == title.lower()
    
    # Update the event
    if mask.any():
        df.loc[mask, 'Date'] = new_date
        df.loc[mask, 'Start Time'] = new_time.strftime("%I:%M %p").lstrip("0")
        df.loc[mask, 'Start Time 24H'] = new_time.strftime("%H:%M")
        df.loc[mask, 'End Time'] = (new_time + timedelta(minutes=df.loc[mask, 'Duration (min)'].iloc[0])).strftime("%I:%M %p")
    
    # Sort the DataFrame
    df = df.sort_values(by='Date').reset_index(drop=True)
    
    return df

# Example usage
new_date = "2025-05-13"  # Calculate this based on "next Tuesday"
new_time = datetime.strptime("6:00 PM", "%I:%M %p")
df = update_event(df, "haircut appointment", new_date, new_time)
st.session_state['calendar_df'] = df
st.dataframe(df)
