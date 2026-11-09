
import streamlit as st

from frontend.api_client import get_health


def render_sidebar():

    with st.sidebar:

        st.markdown("# ⚙️ AEGIS")
        st.caption("INDUSTRIAL AI WORKBENCH")

        st.divider()

        st.markdown("### Navigation")

        st.page_link(
            "streamlit_app.py",
            label="Dashboard",
            icon="🏠",
        )

        st.page_link(
            "pages/1_AI_Workbench.py",
            label="AI Workbench",
            icon="🤖",
        )

        st.page_link(
            "pages/2_Knowledge_Base.py",
            label="Knowledge Base",
            icon="📚",
        )

        st.page_link(
            "pages/3_Data_Analysis.py",
            label="Data Analysis",
            icon="📊",
        )

        st.page_link(
            "pages/4_Report_Center.py",
            label="Report Center",
            icon="📄",
        )

        st.page_link(
            "pages/5_Security_Audit.py",
            label="Security Audit",
            icon="🛡️",
        )

        st.divider()

        st.markdown("### System Status")

        try:
            response = get_health()

            if response.status_code == 200:
                st.success("Backend Online")
            else:
                st.warning("Backend Unavailable")

        except Exception:
            st.error("Backend Offline")

        st.caption("Local AI · Ollama · LangGraph")
        st.caption("Aegis Engine v1.0")
