
import streamlit as st
import pandas as pd

from frontend.api_client import (
    get_audit_logs,
    get_audit_stats,
)

st.set_page_config(
    page_title="Security Audit | Aegis",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Security & Audit Center")

st.caption(
    "Inspect recorded application activity and operational events."
)

col1, col2 = st.columns(2)

try:
    stats = get_audit_stats().json()
    col1.metric(
        "Total Audit Events",
        stats.get("total_events", 0),
    )
except Exception:
    col1.metric("Total Audit Events", "Unavailable")

event_type = st.selectbox(
    "Filter by Event Type",
    ["All", "report", "analysis", "document", "chat"],
)

status = st.selectbox(
    "Filter by Status",
    ["All", "success", "failed"],
)

limit = st.slider(
    "Maximum Records",
    min_value=10,
    max_value=500,
    value=100,
    step=10,
)

if st.button("Load Audit Logs", type="primary"):

    params = {"limit": limit}

    if event_type != "All":
        params["event_type"] = event_type

    if status != "All":
        params["status"] = status

    try:
        logs = get_audit_logs(params).json()

        if not logs:
            st.info("No audit events found.")

        else:
            dataframe = pd.DataFrame(logs)

            st.subheader("Audit Event History")

            st.dataframe(
                dataframe,
                use_container_width=True,
            )

            st.download_button(
                "Export Audit Logs as CSV",
                data=dataframe.to_csv(index=False),
                file_name="aegis_audit_logs.csv",
                mime="text/csv",
            )

    except Exception as error:
        st.error(f"Could not retrieve audit logs: {error}")
