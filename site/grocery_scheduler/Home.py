import streamlit as st
from pathlib import Path

# Correct path reference
base_dir = Path(__file__).parent  # Only .parent needed
css_path = base_dir / "assets" / "custom_styles.css"

st.set_page_config(page_title="Chronologue Grocery Scheduler", layout="wide", initial_sidebar_state="expanded")

# Load custom styles
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Home Page Content
st.title("🛒 Chronologue Grocery Scheduler")
st.subheader("Minimalist Grocery Memory System")

st.markdown("""
Welcome to **Chronologue Grocery Scheduler**.

Easily manage your recurring grocery orders across:
- **Weekly Orders** (recurring every week)
- **Monthly Orders** (recurring every month)
- **Saved List** (future memory for fast additions)

Upload your schedule, edit inline, and generate calendar events to automate your grocery routine.
""")

st.divider()

st.info("Use the sidebar to navigate to Weekly, Monthly, or Saved List management pages.")
