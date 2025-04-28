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


st.title("📆 Monthly Grocery Order Editor")

uploaded_file = st.file_uploader("Upload Monthly Order (.md)", type=["md"])

def parse_md_section(md_text):
    lines = md_text.splitlines()
    items = []
    for line in lines:
        if line.startswith("-"):
            item = line.lstrip("- ").strip()
            if "x " in item:
                quantity, name = item.split("x ", 1)
            else:
                quantity, name = "1", item
            items.append({"Quantity": quantity.strip(), "Item": name.strip()})
    return pd.DataFrame(items)

if uploaded_file:
    md_text = uploaded_file.getvalue().decode("utf-8")
    df = parse_md_section(md_text)

    st.data_editor(df, use_container_width=True, num_rows="dynamic")
    
    if st.button("📥 Download Updated Monthly Order (.md)"):
        lines = [f"- {row['Quantity']}x {row['Item']}" for _, row in df.iterrows()]
        md_output = "## Monthly Order\n" + "\n".join(lines)
        st.download_button("Download .md", md_output, file_name="updated_monthly_order.md", mime="text/markdown")

