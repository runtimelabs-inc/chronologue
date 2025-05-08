# modules/streamlit_chat_editor.py

# streamlit run modules/streamlit/streamlit_chat_editor.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import json
from openai import OpenAI

st.set_page_config(page_title="Chronologue Command Agent", layout="wide")

# --- Initialize OpenAI Client ---
client = OpenAI()

# --- Helper Functions ---

def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("°", "").replace("#", "")
    return f"{base}-{date_str}@chronologue.ai"

def parse_ics_datetime(dt_str: str) -> str:
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def import_ics_content(ics_text: str) -> pd.DataFrame:
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

def generate_ics_content(df: pd.DataFrame) -> str:
    events = []
    for _, row in df.iterrows():
        date = row["Date"]
        start_time = row["Start Time"]
        start_dt = datetime.strptime(f"{date}T{start_time}", "%Y-%m-%dT%H:%M")
        end_dt = start_dt + timedelta(minutes=int(row["Duration (min)"]))

        uid = row.get("UID", "")
        if not uid:
            uid = generate_uid(row["Event Title"], date.replace("-", ""))

        events.append(f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{start_dt.strftime("%Y%m%dT%H%M%SZ")}
DTEND:{end_dt.strftime("%Y%m%dT%H%M%SZ")}
SUMMARY:{row['Event Title']}
DESCRIPTION:{row['Notes']}
LOCATION:{row['Location']}
STATUS:CONFIRMED
END:VEVENT""")

    calendar = "BEGIN:VCALENDAR\rVERSION:2.0\rPRODID:-//Chronologue//EN\r" + "\r".join(events) + "\rEND:VCALENDAR"
    return calendar

def generate_markdown(df: pd.DataFrame) -> str:
    headers = "| Event Title | Date | Start Time | Duration (min) | Location | Notes |"
    separator = "| --- | --- | --- | --- | --- | --- |"
    rows = [
        f"| {row['Event Title']} | {row['Date']} | {row['Start Time']} | {row['Duration (min)']} | {row['Location']} | {row['Notes']} |"
        for _, row in df.iterrows()
    ]
    return "\n".join([headers, separator] + rows)

def call_gpt_for_command(user_message: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": user_message}],
        tools=[{
            "type": "function",
            "function": {
                "name": "calendar_command",
                "description": "Modify calendar events based on user instruction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add_event", "edit_event", "add_collaborator"]
                        },
                        "event_details": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "date": {"type": "string"},
                                "start_time": {"type": "string"},
                                "duration_minutes": {"type": "integer"},
                                "location": {"type": "string"},
                                "notes": {"type": "string"},
                                "collaborators": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "required": ["action", "event_details"]
                }
            }
        }],
        tool_choice="auto"
    )

    # ✅ Debugging: Print raw response
    print(response.model_dump_json(indent=2))

    tool_calls = response.choices[0].message.tool_calls
    parsed_arguments = json.loads(tool_calls[0].function.arguments)
    return parsed_arguments

def apply_command_to_table(command: dict, df: pd.DataFrame) -> pd.DataFrame:
    action = command["action"]
    event = command["event_details"]

    if action == "add_event":
        new_row = {
            "Event Title": event.get("title", ""),
            "Date": event.get("date", ""),
            "Start Time": event.get("start_time", ""),
            "Duration (min)": event.get("duration_minutes", 30),
            "Location": event.get("location", ""),
            "Notes": event.get("notes", ""),
            "UID": ""
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    elif action == "edit_event":
        mask = df["Event Title"].str.contains(event["title"], case=False, na=False)
        df.loc[mask, "Date"] = event.get("date", df.loc[mask, "Date"])
        df.loc[mask, "Start Time"] = event.get("start_time", df.loc[mask, "Start Time"])
        df.loc[mask, "Duration (min)"] = event.get("duration_minutes", df.loc[mask, "Duration (min)"])
        df.loc[mask, "Location"] = event.get("location", df.loc[mask, "Location"])
        df.loc[mask, "Notes"] = event.get("notes", df.loc[mask, "Notes"])

    elif action == "add_collaborator":
        mask = df["Event Title"].str.contains(event["title"], case=False, na=False)
        collaborators = ", ".join(event.get("collaborators", []))
        existing_notes = df.loc[mask, "Notes"].fillna("")
        df.loc[mask, "Notes"] = existing_notes + f" | Collaborators: {collaborators}"

    return df

# --- Streamlit UI ---

st.title("🧠 Chronologue Command Agent")

uploaded_file = st.file_uploader("Upload your Calendar File (.md or .ics)", type=["md", "ics"])

if uploaded_file:
    filename = uploaded_file.name
    filetype = filename.split(".")[-1]

    if filetype == "md":
        lines = uploaded_file.getvalue().decode().splitlines()
        rows = []
        for line in lines[2:]:
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 6:
                rows.append({
                    "Event Title": parts[0],
                    "Date": parts[1],
                    "Start Time": parts[2],
                    "Duration (min)": parts[3],
                    "Location": parts[4],
                    "Notes": parts[5],
                    "UID": ""
                })
        df = pd.DataFrame(rows)

    elif filetype == "ics":
        ics_text = uploaded_file.getvalue().decode()
        df = import_ics_content(ics_text)

    else:
        st.error("Unsupported file type. Please upload .md or .ics")
        st.stop()

    if "calendar_df" not in st.session_state:
        st.session_state["calendar_df"] = df

    st.subheader("Editable Calendar Table")
    edited_df = st.data_editor(
        st.session_state["calendar_df"],
        use_container_width=True,
        num_rows="dynamic",
    )
    st.session_state["calendar_df"] = edited_df

    # --- Chat Interface ---
    st.subheader("Command Your Calendar")

    user_message = st.chat_input("Type a command (e.g., Add a meeting Thursday at 2pm)")

    if user_message:
        try:
            command = call_gpt_for_command(user_message)
            st.session_state["calendar_df"] = apply_command_to_table(command, st.session_state["calendar_df"])
            st.success(f"✅ {command['action']} applied!")
        except Exception as e:
            st.error(f"⚠️ Failed to apply command: {e}")

    # --- Export Section ---
    st.subheader("Export Updated Calendar")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Download ICS"):
            ics_content = generate_ics_content(st.session_state["calendar_df"])
            st.download_button(
                label="📥 Download .ics",
                data=ics_content,
                file_name="edited_calendar.ics",
                mime="text/calendar"
            )

    with col2:
        if st.button("Download Markdown"):
            md_content = generate_markdown(st.session_state["calendar_df"])
            st.download_button(
                label="📥 Download .md",
                data=md_content,
                file_name="edited_calendar.md",
                mime="text/markdown"
            )
