import pandas as pd
import json
import os
from typing import List, Dict, Any
#from tmcid_mapper import TmcidMapper

class DistrictGenderCounter:
    def __init__(self,
                 df: pd.DataFrame,
                 state_col: str = "Patient_State",
                 district_col: str = "Patient_District",
                 gender_col: str = "Patient_Gender",
                 output_json: str = "static/q7_district_count.json"):
        self.df = df
        self.state_col = state_col
        self.district_col = district_col
        self.gender_col = gender_col
        self.output_json = output_json

    def build(self) -> Dict[str, Any]:
        states: List[str] = []
        districts: List[List[str]] = []
        male_counts: List[List[int]] = []
        female_counts: List[List[int]] = []

        for state_raw, sdf in self.df.groupby(self.state_col):
            # Title‑case the state name
            state = state_raw.title()

            # total calls per district
            total_by_district = sdf.groupby(self.district_col).size()
            if total_by_district.size < 5:
                continue

            # pick top‑5 districts
            top5_raw = total_by_district.nlargest(5).index.tolist()
            # title‑case each district
            top5 = [d.title() for d in top5_raw]

            # collect male/female counts
            m_counts: List[int] = []
            f_counts: List[int] = []
            for dist_raw in top5_raw:
                subset = sdf[sdf[self.district_col] == dist_raw]
                vc = subset[self.gender_col].value_counts().to_dict()
                m_counts.append(vc.get("Male", 0))
                f_counts.append(vc.get("Female", 0))

            states.append(state)
            districts.append(top5)
            male_counts.append(m_counts)
            female_counts.append(f_counts)

        
       
        return {
            "states": states,
            "districts": districts,
            "male": male_counts,
            "female": female_counts
        }

    def save(self):
        data = self.build()
        os.makedirs(os.path.dirname(self.output_json), exist_ok=True)
        with open(self.output_json, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved district/gender pyramid data to {self.output_json}")

    def run(self):
        self.save()


# ---------------- Example Usage ----------------
if __name__ == "__main__":
    df = pd.read_csv('database/counselling_complaints.csv')
    # clean column names
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    builder = DistrictGenderCounter(
        df,
        state_col="Patient_State",
        district_col="Patient_District",
        gender_col="Patient_Gender",
        output_json="static/question14_state.json"
    )
    builder.run()
