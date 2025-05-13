import pandas as pd
import json
import os

class CallFlowDashboard:
    """
    Encapsulates funnel computation for call data and writes JSON output per state and overall.
    """
    DEFAULT_EXCLUDE_TMCS = ['ML02_TMC', 'docutoroutboud', 'KIRAN', 'IIITB_OB', 'Training_TMC_UK']
    FUNNEL_STAGES = [
        ("Received", lambda df: df),
        ("Chose State", lambda df: df[df['tmcid'] != 'TeleManas_Master_Inbound_DONOT_TOUCH']),
        ("Chose Language", lambda df: df[~((df['crt_object_id'].isna()) & (df['callstatus'] != 'CONNECTED'))]),
        ("Connected Calls", lambda df: df[df['callstatus'] == 'CONNECTED']),
        ("Successful Calls", lambda df: df[df['telemanas_id'].notna()]),
        ("Gave Rating", lambda df: df[df['rating'].isin(['1','2','3','4','5','No Input'])])
    ]

    def __init__(self, dataframe, exclude_tmcs=None, output_dir='static'):
        self.exclude_tmcs = exclude_tmcs or self.DEFAULT_EXCLUDE_TMCS
        self.output_dir = output_dir
        self.df = dataframe
        self.df_incoming = None
        self.country_data = {}
        self.state_data = []

    def load_and_filter(self):
        self.df = self.df[~self.df['tmcid'].isin(self.exclude_tmcs)]
        self.df_incoming = self.df[self.df['call_type'] == 'Incoming']

    def compute_funnel(self, df: pd.DataFrame) -> dict:
        labels = [label for label, _ in self.FUNNEL_STAGES]
        counts = []
        current = df.copy()

        for _, stage_fn in self.FUNNEL_STAGES:
            current = stage_fn(current)
            counts.append(len(current))

        dropoffs = [counts[i] - counts[i + 1] for i in range(len(counts) - 1)]
        dropoff_pct = [
            round((dropoffs[i] / counts[i] * 100), 1) if counts[i] > 0 else 0.0
            for i in range(len(dropoffs))
        ]

        return {
            "labels": labels,
            "values": counts,
            "dropoffs": dropoffs,
            "dropoffPercentages": dropoff_pct
        }

    def build(self):
        # Build country-level data (just callFlow, no "state")
        self.country_data = {
            "callFlow": self.compute_funnel(self.df_incoming)
        }

        # Build state-level data
        for tmcid in self.df_incoming['tmcid'].unique():
            df_state = self.df_incoming[self.df_incoming['tmcid'] == tmcid]
            self.state_data.append({
                "state": tmcid,
                "callFlow": self.compute_funnel(df_state)
            })

    def save(self):
        os.makedirs(self.output_dir, exist_ok=True)

        # Save country-level JSON
        path_country = os.path.join(self.output_dir, 'question15_country.json')
        with open(path_country, 'w', encoding='utf-8') as f:
            json.dump([self.country_data], f, indent=2)
        print(f"✔ Country-level file saved: {path_country}")

        # Save state-level JSON
        path_state = os.path.join(self.output_dir, 'question15_state.json')
        with open(path_state, 'w', encoding='utf-8') as f:
            json.dump(self.state_data, f, indent=2)
        print(f"✔ State-level file saved: {path_state}")

    def run(self):
        self.load_and_filter()
        self.build()
        self.save()


if __name__ == "__main__":
    df = pd.read_csv("database/Anonymized_Call_Handle_Data.csv")
    dashboard = CallFlowDashboard(dataframe=df)
    dashboard.run()
