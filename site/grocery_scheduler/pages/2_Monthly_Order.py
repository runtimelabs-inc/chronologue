import streamlit as st
import pandas as pd

st.set_page_config(page_title="Monthly Order", layout="wide")
with open('../assets/custom_styles.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

