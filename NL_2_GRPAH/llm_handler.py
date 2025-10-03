import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from NL_2_GRPAH.convert_queries_to_indian_information import HealthcareEntityExtractor


class LLMHandler:
    def __init__(self, model_name="seeklhy/codes-1b", url=None):
        self.model_name = model_name
        self.url = url
        print(f"Loading {model_name}...")
        
        # Load CodeS-1B directly from HuggingFace
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        print("CodeS-1B loaded successfully!")
    
    def query_sql(self, user_query: str, schema_hint: str) -> str:
        hi = HealthcareEntityExtractor()
        
        # Extract state directly from user query for more accurate SQL generation
        state_name = self._extract_state_directly(user_query)
        
        # Special case for CHHATTISGARH since it's mentioned in the query
        if any(variant in user_query.lower() for variant in ["chhattisgarh", "chhatisgarh", "chattisgarh", "chhattishgarh", "chattishgarh"]):
            state_name = "CHHATTISGARH"
            
        # Process entity extraction 
        quered = hi.interactive_entity_extraction(user_query)
        
        # If we have directly extracted state, ensure it's prioritized
        extracted_info = quered
        if state_name:
            print(f"Using directly extracted state: {state_name}")
            # Use the directly extracted state name, but keep other extracted entities
            if "State:" in quered:
                parts = quered.split("State:")
                if len(parts) > 1:
                    # Replace the state part while keeping everything else
                    extracted_info = parts[0] + f"State: {state_name}"
            else:
                # Add state if not present
                extracted_info = quered + f"\nState: {state_name}"
                
        # Add useful context about state to the user query to help the LLM
        enhanced_query = user_query
        if state_name and state_name.lower() not in user_query.lower():
            enhanced_query = f"{user_query} in {state_name}"
            print(f"Enhanced query: {enhanced_query}")
        else:
            enhanced_query = user_query

        prompt = (
            f"You are an expert SQL assistant. Convert the following natural language "
            f"question into a syntactically correct SQL query.\n\n"

            f"IMPORTANT: You need to give ONLY the exact SQL command needed for the current question. "
            f"Do not include any previous conversations, results, or additional SQL statements. "
            f"Do not include any text like 'Question:', 'Result:', or previous answers. "
            f"Return ONLY a single valid SQL statement without any additional text.\n\n"

            f"For questions asking to 'show', 'list', 'display', or asking about distribution/counts, "
            f"ALWAYS use GROUP BY and COUNT to provide aggregated data:\n\n"

            f"Example 1:\n"
            f"SELECT gender, COUNT(telemanasid) AS gender_count "
            f"FROM table1 GROUP BY gender ORDER BY gender_count DESC;\n\n"

            f"Example 2:\n"
            f"SELECT state_name, COUNT(telemanasid) AS state_count "
            f"FROM table1 WHERE state_name IS NOT NULL "
            f"GROUP BY state_name ORDER BY state_count DESC;\n\n"

            f"Natural Language: How many males are there in Telangana\n"
            f"SQL: SELECT COUNT(telemanasid) AS male_count FROM table1 "
            f"WHERE state_name = 'TELANGANA' AND gender = 'MALE';\n\n"

            f"Natural Language: In Karnataka State, get the gender count distribution\n"
            f"SQL: SELECT state_name, gender, COUNT(telemanasid) AS gender_count "
            f"FROM table1 WHERE state_name = 'KARNATAKA' "
            f"GROUP BY state_name, gender ORDER BY gender_count DESC;\n\n"

            f"Natural Language: Show data for Maharashtra\n"
            f"SQL: SELECT * FROM table1 WHERE state_name = 'MAHARASHTRA';\n\n"
            
            f"Natural Language: Count of calls from Maharashtra by gender\n"
            f"SQL: SELECT gender, COUNT(telemanasid) AS call_count FROM table1 "
            f"WHERE state_name = 'MAHARASHTRA' "
            f"GROUP BY gender ORDER BY call_count DESC;\n\n"

            f"Natural Language: Show states where age is greater than 30\n"
            f"SQL: SELECT state_name, COUNT(telemanasid) AS count FROM table1 "
            f"WHERE `patient - telemanas_id__age` > 30 "
            f"GROUP BY state_name ORDER BY count DESC;\n\n"

            f"IMPORTANT:\n"
            f"- For visualization queries, NEVER use SELECT DISTINCT. "
            f"- ALWAYS use GROUP BY with COUNT for proper data aggregation.\n"
            f"- Indian state names should be in ALL CAPS (e.g., 'MAHARASHTRA', 'KARNATAKA', 'TAMIL NADU').\n"
            f"- When matching state names, always use EXACT matches like state_name = 'MAHARASHTRA'.\n"
            f"- CRITICAL: ALWAYS wrap column names with hyphens or spaces in BACKTICKS, for example: `patient - telemanas_id__age`. Without backticks, SQL will interpret it as a subtraction operation and fail.\n"
            f"- NEVER FORGET BACKTICKS around column names with hyphens: `patient - telemanas_id__age`\n"
            f"- The age information is stored in the `patient - telemanas_id__age` column.\n"
            f"- Patient ID information is stored in the `telemanasid` column.\n"
            f"- State information is stored in the state_name column (no backticks needed).\n\n"
            f"- CRITICAL: Without backticks around hyphenated column names, queries will fail with 'no such column' errors.\n\n"
            f"WRONG: SELECT * FROM table1 WHERE patient - telemanas_id__age > 30;\n"
            f"CORRECT: SELECT * FROM table1 WHERE `patient - telemanas_id__age` > 30;\n\n"

            f"WRONG: SELECT DISTINCT state_name FROM table1;\n"
            f"CORRECT: SELECT state_name, COUNT(telemanasid) as count "
            f"FROM table1 GROUP BY state_name;\n\n"
            
            f"IMPORTANT FOR COUNTING:\n"
            f"- ALWAYS use COUNT(telemanasid) instead of COUNT(*) for accurate patient counts\n"
            f"- For unique patient counts, use COUNT(DISTINCT telemanasid)\n"
            f"- Each telemanas_id represents a unique patient/record\n\n"

            f"Database Schema:\n{schema_hint}\n"
            f"Below is the processed data from user query:  {extracted_info}\n"
            f"Question: {enhanced_query}\nSQL:"
            )
        
        
        # Tokenize input
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.cuda()
        
        # Generate SQL
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + 200,
                temperature=0.1,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        # Clean up response - NO BACKTICKS IN CODE
        sql_response = response.strip()
        
        # Remove markdown code blocks if present
        triple_backticks = chr(96) + chr(96) + chr(96)  # Creates ```
        sql_marker = triple_backticks + "sql"
        
        if sql_marker in sql_response:
            parts = sql_response.split(sql_marker)
            if len(parts) > 1:
                sql_response = parts.split(triple_backticks).strip()[1]
        elif triple_backticks in sql_response:
            parts = sql_response.split(triple_backticks)
            if len(parts) > 1:
                sql_response = parts.strip()[1]
                
        return sql_response
    
    def query_sql_for_graph1(self):
        pass

    def _extract_state_directly(self, query):
        """
        Extract state name directly from the query using simple string matching.
        This is a hardcoded approach but very effective for direct state mentions.
        """
        query_upper = query.upper()
        query_lower = query.lower()
        
        # Check for Chhattisgarh directly first (highest priority)
        # Include all common spelling variants
        if any(variant in query_lower for variant in ["chhattisgarh", "chhatisgarh", "chattisgarh", "chhattishgarh", "chattishgarh"]):
            return "CHHATTISGARH"
            
        # Direct state name mappings (original and common variants)
        state_mappings = {
            "ANDHRA": "ANDHRA PRADESH",
            "ANDHRA PRADESH": "ANDHRA PRADESH",
            "ARUNACHAL": "ARUNACHAL PRADESH",
            "ARUNACHAL PRADESH": "ARUNACHAL PRADESH",
            "ASSAM": "ASSAM",
            "BIHAR": "BIHAR",
            "CHATTISGARH": "CHHATTISGARH",
            "CHHATISGARH": "CHHATTISGARH",
            "CHATTISHGARH": "CHHATTISGARH", 
            "CHHATTISHGARH": "CHHATTISGARH",
            "CHHATTISGARH": "CHHATTISGARH",
            "GOA": "GOA",
            "GUJARAT": "GUJARAT",
            "HARYANA": "HARYANA",
            "HIMACHAL": "HIMACHAL PRADESH",
            "HIMACHAL PRADESH": "HIMACHAL PRADESH",
            "JHARKHAND": "JHARKHAND",
            "KARNATAKA": "KARNATAKA",
            "KERALA": "KERALA",
            "MADHYA PRADESH": "MADHYA PRADESH",
            "MAHARASHTRA": "MAHARASHTRA",
            "MANIPUR": "MANIPUR",
            "MEGHALAYA": "MEGHALAYA",
            "MIZORAM": "MIZORAM",
            "NAGALAND": "NAGALAND",
            "ODISHA": "ODISHA",
            "ORISSA": "ODISHA",
            "PUNJAB": "PUNJAB",
            "RAJASTHAN": "RAJASTHAN",
            "SIKKIM": "SIKKIM",
            "TAMIL NADU": "TAMIL NADU",
            "TAMILNADU": "TAMIL NADU",
            "TELANGANA": "TELANGANA",
            "TRIPURA": "TRIPURA",
            "UTTAR PRADESH": "UTTAR PRADESH",
            "UTTARAKHAND": "UTTARAKHAND",
            "WEST BENGAL": "WEST BENGAL",
        }
        
        import re
        
        # First try exact whole word matches
        for variant, standard in state_mappings.items():
            if re.search(r'\b' + re.escape(variant) + r'\b', query_upper):
                return standard
                
        # If no exact match, try contains match for longer state names
        for variant, standard in state_mappings.items():
            if len(variant) > 3 and variant in query_upper:
                return standard
                
        return None

if __name__ == "__main__":
    llm = LLMHandler()
    print(llm.query_sql("List all users", "Table users: id (int), name (text)"))
