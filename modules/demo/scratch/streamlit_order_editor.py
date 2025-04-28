# streamlit run modules/demo/streamlit_order_editor.py



import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Chronologue Grocery Order Editor", page_icon="🛒", layout="wide")

# --- Helper Functions ---

def load_order_json(uploaded_file) -> pd.DataFrame:
    """Load grocery orders JSON into a DataFrame."""
    data = json.load(uploaded_file)
    rows = []
    for frequency, items in data.items():
        for item in items:
            rows.append({
                "Frequency": frequency,
                "Item": item["item"],
                "Quantity": item["quantity"],
                "Link": item["link"]
            })
    return pd.DataFrame(rows)

def save_orders_to_json(df: pd.DataFrame) -> str:
    """Convert edited DataFrame back into JSON format."""
    orders = {"weekly": [], "monthly": []}
    for _, row in df.iterrows():
        freq = row["Frequency"].lower()
        if freq not in orders:
            orders[freq] = []
        orders[freq].append({
            "item": row["Item"],
            "quantity": row["Quantity"],
            "link": row["Link"]
        })
    return json.dumps(orders, indent=2)

# --- Streamlit Interface ---

st.title("🛒 Chronologue Grocery Order Editor")

st.markdown("""
Upload your grocery orders JSON, edit items and links, and download the updated file.
This will control your scheduled Instacart/Amazon Fresh orders.
""")

uploaded_file = st.file_uploader("Upload Grocery Orders (.json)", type=["json"])

if uploaded_file:
    df = load_order_json(uploaded_file)

    st.subheader("Editable Grocery Order List")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Frequency": st.column_config.SelectboxColumn(options=["weekly", "monthly"]),
            "Item": st.column_config.TextColumn(help="Name of the grocery item"),
            "Quantity": st.column_config.TextColumn(help="Example: '2 lbs', '1 bottle'"),
            "Link": st.column_config.TextColumn(help="URL link to specific product (Instacart/Amazon Fresh)")
        }
    )

    if st.button("\u2795 Add New Item"):
        new_row = pd.DataFrame([{
            "Frequency": "weekly",
            "Item": "",
            "Quantity": "",
            "Link": ""
        }])
        edited_df = pd.concat([edited_df, new_row], ignore_index=True)

    st.subheader("Download Updated Grocery Orders")

    json_output = save_orders_to_json(edited_df)

    st.download_button(
        label="📥 Download Updated Grocery JSON",
        data=json_output,
        file_name="updated_grocery_orders.json",
        mime="application/json"
    )

    st.divider()
    st.subheader("Next Scheduled Orders Preview")
    today = datetime.now()
    next_weekly = today + pd.DateOffset(weeks=1)
    next_monthly = today + pd.DateOffset(months=1)

    st.markdown(f"- **Next Weekly Order:** {next_weekly.strftime('%A, %B %d, %Y')}")
    st.markdown(f"- **Next Monthly Order:** {next_monthly.strftime('%A, %B %d, %Y')}")

else:
    st.info("Upload your current grocery order file to get started.")

