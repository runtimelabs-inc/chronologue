# streamlit run modules/streamlit/streamlit_tempo.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from openai import OpenAI

st.set_page_config(page_title="Chronologue Tempo Assistant", page_icon="🧠", layout="wide")
client = OpenAI()

# --- Tempo Token Generator ---
def generate_tempo_tokens_from_row(row):
    tokens = []
    start_dt = datetime.fromisoformat(row["Date"] + "T" + row["Start Time"])
    duration = int(row["Duration (min)"])

    tokens.append(f"<tempo:{start_dt.strftime('%Y-%m-%dT%H:%MZ')}>")
    tokens.append(f"<tempo:{start_dt.strftime('%A')}>")

    hour = start_dt.hour
    if hour < 12:
        tokens.append("<tempo:Morning>")
    elif hour < 17:
        tokens.append("<tempo:Afternoon>")
    else:
        tokens.append("<tempo:Evening>")

    tokens.append(f"<tempo:duration-{duration}min>")

    if "meeting" in row["Event Title"].lower():
        tokens.append("<tempo:meeting>")
    return tokens

# --- ICS Parser ---
def parse_ics_datetime(dt_str):
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def import_ics_content(ics_text):
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
                trace["Date"] = start_dt.split("T")[0]
                trace["Start Time"] = start_dt.split("T")[1].replace("Z", "")
            elif line.startswith("DTEND:"):
                end_dt = parse_ics_datetime(line[6:].strip())
                trace["End Time"] = end_dt.split("T")[1].replace("Z", "")
            elif line.startswith("UID:"):
                trace["UID"] = line[4:].strip()
            elif line.startswith("LOCATION:"):
                trace["Location"] = line[9:].strip()
        if "Date" in trace and "Start Time" in trace and "End Time" in trace:
            start_dt_obj = datetime.fromisoformat(trace["Date"] + "T" + trace["Start Time"])
            end_dt_obj = datetime.fromisoformat(trace["Date"] + "T" + trace["End Time"])
            trace["Duration (min)"] = int((end_dt_obj - start_dt_obj).total_seconds() / 60)
        events.append(trace)
    return pd.DataFrame(events)

# --- Context Builder ---
def build_context_prompt(df, target_date):
    context = []
    for _, row in df.iterrows():
        if row["Date"] == target_date:
            tokens = generate_tempo_tokens_from_row(row)
            context.append(f"- {row['Event Title']} at {row['Start Time']} {' '.join(tokens)}")
    return "\n".join(context)

# --- Streamlit App ---
st.title("🧠 Chronologue Tempo Assistant")

uploaded_file = st.file_uploader("Upload your Calendar (.ics)", type=["ics"])

if uploaded_file:
    ics_text = uploaded_file.getvalue().decode()
    df = import_ics_content(ics_text)
    st.session_state["calendar_df"] = df

    st.subheader("Your Schedule")
    st.dataframe(df, use_container_width=True)

    st.subheader("Ask a Question About Your Schedule")
    nl_query = st.text_input("Enter a prompt", "What time should I schedule a haircut next Tuesday?")

    if st.button("Ask Chronologue"):
        try:
            target_date = "2025-05-13"
            context_prompt = build_context_prompt(st.session_state["calendar_df"], target_date)
            full_prompt = (
                "You are a calendar-aware assistant. Based on the following schedule:\n"
                + context_prompt +
                "\n\nThe barbershop is open from 10:00 AM to 6:30 PM.\n"
                + f"\nUser query: {nl_query}"
            )
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": full_prompt},
                        {"role": "user", "content": nl_query}
                    ]
                )
                reply = response.choices[0].message.content.strip()
                st.success("Response:")
                st.markdown(reply)
        except Exception as e:
            st.error(f"⚠️ Failed to process query: {e}")
