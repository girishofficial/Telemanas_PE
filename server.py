import os
import sys
import time
import logging
import subprocess
from threading import Thread
from flask import Flask, render_template, request
from flask_cors import CORS

import pandas as pd
import numpy as np

from backend.q1_repeated_calls.charts_generator import graph_generator
from backend.dashboard import extract_for_dashboard
from backend.q2_time_bar_call_analysis import TimeWindowCounter
from backend.q6_statewise_call_chroloropleth import TmcidJsonExporter
from backend.q14_district_wise_call_complaints import DistrictGenderCounter
from backend.q9_sankey_transfer_between_states import SankeyDataBuilder
from backend.q11_sankey_health_care_analysis import SankeyJSONGenerator
from backend.q12_violin_monthly_analysis import ViolinDataBuilder
from backend.q13_calendar import WeekdayMonthlyAggregator
from backend.q15_funnel_chart import CallFlowDashboard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticJSONGeneratorForDashboardAndQuestions:
    def __init__(self):
        logger.info("Preparing to generate static JSON files...")

    def generate(self):
        # Dashboard
        extract_for_dashboard(
            call_analysis_path="database/counselling_data.csv",
            funnel_chart_dataset="database/Anonymized_Call_Handle_Data.csv"
        ).index()

        # Q2 - Time Bar Chart
        TimeWindowCounter(
            csv_path="database/Anonymized_Call_Handle_Data.csv",
            tmcid_col="tmcid",
            time_col="createdtime"
        ).run()

        # Q6 - Choropleth Map
        exporter = TmcidJsonExporter(
        csv_path="database/counselling_data.csv",
        mapper_csv_path="database/mapped_states.csv",
        out_path="static/question6_country.json"
    )
        exporter.load_data()
        exporter.save_json()
        exporter.save_statewise_top_districts("static/question6_state.json")


        # Q14 - Population Pyramid
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

        # Q9 - Sankey (State Transfers)
        builder = SankeyDataBuilder(csv_path="database/Anonymized_Call_Handle_Data.csv")
        builder.run_all()

        # Q11 - Sankey (Healthcare)
        df = pd.read_csv('database/counselling_data.csv')  # make sure 'tmcid' is present
        gen = SankeyJSONGenerator(df, output_dir='static')
        gen.generate_country_json()    # writes static/question11_country.json
        gen.generate_state_json() 

        # Q12 - Violin Charts
        builder = ViolinDataBuilder(
            csv_path="database/Anonymized_Call_Handle_Data.csv",
            state_col="State_Name",
            date_col="createdtime",
            output_country_json="static/question12_country.json",
            output_state_json="static/question12_state.json"
            )
        builder.run()


        # Q13 - Calendar Aggregation
        aggregator = WeekdayMonthlyAggregator(
            csv_path="database/Anonymized_Call_Handle_Data.csv",
            tmcid_col="tmcid",
            time_col="createdtime",
            country_output="static/question13_country.json",
            state_output="static/question13_state.json",
            target_year=2024
        )
        aggregator.run()

        # Q15 - Funnel Chart
        df = pd.read_csv("database/Anonymized_Call_Handle_Data.csv")
        dashboard = CallFlowDashboard(dataframe=df)
        dashboard.run()

        logger.info("Static JSON files generated successfully.")

# Flask Application Setup
# app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
CORS(app)

# Initialize repeated callers chart generator
CSV_FILE_PATH = "database/repeated_callers.csv"
chart_generator = graph_generator(CSV_FILE_PATH)
tmc_list = chart_generator.data_obj.return_tmc_list()


def delete_only_files_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        return
    for entry in os.listdir(folder_path):
        entry_path = os.path.join(folder_path, entry)
        if os.path.isfile(entry_path):
            os.remove(entry_path)


@app.route("/", methods=["GET", "POST"])
def index():
    tmc_charts = []
    india_charts = []

    if request.method == "POST":
        charts_dir = os.path.join(app.static_folder, "charts")
        delete_only_files_in_folder(charts_dir)

        call_type = request.form.get("call_type")
        call_type = None if call_type == "N" else call_type

        selected_tmc = request.form.get("tmc")
        tmc = None if selected_tmc in ("", "India") else selected_tmc

        try:
            days = int(request.form.get("days", 7))
        except ValueError:
            days = 7
        try:
            bins = int(request.form.get("bins", 7))
        except ValueError:
            bins = 7

        logger.info("Generating charts for TMC: %s, Call Type: %s", tmc, call_type)

        tmc_charts, india_charts = chart_generator.deciding_factors(
            tmc=tmc,
            call_type=call_type,
            days=days,
            bins=bins
        )

    return render_template(
        "index.html",
        all_tmcs=tmc_list,
        tmc_charts=tmc_charts,
        india_charts=india_charts
    )


# Streamlit Launcher

def launch_streamlit(script_path="run.py", port=8501):
    logger.info("Launching Streamlit app...")

    cmd = [
        sys.executable, "-m", "streamlit", "run", script_path,
        "--server.port", str(port),
        "--server.headless", "true"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in process.stdout:
        print(line, end="")
        if "Local URL:" in line:
            break

    logger.info("Streamlit is running at http://localhost:%d", port)
    return process


# Main Application Runner
if __name__ == "__main__":
    # Generate static JSONs
    StaticJSONGeneratorForDashboardAndQuestions().generate()

    # Ensure charts directory exists
    os.makedirs(os.path.join(app.static_folder, "charts"), exist_ok=True)

    # Launch Streamlit in background
    t1 = Thread(target=launch_streamlit, args=("run.py", 8501))
    t1.start()

    # Run Flask app
    app.run(port=8001)
    t1.join()