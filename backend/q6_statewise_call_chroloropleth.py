import pandas as pd
import json
from pathlib import Path
from backend.tmcid_mapper import TmcidMapper

class TmcidJsonExporter:
    def __init__(self,
                 csv_path: str,
                 mapper_csv_path: str,
                 out_path: str = "static/question6_mapped.json"):
        self.csv_path = csv_path
        self.out_path = out_path
        self.df = None

        # Use mapper class
        self.mapper = TmcidMapper()
        self.mapper.load_mapper()

    def load_data(self):
        self.df = pd.read_csv(self.csv_path, low_memory=False)

    def compute_tmcid_counts(self):
        if self.df is None:
            raise RuntimeError("Data not loaded. Call load_data() first.")

        counts_series = (
            self.df
               .groupby("tmcid")
               .size()
               .sort_values(ascending=False)
        )
        actual_locs = list(counts_series.index)
        counts = [int(v) for v in counts_series.values]
        return actual_locs, counts

    def to_dict(self) -> dict:
        actual_locs, counts = self.compute_tmcid_counts()
        pretty_locs = self.mapper.map_list(actual_locs)

        return {
            "locations": pretty_locs,
            "values":     counts,
            "text":       pretty_locs
        }

    def save_json(self):
        data = self.to_dict()
        out_file = Path(self.out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved mapped JSON to {out_file}")

    def save_statewise_top_districts(self, output_path: str = "static/question6_state.json"):
        if self.df is None:
            raise RuntimeError("Data not loaded. Call load_data() first.")

        grouped = self.df.groupby(["tmcid", "Patient_district"]).size()
        grouped = grouped.reset_index(name='count')

        states = []
        values = []
        labels = []

        for state_code in grouped["tmcid"].unique():
            state_data = grouped[grouped["tmcid"] == state_code]
            top5 = state_data.sort_values("count", ascending=False).head(5)

            pretty_state = self.mapper.map_list([state_code])[0]
            states.append(pretty_state)
            values.append(list(top5["count"]))
            labels.append(list(top5["Patient_district"]))

        data = {
            "states": states,
            "values": values,
            "labels": labels
        }

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved state-wise district call JSON to {out_file}")


if __name__ == "__main__":
    exporter = TmcidJsonExporter(
        csv_path="database/counselling_data.csv",
        mapper_csv_path="database/mapped_states.csv",
        out_path="static/question6_country.json"
    )
    exporter.load_data()
    exporter.save_json()
    exporter.save_statewise_top_districts("static/question6_state.json")
