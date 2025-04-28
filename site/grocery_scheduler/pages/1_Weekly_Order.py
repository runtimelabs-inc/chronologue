import streamlit as st
import pandas as pd
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date

# Set up page
st.set_page_config(page_title="Chronologue Grocery Scheduler", layout="wide", initial_sidebar_state="expanded")

# --- Theme Loader Function ---
def load_css(theme: str):
    base_dir = Path(__file__).parent.parent
    if theme == "Dark Mode":
        css_path = base_dir / "assets" / "custom_styles_dark.css"
    else:
        css_path = base_dir / "assets" / "custom_styles_light.css"

    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Theme Selection ---
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Light Mode"

theme = st.sidebar.selectbox(
    "Select Theme",
    options=["Dark Mode", "Light Mode"],
    index=0 if st.session_state.theme_choice == "Dark Mode" else 1
)

st.session_state.theme_choice = theme

# Load selected theme
load_css(st.session_state.theme_choice)

# --- Helper Functions ---
def extract_text(file, filetype):
    if filetype == "html":
        soup = BeautifulSoup(file.getvalue(), "html.parser")
        text = soup.get_text(separator="\n")
    else:  # .md or .txt
        text = file.getvalue().decode("utf-8")
    return text

def parse_grocery_items(text):
    lines = text.splitlines()
    items = []
    for line in lines:
        line = line.strip()
        if line.startswith("-"):
            line = line.lstrip("- ").strip()
        match = re.match(r"(\d+)x\s+(.*)", line)
        if match:
            quantity, item = match.groups()
            items.append({"Quantity": quantity.strip(), "Item": item.strip()})
        elif line:
            items.append({"Quantity": "1", "Item": line.strip()})
    return pd.DataFrame(items)

def generate_purchase_approval_ics(df, approval_datetime):
    start_dt = datetime.combine(approval_datetime.date(), approval_datetime.time())
    end_dt = start_dt + timedelta(minutes=30)

    items_list = "\n".join([
        f"- {row['Quantity']}x {row['Item']} (https://www.example.com/search?q={row['Item'].replace(' ', '+')})"
        for _, row in df.iterrows()
    ])

    event = f"""BEGIN:VEVENT
UID:purchase-approval-{start_dt.strftime('%Y%m%d')}@chronologue.ai
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}
RRULE:FREQ=WEEKLY;INTERVAL=1
SUMMARY:Grocery List Approval Needed
DESCRIPTION:Please review and confirm your grocery list:\n{items_list}\n[View/Edit Order](https://your-site.com/weekly-orders/12345)
STATUS:CONFIRMED
END:VEVENT"""

    calendar = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Chronologue//EN
""" + event + "\nEND:VCALENDAR"
    return calendar

def generate_delivery_tracking_ics(df, delivery_datetime):
    start_dt = datetime.combine(delivery_datetime.date(), delivery_datetime.time())
    end_dt = start_dt + timedelta(hours=2)

    event = f"""BEGIN:VEVENT
UID:delivery-tracking-{start_dt.strftime('%Y%m%d')}@chronologue.ai
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}
RRULE:FREQ=WEEKLY;INTERVAL=1
SUMMARY:Grocery Delivery Scheduled
DESCRIPTION:Estimated Delivery Window: {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}\n[Feedback Form](https://your-site.com/feedback/12345)\n[Prepare Next Week](https://your-site.com/weekly-orders/12345)
STATUS:CONFIRMED
END:VEVENT"""

    calendar = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Chronologue//EN
""" + event + "\nEND:VCALENDAR"
    return calendar

def sample_items():
    return pd.DataFrame([
        {"Quantity": "1", "Item": "Organic Blueberries"},
        {"Quantity": "2", "Item": "Dino Kale"},
        {"Quantity": "1", "Item": "Chamomile Tea"},
        {"Quantity": "1", "Item": "Mint Ice Cream"},
        {"Quantity": "1", "Item": "Split Pea Soup"},
        {"Quantity": "1", "Item": "Irish Breakfast Tea"},
        {"Quantity": "1", "Item": "Organic Spinach"},
        {"Quantity": "1", "Item": "Red Bell Peppers"},
        {"Quantity": "1", "Item": "Chili Crisp"},
        {"Quantity": "1", "Item": "Navel Oranges"}
    ])

# --- Page Content ---
st.title("🛒 Chronologue Weekly Grocery Order")

uploaded_file = st.file_uploader("Upload your Weekly Order (.md, .txt, .html)", type=["md", "txt", "html"])

if uploaded_file:
    filetype = uploaded_file.name.split(".")[-1]
    raw_text = extract_text(uploaded_file, filetype)
    df = parse_grocery_items(raw_text)
    if df.empty:
        st.warning("No items detected. Please check your file formatting.")
    else:
        st.success(f"✅ Parsed {len(df)} items!")
        st.data_editor(df, use_container_width=True, num_rows="dynamic")

        approval_date = st.date_input("Select Order Approval Date")
        approval_time = st.time_input("Select Order Approval Time", value=datetime.strptime("09:00", "%H:%M").time())
        delivery_date = st.date_input("Select Delivery Date")
        delivery_time = st.time_input("Select Delivery Window Start Time", value=datetime.strptime("08:00", "%H:%M").time())

        approval_datetime = datetime.combine(approval_date, approval_time)
        delivery_datetime = datetime.combine(delivery_date, delivery_time)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 Download Purchase Approval .ics"):
                ics_content = generate_purchase_approval_ics(df, approval_datetime)
                st.download_button(
                    label="Download Purchase Approval .ics",
                    data=ics_content,
                    file_name="weekly_purchase_approval.ics",
                    mime="text/calendar"
                )

        with col2:
            if st.button("📥 Download Delivery Tracking .ics"):
                ics_content = generate_delivery_tracking_ics(df, delivery_datetime)
                st.download_button(
                    label="Download Delivery Tracking .ics",
                    data=ics_content,
                    file_name="weekly_delivery_tracking.ics",
                    mime="text/calendar"
                )
else:
    st.subheader("No File? Try a Sample!")
    df = sample_items()
    st.data_editor(df, use_container_width=True, num_rows="dynamic")

    approval_date = st.date_input("Select Sample Order Approval Date", key="sample_approval_date")
    approval_time = st.time_input("Select Sample Order Approval Time", value=datetime.strptime("09:00", "%H:%M").time(), key="sample_approval_time")
    delivery_date = st.date_input("Select Sample Delivery Date", key="sample_delivery_date")
    delivery_time = st.time_input("Select Sample Delivery Time", value=datetime.strptime("08:00", "%H:%M").time(), key="sample_delivery_time")

    approval_datetime = datetime.combine(approval_date, approval_time)
    delivery_datetime = datetime.combine(delivery_date, delivery_time)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Download Sample Purchase Approval .ics"):
            ics_content = generate_purchase_approval_ics(df, approval_datetime)
            st.download_button(
                label="Download Sample Purchase Approval .ics",
                data=ics_content,
                file_name="sample_weekly_purchase_approval.ics",
                mime="text/calendar"
            )

    with col2:
        if st.button("📥 Download Sample Delivery Tracking .ics"):
            ics_content = generate_delivery_tracking_ics(df, delivery_datetime)
            st.download_button(
                label="Download Sample Delivery Tracking .ics",
                data=ics_content,
                file_name="sample_weekly_delivery_tracking.ics",
                mime="text/calendar"
            )
