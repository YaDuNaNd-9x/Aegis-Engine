
import streamlit as st

from frontend.api_client import (
    get_document_stats,
    get_reports,
    get_audit_stats,
)


def render_dashboard():

    st.title("⚙️ Aegis Engine")
    st.markdown(
        '<p class="aegis-subtitle">'
        'Private, Offline-First Agentic AI Workbench '
        'for Industrial Operations'
        '</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("System Overview")

    col1, col2, col3 = st.columns(3)

    try:
        stats = get_document_stats().json()
        document_count = stats.get(
            "total_documents",
            stats.get("document_count", 0)
        )
    except Exception:
        document_count = "Unavailable"

    try:
        reports = get_reports().json()
        report_count = len(reports) if isinstance(reports, list) else 0
    except Exception:
        report_count = "Unavailable"

    try:
        audit = get_audit_stats().json()
        audit_count = audit.get("total_events", 0)
    except Exception:
        audit_count = "Unavailable"

    col1.metric("Knowledge Base", document_count)
    col2.metric("Generated Reports", report_count)
    col3.metric("Audit Events", audit_count)

    st.divider()

    st.subheader("Available Capabilities")

    cards = [
        (
            "🤖 AI Workbench",
            "Interact with local LLMs and ask technical questions."
        ),
        (
            "📚 Knowledge Base",
            "Upload SOPs, manuals and technical documents."
        ),
        (
            "📊 Data Analysis",
            "Analyze industrial CSV data using AI-generated Python."
        ),
        (
            "📄 Report Center",
            "Generate downloadable professional DOCX reports."
        ),
        (
            "🛡️ Security Audit",
            "Inspect application events and operational activity."
        ),
    ]

    for title, description in cards:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(description)

    st.divider()

    st.info(
        "Aegis Engine uses locally hosted Ollama models, "
        "retrieval-augmented generation and Docker-based "
        "execution isolation."
    )
