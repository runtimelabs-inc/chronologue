# streamlit run modules/tempo/streamlit-demo.py

import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar
from openai import OpenAI
import re
import json
from zoneinfo import ZoneInfo

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

# --- ICS Parser ---
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

# --- Prompt Constructor ---
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

# --- Tool Calling Spec ---
calendar_tool = {
    "type": "function",
    "function": {
        "name": "calendar_update",
        "description": "Add, edit, or delete a calendar event.",
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

    def parse_start(dt_str, minutes):
        start = datetime.strptime(dt_str, "%H:%M")
        end = (start + pd.to_timedelta(minutes, unit='m')).strftime("%I:%M %p").lstrip("0")
        return start, end

    if action == "add":
        start_dt, end_time = parse_start(event["start_time"], event["duration_minutes"])
        new_row = {
            "Date": event["date"],
            "Day": datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A"),
            "Start Time": start_dt.strftime("%I:%M %p").lstrip("0"),
            "Start Time 24H": start_dt.strftime("%H:%M"),
            "End Time": end_time,
            "Duration (min)": event["duration_minutes"],
            "Event Title": event["title"],
            "Location": event.get("location", ""),
            "Notes": event.get("notes", "")
        }
        return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    elif action == "edit":
        mask = df["Event Title"].str.lower() == event["title"].lower()
        if not mask.any():
            return df
        start_dt, end_time = parse_start(event["start_time"], event["duration_minutes"])
        df.loc[mask, "Date"] = event["date"]
        df.loc[mask, "Day"] = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A")
        df.loc[mask, "Start Time"] = start_dt.strftime("%I:%M %p").lstrip("0")
        df.loc[mask, "Start Time 24H"] = start_dt.strftime("%H:%M")
        df.loc[mask, "End Time"] = end_time
        df.loc[mask, "Duration (min)"] = event["duration_minutes"]
        df.loc[mask, "Location"] = event.get("location", "")
        df.loc[mask, "Notes"] = event.get("notes", "")
        return df

    elif action == "delete":
        mask = (df["Event Title"].str.lower() == event["title"].lower()) & (df["Date"] == event["date"])
        return df[~mask]

    return df

# --- Load Default ICS File ---
try:
    with open('modules/tempo/example_schedule.ics', 'r') as default_file:
        default_ics_text = default_file.read()
        default_df = import_ics_to_dataframe(default_ics_text)
        st.session_state['calendar_df'] = default_df
except FileNotFoundError:
    st.error('Default calendar file not found.')

# --- UI ---
st.title("Chronologue Tempo Token Scheduler")

uploaded_file = st.file_uploader("Upload your Calendar (.ics)", type=["ics"])
if uploaded_file:
    ics_text = uploaded_file.getvalue().decode()
    df = import_ics_to_dataframe(ics_text)
    st.session_state['calendar_df'] = df
else:
    df = st.session_state.get('calendar_df', pd.DataFrame())

if not df.empty:
    display_cols = ["Date", "Day", "Start Time", "End Time", "Duration (min)", "Event Title", "Location", "Notes"]
    st.dataframe(df[display_cols], use_container_width=True)

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
    default_query = prompt_options[selected_prompt]
    user_query = st.text_input("Prompt", value=default_query)

    if st.button("Run Prompt"):
        try:
            grounded_prompt = build_prompt(df, user_query)
            with st.spinner("Thinking..."):
                res = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": grounded_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    tools=[calendar_tool],
                    tool_choice="auto"
                )

                message = res.choices[0].message
                tool_calls = message.tool_calls

                if message.content:
                    st.markdown("### 🧠 Model Interpretation")
                    st.markdown(message.content.strip())

                if tool_calls and tool_calls[0].function.arguments:
                    parsed = json.loads(tool_calls[0].function.arguments)
                    df = apply_command(df.copy(), parsed)

                    # Sort chronologically by date and time
                    df["Sort Key"] = df["Date"] + " " + df["Start Time 24H"]
                    df = df.sort_values("Sort Key").drop(columns=["Sort Key"]).reset_index(drop=True)

                    st.session_state['calendar_df'] = df
                    st.success(f"✅ Calendar updated using action: `{parsed['action']}`")
                else:
                    st.info("No structured update requested by the model.")
        except Exception as e:
            st.error(f"⚠️ Failed to process prompt: {e}")
