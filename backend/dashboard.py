import pandas as pd
import json
import os
from backend.tmcid_mapper import TmcidMapper

class CallFlowDashboard:
    """
    Encapsulates funnel computation for call data.
    """
    DEFAULT_EXCLUDE_TMCS = ['ML02_TMC', 'docutoroutboud', 'KIRAN', 'IIITB_OB', 'Training_TMC_UK']
    FUNNEL_STAGES = [
        ("Received",       lambda df: df),
        ("Chose State",    lambda df: df[df['tmcid'] != 'TeleManas_Master_Inbound_DONOT_TOUCH']),
        ("Chose Language", lambda df: df[~((df['crt_object_id'].isna()) & (df['callstatus'] != 'CONNECTED'))]),
        ("Connected",      lambda df: df[df['callstatus'] == 'CONNECTED']),
        ("Successful",     lambda df: df[df['telemanas_id'].notna()]),
        ("Gave Rating",    lambda df: df[df['rating'].isin(['1','2','3','4','5','No Input'])])
    ]

    def __init__(self, df: pd.DataFrame, exclude_tmcs=None):
        self.exclude_tmcs = exclude_tmcs or self.DEFAULT_EXCLUDE_TMCS
        self.df = df.copy()
        self.df_in = None

    def load_and_filter(self):
        # remove unwanted tmcs, keep only Incoming
        self.df = self.df[~self.df['tmcid'].isin(self.exclude_tmcs)]
        self.df_in = self.df[self.df['call_type'] == 'Incoming']

    def compute_funnel(self, df: pd.DataFrame) -> dict:
        labels = [lbl for lbl,_ in self.FUNNEL_STAGES]
        counts = []
        cur = df
        for _, fn in self.FUNNEL_STAGES:
            cur = fn(cur)
            counts.append(len(cur))
        dropoffs = [counts[i] - counts[i+1] for i in range(len(counts)-1)]
        dropoffPct = [
            round(dropoffs[i]/counts[i]*100,1) if counts[i]>0 else 0.0
            for i in range(len(dropoffs))
        ]
        return {
            "labels": labels,
            "values": counts,
            "dropoffs": dropoffs,
            "dropoffPercentages": dropoffPct
        }

    def run(self):
        self.load_and_filter()
        out = []
        # country-level
        out.append({"state":"India", "callFlow": self.compute_funnel(self.df_in)})
        # state-level
        after_state = self.FUNNEL_STAGES[1][1](self.df_in)  # after "Chose State"
        for st in after_state['tmcid'].unique():
            df_st = self.df_in[self.df_in['tmcid']==st]
            out.append({"state": st, "callFlow": self.compute_funnel(df_st)})
        return out


class extract_for_dashboard:
    def __init__(self, call_analysis_path, funnel_chart_dataset):
        # load main call data
        self.df = pd.read_csv(call_analysis_path)
        # filter genders
        self.df = self.df[self.df['Gender'].isin(['Male','Female','Transgender'])]
        # load funnel dataset
        self.funnel_df = pd.read_csv(funnel_chart_dataset)

        self.final_json = []

    def prepare_data_before_moving_on(self):
        df = self.df
        # parse times
        df['callstarttime'] = pd.to_datetime(df['callstarttime'], errors='coerce')
        df['callendtime']   = pd.to_datetime(df['callendtime'],   errors='coerce')
        df = df.dropna(subset=['callstarttime','callendtime'])
        df['callenddate'] = df['callendtime'].dt.date
        df['day']        = df['callenddate'].apply(lambda d: pd.to_datetime(d).day_name())
        df['Month']      = df['callenddate'].apply(lambda d: d.strftime('%b'))
        # customer talk time: convert then normalize
        df['customertalktime'] = pd.to_datetime(df['customertalktime'], errors='coerce')
        df = df.dropna(subset=['customertalktime'])
        midnight = df['customertalktime'].dt.normalize()
        df['customertalktime'] = df['customertalktime'] - midnight
        self.df = df

    def avg_duration(self, df):
        # average of customertalktime per day
        out = []
        for date, grp in df.groupby('callenddate'):
            mins = grp['customertalktime'].dt.total_seconds().mean() / 60
            out.append({"date": str(date), "minutes": round(mins,2)})
        return out

    def gender_count(self, df):
        cnt = df['Gender'].value_counts().to_dict()
        for g in ['Male','Female','Transgender']:
            cnt.setdefault(g,0)
        return cnt

    def timeseries(self, df):
        return [{"date":str(d), "calls":len(g)} for d,g in df.groupby('callenddate')]

    def byWeekday(self, df):
        # Ensure output is ordered Mon–Sun
        order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        # Count grouped by three-letter day
        counts = df.groupby(df['day'].str[:3]).size().to_dict()
        return {day: counts.get(day, 0) for day in order}

    def byAgeGroup(self, df):
        col = "patient â†’ age"
        df2 = df.dropna(subset=[col])
        df2[col] = pd.to_numeric(df2[col], errors='coerce')
        df2 = df2.dropna(subset=[col])
        bins = [0,18,25,35,45,55,float('inf')]
        labels = ["Under 18","18-24","25-34","35-44","45-54","55+"]
        grp = pd.cut(df2[col], bins=bins, labels=labels, right=False)
        return grp.value_counts().reindex(labels, fill_value=0).to_dict()

    def callsByDirection(self, df):
        out = []
        for m,grp in df.groupby('Month'):
            d = {"month":m}
            d.update(grp['call_type'].value_counts().to_dict())
            out.append(d)
        return out

    def triage(self, df):
        return df['triage'].value_counts().to_dict()

    def index(self):
        # preprocess
        self.prepare_data_before_moving_on()
        # funnel object
        funneler = CallFlowDashboard(self.funnel_df)
        funnel_out = funneler.run()

        # India summary
        india = {
            "state":"India",
            "totalCalls": len(self.df),
            "byGender": self.gender_count(self.df),
            "timeseries": self.timeseries(self.df),
            "avgDuration": self.avg_duration(self.df),
            "byWeekday": self.byWeekday(self.df),
            "byAgeGroup": self.byAgeGroup(self.df),
            "callsByDirection": self.callsByDirection(self.df),
            "triage": self.triage(self.df),
            "callflow": next(x for x in funnel_out if x['state']=="India")['callFlow']
        }
        self.final_json.append(india)

        # per-state
        for state in self.df['tmcid'].unique():
            df_st = self.df[self.df['tmcid']==state]

            m = TmcidMapper()
            m.load_mapper()
            state1 = m.map_list([state])[0]

            print("\n*******State*****\n", state)
            self.final_json.append({
                "state": state1,
                "totalCalls": len(df_st),
                "byGender": self.gender_count(df_st),
                "timeseries": self.timeseries(df_st),
                "avgDuration": self.avg_duration(df_st),
                "byWeekday": self.byWeekday(df_st),
                "byAgeGroup": self.byAgeGroup(df_st),
                "callsByDirection": self.callsByDirection(df_st),
                "triage": self.triage(df_st),
                "callflow": next(x for x in funnel_out if x['state']==state)["callFlow"]
            })

        # store
        os.makedirs("static", exist_ok=True)
        with open("static/states.json","w") as f:
            json.dump(self.final_json, f, indent=2)

        return self.final_json

if __name__ == "__main__":
    extractor = extract_for_dashboard(
        call_analysis_path="database/counselling_data.csv",
        funnel_chart_dataset="database/Anonymized_Call_Handle_Data.csv"
    )
    data = extractor.index()
