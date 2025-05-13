import requests
import subprocess
import time
import psutil  # to check if ollama is already running


class LLMHandler:
    def __init__(self, model="llama3.2", url="http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.ensure_ollama_model_ready()

    def ensure_ollama_model_ready(self):
        if not self.is_ollama_running():
            print("Starting Ollama server...")
            subprocess.Popen(["ollama", "serve"])
            time.sleep(2)  # wait briefly for server to start

        if not self.is_model_ready():
            print(f"Loading model: {self.model}")
            subprocess.Popen(["ollama", "run", self.model])
            time.sleep(10)  # wait for model to load

    def is_ollama_running(self):
        for proc in psutil.process_iter(attrs=["name", "cmdline"]):
            try:
                if "ollama" in proc.info["name"] or "ollama" in " ".join(proc.info["cmdline"]):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_model_ready(self):
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = [m["name"] for m in resp.json().get("models", [])]
            return self.model in models
        except Exception:
            return False


    def query_sql_for_graph1():
        pass
    def query_sql(self, user_query: str, schema_hint: str) -> str:
        prompt = (
            f"You are an expert SQL assistant. Convert the following natural language "
            f"question into a syntactically correct SQL query.\n\n"
            f"""You need to give only SQL commands, nothing other than that. Example: Prompt  Output from the model: 
                SELECT patient.Gender, COUNT(patient.Gender) as Gender_count
                FROM table1
                GROUP BY patient.Gender;
                ```
                This query works by grouping the data in `table1` by the `patient.Gender` column and then counting the number of rows in each group. The result will be a list of unique genders with their corresponding counts.

                If you want to get the count of patients, regardless of the gender, you can use:
                ```sql
                SELECT patient.Gender, COUNT(patient.Gender) as Gender_count
                FROM table1
                GROUP BY patient.Gender;

                ```  "
                need to return only top 1 sql query which is best match for the prompt givn as input:
                SELECT Patient_Gender, COUNT(Patient_Gender) as Gender_count
                FROM table1
                GROUP BY Patient_Gender;  
                Patient_Gender****this must be relevant to the query but from the column name of table in the database***
                
                Natural Language : Number of Male and Females in whole dataset
                SQL: SELECT COUNT(CASE WHEN patient_Gender = 'Male' THEN 1 END) AS Males, COUNT(CASE WHEN patient_Gender = 'Female' THEN 1 END) AS Females FROM table1;

                Natural Language: How many gender female called from tmc odisha who have age above 30
                SQL: SELECT COUNT(CASE WHEN patient_Gender = 'Female' THEN 1 END) AS Females FROM table1 WHERE Patient_District = 'TMC ODISHA' AND patient_age > 30;

                Natural Langauage:  In Karnataka State, get the gender count distribution , that is numner of Female and Male called Per each district in Karnataka
                SQL:SELECT  Patient_District, Patient_Gender, COUNT(Patient_Gender) AS Gender_count  FROM  table1
                    WHERE Patient_State = 'KARNATAKA'  GROUP BY Patient_District, Patient_Gender;
            
                Description about columns of Table: 
                -Patient_State - Tells about the patient state
                -Patient_Gender -  Gives th epatient gender
                -Patient_District - This is for patient District
                -patient_age -  Pateint age
                
                Use the above descriptions of column while generating the SQL    

                Natural language: How many female called from odisha who have age above 30
                SQL: SELECT COUNT(CASE WHEN patient_Gender = 'Female' AND Patient_State = 'ODISHA' THEN 1 END) AS Females FROM table1 WHERE patient_age > 30;        
            """
            

            f"Database Schema:\n{schema_hint}\n"
            f"Question: {user_query}\nSQL:"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            data = response.json()
            if data.get("error"):
                return f"-- ERROR: {data['error']}"
            
            temp = data.get("response", "").strip()

            #print(temp)
            
            return temp
        
        except Exception as e:
            return f"-- ERROR: Failed to generate SQL: {e}"


if __name__ == "__main__":
    llm = LLMHandler()
    print(llm.query_sql("List all users", "Table users: id (int), name (text)"))
