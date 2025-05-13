# tmcid_mapper.py

import pandas as pd

class TmcidMapper:
    def __init__(self, mapper_csv_path: str="database/mapped_states.csv"):
        self.mapper_csv_path = mapper_csv_path
        self.mapper_df = None
        self.lookup = {}

    def load_mapper(self):
        self.mapper_df = pd.read_csv(self.mapper_csv_path)
        self.lookup = dict(zip(self.mapper_df['actual'], self.mapper_df['mapping']))

    def map_list(self, input_list: list[str]) -> list[str]:
        if not self.lookup:
            raise RuntimeError("Mapper not loaded. Call load_mapper() first.")
        return [self.lookup.get(item, item) for item in input_list]
