import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non‑interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker


import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non‑interactive backend
import matplotlib.pyplot as plt


class DynamicPieChart:
    def __init__(
        self,
        data_dict: dict[int, int],
        bin_gap: int,
        max_sectors: int = 5,
        pct_threshold: float = 6,
        cmap_name: str = 'Set3',
        default_save_path: str | None = None
    ):
        self.data = data_dict
        self.bin_gap = bin_gap
        self.max_sectors = max_sectors
        self.pct_threshold = pct_threshold
        self.cmap = plt.get_cmap(cmap_name)
        self.default_save_path = default_save_path
        self.binned: list[tuple[str, int]] | None = None

    def _compute_bins(self):
        total_count = sum(self.data.values()) or 1
        overflow_start = (self.max_sectors - 1) * self.bin_gap

        binned: list[tuple[str, int]] = []
        for i in range(self.max_sectors):
            if i < self.max_sectors - 1:
                start = i * self.bin_gap
                end = (i + 1) * self.bin_gap - 1
                this_cnt = sum(
                    v for day, v in self.data.items()
                    if start <= day <= end
                )
                this_pct = this_cnt / total_count * 100

                # merge into overflow if below threshold (and not first bin)
                if this_pct < self.pct_threshold and i > 0:
                    rem_cnt = sum(
                        v for day, v in self.data.items()
                        if day > end
                    )
                    this_cnt += rem_cnt
                    label = f">={start} days\n"
                    binned.append((label, this_cnt))
                    break

                label = f"{start}–{end} days"
                binned.append((label, this_cnt))
            else:
                final_cnt = sum(
                    v for day, v in self.data.items()
                    if day >= overflow_start
                )
                label = f">={overflow_start} days\n({final_cnt})"
                binned.append((label, final_cnt))

        self.binned = binned

    def get_binned(self) -> dict[str, list]:
        """
        Returns the computed bins as a dict:
          { "labels": [...], "counts": [...] }
        """
        if self.binned is None:
            self._compute_bins()
        labels, counts = zip(*self.binned)
        return {"labels": list(labels), "counts": list(counts)}


    def save_binned_json(self, path: str) -> str:
        """
        Writes the binned data to `path` as JSON.
        Returns the file path.
        """
        binned_dict = self.get_binned()
        with open(path, 'w') as f:
            json.dump(binned_dict, f, indent=2)
        return path

    def plot(self, title: str | None = None, save_path: str | None = None):
        if self.binned is None:
            self._compute_bins()

        # filter out zero-count slices
        filtered = [(lab, cnt) for lab, cnt in self.binned if cnt > 0]
        if not filtered:
            print("⚠️  No data to plot; skipping pie chart.")
            return

        labels, values = zip(*filtered)
        total = sum(values)

        # use single base color with alpha by proportion
        base_rgb = self.cmap(0.5)[:3]
        colors = [(*base_rgb, cnt / total) for cnt in values]

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            values,
            labels=labels,
            autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct * total / 100))})",
            startangle=90,
            colors=colors,
            textprops={'fontweight': 'bold', 'fontsize': 16}
        )
        ax.axis('equal')
        if title:
            ax.set_title(title, fontweight='extra bold', fontsize=16, pad=30)
        plt.tight_layout()

        out = save_path or self.default_save_path
        if out:
            fig.savefig(out, bbox_inches='tight')
            print(f"✔ Pie chart saved to: {out}")
        plt.close(fig)



import matplotlib.pyplot as plt
import numpy as np

class DynamicBarChart:
    def __init__(
        self,
        data_dict: dict[int, int],
        bin_gap: int,
        max_bars: int = 7,
        cmap_name: str = 'Set3',
        default_save_path: str | None = None
    ):
        self.data = data_dict
        self.bin_gap = bin_gap
        self.max_bars = max_bars
        self.cmap = plt.get_cmap(cmap_name)
        self.default_save_path = default_save_path
        self.binned: list[tuple[str, int]] | None = None

    def _compute_bins(self):
        bins = [0] * self.max_bars
        overflow_start = (self.max_bars - 1) * self.bin_gap
        for day, cnt in self.data.items():
            idx = day // self.bin_gap if day < overflow_start else self.max_bars - 1
            bins[idx] += cnt

        labels = []
        for i, total in enumerate(bins):
            if i < self.max_bars - 1:
                start = i * self.bin_gap
                end = (i + 1) * self.bin_gap - 1
                lbl = f"{start}–{end}"
            else:
                lbl = f">={overflow_start}"
            labels.append((lbl, total))

        self.binned = labels

    def get_binned(self) -> dict[str, list]:
        """
        Returns the binned data as a dict:
          { "labels": [...], "counts": [...] }
        """
        if self.binned is None:
            self._compute_bins()
        labels, counts = zip(*self.binned)
        return {"labels": list(labels), "counts": list(counts)}

    def save_binned_json(self, path: str) -> str:
        """
        Saves the binned data to `path` as JSON.
        Returns the file path.
        """
        binned_dict = self.get_binned()
        with open(path, 'w') as f:
            json.dump(binned_dict, f, indent=2)
        return path

    def plot(self, title: str | None = None, save_path: str | None = None):
        if self.binned is None:
            self._compute_bins()

        filtered = [(lbl, val) for lbl, val in self.binned if val > 0]
        if not filtered:
            print("⚠️  No data to plot; skipping bar chart.")
            return

        labels, counts = zip(*filtered)
        x = np.arange(len(labels))

        single_color = self.cmap(0.5)

        fig, ax = plt.subplots(figsize=(max(6, len(labels)*1.2), 5))
        bars = ax.bar(x, counts, color=single_color)

        total = sum(counts)
        for i, bar in enumerate(bars):
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                h + total*0.005,
                f"{counts[i]}",
                ha='center', va='bottom',
                fontsize=10, fontweight='bold'
            )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontweight='bold', rotation=45, ha='right')
        ax.set_xlabel("Days Bin", fontweight='bold')
        ax.set_ylabel("Count", fontweight='bold')

        if title:
            ax.set_title(title, fontweight='extra bold', fontsize=14, pad=15)

        plt.tight_layout()

        out = save_path or self.default_save_path
        if out:
            fig.savefig(out, bbox_inches='tight')
            print(f"✔ Bar chart saved to: {out}")
        plt.close(fig)


class DynamicSpiderChart:
    def __init__(
        self,
        data_dict: dict[int, int],
        bin_gap: int,
        max_axes: int = 7,
        cmap_name: str = 'Set3',
        default_save_path: str | None = None
    ):
        self.data = data_dict
        self.bin_gap = bin_gap
        self.max_axes = max_axes
        self.cmap = plt.get_cmap(cmap_name)
        self.default_save_path = default_save_path
        self.binned: list[tuple[str, int]] | None = None

    def _compute_bins(self):
        bins = [0] * self.max_axes
        overflow_start = (self.max_axes - 1) * self.bin_gap
        for day, cnt in self.data.items():
            idx = day // self.bin_gap if day < overflow_start else self.max_axes - 1
            bins[idx] += cnt
        labels = []
        for i, total in enumerate(bins):
            if total == 0:
                continue
            if i < self.max_axes - 1:
                start, end = i*self.bin_gap, (i+1)*self.bin_gap - 1
                lbl = f"{start}–{end}"
            else:
                lbl = f">={overflow_start}"
            labels.append((lbl, total))
        self.binned = labels

    def plot(self, title: str | None = None, save_path: str | None = None):
        if self.binned is None:
            self._compute_bins()

        filtered = [(l, v) for l, v in self.binned if v > 0]
        if not filtered:
            print("⚠️  No data to plot; skipping spider chart.")
            return

        labels, values = zip(*filtered)
        n = len(values)
        angles = np.linspace(0, 2*np.pi, n, endpoint=False).tolist()
        stats = list(values) + [values[0]]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True), dpi=200)
        ax.plot(angles, stats, color=self.cmap(0.5), linewidth=2, marker='o')
        ax.fill(angles, stats, alpha=0.25, color=self.cmap(0.5))

        max_stat = max(values)
        for angle, val in zip(angles[:-1], values):
            ax.text(angle, val + max_stat*0.10, str(val), ha='center', va='bottom', fontsize=14, fontweight='bold')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontweight='bold', fontsize=16)
        ax.tick_params(axis='x', pad=50)
        ax.yaxis.set_visible(False)
        if title:
            ax.set_title(title, fontweight='extra bold', fontsize=18, pad=30)
        plt.tight_layout()

        out = save_path or self.default_save_path
        if out:
            fig.savefig(out, bbox_inches='tight')
            print(f"✔ Spider chart saved to: {out}")
        plt.close(fig)


class DynamicRadarChart:
    def __init__(
        self,
        data_dict: dict[int, int],
        bin_gap: int,
        max_axes: int = 7,
        cmap_name: str = 'Set3',
        default_save_path: str | None = None
    ):
        self.data = data_dict
        self.bin_gap = bin_gap
        self.max_axes = max_axes
        self.cmap = plt.get_cmap(cmap_name)
        self.default_save_path = default_save_path
        self.binned: tuple[list[str], list[int]] | None = None

    def _compute_bins(self):
        bins = [0] * self.max_axes
        overflow_start = (self.max_axes - 1) * self.bin_gap
        for day, cnt in self.data.items():
            idx = day // self.bin_gap if day < overflow_start else self.max_axes - 1
            bins[idx] += cnt

        labels, counts = [], []
        for i, total in enumerate(bins):
            if total == 0:
                continue
            if i < self.max_axes - 1:
                start = i * self.bin_gap
                end = (i + 1) * self.bin_gap - 1
                lbl = f"{start}–{end} days"
            else:
                lbl = f">={overflow_start} days"
            labels.append(lbl)
            counts.append(total)

        self.binned = (labels, counts)

    def get_binned(self) -> dict[str, list]:
        """
        Returns the computed bins as a Python dict:
          { "labels": [...], "counts": [...] }
        """
        if self.binned is None:
            self._compute_bins()
        labels, counts = self.binned
        return {"labels": labels, "counts": counts}

    def save_binned_json(self, path: str) -> str:
        """
        Computes (if needed) and writes the binned data to `path` as JSON.
        Returns the file path for your reference.
        """
        binned_dict = self.get_binned()
        with open(path, 'w') as f:
            json.dump(binned_dict, f, indent=2)
        return path

    def plot(self, title: str | None = None, save_path: str | None = None):
        if self.binned is None:
            self._compute_bins()

        labels, counts = self.binned
        if len(counts) < 3:
            print("⚠️  Need at least 3 non-zero bins for a radar chart; skipping.")
            return

        N = len(counts)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        values = counts + [counts[0]]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi/2 + np.deg2rad(10))
        ax.plot(angles, values, color=self.cmap(0.5), linewidth=2)
        ax.fill(angles, values, facecolor=self.cmap(0.5), alpha=0.4)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontweight='bold')
        ax.tick_params(axis='x', pad=20)

        max_val = max(counts)
        for angle, val in zip(angles[:-1], counts):
            ax.text(
                angle,
                val + max_val * 0.05,
                str(val),
                ha='center',
                va='center',
                fontweight='bold',
                fontsize=9
            )

        ax.set_yticklabels([])
        if title:
            ax.set_title(title, fontweight='extra bold', fontsize=18, pad=30)
        plt.tight_layout()

        out = save_path or self.default_save_path
        if out:
            fig.savefig(out, bbox_inches='tight')
            print(f"✔ Radar chart saved to: {out}")
        plt.close(fig)

# ... rest of your data-prep and graph_generator classes unchanged ...





class prepare_data_in_dictioanry_to_make:
    def __init__(self, data):
        # copy & parse datetime with mixed formats
        self.data = data.copy()
        self.data['callendtime'] = pd.to_datetime(
            self.data['callendtime'],
            infer_datetime_format=True,
            errors='coerce'           # invalid parses → NaT
        )
        self.dictionary = {}
        self.total_count_unique_maksed_in_succesful = 0

    def procedure(self):
        print("""
        1. Read or download the data and store it in memory cache.\n
        2. Do you want decide the call type , consider the state , anything at low level and send data to this class.\n
        3. Consider the rows which are successful only.\n
        4. Consider the unique masked calls from the  successful.\n
        5. Remove all the rows which were before the first succesful, that is all unsucessful before successful.\n 
        6. Now pass  only this column to the function which make the days difference and sends dictioanry making the counts for days differnce and give the final result in terms of dictionary.\n
        7. use this makenay of theh raphs of your own wish. 
        """)

    def preprocess_data_return_dictionary(self):
        df = self.data

        # filter only successful
        mask_succ = (
            df['counselling_data - crt_object_id â†’ resolution'] == 'Successful'
        )

        # each phone’s first success
        first_success = (
            df.loc[mask_succ]
              .groupby('masked_phone')['callendtime']
              .min()
        )
        self.total_count_unique_maksed_in_succesful = first_success.shape[0]

        # map back, keep calls >= first success
        df['first_success_time'] = df['masked_phone'].map(first_success)
        df = df[df['callendtime'] >= df['first_success_time']]

        # sort & compute predecessor gap
        df = df.sort_values(['masked_phone','callendtime'])
        df['prev_call'] = df.groupby('masked_phone')['callendtime'].shift(1)
        df = df[df['prev_call'].notna()]

        # day‐diff
        df['day_diff'] = (df['callendtime'] - df['prev_call']) \
                          .dt.days.abs().astype(int)

        # tally
        #df.to_csv("Explanation2.csv")
        self.dictionary = df['day_diff'].value_counts().to_dict()
        return self.dictionary











class get_the_dictionary_based_on_the_filters:
    def __init__(self, path):
        # read with low_memory=False to suppress mixed‑dtype warnings
        self.df = pd.read_csv(path, low_memory=False)
        print("Data is loaded\n")

    def return_tmc_list(self):
        return list(self.df['tmcid'].unique())

    def collect_data(self):
        return self.df

    def filter_based_on_the_call_type(self, data, type='Incoming'):
        if type is None: 
            return data
        return data[data['call - crt_object_id â†’ call_types'] == type]

    def filter_based_on_tmc(self, data, tmc=None):
        if tmc is None:
            return data
        return data[data['tmcid'] == tmc]
    
    def remove_crt_object_id_to_make_the_zeroth_day_more_entries_removal(self,data):
        return data.drop_duplicates(subset='crt_object_id', keep='first')

    def make_it(self, tmc=None, type=None):
        

        df = self.collect_data()
        df = self.filter_based_on_the_call_type(df, type)
        df = self.filter_based_on_tmc(df, tmc)
        df = self.remove_crt_object_id_to_make_the_zeroth_day_more_entries_removal(df)
        #Now I am  removing the duplicates of the crt object id, which keeps the actual 
        #0th day data


        prep = prepare_data_in_dictioanry_to_make(df)
        return prep.preprocess_data_return_dictionary()
        




class graph_generator:
    def __init__(self,path):
        self.data_obj = get_the_dictionary_based_on_the_filters(path)


    
    def deciding_factors(self,tmc=None, call_type=None, days=None, bins=None):
        
        self.India = self.data_obj.make_it(type=call_type)
        self.India =  dict(sorted(self.India.items()))
        self.total_india = sum(self.India.values())
        print("India: ", self.India)


        print("India's Data is ready, now it is time to make the graphs\n")
        chart = DynamicPieChart(self.India, bin_gap=days, max_sectors=bins, cmap_name='Set3')
        chart.plot(title=f"", save_path='static/charts/INDIA_PIE_CHART.png')
        print()


        #this is about the bar  chart
        bar_chart = DynamicBarChart(self.India, bin_gap=days, max_bars=bins)
        bar_chart.plot(title=f"", save_path='static/charts/INDIA_BAR_CHART.png')

        #spider = DynamicSpiderChart(self.India, bin_gap=days, max_axes= bins)
        #spider.plot(title=f"", save_path='static/charts/INDIA_SPIDER_CHART.png')

        radar =  DynamicRadarChart(self.India, bin_gap= days,max_axes= bins)
        radar.plot(title=f"", save_path="static/charts/INDIA_RADAR_PLOT.png")
        print("Indian charts are done\n\n")

        indian_list_names=['INDIA_PIE_CHART.png', 
                           'INDIA_BAR_CHART.png',
                          
                           "INDIA_RADAR_PLOT.png"
                           ]

       ########################TMC STARTS#########################

        print(f"TMC Started\nTMC name{tmc}")
        self.tmc = self.data_obj.make_it(type=call_type,tmc=tmc)
        self.tmc =  dict(sorted(self.tmc.items()))
        self.total_tmc = sum(self.tmc.values())
        print("TMC: ",self.tmc ,"\n")

        #print("India's Data is ready, now it is time to make the graphs\n")
        chart = DynamicPieChart(self.tmc, bin_gap=days, max_sectors=bins, cmap_name='Set3')
        chart.plot(title=f"", save_path=f'static/charts/{tmc}_PIE_CHART.png')
        print()


        #this is about the bar  chart
        bar_chart = DynamicBarChart(self.tmc, bin_gap=days, max_bars=bins)
        bar_chart.plot(title=f"", save_path=f'static/charts/{tmc}_BAR_CHART.png')

        #spider = DynamicSpiderChart(self.tmc, bin_gap=days, max_axes= bins)
        #spider.plot(title=f"{tmc}   COUNT = {self.total_tmc}", save_path=f'static/charts/{tmc}_SPIDER_CHART.png')

        radar =  DynamicRadarChart(self.tmc, bin_gap= days,max_axes= bins)
        radar.plot(title=f"", save_path=f"static/charts/{tmc}_RADAR_PLOT.png")
        print("TMC charts are done\n\n")

        tmc_list_names=[f'{tmc}_PIE_CHART.png', 
                        f'{tmc}_BAR_CHART.png', 
                        f"{tmc}_RADAR_PLOT.png"
                        ]
        
        return indian_list_names, tmc_list_names

       

incoming_pie_chart_json = {}
incoming_bar_chart_json = {}
incoming_radar_chart_json={}

# Example usage
if __name__ == "__main__":
    data_obj = get_the_dictionary_based_on_the_filters("data.csv")
    India = data_obj.make_it(type=None)
    India =  dict(sorted(India.items()))
    total_india = sum(India.values())
    #print(sorted_by_key)
    #print("India: ", India)
    
    # this was about the pie chart
    chart = DynamicPieChart(India, bin_gap=5, max_sectors=7, cmap_name='Set3')
    chart.plot(title=f"INDIA  COUNT = {total_india}", save_path='INDIA_PIE_CHART.png')
    print("pie binnned ",chart.get_binned())
    incoming_pie_chart_json["INDIA"] = chart.get_binned()



    #this is about the bar  chart
    bar_chart = DynamicBarChart(India, bin_gap=5, max_bars=7)
    bar_chart.plot(title=f"", save_path='INDIA_BAR_CHART.png')
    print("Bar binnned ",bar_chart.get_binned())
    incoming_bar_chart_json["INDIA"] = bar_chart.get_binned()

   

    radar =  DynamicRadarChart(India, bin_gap= 5,max_axes= 7)
    radar.plot(title=f"", save_path="INDIA_RADAR_PLOT.png")
    binned = radar.get_binned()
    print("Binned: ", binned)
    incoming_radar_chart_json["INDIA"] = radar.get_binned()


    ##now it is the time to make teh json for each and every state or TMC based. 





    for i in ['Uttar_Pradesh', 'Kerala', 'Gujarat', 'Tamil_Nadu', 'Maharashtra',
       'Madhya_Pradesh', 'Odisha', 'Jharkhand', 'Karnataka',
       'Chhattisgarh', 'West_Bengal', 'Mizoram', 'Telangana',
       'Jammu_Kashmir', 'Pondicherry', 'Dadra_Daman_Diu', 'Goa', 'Assam',
       'Punjab', 'Andhra_Pradesh', 'Delhi', 'Tripura', 'Chandigarh',
       'Bihar', 'Rajasthan', 'TeleManas_Master_Inbound_DONOT_TOUCH',
       'Haryana', 'Arunachal_Pradesh', 'Lakshadweep',
       'Ladakh', 'Manipur', 'Meghalaya', 'Nagaland', 'Himachal_Pradesh',
       'Uttarakhand', 'Andaman_Nicobar', 'Sikkim', 'AFMS'
       ]:
        tmc= data_obj.make_it(type=None,tmc=i)
        tmc = dict(sorted(tmc.items()))

        pie =   DynamicPieChart(tmc, bin_gap=5, max_sectors=7, cmap_name='Set3')
        chart.plot(title=f"INDIA  COUNT = {total_india}", save_path='INDIA_PIE_CHART.png')
        #print("pie binnned ",chart.get_binned())
        incoming_pie_chart_json[i] = chart.get_binned()

        bar_chart = DynamicBarChart(tmc, bin_gap=5, max_bars=7)
        bar_chart.plot(title=f"", save_path='INDIA_BAR_CHART.png')
        print("Bar binnned ",bar_chart.get_binned())
        incoming_bar_chart_json[i] = bar_chart.get_binned()

        radar =  DynamicRadarChart(tmc, bin_gap= 5,max_axes= 7)
        radar.plot(title=f"", save_path="INDIA_RADAR_PLOT.png")
        binned = radar.get_binned()
        print("Binned: ", binned)
        incoming_radar_chart_json[i] = radar.get_binned()
        


    file_path = "overall_radar.json"

    # Save dictionary to a JSON file
    import json
    with open(file_path, 'w') as f:
        json.dump(incoming_radar_chart_json, f, indent=2)

    print(f"✔ JSON saved to {file_path}")


    file_path = "overall_pie.json"
    with open(file_path, 'w') as f:
        json.dump(incoming_radar_chart_json, f, indent=2)

    print(f"✔ JSON saved to {file_path}")

    file_path = "overall_bar.json"
    with open(file_path, 'w') as f:
        json.dump(incoming_bar_chart_json, f, indent=2)

    print(f"✔ JSON saved to {file_path}")













