import pandas as pd
from sqlalchemy import create_engine, text

# Paths
csv_file = r"E:\PE\BackendIntelligent_Dashboard\NL_2_GRPAH\create_database_sqlite\Data_set_V2.csv"
db_file  = r"E:\PE\BackendIntelligent_Dashboard\NL_2_GRPAH\create_database_sqlite\database.sqlite"

# Load CSV
df = pd.read_csv(csv_file, low_memory=False)  # avoids dtype warning

# Clean column names
df.columns = df.columns.str.strip().str.replace(" ", "_")

# Save cleaned CSV back
df.to_csv(csv_file, index=False)

# Create SQLite engine (absolute path)
engine = create_engine(f"sqlite:///{db_file}")

# Write to SQLite
df.to_sql("table1", engine, if_exists="replace", index=False)

# Verify tables
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    print("Tables in DB:", result.fetchall())

print(f"CSV data has been successfully written to {db_file} with cleaned column names.")

