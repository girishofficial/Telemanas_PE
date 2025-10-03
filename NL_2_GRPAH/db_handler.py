from sqlalchemy import create_engine, text
import sqlite3
from pathlib import Path
import pandas as pd
from NL_2_GRPAH.generate_graphs import FlexiblePieChart
import os


class DBHandler:
    def __init__(self, db_choice: str, creds: dict = {}, db_path: str = "NL_2_GRPAH/database.sqlite"):
        self.db_choice = db_choice
        self.creds = creds
        self.db_path = Path(db_path).absolute()
        self.engine = self._create_engine()

    def _create_engine(self):
        if self.db_choice == "SQLite":
            creator = lambda: sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            return create_engine("sqlite://", creator=creator)
        elif self.db_choice == "MySQL":
            if not all(self.creds.values()):
                return None
            url = f"mysql+mysqlconnector://{self.creds['user']}:{self.creds['password']}@{self.creds['host']}/{self.creds['db']}"
            return create_engine(url)
        return None

    def get_schema_hint(self) -> str:
        schema_hint = ""
        if not self.engine:
            return "-- ERROR: Engine not initialized"
        with self.engine.connect() as conn:
            if self.db_choice == "SQLite":
                tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            else:
                tables = conn.execute(text("SHOW TABLES;"))

            for row in tables:
                table = row[0]
                schema_hint += f"\nTable {table}:\n"
                if self.db_choice == "SQLite":
                    cols = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
                    cols = [(c[1], c[2]) for c in cols]
                else:
                    cols = conn.execute(text(f"DESCRIBE {table};")).fetchall()
                    cols = [(c[0], c[1]) for c in cols]
                for name, dtype in cols:
                    schema_hint += f" - {name} ({dtype})\n"
        return schema_hint

    def execute_query(self, sql: str, as_dataframe: bool = True):
        # Safety check: ensure we're only executing a single statement
        sql = sql.strip()
        if ";" in sql and not sql.endswith(";"):
            # Only keep the first statement if multiple are present
            sql = sql.split(";")[0] + ";"
        
        # Clean the SQL to ensure it's a valid statement
        if "Question:" in sql:
            sql = sql.split("Question:")[0].strip()
        if "Result:" in sql:
            sql = sql.split("Result:")[0].strip()
        
        # Fix column names with spaces and hyphens - critical to prevent SQL errors
        # No need to handle state_name as it doesn't have hyphens anymore
        
        if "patient - telemanas_id__age" in sql and "`patient - telemanas_id__age`" not in sql:
            import re
            sql = re.sub(r'(?<!`)patient - telemanas_id__age(?!`)', '`patient - telemanas_id__age`', sql)
        
        # Handle WHERE clause specifically for hyphenated column names
        if "WHERE patient - telemanas_id__age" in sql:
            sql = sql.replace("WHERE patient - telemanas_id__age", "WHERE `patient - telemanas_id__age`")
        if "where patient - telemanas_id__age" in sql:
            sql = sql.replace("where patient - telemanas_id__age", "where `patient - telemanas_id__age`")
            
        print("SQL: \n", sql)
        if not self.engine:
            raise RuntimeError("Database engine is not initialized.")
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                columns = list(columns)

                print("Columns:\n",columns)
                print("Rows:\n",rows)
                print("Calling the graph to generate\n")
                
                # Extract state from SQL if it exists for more accurate chart title
                chart_title = "Distribution"
                import re
                state_match = re.search(r"state_name\s*=\s*['\"]([A-Z\s]+)['\"]", sql, re.IGNORECASE)
                if state_match:
                    state_name = state_match.group(1)
                    chart_title = f"{state_name} Distribution"
                
                FlexiblePieChart(columns=columns, rows=rows).make_pie(chart_title)

                
                return rows, columns
            return None, None


if __name__ == "__main__":
    # For SQLite
    handler = DBHandler("SQLite", db_path="database.sqlite")

    # Optional: Get schema
    print(handler.get_schema_hint())

    # Example: Running a query
    sql = """
    SELECT 
    district_name,
    gender,
    COUNT(telemanasid) AS Gender_count
    FROM 
        table1
    WHERE 
        state_name = 'KARNATAKA'
    GROUP BY 
        district_name, gender;

        """
    df = handler.execute_query(sql)  # returns a DataFrame
    print(df)
