import pandas as pd
import json
import os
from collections import defaultdict
from typing import Dict, List, Any
from backend.tmcid_mapper import TmcidMapper


class WeekdayMonthlyAggregator:
    def __init__(self,
                 csv_path: str,
                 tmcid_col: str = "tmcid",
                 time_col: str = "createdtime",
                 country_output: str = "static/question13_country.json",
                 state_output: str = "static/question13_state.json",
                 target_year: int = 2024):
        self.csv_path = csv_path
        self.tmcid_col = tmcid_col
        self.time_col = time_col
        self.country_output = country_output
        self.state_output = state_output
        self.target_year = target_year
        self.df = None

    def load_data(self):
        df = pd.read_csv(self.csv_path)
        df[self.time_col] = pd.to_datetime(df[self.time_col], errors="coerce")
        df = df.dropna(subset=[self.tmcid_col, self.time_col])
        df["year"] = df[self.time_col].dt.year
        df["month"] = df[self.time_col].dt.month
        df["weekday"] = df[self.time_col].dt.weekday  # 0 = Monday
        df["date"] = df[self.time_col].dt.date
        self.df = df[df["year"] == self.target_year]

    def _init_monthday_matrix(self) -> List[List[int]]:
        return [[0] * 7 for _ in range(12)]  # 12 months x 7 weekdays

    def _aggregate(self, df: pd.DataFrame) -> List[List[int]]:
        matrix = self._init_monthday_matrix()
        grouped = df.groupby(["month", "weekday"])["date"].count()
        for (month, weekday), count in grouped.items():
            matrix[month - 1][weekday] = count
        return matrix

    def build_country_data(self) -> Dict[str, Any]:
        matrix = self._aggregate(self.df)
        return {
            "year": self.target_year,
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "values": matrix
        }

    def build_state_data(self) -> Dict[str, Any]:
        state_matrices = []
        state_names = []

        for state, subdf in self.df.groupby(self.tmcid_col):
            matrix = self._aggregate(subdf)
            state_matrices.append(matrix)
            state_names.append(state)

        print(state_names)
        m = TmcidMapper()
        m.load_mapper()
        uni = m.map_list(state_names)
        print(uni)

        return {
            "states": uni,
            "year": self.target_year,
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "values": state_matrices
        }

    def save_json(self, data: Dict[str, Any], path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved to {path}")

    def run(self):
        self.load_data()
        country_data = self.build_country_data()
        state_data = self.build_state_data()
        self.save_json(country_data, self.country_output)
        self.save_json(state_data, self.state_output)


if __name__ == "__main__":
    aggregator = WeekdayMonthlyAggregator(
        csv_path="database/Anonymized_Call_Handle_Data.csv",
        tmcid_col="tmcid",
        time_col="createdtime",
        country_output="static/question13_country.json",
        state_output="static/question13_state.json",
        target_year=2024
    )
    aggregator.run()
