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
                FlexiblePieChart(columns=columns, rows=rows).make_pie()

                
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
    Patient_District,
    Patient_Gender,
    COUNT(Patient_Gender) AS Gender_count
    FROM 
        table1
    WHERE 
        Patient_State = 'KARNATAKA'
    GROUP BY 
        Patient_District, Patient_Gender;

        """
    df = handler.execute_query(sql)  # returns a DataFrame
    print(df)
