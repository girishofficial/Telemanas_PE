import streamlit as st
from pathlib import Path
from db_handler import DBHandler
from llm_handler import LLMHandler
from chat_manager import ChatManager
from ui_manager import UIManager
import pandas as pd
import os

def main():
    ui = UIManager()
    db_choice, creds = ui.get_user_inputs()

    db_handler = DBHandler(db_choice, creds)
    if db_handler.engine:
        ui.show_schema_sidebar(db_handler)

    chat = ChatManager()
    chat.render()

    if user_query := st.chat_input("Ask your database..."):

        file_path = 'pie_chart.png'
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"{file_path} deleted.")
        else:
            print(f"{file_path} does not exist.")

        chat.add_user_message(user_query)
        schema_hint = db_handler.get_schema_hint()
        llm = LLMHandler()
        sql = llm.query_sql(user_query, schema_hint)
        
        # Clean the SQL to ensure only one statement is executed
        # Remove any "Result:" and everything after it
        if "Result:" in sql:
            sql = sql.split("Result:")[0].strip()
        
        # Remove any "Question:" and everything after it
        if "Question:" in sql:
            sql = sql.split("Question:")[0].strip()
            
        # Remove any trailing semicolons or extra whitespace
        sql = sql.strip().rstrip(';')
        
        st.write(sql)

        if sql.startswith("-- ERROR"):
            st.error(sql)
            chat.add_bot_message(sql)
        else:
            try:
                # Extract state from SQL query to ensure consistency
                import re
                state_in_sql = None
                state_pattern = r"state_name\s*=\s*['\"]([A-Z\s]+)['\"]"
                state_match = re.search(state_pattern, sql, re.IGNORECASE)
                if state_match:
                    state_in_sql = state_match.group(1)
                    st.write(f"State: {state_in_sql}")
                
                rows, columns = db_handler.execute_query(sql)
                if rows:
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df)

                    

                    img_path = Path("pie_chart.png")
                    if img_path.exists():
                        st.image(
                            str(img_path),
                            caption="Gender Distribution Pie Chart",
                            width=400
                        )

                        with open(img_path, "rb") as f:
                            img_bytes = f.read()
                        st.download_button(
                            label="Download chart as PNG",
                            data=img_bytes,
                            file_name="pie_chart.png",
                            mime="image/png"
                        )
                    else:
                        st.info("No chart available for this query.")

                    chat.add_bot_message("Here's the result of your query.")
                else:
                    st.success("Query executed successfully. No rows returned.")
                    chat.add_bot_message("Query executed successfully. No rows returned.")
            except Exception as e:
                err_msg = f"Execution error: {e}"
                st.error(err_msg)
                chat.add_bot_message(err_msg)

if __name__ == "__main__":
    main()
