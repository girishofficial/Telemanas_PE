import pandas as pd
import numpy as np
import json
import os
import calendar
from collections import defaultdict
from typing import List, Dict
from backend.tmcid_mapper import TmcidMapper


class ViolinDataBuilder:
    def __init__(self,
                 csv_path: str,
                 state_col: str = "State_Name",
                 date_col: str = "createdtime",
                 output_country_json: str = "static/question12_country.json",
                 output_state_json: str = "static/question12_state.json"):
        self.csv_path = csv_path
        self.state_col = state_col
        self.date_col = date_col
        self.output_country_json = output_country_json
        self.output_state_json = output_state_json

        self.df = None
        self.month_labels = [calendar.month_abbr[i] for i in range(1, 13)]
        self.state_names = []
        self.state_beg_end = []
        self.state_middle = []
        self.country_beg_end = defaultdict(list)
        self.country_middle = defaultdict(list)

    def load_and_clean(self):
        df = pd.read_csv(self.csv_path)

        if 'usertmcmapping â†’ statename' in df.columns:
            df = df.rename(columns={'usertmcmapping â†’ statename': self.state_col})

        df[self.date_col] = pd.to_datetime(df[self.date_col], errors="coerce")
        df = df.dropna(subset=[self.state_col, self.date_col])

        if pd.api.types.is_string_dtype(df[self.state_col]):
            df[self.state_col] = df[self.state_col].str.strip().str.title()

        self.df = df

    @staticmethod
    def month_split_counts(subdf: pd.DataFrame, date_col: str) -> Dict[str, List[int]]:
        counts = subdf[date_col].dt.day.value_counts().sort_index()
        beg_end = []
        middle = []

        for day, cnt in counts.items():
            if day <= 5 or day >= 25:
                beg_end.append(int(cnt))
            else:
                middle.append(int(cnt))
        return {"beg_end": beg_end, "middle": middle}

    @staticmethod
    def compute_summary(monthly_data: List[List[int]]) -> Dict[str, List[int]]:
        summary = {"min": [], "q1": [], "median": [], "q3": [], "max": []}
        for values in monthly_data:
            if values:
                arr = np.array(values)
                summary["min"].append(int(np.min(arr)))
                summary["q1"].append(int(np.percentile(arr, 25)))
                summary["median"].append(int(np.median(arr)))
                summary["q3"].append(int(np.percentile(arr, 75)))
                summary["max"].append(int(np.max(arr)))
            else:
                summary["min"].append(0)
                summary["q1"].append(0)
                summary["median"].append(0)
                summary["q3"].append(0)
                summary["max"].append(0)
        return summary

    def build(self):
        # --- India-level summary from all rows ---
        beg_end_per_month = [[] for _ in range(12)]
        middle_per_month = [[] for _ in range(12)]

        for period, mdf in self.df.groupby(self.df[self.date_col].dt.to_period("M")):
            month_idx = period.month - 1
            counts = self.month_split_counts(mdf, self.date_col)
            beg_end_per_month[month_idx].extend(counts["beg_end"])
            middle_per_month[month_idx].extend(counts["middle"])

        for i in range(12):
            self.country_beg_end[i].extend(beg_end_per_month[i])
            self.country_middle[i].extend(middle_per_month[i])

        # --- State-level summary excluding "India" ---
        for state, sdf in self.df.groupby(self.state_col):
            if state == "India":
                continue

            beg_end_per_month = [[] for _ in range(12)]
            middle_per_month = [[] for _ in range(12)]

            for period, mdf in sdf.groupby(sdf[self.date_col].dt.to_period("M")):
                month_idx = period.month - 1
                counts = self.month_split_counts(mdf, self.date_col)
                beg_end_per_month[month_idx].extend(counts["beg_end"])
                middle_per_month[month_idx].extend(counts["middle"])

            self.state_names.append(state)
            self.state_beg_end.append(beg_end_per_month)
            self.state_middle.append(middle_per_month)


    def save(self):
        os.makedirs("static", exist_ok=True)

        # Build country JSON
        country_json = {
            "months": self.month_labels,
            "beg_end": self.compute_summary([self.country_beg_end[i] for i in range(12)]),
            "middle": self.compute_summary([self.country_middle[i] for i in range(12)])
        }

        # Build state JSON
        print(self.state_names)
        m = TmcidMapper()
        m.load_mapper()
        uni = m.map_list(self.state_names)
        print(uni)

        state_json = {
            "states": uni,
            "months": self.month_labels,
            "beg_end": [self.compute_summary(self.state_beg_end[i]) for i in range(len(self.state_names))],
            "middle": [self.compute_summary(self.state_middle[i]) for i in range(len(self.state_names))]
        }

        with open(self.output_country_json, "w") as f:
            json.dump(country_json, f, indent=2)

        with open(self.output_state_json, "w") as f:
            json.dump(state_json, f, indent=2)

        print(f"✅ Saved: {self.output_country_json} and {self.output_state_json}")

    def run(self):
        self.load_and_clean()
        self.build()
        self.save()


if __name__ == "__main__":
    builder = ViolinDataBuilder(
        csv_path="database/Anonymized_Call_Handle_Data.csv",
        state_col="State_Name",
        date_col="createdtime",
        output_country_json="static/question12_country.json",
        output_state_json="static/question12_state.json"
    )
    builder.run()
