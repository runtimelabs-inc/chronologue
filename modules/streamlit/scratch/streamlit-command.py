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

# --- UID Generation ---
def generate_uid(title: str, date: str) -> str:
    base = re.sub(r'\W+', '_', title.lower())
    return f"{base}-{date}-{datetime.utcnow().strftime('%H%M%S')}"

# --- Date Correction (for hallucinated model outputs) ---
def correct_to_nearest_weekday(weekday_str: str) -> str:
    today = datetime.now().date()
    days = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6}
    target = days.get(weekday_str, today.weekday())
    delta = (target - today.weekday()) % 7
    return (today + timedelta(days=delta)).isoformat()

# --- Time Parsing ---
def parse_time_string(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%I:%M %p")
    except ValueError:
        return datetime.strptime(time_str.strip(), "%H:%M")

# --- ICS Importer ---
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

# --- Command Function Schema ---
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

# --- Apply Command to DataFrame ---
def apply_command(df, command):
    action = command["action"]
    event = command["event"]

    print(f"\n[DEBUG] Action: {action}")
    print(f"[DEBUG] Event: {json.dumps(event, indent=2)}")

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
        if uid and "UID" in df.columns:
            mask = df["UID"] == uid
        else:
            mask = df["Event Title"].str.lower() == event["title"].lower()

        if not mask.any():
            print("[WARN] No matching event found.")
            return df

        df.loc[mask, "Date"] = event["date"]
        df.loc[mask, "Day"] = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        df.loc[mask, "Start Time"] = parse_time_string(event["start_time"]).strftime("%I:%M %p").lstrip("0")
        df.loc[mask, "Start Time 24H"] = parse_time_string(event["start_time"]).strftime("%H:%M")
        df.loc[mask, "End Time"] = (parse_time_string(event["start_time"]) + timedelta(minutes=event["duration_minutes"])).strftime("%I:%M %p")
        df.loc[mask, "Duration (min)"] = event["duration_minutes"]
        df.loc[mask, "Location"] = event.get("location", "")
        df.loc[mask, "Notes"] = event.get("notes", "")

        return df

    elif action == "delete":
        return df[~((df["Event Title"].str.lower() == event["title"].lower()) & (df["Date"] == event["date"]))]

    return df

# --- Load Default Calendar ---
if "calendar_df" not in st.session_state:
    try:
        with open('modules/tempo/example_schedule.ics', 'r') as default_file:
            default_ics_text = default_file.read()
            st.session_state['calendar_df'] = import_ics_to_dataframe(default_ics_text)
    except FileNotFoundError:
        st.session_state['calendar_df'] = pd.DataFrame()
        st.error("Default calendar file not found.")

# --- UI Layout ---
st.title("Chronologue Tempo Token Scheduler")

uploaded_file = st.file_uploader("Upload your Calendar (.ics)", type=["ics"])
if uploaded_file:
    ics_text = uploaded_file.getvalue().decode()
    st.session_state['calendar_df'] = import_ics_to_dataframe(ics_text)

df = st.session_state['calendar_df']

if not df.empty and "UID" in df.columns:
    last_uid = df["UID"].iloc[-1]
    st.markdown(f"**Last Event UID Reference:** `{last_uid}`")
else:
    last_uid = None

st.subheader("Command Your Calendar")
user_command = st.text_input("Describe an action", "Change Haircut Appointment to Wednesday at 6 PM")

if st.button("Update Calendar"):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are modifying a structured calendar. "
                    f"The most recent event UID is: {last_uid}. "
                    "Always return an action and include event fields in structured format. "
                    "If editing an event, identify by UID if possible, otherwise by title."
                )
            },
            {"role": "user", "content": user_command}
        ]
        result = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            tools=[calendar_tool],
            tool_choice="auto"
        )

        tool_calls = result.choices[0].message.tool_calls
        if not tool_calls or not tool_calls[0].function.arguments:
            raise ValueError("No valid tool call received from model.")

        parsed = json.loads(tool_calls[0].function.arguments)
        df = apply_command(df.copy(), parsed)
        st.session_state['calendar_df'] = df
        st.success(f"✅ Calendar updated using '{parsed['action']}' command.")

    except Exception as e:
        st.error(f"⚠️ Failed to update calendar: {e}")
        print(f"[ERROR] {e}")

# --- Display Calendar Table ---
if not df.empty:
    display_cols = ["Date", "Day", "Start Time", "End Time", "Duration (min)", "Event Title", "Location", "Notes", "UID"]
    st.dataframe(df[display_cols], use_container_width=True)

    now_pt = datetime.now(ZoneInfo("America/Los_Angeles"))
    st.markdown(f"**Current Time (Pacific):** {now_pt.strftime('%A, %B %d %Y – %I:%M %p')} PT")
