# streamlit_grocery_scheduler.py
# streamlit run modules/streamlit/streamlit_grocery_scheduler.py
import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Chronologue Grocery Scheduler", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS Styling ---
st.markdown("""
<style>
    /* Background */
    body, .stApp {
        background-color: #121212;
        color: #00ff99; /* Default text color neon green */
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #00ff99;
    }

    /* Markdown text */
    .markdown-text-container {
        color: #00ff99;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #2a2a2a;
        color: #00ff99;
    }

    /* Data Editor */
    .stDataEditor {
        background-color: #2a2a2a;
        color: #00ff99;
    }

    /* Buttons */
    .stButton>button {
        background-color: #00ff99;
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def parse_md_to_df(md_text, section):
    """Parse markdown text into a DataFrame for a given section."""
    pattern = rf"## {section}.*?(?:\n- .+)+"
    match = re.search(pattern, md_text, re.DOTALL | re.IGNORECASE)
    
    items = []
    if match:
        lines = match.group(0).splitlines()
        for line in lines:
            if line.startswith("-"):
                item = line.lstrip("- ").strip()
                if "x " in item:
                    quantity, name = item.split("x ", 1)
                else:
                    quantity, name = "1", item
                items.append({"Quantity": quantity.strip(), "Item": name.strip()})
    return pd.DataFrame(items)

def generate_md_from_dfs(weekly_df, monthly_df, saved_df):
    """Generate markdown content from DataFrames."""
    lines = []
    
    lines.append("# Chronologue Grocery Order\n")
    
    lines.append("## Weekly Order\n")
    for _, row in weekly_df.iterrows():
        lines.append(f"- {row['Quantity']}x {row['Item']}")
    lines.append("")
    
    lines.append("## Monthly Order\n")
    for _, row in monthly_df.iterrows():
        lines.append(f"- {row['Quantity']}x {row['Item']}")
    lines.append("")
    
    lines.append("## Internal Save List\n")
    for _, row in saved_df.iterrows():
        lines.append(f"- {row['Item']}")
    lines.append("")
    
    return "\n".join(lines)

# --- Landing Page ---
with st.container():
    st.title("🛒 Chronologue Grocery Scheduler")
    st.subheader("Minimalist Grocery Order Memory System")
    st.markdown("""
    Welcome to Chronologue Grocery Scheduler.
    
    **Structure:**
    - **Weekly Orders:** Items you want automatically scheduled every week.
    - **Monthly Orders:** Staples you restock once per month.
    - **Saved List:** Items you want to quickly add in future weeks.

    Upload your grocery schedule, edit it inline, and download your updated memory or calendar!
    """)

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your Grocery Schedule (.md)", type=["md"])

if uploaded_file:
    md_text = uploaded_file.getvalue().decode("utf-8")

    weekly_df = parse_md_to_df(md_text, "Weekly Order")
    monthly_df = parse_md_to_df(md_text, "Monthly Order")
    saved_df = parse_md_to_df(md_text, "Internal Save List")

    # --- Tabs for Weekly, Monthly, Saved ---
    tab1, tab2, tab3 = st.tabs(["📅 Weekly Order", "📆 Monthly Order", "📝 Saved List"])

    with tab1:
        st.subheader("Edit Weekly Grocery Orders")
        weekly_df = st.data_editor(weekly_df, use_container_width=True, num_rows="dynamic")

    with tab2:
        st.subheader("Edit Monthly Grocery Orders")
        monthly_df = st.data_editor(monthly_df, use_container_width=True, num_rows="dynamic")

    with tab3:
        st.subheader("Edit Saved Items")
        saved_df = st.data_editor(saved_df, use_container_width=True, num_rows="dynamic")

    st.divider()

    # --- Download Updated Markdown ---
    if st.button("📥 Download Updated Grocery Schedule (.md)"):
        updated_md = generate_md_from_dfs(weekly_df, monthly_df, saved_df)
        st.download_button(
            label="📥 Download Updated Grocery Schedule",
            data=updated_md,
            file_name="updated_grocery_schedule.md",
            mime="text/markdown"
        )

else:
    st.info("Upload a `.md` file structured with Weekly, Monthly, and Saved List sections to begin.")

