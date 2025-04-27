import streamlit as st
import requests
import time

st.set_page_config(page_title="Student DB AI Agent")
st.title("AI Agent for Managing Student Database")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display all past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Handle bot trace
        if message["role"] == "assistant" and "trace" in message:
            for thought, observation in message["trace"]:
                st.markdown(f"**Thought:** {thought}")
                st.markdown(f"**Observation:** {observation}")
            st.markdown(f"**Final Answer:** {message['content']}")
        else:
            st.markdown(message["content"])

# Accept user input via Chat Input
if user_input := st.chat_input("Nhập yêu cầu của bạn..."):
    # Save user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user's message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Bot thinking spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post("http://localhost:8000/ask", json={"question": user_input})
                data = res.json()
                final_answer = data.get("final_answer", "No final answer.")
                trace = data.get("trace", [])

                # Display trace step-by-step
                for thought, observation in trace:
                    st.markdown(f"**Thought:** {thought}")
                    st.markdown(f"**Observation:** {observation}")
                st.markdown(f"**Final Answer:** {final_answer}")

                # Save bot full response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "trace": trace
                })

            except Exception as e:
                st.error(f"API Error: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"API Error: {e}"
                })
