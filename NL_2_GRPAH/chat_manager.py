import streamlit as st

class ChatManager:
    def __init__(self):
        if "messages" not in st.session_state or st.sidebar.button("Clear History"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi! Ask me anything about your database."}
            ]

    def render(self):
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    def add_user_message(self, content):
        st.session_state.messages.append({"role": "user", "content": content})
        st.chat_message("user").write(content)

    def add_bot_message(self, content):
        st.session_state.messages.append({"role": "assistant", "content": content})
        st.chat_message("assistant").write(content)

if __name__ == "__main__":
    st.write("Run this with Streamlit to see chat interface.")
