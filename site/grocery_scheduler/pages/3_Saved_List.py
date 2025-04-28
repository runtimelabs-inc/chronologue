import streamlit as st
import pandas as pd

from pathlib import Path

# Set up page
st.set_page_config(page_title="Chronologue Grocery Scheduler", layout="wide", initial_sidebar_state="expanded")

# --- Theme Loader Function ---
def load_css(theme: str):
    """Dynamically load dark or light mode styles."""
    base_dir = Path(__file__).parent
    if theme == "Dark Mode":
        css_path = base_dir / "assets" / "custom_styles_dark.css"
    else:
        css_path = base_dir / "assets" / "custom_styles_light.css"

    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Theme Selection ---
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Light Mode"  # Default theme

theme = st.sidebar.selectbox(
    "Select Theme",
    options=["Dark Mode", "Light Mode"],
    index=0 if st.session_state.theme_choice == "Dark Mode" else 1
)

st.session_state.theme_choice = theme

st.title("📝 Saved Items for Future Orders")

uploaded_file = st.file_uploader("Upload Saved List (.md)", type=["md"])

def parse_md_section(md_text):
    lines = md_text.splitlines()
    items = []
    for line in lines:
        if line.startswith("-"):
            item = line.lstrip("- ").strip()
            items.append({"Item": item})
    return pd.DataFrame(items)

if uploaded_file:
    md_text = uploaded_file.getvalue().decode("utf-8")
    df = parse_md_section(md_text)

    st.data_editor(df, use_container_width=True, num_rows="dynamic")
    
    if st.button("📥 Download Updated Saved List (.md)"):
        lines = [f"- {row['Item']}" for _, row in df.iterrows()]
        md_output = "## Internal Save List\n" + "\n".join(lines)
        st.download_button("Download .md", md_output, file_name="updated_saved_list.md", mime="text/markdown")

