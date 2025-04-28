import streamlit as st
from pathlib import Path

# streamlit run site/grocery_scheduler/Home.py

# --- Page Setup: must be first ---
st.set_page_config(page_title="Chronologue Grocery Scheduler", layout="wide", initial_sidebar_state="expanded")

# --- Theme Loader ---
def load_css(theme: str):
    base_dir = Path(__file__).parent
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

# --- Page Content ---

st.title("Chronologue Grocery Scheduler")
st.subheader("Minimalist Grocery Memory System")

st.markdown(
    "Welcome to **Chronologue Grocery Scheduler**.\n\n"
    "Easily manage your recurring grocery orders across:\n"
    "- **Weekly Orders** (recurring every week)\n"
    "- **Monthly Orders** (recurring every month)\n"
    "- **Saved List** (future memory for fast additions)\n\n"
    "Upload your schedule, edit inline, and generate calendar events to automate your grocery routine.\n\n"
    "Use the sidebar to navigate to Weekly, Monthly, or Saved List management pages."
)

st.markdown(
    "##  Walkthrough: How Chronologue Works\n\n"
    "#### 1. Input: Capture Your Grocery Memory\n"
    "- Upload a receipt, invoice, or order history text\n"
    "- System parses it into:\n"
    "    - **Weekly Recurring Orders**\n"
    "    - **Monthly Recurring Orders**\n"
    "    - **Internal Save List** (for spontaneous future additions)\n\n"
    "## 2. Structure: Editable Markdown Memory\n"
    "- File is clear for humans and parsable for agents\n"
    "- Sections:\n"
    "    - Weekly Order\n"
    "    - Monthly Order\n"
    "    - Saved List\n"
    "- Quantities inline (e.g., 1x, 2x)\n"
    "- Editable links optional for future expansion\n\n"
    "#### 3. Calendar Representation\n\n"
    "| Field | Content |\n"
    "|:------|:--------|\n"
    "| **Summary** | \"Weekly Grocery Order\" |\n"
    "| **Description** | Items + Quantities |\n"
    "| **Start Time** | Scheduled day/time for orders |\n"
    "| **Recurrence Rule** | FREQ=WEEKLY;INTERVAL=1 |\n"
    "| **Link/Location** | (Optional) Streamlit app link for editing |\n\n"
    "Minimal Summary, Full item list in Description, Optional Edit Link.\n\n"
    "#### 4. Dataset Organization\n\n"
    "| Dataset | Purpose |\n"
    "|:--------|:--------|\n"
    "| **Weekly Orders** | Recurring weekly scheduled events |\n"
    "| **Monthly Orders** | Recurring monthly scheduled events |\n"
    "| **Internal Save List** | Future spontaneous additions |\n\n"
    "Each user has:\n"
    "- `weekly_orders.md`\n"
    "- `monthly_orders.md`\n"
    "- `internal_save_list.md`\n\n"
    "#### 5. Upcoming Steps\n\n"
    "Chronologue grows by:\n"
    "- Structured ingestion\n"
    "- Persistent memory traces\n"
    "- Action scheduling\n"
    "- Editable agent interaction\n"
)

st.markdown(
    "## Example Calendar Events\n\n"
    "### Weekly Order\n\n"
    "SUMMARY:Weekly Grocery Order\n"
    "DESCRIPTION:Grocery list for this week's order:\n\n"
    "- 1x STEVEN SMITH TEAMAKER Organic Lullaby Wellness Tea\n"
    "- 1x BIGELOW Cozy Chamomile Tea\n"
    "- 1x Ben & Jerry's Mint Chocolate Cookie Ice Cream\n"
    "- 1x WHOLE FOODS KITCHENS Classic Beef Chili with Beans\n"
    "- 1x CAL ORGANIC Organic Mixed Fingerling Potatoes\n"
    "- 1x Fly by Jing Original Chili Crisp\n"
    "- 1x PRODUCE Organic Dino Kale\n"
    "- 2x Blueberries\n"
    "- 1x TAYLORS OF HARROGATE Irish Breakfast Tea\n"
    "- 1x Navel Oranges\n"
    "- 1x WHOLE FOODS KITCHENS Organic Split Pea Soup\n"
    "- 1x PRODUCE Red Bell Peppers\n"
    "- 1x 365 by Whole Foods Market Organic Baby Spinach\n"
    "- 1x PRODUCE Test Banana\n"
    "- 1x Country Natural Beef Blend Ground Beef Burgers\n\n"
    "DESCRIPTION:Grocery list for this month's order:\n\n"
    "- Dish soap\n"
    "- Sponges\n"
    "- Toothbrush\n"
    "- Toothpaste\n"
    "- Floss sticks\n"
    "- Olive oil\n"
    "- Butter\n"
    "- Salt\n"
    "- Pepper\n"
    "- Cayenne Pepper\n"
    "- Rosemary\n"
    "- Garlic clove\n"
    "- Coffee beans\n\n"
   
)
