import pandas as pd
import json
import os
from datetime import time
from typing import List, Dict, Any


class TimeWindowCounter:
    def __init__(self,
                 csv_path: str,
                 tmcid_col: str = "tmcid",
                 time_col: str = "createdtime"):
        """
        Initializes the TimeWindowCounter.

        Args:
            csv_path (str): Path to the input CSV file.
            tmcid_col (str): Name of the column containing the TMC ID (used for state-wise aggregation).
            time_col (str): Name of the column containing the timestamp.
        """
        self.csv_path = csv_path
        self.tmcid_col = tmcid_col
        self.time_col = time_col
        self.df: pd.DataFrame = None # To be loaded by load_and_parse

        # Define time windows as (label, start_time, end_time)
        # These represent different parts of the day.
        self.windows = [
            ("5:00 - 8:59", time(5, 0), time(8, 59, 59)),
            ("9:00 - 11:59", time(9, 0), time(11, 59, 59)),
            ("12:00 - 15:59", time(12, 0), time(15, 59, 59)),
            ("16:00 - 20:30", time(16, 0), time(20, 30, 0)),
            ("20:31 - 23:59", time(20, 31), time(23, 59, 59)),
            ("00:00 - 04:59", time(0, 0), time(4, 59, 59)), # Handles overnight window
        ]
        # Extract just the labels for convenience
        self.window_labels = [label for label, _, _ in self.windows]

    def load_and_parse(self):
        """
        Loads the CSV file into a pandas DataFrame and parses the time column.
        It also drops rows where tmcid or time is missing.
        """
        try:
            df = pd.read_csv(self.csv_path)
        except FileNotFoundError:
            print(f"Error: The file {self.csv_path} was not found.")
            self.df = pd.DataFrame() # Initialize with empty DataFrame to prevent errors later
            return

        # Convert the time column to datetime objects, coercing errors to NaT (Not a Time)
        df[self.time_col] = pd.to_datetime(df[self.time_col], errors="coerce")
        # Drop rows where essential data (tmcid or parsed time) is missing
        df = df.dropna(subset=[self.tmcid_col, self.time_col])
        self.df = df
        print(f"Loaded and parsed {len(self.df)} rows from {self.csv_path}")

    def assign_window(self, t: time) -> str:
        """
        Assigns a given time object to one of the predefined time windows.

        Args:
            t (datetime.time): The time to assign.

        Returns:
            str: The label of the time window, or "Unknown" if no window matches.
        """
        for label, start, end in self.windows:
            if start <= end:  # Standard window (e.g., 9:00 to 11:59)
                if start <= t <= end:
                    return label
            else:  # Overnight window (e.g., 20:31 to 04:59)
                if t >= start or t <= end: # Checks if time is after start OR before end
                    return label
        return "Unknown" # Should not happen if windows cover 24h

    def process(self):
        """
        Processes the DataFrame to count occurrences within each time window,
        both country-wide and state-wise. Saves the results to JSON files.
        """
        if self.df is None or self.df.empty:
            print("DataFrame is not loaded or is empty. Skipping processing.")
            return

        # Apply the assign_window function to create a new 'window' column
        self.df["window"] = self.df[self.time_col].dt.time.apply(self.assign_window)

        # ---------- Country-wide aggregation ----------
        # Count occurrences of each window label
        country_counts = self.df["window"].value_counts().to_dict()
        # Ensure all window labels are present in the output, with 0 if no counts
        country_values = [country_counts.get(label, 0) for label in self.window_labels]

        country_json = {
            "labels": self.window_labels, # Changed from "x"
            "values": country_values,     # Changed from "y"
            "series_labels": ["CALL COUNT"] # Renamed from "labels" to "series_labels" for clarity
        }
        # Create 'static' directory if it doesn't exist
        os.makedirs("static", exist_ok=True)
        country_output_path = "static/question2_country.json"
        with open(country_output_path, "w") as f:
            json.dump(country_json, f, indent=2)
        print(f"Saved country-wide data to: {country_output_path}")

        # ---------- State-wise aggregation ----------
        processed_states = []
        state_values_all = [] # List of lists, each inner list is counts for a state

        # Group data by the tmcid column (representing states)
        for state_name_raw, group in self.df.groupby(self.tmcid_col):
            # Process state name: convert to string and replace underscores
            state_name_processed = str(state_name_raw).replace("_", " ")

            window_counts = group["window"].value_counts().to_dict()
            # Get counts for each window label for the current state
            state_specific_values = [window_counts.get(label, 0) for label in self.window_labels]

            processed_states.append(state_name_processed)
            state_values_all.append(state_specific_values)

        state_json = {
            "states": processed_states,    # List of processed state names
            "labels": self.window_labels,  # Changed from "x" (time window labels)
            "values": state_values_all,    # Changed from "y" (list of value lists for each state)
            "series_labels": ["CALL COUNT"]# Renamed from "labels" to "series_labels" for clarity
        }
        state_output_path = "static/question2_state.json"
        with open(state_output_path, "w") as f:
            json.dump(state_json, f, indent=2)
        print(f"Saved state-wise data to: {state_output_path}")

    def run(self):
        """
        Executes the full pipeline: load, parse, and process data.
        """
        self.load_and_parse()
        self.process()


if __name__ == "__main__":
    # Example usage:
    # Create a dummy CSV for testing if 'database/counselling_data.csv' doesn't exist
    dummy_data_path = "database/counselling_data.csv"
    if not os.path.exists(dummy_data_path):
        os.makedirs("database", exist_ok=True)
        print(f"Creating dummy data at {dummy_data_path} for demonstration.")
        dummy_df = pd.DataFrame({
            "tmcid": ["STATE_A", "STATE_B", "STATE_A", "STATE_C", "STATE_B", "ANDHRA_PRADESH"],
            "createdtime": [
                "2023-01-01 06:30:00", "2023-01-01 10:00:00",
                "2023-01-01 14:00:00", "2023-01-01 18:00:00",
                "2023-01-01 22:00:00", "2023-01-01 02:00:00"
            ],
            "other_col": [1,2,3,4,5,6]
        })
        dummy_df.to_csv(dummy_data_path, index=False)

    builder = TimeWindowCounter(
        csv_path=dummy_data_path, # Use the dummy data or your actual path
        tmcid_col="tmcid",
        time_col="createdtime"
    )
    builder.run()
