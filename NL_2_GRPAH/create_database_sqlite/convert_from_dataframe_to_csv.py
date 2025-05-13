import pandas as pd
from sqlalchemy import create_engine

# Load CSV file and clean column names
csv_file = "counselling_complaints.csv"
df = pd.read_csv(csv_file)

# Replace spaces with underscores in all column names
df.columns = df.columns.str.strip().str.replace(" ", "_")
df.to_csv("counselling_complaints.csv", index=False)

# Create SQLite engine (creates database.sqlite if it doesn't exist)
engine = create_engine("sqlite:///database.sqlite")

# Write cleaned DataFrame to SQLite
df.to_sql("table1", engine, if_exists="replace", index=False)

print("CSV data has been successfully written to database.sqlite with cleaned column names.")
