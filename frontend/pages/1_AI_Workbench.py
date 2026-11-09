
import streamlit as st

from frontend.api_client import send_chat

st.set_page_config(
    page_title="AI Workbench | Aegis",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI Workbench")
st.caption("Interact with your local industrial AI assistant.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

prompt = st.chat_input(
    "Ask Aegis about maintenance, industrial operations..."
)

if prompt:

    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Aegis is thinking..."):

            try:
                response = send_chat(prompt)
                result = response.json()

                answer = (
                    result.get("response")
                    or result.get("answer")
                    or result.get("message")
                    or str(result)
                )

                st.markdown(answer)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                })

            except Exception as error:

                st.error(
                    f"Unable to communicate with Aegis: {error}"
                )

if st.button("Clear Conversation"):
    st.session_state.chat_history = []
    st.rerun()
