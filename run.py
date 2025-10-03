import streamlit as st
from pathlib import Path
from NL_2_GRPAH.db_handler import DBHandler
from NL_2_GRPAH.llm_handler import LLMHandler
from NL_2_GRPAH.chat_manager import ChatManager
from NL_2_GRPAH.ui_manager import UIManager
import pandas as pd
import os

def main():
    ui = UIManager()
    db_choice, creds = ui.get_user_inputs()

    db_handler = DBHandler(db_choice, creds)
    if db_handler.engine:
        ui.show_schema_sidebar(db_handler)

    chat = ChatManager()
    
    # Add a clear button to the main UI for better usability
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Clear Chat"):
            # Reset session state for messages
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi! Ask me anything about your database."}
            ]
            st.rerun()  # Force a rerun to update the UI
    
    chat.render()

    user_query = st.chat_input("Ask your database...")
    if user_query:

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
        
        # Fix column names with spaces and hyphens if needed - need to be more aggressive
        # No need to handle state_name as it doesn't have hyphens anymore
            
        if "patient - telemanas_id__age" in sql and "`patient - telemanas_id__age`" not in sql:
            import re
            sql = re.sub(r'(?<!`)patient - telemanas_id__age(?!`)', '`patient - telemanas_id__age`', sql)
            
        # Also handle WHERE clauses specifically which is where the error is occurring
        if "WHERE patient - telemanas_id__age" in sql:
            sql = sql.replace("WHERE patient - telemanas_id__age", "WHERE `patient - telemanas_id__age`")
        if "where patient - telemanas_id__age" in sql:
            sql = sql.replace("where patient - telemanas_id__age", "where `patient - telemanas_id__age`")
        
        # If using COUNT(*), replace with COUNT(telemanasid) for more accurate counting
        if "COUNT(*)" in sql:
            sql = sql.replace("COUNT(*)", "COUNT(telemanasid)")
        
        # Display the cleaned SQL
        st.write(sql)

        if sql.startswith("-- ERROR"):
            st.error(sql)
            chat.add_bot_message(sql)
        else:
            try:
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
