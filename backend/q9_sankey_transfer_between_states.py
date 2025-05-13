import pandas as pd
import json
import os
from backend.tmcid_mapper import TmcidMapper

class SankeyDataBuilder:
    def __init__(self, csv_path, output_json_path="static/question9_state.json", threshold=5):
        self.csv_path = csv_path
        self.output_json_path = output_json_path
        self.threshold = threshold
        self.df = None
        self.filtered_df = None
        self.unique_states = []
        self.sankey_data = {}

    def load_and_preprocess(self):
        df = pd.read_csv(self.csv_path)
        # Rename the malformed column name
        df = df.rename(columns={'usertmcmapping â†’ statename': 'State_Name'})

        # Keep necessary columns
        df = df[['crt_object_id', 'State_Name', 'createdtime', 'transferredto']]

        # Only IDs with multiple events
        ids_to_keep = df['crt_object_id'].value_counts()[lambda x: x > 1].index
        df = df[df['crt_object_id'].isin(ids_to_keep)]

        # Clean and dedupe
        df['createdtime'] = pd.to_datetime(df['createdtime'], errors='coerce')
        df = df.dropna(subset=['createdtime', 'crt_object_id']).drop_duplicates()
        df['State_Name'] = df['State_Name'].str.strip().str.title()

        # Only initial transfers (transferredto == '0')
        df = df[df['transferredto'] == '0']
        df = df.sort_values(by=['crt_object_id', 'createdtime'])

        self.df = df

    def compute_transfers(self):
        transfers = []
        for crt_id, group in self.df.groupby('crt_object_id'):
            states = group['State_Name'].tolist()
            for i in range(len(states) - 1):
                if states[i] != states[i + 1]:
                    transfers.append({'from_state': states[i], 'to_state': states[i + 1]})

        if transfers:
            df_transfers = pd.DataFrame(transfers)
            df_counts = (
                df_transfers
                .groupby(['from_state', 'to_state'])
                .size()
                .reset_index(name='transfer_count')
            )
        else:
            df_counts = pd.DataFrame(columns=['from_state', 'to_state', 'transfer_count'])

        # Apply threshold
        df_counts['transfer_count'] = pd.to_numeric(df_counts['transfer_count'], errors='coerce')
        self.filtered_df = df_counts[df_counts['transfer_count'] > self.threshold]

    def build_sankey_json(self):
        # Build a single list of unique node labels
        self.unique_states = sorted(
            set(self.filtered_df['from_state']).union(self.filtered_df['to_state'])
        )

        # Map each transfer to source/target indices in that list
        source_indices = [self.unique_states.index(s) for s in self.filtered_df['from_state']]
        target_indices = [self.unique_states.index(t) for t in self.filtered_df['to_state']]
        values = self.filtered_df['transfer_count'].tolist()

        print(self.unique_states)
        m = TmcidMapper()
        m.load_mapper()
        uni = m.map_list(self.unique_states)
        print(uni)

        self.sankey_data = {
            'nodes': uni,
            'source': source_indices,
            'target': target_indices,
            'value': values
        }

    def save_to_json(self):
        os.makedirs(os.path.dirname(self.output_json_path), exist_ok=True)

        
        #self.sankey_data[]

        with open(self.output_json_path, 'w') as f:
            json.dump(self.sankey_data, f, indent=4)
        print(f"Sankey data saved to {self.output_json_path}")

    def run_all(self):
        self.load_and_preprocess()
        self.compute_transfers()
        self.build_sankey_json()
        self.save_to_json()


if __name__ == "__main__":
    builder = SankeyDataBuilder(csv_path="database/Anonymized_Call_Handle_Data.csv")
    builder.run_all()
