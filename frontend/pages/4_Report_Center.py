
import streamlit as st

from frontend.api_client import (
    generate_report,
    get_reports,
    download_report,
)

st.set_page_config(
    page_title="Report Center | Aegis",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Report Center")

st.caption(
    "Generate, manage and download industrial analysis reports."
)

st.subheader("Generate New Report")

title = st.text_input(
    "Report Title",
    value="Industrial Machine Analysis Report",
)

report_type = st.selectbox(
    "Report Type",
    [
        "machine_analysis",
        "maintenance_report",
        "operational_summary",
        "general_analysis",
    ],
)

source_dataset = st.text_input(
    "Source Dataset",
    value="machine_readings.csv",
)

summary = st.text_area(
    "Executive Summary",
    placeholder="Enter the report summary...",
)

observations = st.text_area(
    "Observations",
    placeholder="Enter important observations...",
)

recommendations = st.text_area(
    "Recommendations",
    placeholder="Enter recommendations, one per line...",
)

metrics_text = st.text_area(
    "Metrics (optional)",
    placeholder="Example:\nAverage Temperature: 63.48 °C\nMaximum Temperature: 79.1 °C",
)

if st.button("Generate DOCX Report", type="primary"):

    metrics = {}

    for line in metrics_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metrics[key.strip()] = value.strip()

    payload = {
        "title": title,
        "report_type": report_type,
        "source_dataset": source_dataset or None,
        "content": {
            "summary": summary,
            "sections": [
                {
                    "heading": "Observations",
                    "content": [
                        item.strip()
                        for item in observations.splitlines()
                        if item.strip()
                    ],
                }
            ],
            "metrics": metrics,
            "recommendations": [
                item.strip()
                for item in recommendations.splitlines()
                if item.strip()
            ],
        },
    }

    try:
        with st.spinner("Generating DOCX report..."):
            result = generate_report(payload).json()

        st.success("Report generated successfully!")
        st.json(result)

    except Exception as error:
        st.error(f"Report generation failed: {error}")

st.divider()

st.subheader("Report History")

if st.button("Refresh Reports"):

    try:
        reports = get_reports().json()

        if not reports:
            st.info("No reports generated yet.")

        for report in reports:

            with st.container(border=True):

                st.markdown(
                    f"### {report.get('title', 'Untitled Report')}"
                )

                st.caption(
                    f"ID: {report.get('id')} | "
                    f"Status: {report.get('status')}"
                )

                if st.button(
                    "Download Report",
                    key=f"download_{report.get('id')}",
                ):

                    file_response = download_report(
                        report["id"]
                    )

                    st.download_button(
                        "Save DOCX",
                        data=file_response.content,
                        file_name=report["filename"],
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        ),
                        key=f"save_{report['id']}",
                    )

    except Exception as error:
        st.error(f"Could not retrieve reports: {error}")
