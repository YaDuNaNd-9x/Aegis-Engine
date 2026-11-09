
import streamlit as st

from frontend.api_client import (
    upload_document,
    search_documents,
    get_document_stats,
)

st.set_page_config(
    page_title="Knowledge Base | Aegis",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Knowledge Base")
st.caption("Manage industrial SOPs, manuals and technical documents.")

st.subheader("Upload Documents")

uploaded_files = st.file_uploader(
    "Upload PDF, DOCX or TXT files",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if st.button("Upload Documents", type="primary"):

    if not uploaded_files:
        st.warning("Please select at least one document.")

    else:
        for uploaded_file in uploaded_files:

            with st.spinner(f"Processing {uploaded_file.name}..."):

                try:
                    response = upload_document(uploaded_file)
                    st.success(
                        f"{uploaded_file.name}: {response.json()}"
                    )

                except Exception as error:
                    st.error(
                        f"Upload failed for {uploaded_file.name}: {error}"
                    )

st.divider()

st.subheader("Search Knowledge Base")

query = st.text_input(
    "Enter a technical question or search phrase"
)

if st.button("Search Documents"):

    if not query.strip():
        st.warning("Enter a search query.")

    else:
        try:
            response = search_documents(query)
            result = response.json()

            st.subheader("Search Results")
            st.json(result)

        except Exception as error:
            st.error(f"Search failed: {error}")

st.divider()

st.subheader("Knowledge Base Statistics")

if st.button("Refresh Statistics"):

    try:
        stats = get_document_stats().json()
        st.json(stats)

    except Exception as error:
        st.error(f"Could not retrieve statistics: {error}")
