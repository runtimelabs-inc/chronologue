# modules/streamlit_ics_editor.py

# streamlit run modules/streamlit_ics_editor.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Chronologue Calendar Editor", page_icon="🗓️", layout="wide")

# --- Helper Functions ---

def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("\u00b0", "").replace("#", "")
    return f"{base}-{date_str}@chronologue.ai"

def parse_ics_datetime(dt_str: str) -> str:
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def safe_parse_start_time(date: str, start_time: str) -> datetime:
    """Handle start_time with or without seconds."""
    try:
        return datetime.strptime(f"{date}T{start_time}", "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return datetime.strptime(f"{date}T{start_time}", "%Y-%m-%dT%H:%M")

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
        start_dt = safe_parse_start_time(date, start_time)
        end_dt = start_dt + timedelta(minutes=int(row["Duration (min)"]))

        uid = row.get("UID", "") or generate_uid(row["Event Title"], date.replace("-", ""))

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

# --- Streamlit Interface ---

st.title("🗓️ Chronologue Calendar Editor")

st.markdown("Upload your `.md` or `.ics` calendar file. Edit events, add new ones, and export updated calendars.")

uploaded_file = st.file_uploader("Upload your Calendar File (.md or .ics)", type=["md", "ics"])

if uploaded_file:
    filename = uploaded_file.name
    filetype = filename.split(".")[-1]

    if filetype == "md":
        lines = uploaded_file.getvalue().decode().splitlines()
        rows = []
        for line in lines[2:]:  # Skip header lines
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

    st.subheader("Editable Calendar Table")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.TextColumn(help="YYYY-MM-DD"),
            "Start Time": st.column_config.TextColumn(help="24h format, HH:MM or HH:MM:SS"),
            "Duration (min)": st.column_config.NumberColumn(),
        }
    )

    if st.button("\u2795 Add Row"):
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
