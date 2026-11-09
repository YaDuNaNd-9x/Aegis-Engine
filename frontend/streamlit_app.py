
import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.dashboard import render_dashboard

st.set_page_config(
    page_title="Aegis Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling
st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #e2e8f0;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #263449;
    }

    h1, h2, h3 {
        color: #f1f5f9;
    }

    div[data-testid="stMetric"] {
        background: #172235;
        border: 1px solid #2b3b52;
        padding: 18px;
        border-radius: 12px;
    }

    .stButton button {
        border-radius: 8px;
    }

    .block-container {
        padding-top: 2rem;
    }

    .aegis-subtitle {
        color: #94a3b8;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

render_sidebar()
render_dashboard()
