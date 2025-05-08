# streamlit run modules/streamlit/streamlit-demo.py

import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar
from openai import OpenAI
import json
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Chronologue Tempo Token Scheduler", layout="wide")
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
    if 'urgent' in row.get('Notes', '').lower():
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

# --- JSON Parser ---
def import_json_to_dataframe(json_text):
    raw = json.loads(json_text)
    events = []
    for item in raw:
        start_dt = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        events.append({
            "Date": start_dt.date().isoformat(),
            "Day": start_dt.strftime("%A"),
            "Start Time": start_dt.strftime("%I:%M %p").lstrip("0"),
            "Start Time 24H": start_dt.strftime("%H:%M"),
            "Start ISO": start_dt.isoformat(),
            "End Time": (start_dt + pd.to_timedelta(item["duration_minutes"], unit='m')).strftime("%I:%M %p").lstrip("0"),
            "Duration (min)": item["duration_minutes"],
            "Event Title": item["title"],
            "Notes": item.get("content", ""),
            "Location": item.get("location", "")
        })
    return pd.DataFrame(events)

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

# --- Load Default File (ICS or JSON) ---
default_df = pd.DataFrame()
try:
    with open('modules/streamlit/data/example_schedule.ics', 'r') as f_ics:
        default_df = import_ics_to_dataframe(f_ics.read())
except FileNotFoundError:
    try:
        with open('modules/streamlit/data/example_schedule.json', 'r') as f_json:
            default_df = import_json_to_dataframe(f_json.read())
    except FileNotFoundError:
        st.warning("No default file found in data/")

st.session_state['calendar_df'] = default_df

# --- UI ---
st.title("Chronologue Tempo Token Scheduler")

uploaded_file = st.file_uploader(
    "Upload your Calendar (.ics or .json)",
    type=["ics", "json"],
    help="Upload your .ics calendar or .json memory trace."
)

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]
    text = uploaded_file.getvalue().decode()
    if file_type == "ics":
        df = import_ics_to_dataframe(text)
    elif file_type == "json":
        df = import_json_to_dataframe(text)
    else:
        st.error("Unsupported file format.")
        df = pd.DataFrame()
    st.session_state['calendar_df'] = df
else:
    df = st.session_state.get('calendar_df', pd.DataFrame())

if not df.empty:
    desired_order = [
        "Date", "Day", "Start Time", "End Time", "Duration (min)",
        "Event Title", "Location", "Notes"
    ]
    display_cols = [col for col in desired_order if col in df.columns]
    st.markdown("### Schedule Table")
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
                    ]
                )
                st.success("Response:")
                st.markdown(res.choices[0].message.content.strip())
        except Exception as e:
            st.error(f"Failed to process prompt: {e}")
