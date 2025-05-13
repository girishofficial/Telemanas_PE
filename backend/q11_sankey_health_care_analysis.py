import os
import json
import pandas as pd
import numpy as np
from backend.tmcid_mapper import TmcidMapper 

class SankeyJSONGenerator:
    """
    Generate Sankey JSONs:
      • Country: single-stage Gender → Age_Group
      • State: single-stage Gender → Age_Group, for each tmcid
    Total flow in each JSON equals number of rows in the relevant subset.
    """

    def __init__(self, df: pd.DataFrame, output_dir: str = 'static'):
        self.df = df.copy()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._preprocess()

    def _preprocess(self):
        # Rename columns
        self.df = self.df.rename(columns={
            'patient â†’ age': 'Patient_age',
            'config_individual_calling â†’ name': 'Called_by',
            'Gender': 'Gender',
            'tmcid': 'tmcid'
        })
        # Fill defaults & drop bad rows
        self.df['Called_by'].fillna('Patient', inplace=True)
        self.df.dropna(subset=['Patient_age'], inplace=True)
        self.df['Gender'].fillna('Prefer Not To Say', inplace=True)
        # Derive Age_Group
        self.df['Age_Group'] = self.df['Patient_age'].apply(self._categorize_age)

    @staticmethod
    def _categorize_age(age: float) -> str:
        if age <= 20:
            return 'Children'
        elif age <= 60:
            return 'Adults'
        else:
            return 'Elders'

    def _build_nodes_gender_age(self):
        # nodes = sorted unique genders + fixed age groups
        genders    = sorted(self.df['Gender'].unique())
        age_groups = ['Adults', 'Children', 'Elders']
        return genders + age_groups

    def _build_links_gender_age(self, subset: pd.DataFrame):
        # returns (nodes, source, target, value) for Gender→Age_Group
        links = (
            subset
            .groupby(['Gender', 'Age_Group'])
            .size()
            .reset_index(name='Count')
        )
        nodes = self._build_nodes_gender_age()
        idx   = {n:i for i,n in enumerate(nodes)}

        source = links['Gender'].map(idx).tolist()
        target = links['Age_Group'].map(idx).tolist()
        value  = links['Count'].tolist()
        return nodes, source, target, value

    def generate_country_json(self, filename: str = 'question11_country.json'):
        nodes, source, target, value = self._build_links_gender_age(self.df)
        data = {
            'nodes':      nodes,
            'source':     source,
            'target':     target,
            'value':      value,
            'nodeColors': [
                "#4f83cc","#3498db","#9b59b6","#95a5a6","#34495e",
                "#2ecc71","#e74c3c","#f1c40f","#e67e22","#8e44ad",
                "#16a085","#7f8c8d"
            ]
        }
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"▶ Country JSON written to {path}")

    def generate_state_json(self, filename: str = 'question11_state.json'):
        states = sorted(self.df['tmcid'].unique())
        self.mapper = TmcidMapper()
        self.mapper.load_mapper()
        states = self.mapper.map_list(states)


        state_data = {
            'states': states,
            'nodes': self._build_nodes_gender_age(),
            'sources': [],
            'targets': [],
            'values': []
        }

        nodes = state_data['nodes']
        node_indices = {node: i for i, node in enumerate(nodes)}

        for state in states:
            subset = self.df[self.df['tmcid'] == state]
            links = (
                subset
                .groupby(['Gender', 'Age_Group'])
                .size()
                .reset_index(name='Count')
            )
            sources = links['Gender'].map(node_indices).tolist()
            targets = links['Age_Group'].map(node_indices).tolist()
            values = links['Count'].tolist()

            state_data['sources'].append(sources)
            state_data['targets'].append(targets)
            state_data['values'].append(values)

        state_data['nodeColors'] = [
            "#4f83cc","#3498db","#9b59b6","#95a5a6","#34495e",
            "#2ecc71","#e74c3c","#f1c40f","#e67e22","#8e44ad",
            "#16a085","#7f8c8d"
        ]

        path = os.path.join(self.output_dir, filename)
        with open(path, 'w') as f:
            json.dump(state_data, f, indent=2)
        print(f"▶ State JSON written to {path}")


if __name__ ==  "__main__":
    df = pd.read_csv('database/counselling_data.csv')  # make sure 'tmcid' is present
    gen = SankeyJSONGenerator(df, output_dir='static')
    gen.generate_country_json()    # writes static/question11_country.json
    gen.generate_state_json()      # writes static/question11_state.json