import streamlit as st
from sqlalchemy import text



class UIManager:
    def __init__(self):
        st.set_page_config(page_title="Chat with SQL DB", page_icon="🦜")
        st.title("Chat with SQL Database (Ollama)")

    def get_user_inputs(self):
        db_choice = st.sidebar.radio("Select Database", ["SQLite", "MySQL"])
        creds = {}
        if db_choice == "MySQL":
            creds["host"] = st.sidebar.text_input("Host", "localhost")
            creds["user"] = st.sidebar.text_input("User", "root")
            creds["password"] = st.sidebar.text_input("Password", type="password")
            creds["db"] = st.sidebar.text_input("Database")
        return db_choice, creds

    def show_schema_sidebar(self, db_handler):
        with db_handler.engine.connect() as conn:
            if db_handler.db_choice == "SQLite":
                tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            else:
                tables = conn.execute("SHOW TABLES;")
            st.sidebar.markdown("### Tables")
            for row in tables:
                st.sidebar.write(f"📂 {row[0]}")

if __name__ == "__main__":
    st.write("Run this with Streamlit.")
