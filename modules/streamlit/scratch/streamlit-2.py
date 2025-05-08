# streamlit run modules/streamlit/scratch/streamlit-2.py

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

# --- UID Generator ---
def generate_uid(title: str, date: str) -> str:
    base = re.sub(r'\W+', '_', title.lower())
    return f"{base}-{date}-{datetime.utcnow().strftime('%H%M%S')}"

# --- Weekday Correction (fallback for bad date) ---
def correct_to_nearest_weekday(weekday_str: str) -> str:
    today = datetime.now().date()
    weekday_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
    target = weekday_map.get(weekday_str, today.weekday())
    delta = (target - today.weekday()) % 7
    return (today + timedelta(days=delta)).isoformat()

# --- Time Parser ---
def parse_time_string(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p")
    except ValueError:
        return datetime.strptime(time_str.strip(), "%H:%M")

# --- ICS Parser ---
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

# --- Tool Definition ---
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
                        "uid": {"type": "string"},
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

# --- Apply Command ---
def apply_command(df, command):
    action = command["action"]
    event = command["event"]

    print(f"[DEBUG] Action: {action}")
    print(f"[DEBUG] Event: {json.dumps(event, indent=2)}")

    # Auto-correct invalid old dates
    if "2023" in event["date"]:
        parsed_day = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        event["date"] = correct_to_nearest_weekday(parsed_day)

    if action == "add":
        start_dt = parse_time_string(event["start_time"])
        new_row = {
            "Date": event["date"],
            "Day": datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A"),
            "Start Time": start_dt.strftime("%I:%M %p").lstrip("0"),
            "Start Time 24H": start_dt.strftime("%H:%M"),
            "End Time": (start_dt + timedelta(minutes=event["duration_minutes"])).strftime("%I:%M %p"),
            "Duration (min)": event["duration_minutes"],
            "Event Title": event["title"],
            "Location": event.get("location", ""),
            "Notes": event.get("notes", ""),
            "UID": generate_uid(event["title"], event["date"])
        }
        return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    elif action == "edit":
        uid = event.get("uid")
        mask = df["UID"] == uid if uid else df["Event Title"].str.lower() == event["title"].lower()

        if not mask.any():
            print("[WARN] No matching event found.")
            return df

        start_dt = parse_time_string(event["start_time"])
        df.loc[mask, "Date"] = event["date"]
        df.loc[mask, "Day"] = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        df.loc[mask, "Start Time"] = start_dt.strftime("%I:%M %p").lstrip("0")
        df.loc[mask, "Start Time 24H"] = start_dt.strftime("%H:%M")
        df.loc[mask, "End Time"] = (start_dt + timedelta(minutes=event["duration_minutes"])).strftime("%I:%M %p")
        df.loc[mask, "Duration (min)"] = event["duration_minutes"]
        df.loc[mask, "Location"] = event.get("location", "")
        df.loc[mask, "Notes"] = event.get("notes", "")
        return df

    elif action == "delete":
        return df[~((df["Event Title"].str.lower() == event["title"].lower()) & (df["Date"] == event["date"]))]

    return df

# --- Load Calendar ---
if "calendar_df" not in st.session_state:
    try:
        with open('modules/tempo/example_schedule.ics', 'r') as f:
            st.session_state['calendar_df'] = import_ics_to_dataframe(f.read())
    except FileNotFoundError:
        st.session_state['calendar_df'] = pd.DataFrame()
        st.error("Default calendar file not found.")

# --- UI ---
st.title("Chronologue Tempo Scheduler")

uploaded_file = st.file_uploader("Upload a calendar (.ics)", type=["ics"])
if uploaded_file:
    st.session_state['calendar_df'] = import_ics_to_dataframe(uploaded_file.getvalue().decode())

df = st.session_state['calendar_df']
last_uid = df["UID"].iloc[-1] if not df.empty and "UID" in df.columns else None

st.subheader("Command Input")
example = "Add a yoga class on Friday at 9 AM for 60 minutes."
user_command = st.text_input("Enter a calendar command:", example)

if st.button("Update Calendar"):
    try:
        messages = [
            {"role": "system", "content": (
                f"You are editing a structured calendar. Most recent UID is: {last_uid}. "
                "Output an action with an event object containing all necessary fields."
            )},
            {"role": "user", "content": user_command}
        ]
        result = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            tools=[calendar_tool],
            tool_choice="auto"
        )
        parsed = json.loads(result.choices[0].message.tool_calls[0].function.arguments)
        df = apply_command(df.copy(), parsed)
        st.session_state['calendar_df'] = df
        st.success(f"✅ Updated calendar with '{parsed['action']}' command.")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        print(f"[ERROR] {e}")

# --- Display Updated Schedule ---
if not df.empty:
    display_cols = ["Date", "Day", "Start Time", "End Time", "Duration (min)", "Event Title", "Location", "Notes", "UID"]
    st.dataframe(df[display_cols], use_container_width=True)
    now = datetime.now(ZoneInfo("America/Los_Angeles"))
    st.caption(f"📍 Current Time (PT): {now.strftime('%A, %B %d %Y – %I:%M %p')}")

