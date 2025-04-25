# modules/streamlit_ics_editor.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Chronologue Calendar Editor", page_icon="🗓️", layout="wide")

# --- Helper Functions ---

def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("°", "").replace("#", "")
    return f"{base}-{date_str}@chronologue.ai"

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
    rows = [f"| {row['Event Title']} | {row['Date']} | {row['Start Time']} | {row['Duration (min)']} | {row['Location']} | {row['Notes']} |" for _, row in df.iterrows()]
    return "\n".join([headers, separator] + rows)

# --- Interface ---

st.title("🗓️ Chronologue Calendar Editor")

st.markdown("Edit your calendar memory traces. Add or remove events as needed. Export updated `.ics` or `.md`.")

uploaded_file = st.file_uploader("Upload your Markdown (.md) Calendar File", type=["md"])

if uploaded_file:
    lines = uploaded_file.getvalue().decode().splitlines()
    rows = []
    for line in lines[2:]:  # Skip header lines
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) == 6:
            rows.append({
                "Event Title": parts[0],
                "Date": parts[1],
                "Start Time": parts[2],
                "Duration (min)": parts[3],
                "Location": parts[4],
                "Notes": parts[5],
                "UID": ""  # Placeholder, will reuse or generate on export
            })
    df = pd.DataFrame(rows)

    st.subheader("Editable Calendar Table")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.TextColumn(help="YYYY-MM-DD"),
            "Start Time": st.column_config.TextColumn(help="24h format, HH:MM"),
            "Duration (min)": st.column_config.NumberColumn(),
        }
    )

    # Add new row
    if st.button("➕ Add Row"):
        new_row = pd.DataFrame([{
            "Event Title": "",
            "Date": "",
            "Start Time": "",
            "Duration (min)": 30,
            "Location": "",
            "Notes": "",
            "UID": ""
        }])
        edited_df = pd.concat([edited_df, new_row], ignore_index=True)

    # Save and Export
    st.subheader("Export Edited Calendar")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Download ICS"):
            ics_content = generate_ics_content(edited_df)
            st.download_button(
                label="📥 Download .ics",
                data=ics_content,
                file_name="edited_calendar.ics",
                mime="text/calendar"
            )

    with col2:
        if st.button("Download Markdown"):
            md_content = generate_markdown(edited_df)
            st.download_button(
                label="📥 Download .md",
                data=md_content,
                file_name="edited_calendar.md",
                mime="text/markdown"
            )
