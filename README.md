# 🦙 Llama‑Powered SQL‑to‑Graph Demo

This repository demonstrates converting **CSV to SQLite**, running a **Flask/Streamlit** server, and interacting with a **2B‑parameter LLaMA model** to convert **Natural Language → SQL → Graphs**.

---

## 🚀 Quick Setup Instructions

### 🔗 [Google Drive Link for Data & Resources](https://drive.google.com/drive/folders/19UJ9TeaU3_HcQV8BI0BBNtPbs2jcTqjT)

---

### ⚙️ 1. Create and Activate a Virtual Environment

```bash
python3 -m venv env
source env/bin/activate  # for macOS/Linux
```

### 📦 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ If you get an error for packages like `json`, `typing`, `logging`, etc. — they are part of Python’s standard library. You do **not** need to list or install them separately.

### 🧠 3. Run LLaMA-based Server

> The model used is around **2B parameters**, requiring approximately **8 GB RAM**.

* If you **have 8 GB RAM or more**, you're good to go!
* If **not**, then open `server.py` and **comment out** the last line:

```python
# t1.start()
```

### ▶️ 4. Start the Server

```bash
python server.py
```

Your server will now be live at `http://localhost:8000`

---

## 🗃️ Convert CSV to SQLite

First step is to convert your input CSV file into a SQLite database.

```bash
python nl_to_sql_to_graph/csv_to_sqlite.py
```

This generates `database.sqlite` in the root folder.

---

## 🛠️ Tips to Improve Results

### ✅ Prompt Engineering

* Provide **multiple variations** of your natural language prompts.

### ✅ Fine‑Tuning

* Fine‑tune the LLM with **diverse SQL queries**.

### ✅ Use More Powerful LLMs

* You can swap in a stronger LLaMA variant or a completely different model via the loader logic in `server.py`.

---

## 💡 Summary of Commands

```bash
git clone <your-repo-url>
cd <your-repo-folder>
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python nl_to_sql_to_graph/csv_to_sqlite.py
python server.py
```

---

## 📌 Environment Variables (Optional)

```bash
export PORT=8000
export MAX_RAM_GB=8
export LLAMA_MODEL_PATH="/path/to/llama-2b"
```

---

> *Built to simplify NL → SQL → Graph workflows!*
