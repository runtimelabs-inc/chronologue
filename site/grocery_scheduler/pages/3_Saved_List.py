import streamlit as st
import pandas as pd

st.set_page_config(page_title="Saved List", layout="wide")
with open('../assets/custom_styles.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

