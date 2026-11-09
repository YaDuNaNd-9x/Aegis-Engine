
import streamlit as st

from frontend.api_client import analyze_csv

st.set_page_config(
    page_title="Data Analysis | Aegis",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Industrial Data Analysis")

st.caption(
    "Upload machine readings and ask your AI assistant "
    "to perform structured analysis."
)

uploaded_file = st.file_uploader(
    "Upload industrial CSV dataset",
    type=["csv"],
)

question = st.text_area(
    "What would you like Aegis to analyze?",
    placeholder=(
        "Calculate average temperature, identify abnormal "
        "readings and summarize potential issues."
    ),
)

if uploaded_file:

    st.subheader("Dataset Preview")

    try:
        import pandas as pd

        dataframe = pd.read_csv(uploaded_file)

        st.dataframe(
            dataframe.head(10),
            use_container_width=True,
        )

        st.write(
            f"Rows: {len(dataframe)} | "
            f"Columns: {len(dataframe.columns)}"
        )

        uploaded_file.seek(0)

    except Exception as error:
        st.error(f"Could not preview CSV: {error}")


if st.button("Run AI Analysis", type="primary"):

    if uploaded_file is None:
        st.warning("Upload a CSV file first.")

    elif not question.strip():
        st.warning("Enter an analysis instruction.")

    else:

        with st.spinner(
            "Aegis is generating and executing analysis..."
        ):

            try:
                uploaded_file.seek(0)

                response = analyze_csv(
                    uploaded_file,
                    question,
                )

                result = response.json()

                st.success("Analysis completed!")

                st.subheader("Analysis Results")
                st.json(result)

            except Exception as error:
                st.error(f"Analysis failed: {error}")
