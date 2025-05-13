from flask import Flask, render_template, request
import os
from charts_generator import graph_generator

app = Flask(__name__)

# Initialize generator & TMC list
CSV_FILE_PATH = "data.csv"
chart_generator = graph_generator(CSV_FILE_PATH)
tmc_list = chart_generator.data_obj.return_tmc_list()

# Helper to delete only files, not subfolders

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
        # 1) Clear out old chart files
        charts_dir = os.path.join(app.static_folder, "charts")
        delete_only_files_in_folder(charts_dir)

        # 2) Read & normalize form data
        call_type = request.form.get("call_type")
        if call_type == "N":
            call_type = None

        print("***********Call Type************\n",call_type)

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

        # 3) Generate the charts lists: (tmc_charts, india_charts)
        tmc_charts, india_charts = chart_generator.deciding_factors(
            tmc=tmc,
            call_type=call_type,
            days=days,
            bins=bins
        )

    # 4) Render template
    return render_template(
        "index.html",
        all_tmcs=tmc_list,
        tmc_charts=tmc_charts,
        india_charts=india_charts
    )


if __name__ == "__main__":
    # Ensure charts folder exists
    os.makedirs(os.path.join(app.static_folder, "charts"), exist_ok=True)
    app.run(debug=True, port=8001)