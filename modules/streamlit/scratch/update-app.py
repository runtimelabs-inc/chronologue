# streamlit run modules/tempo/update-app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ics import Calendar
from openai import OpenAI
from zoneinfo import ZoneInfo
import json
import re

st.set_page_config(page_title="Chronologue Scheduler", layout="wide")
client = OpenAI()

# --- Helper Functions ---
def generate_uid(title: str, date_str: str) -> str:
    base = re.sub(r'\W+', '_', title.lower())
    return f"{base}-{date_str}"

def parse_time_string(time_str: str) -> datetime:
    return datetime.strptime(time_str.strip(), "%H:%M")

def correct_to_nearest_weekday(target_day: str) -> str:
    today = datetime.today()
    for i in range(7):
        candidate = today + timedelta(days=i)
        if candidate.strftime("%A") == target_day:
            return candidate.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

def parse_ics_datetime(dt_str):
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ")

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
                start_dt = parse_ics_datetime(line[8:].strip())
                trace["Date"] = start_dt.date().isoformat()
                trace["Start Time"] = start_dt.strftime("%I:%M %p").lstrip("0")
                trace["Start Time 24H"] = start_dt.strftime("%H:%M")
                trace["Day"] = start_dt.strftime("%A")
                trace["Start ISO"] = start_dt.isoformat()
            elif line.startswith("DTEND:"):
                end_dt = parse_ics_datetime(line[6:].strip())
                trace["End Time"] = end_dt.strftime("%I:%M %p").lstrip("0")
            elif line.startswith("UID:"):
                trace["UID"] = line[4:].strip()
            elif line.startswith("LOCATION:"):
                trace["Location"] = line[9:].strip()
        if "Date" in trace and "Start Time" in trace and "End Time" in trace:
            trace['Duration (min)'] = int((end_dt - start_dt).total_seconds() / 60)
        events.append(trace)
    df = pd.DataFrame(events)
    return df.drop(columns=['UID']) if 'UID' in df.columns else df

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

def build_prompt(df, user_query):
    now_utc = datetime.utcnow()
    now_token = f"<tempo:now-{now_utc.strftime('%Y-%m-%dT%H:%MZ')}>"
    current_day = now_utc.strftime("%A")
    prompt = f"You are a calendar-aware assistant. Current time is {now_token} ({current_day}). Based on the user's schedule:\n"
    for _, row in df.iterrows():
        tokens = generate_tempo_tokens(row)
        prompt += f"- {row['Event Title']} at {row['Start Time']}. {' '.join(tokens)}\n"
    prompt += f"\nUser prompt: {user_query}\n"
    return prompt

# --- Tool Call Logic ---
calendar_tool = {
    "type": "function",
    "function": {
        "name": "apply_calendar_command",
        "description": "Modifies the calendar by adding, editing, or deleting events.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "edit", "delete"]
                },
                "event": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string", "format": "date"},
                        "start_time": {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "location": {"type": "string"},
                        "notes": {"type": "string"},
                        "uid": {"type": "string"}
                    },
                    "required": ["title", "date", "start_time", "duration_minutes"]
                }
            },
            "required": ["action", "event"]
        }
    }
}

def apply_command(df, command):
    action = command["action"]
    event = command["event"]

    print(f"[DEBUG] Action: {action}")
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

# --- Streamlit UI ---
st.title("Chronologue Tempo Token Scheduler")

try:
    with open('modules/tempo/example_schedule.ics', 'r') as default_file:
        default_ics_text = default_file.read()
        default_df = import_ics_to_dataframe(default_ics_text)
        st.session_state['calendar_df'] = default_df
except FileNotFoundError:
    st.error('Default calendar file not found.')

uploaded_file = st.file_uploader("Upload your Calendar (.ics)", type=["ics"])

if uploaded_file:
    ics_text = uploaded_file.getvalue().decode()
    df = import_ics_to_dataframe(ics_text)
    st.session_state['calendar_df'] = df
else:
    df = st.session_state.get('calendar_df', pd.DataFrame())

if not df.empty:
    desired_order = ["Date", "Day", "Start Time", "End Time", "Duration (min)", "Event Title", "Location", "Notes"]
    ordered_cols = [col for col in desired_order if col in df.columns]
    st.dataframe(df[ordered_cols], use_container_width=True)

    now_pt = datetime.now(ZoneInfo("America/Los_Angeles"))
    st.markdown(f"**Current Time (Pacific):** {now_pt.strftime('%A, %B %d %Y – %I:%M %p')} PT")

    st.subheader("Select a Demo Prompt Type")
    prompt_options = {
        "Calendar Query": "What events do I have on Thursday?",
        "Summarization": "Summarize my upcoming week.",
        "Add Event": "Schedule a 30-minute meeting with Jamie on Wednesday at 2 PM.",
        "Edit Event": "Move my Thursday client call to 4 PM.",
        "Remove Event": "Cancel the lab meeting scheduled for Wednesday.",
        "Conflict Check": "Can I add a meeting at 3 PM on Thursday?",
        "Availability": "What’s my next free hour this afternoon?"
    }
    selected_prompt = st.selectbox("Choose a test case", list(prompt_options.keys()))
    user_query = st.text_input("Prompt", value=prompt_options[selected_prompt])

    if st.button("Run Prompt"):
        try:
            grounded_prompt = build_prompt(df, user_query)
            with st.spinner("Thinking..."):
                res = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": grounded_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    tools=[calendar_tool],
                    tool_choice="auto"
                )
                message = res.choices[0].message
                if message.tool_calls:
                    command = json.loads(message.tool_calls[0].function.arguments)
                    df = apply_command(df, command)
                    st.session_state['calendar_df'] = df
                    st.success("Calendar updated with tool call.")
                else:
                    st.success("Response:")
                    st.markdown(message.content.strip())
        except Exception as e:
            st.error(f"Failed to process prompt: {e}")
