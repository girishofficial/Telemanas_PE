# Healthcare Entity Extraction for Indian Healthcare Queries
# Uses a hybrid approach combining zero-shot classification with rule-based extraction
# 
# This implementation uses the strengths of both approaches:
# 1. Zero-shot classification with BART for understanding semantic relationships
# 2. Rule-based extraction for high precision with domain-specific knowledge
# 3. Post-processing to correct common errors and improve accuracy

import torch
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class HealthcareEntityExtractor:
    def _install_dependencies(self):
        """Check and install required dependencies"""
        try:
            import importlib
            
            dependencies = ['torch', 'transformers']
            missing = []
            
            for pkg in dependencies:
                try:
                    importlib.import_module(pkg)
                except ImportError:
                    missing.append(pkg)
            
            if missing:
                print(f"Installing missing dependencies: {', '.join(missing)}")
                import subprocess
                subprocess.check_call(["pip", "install"] + missing)
                print("Dependencies installed successfully!")
                return True
            return False
        except Exception as e:
            print(f"Failed to install dependencies: {str(e)}")
            return False
    
    def __init__(self):
        """
        Initialize the healthcare entity extractor with pre-trained models
        for zero-shot classification to identify diseases, states, and districts.
        """
        print("Initializing Healthcare Entity Extractor...")
        
        # First attempt to install dependencies if needed
        self._install_dependencies()
        
        try:
            # Now try importing the necessary modules
            import torch
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            
            # Load the zero-shot classification model
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli")
            self.model = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli")
            self.classifier = pipeline("zero-shot-classification", 
                                      model=self.model, 
                                      tokenizer=self.tokenizer,
                                      device=-1)  # -1 for CPU, or specific GPU id
            
            # Initialize knowledge bases
            self._initialize_knowledge_bases()
            print("Healthcare Entity Extractor loaded successfully!")
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            print("Falling back to rule-based extraction...")
            self.classifier = None
    
    def _initialize_knowledge_bases(self):
        """Initialize the lists of states, diseases, and districts"""
        # Common Indian diseases
        self.diseases = [
            "FEVER", "TYPHOID", "MALARIA", "DENGUE", "CHIKUNGUNYA", 
            "TUBERCULOSIS", "COVID-19", "INFLUENZA", "PNEUMONIA", "DIARRHEA",
            "HYPERTENSION", "DIABETES", "ASTHMA", "HEART DISEASE", "STROKE",
            "CHOLERA", "HEPATITIS", "MEASLES", "TETANUS", "POLIO"
        ]
        
        # Indian states
        self.states = [
            "ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR", 
            "CHHATTISGARH", "GOA", "GUJARAT", "HARYANA", "HIMACHAL PRADESH", 
            "JHARKHAND", "KARNATAKA", "KERALA", "MADHYA PRADESH", "MAHARASHTRA", 
            "MANIPUR", "MEGHALAYA", "MIZORAM", "NAGALAND", "ODISHA", "PUNJAB", 
            "RAJASTHAN", "SIKKIM", "TAMIL NADU", "TELANGANA", "TRIPURA", 
            "UTTAR PRADESH", "UTTARAKHAND", "WEST BENGAL"
        ]
    
    def extract_entities(self, query):
        """
        Extract healthcare-related entities from the query using zero-shot classification.
        
        Args:
            query (str): The user's natural language query
            
        Returns:
            dict: Categories of entities found in the query
        """
        # First check for direct state mentions in the query - higher priority
        entities = self._direct_state_extraction(query)
        
        # If no state found, try more sophisticated methods
        if not entities or "state" not in entities:
            if self.classifier is None:
                # Fall back to rule-based if model loading failed
                return self._rule_based_extraction(query)
            else:
                return self._zero_shot_extraction(query)
        
        return entities
        
    def _direct_state_extraction(self, query):
        """
        Directly extract state names mentioned in the query, bypassing other methods
        for more accurate results when states are clearly mentioned.
        
        Args:
            query (str): The user's query
            
        Returns:
            dict: Extracted entities focusing on states
        """
        entities = {}
        query_upper = query.upper()
        query_lower = query.lower()
        
        # Special case for Chhattisgarh with various spellings
        if any(variant in query_lower for variant in ["chhattisgarh", "chhatisgarh", "chattisgarh", "chhattishgarh", "chattishgarh"]):
            entities["state"] = "CHHATTISGARH"
            return entities
        
        # Direct state name mapping - including common variations and spellings
        state_mappings = {
            "ANDHRA": "ANDHRA PRADESH",
            "AP": "ANDHRA PRADESH",
            "ANDHRA PRADESH": "ANDHRA PRADESH",
            "ARUNACHAL": "ARUNACHAL PRADESH", 
            "ARUNACHAL PRADESH": "ARUNACHAL PRADESH",
            "ASSAM": "ASSAM",
            "BIHAR": "BIHAR",
            "CHHATTISGARH": "CHHATTISGARH",
            "CHATTISGARH": "CHHATTISGARH",
            "CHHATISGARH": "CHHATTISGARH",
            "CHATTISHGARH": "CHHATTISGARH",
            "CHHATTISHGARH": "CHHATTISGARH",
            "GOA": "GOA",
            "GUJARAT": "GUJARAT",
            "HARYANA": "HARYANA",
            "HIMACHAL": "HIMACHAL PRADESH",
            "HP": "HIMACHAL PRADESH",
            "HIMACHAL PRADESH": "HIMACHAL PRADESH",
            "JHARKHAND": "JHARKHAND",
            "KARNATAKA": "KARNATAKA",
            "KERALA": "KERALA",
            "MP": "MADHYA PRADESH",
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
            "TN": "TAMIL NADU",
            "TAMILNADU": "TAMIL NADU",
            "TAMIL NADU": "TAMIL NADU",
            "TELANGANA": "TELANGANA",
            "TRIPURA": "TRIPURA",
            "UP": "UTTAR PRADESH",
            "UTTAR PRADESH": "UTTAR PRADESH",
            "UTTARAKHAND": "UTTARAKHAND",
            "UK": "UTTARAKHAND",
            "WB": "WEST BENGAL",
            "WEST BENGAL": "WEST BENGAL",
        }
        
        # Try to find exact state name matches first
        for key, state in state_mappings.items():
            # Check if the key appears as a whole word in the query
            # This helps prevent partial matches like "GO" matching "GOA"
            if re.search(r'\b' + key + r'\b', query_upper):
                entities["state"] = state
                return entities
        
        # Try to find state name fragments in case of inexact mentions
        # This is lower priority than exact matches
        for word in query_upper.split():
            for key, state in state_mappings.items():
                if key in word and len(key) > 2:  # Avoid very short matches
                    entities["state"] = state
                    return entities
        
        return entities
        
    def _zero_shot_extraction(self, query):
        """
        Extract entities using zero-shot classification with BART.
        
        Args:
            query (str): The user's query
            
        Returns:
            dict: Extracted entities
        """
        entities = {}
        
        # Use more targeted hypothesis templates
        
        # Identify if the query is about a disease
        disease_result = self.classifier(
            query,
            candidate_labels=self.diseases,
            hypothesis_template="The health condition mentioned is {}."
        )
        if disease_result["scores"][0] > 0.50:  # Lower threshold
            entities["disease"] = disease_result["labels"][0]
        
        # Identify if the query mentions an Indian state
        state_result = self.classifier(
            query,
            candidate_labels=self.states,
            hypothesis_template="The location mentioned is in {}."
        )
        if state_result["scores"][0] > 0.40:  # Even lower threshold for states
            entities["state"] = state_result["labels"][0]
        
        # Try combined approach: use rule-based to augment zero-shot results
        rule_based = self._rule_based_extraction(query)
        
        # Combine results, preferring rule-based for specific types of entities
        if "disease" not in entities and "disease" in rule_based:
            entities["disease"] = rule_based["disease"]
        
        # For location entities, always prefer rule-based since it has better precision
        # for specific Indian locations
        if "state" in rule_based:
            entities["state"] = rule_based["state"]
            
        if "district" in rule_based:
            entities["district"] = rule_based["district"]
        
        # Post-processing for common city-state mappings
        self._post_process_locations(query, entities)
            
        return entities
        
    def _post_process_locations(self, query, entities):
        """
        Post-process location entities to correct common errors
        
        Args:
            query (str): Original query
            entities (dict): Extracted entities to modify in-place
        """
        # Define major city to state mappings
        city_to_state = {
            "MUMBAI": "MAHARASHTRA",
            "DELHI": "DELHI",
            "KOLKATA": "WEST BENGAL",
            "CHENNAI": "TAMIL NADU",
            "BENGALURU": "KARNATAKA",
            "BANGALORE": "KARNATAKA",
            "HYDERABAD": "TELANGANA",
            "AHMEDABAD": "GUJARAT",
            "PUNE": "MAHARASHTRA",
            "JAIPUR": "RAJASTHAN"
        }
        
        # Check if any city is mentioned in the query
        query_upper = query.upper()
        for city, state in city_to_state.items():
            if city in query_upper:
                entities["state"] = state
                if "district" not in entities:
                    entities["district"] = city
    
    def _rule_based_extraction(self, query):
        """
        Extract entities using rule-based matching
        
        Args:
            query (str): The user's query
            
        Returns:
            dict: Extracted entities
        """
        query_upper = query.upper()
        entities = {}
        
        # Define our knowledge base
        diseases = [
            "FEVER", "TYPHOID", "MALARIA", "DENGUE", "CHIKUNGUNYA", 
            "TUBERCULOSIS", "COVID-19", "INFLUENZA", "PNEUMONIA", "DIARRHEA",
            "HYPERTENSION", "DIABETES", "ASTHMA", "HEART DISEASE", "STROKE",
            "CHOLERA", "HEPATITIS", "MEASLES", "TETANUS", "POLIO"
        ]
        
        state_districts = {
    "ANDHRA PRADESH": [
        "ANANTAPUR", "CHITTOOR", "EAST GODAVARI", "GUNTUR", "KRISHNA", "KURNOOL", "PRAKASAM",
        "SRIKAKULAM", "VISAKHAPATNAM", "VIZIANAGARAM", "WEST GODAVARI", "YSR KADAPA",
        "NELLORE", "ANAKAPALLI", "ALLURI SITHARAMA RAJU", "BAPATLA", "KAKINADA",
        "KONASEEMA", "NTR", "PALNADU", "PARVATHIPURAM MANYAM", "SRI SATHYA SAI", "TIRUPATI"
    ],
    "ARUNACHAL PRADESH": [
        "TAWANG", "WEST KAMENG", "EAST KAMENG", "PAPUM PARE", "KURUNG KUMEY", "KRA DAADI",
        "LOWER SUBANSIRI", "UPPER SUBANSIRI", "WEST SIANG", "EAST SIANG", "UPPER SIANG",
        "LOWER SIANG", "SIANG", "NAMSAI", "CHANGLANG", "TIRAP", "LONGDING", "LEPARADA",
        "SHI YOMI", "KAMLE", "ANJAW", "LOHIT", "DIBANG VALLEY", "LOWER DIBANG VALLEY"
    ],
    "ASSAM": [
        "BAKSA", "BARPETA", "BISWANATH", "BONGAIGAON", "CACHAR", "CHARAIDEO", "CHIRANG",
        "DARRANG", "DHEMAJI", "DHUBRI", "DIBRUGARH", "DIMA HASAO", "GOALPARA", "GOLAGHAT",
        "HAILAKANDI", "HOJAI", "JORHAT", "KAMRUP", "KAMRUP METRO", "KARBI ANGLONG",
        "KARIMGANJ", "KOKRAJHAR", "LAKHIMPUR", "MAJULI", "MORIGAON", "NAGAON", "NALBARI",
        "SIVASAGAR", "SONITPUR", "SOUTH SALMARA", "TINSUKIA", "UDALGURI", "WEST KARBI ANGLONG"
    ],
    "BIHAR": [
        "ARARIA", "ARWAL", "AURANGABAD", "BANKA", "BEGUSARAI", "BHAGALPUR", "BHOJPUR",
        "BUXAR", "DARBHANGA", "EAST CHAMPARAN", "GAYA", "GOPALGANJ", "JAMUI", "JEHANABAD",
        "KAIMUR", "KATIHAR", "KHAGARIA", "KISHANGANJ", "LAKHISARAI", "MADHEPURA", "MADHUBANI",
        "MUNGER", "MUZAFFARPUR", "NALANDA", "NAWADA", "PATNA", "PURNIA", "ROHTAS", "SAHARSA",
        "SAMASTIPUR", "SARAN", "SHEIKHPURA", "SHEOHAR", "SITAMARHI", "SIWAN", "SUPAUL",
        "VAISHALI", "WEST CHAMPARAN"
    ],
    "CHHATTISGARH": [
        "BALOD", "BALODA BAZAR", "BALRAMPUR", "BASTAR", "BEMETARA", "BIJAPUR", "BILASPUR",
        "DANTEWADA", "DHAMTARI", "DURG", "GARIYABAND", "JANJGIR-CHAMPA", "JASHPUR", "KABIRDHAM",
        "KANKER", "KONDAGAON", "KORBA", "KORIYA", "MAHASAMUND", "MUNGELI", "NARAYANPUR",
        "RAIGARH", "RAIPUR", "RAJNANDGAON", "SUKMA", "SURAJPUR", "SURGUJA", "GAURELA-PENDRA-MARWAHI"
    ],
    "GOA": [
        "NORTH GOA", "SOUTH GOA"
    ],
    "GUJARAT": [
        "AHMEDABAD", "AMRELI", "ANAND", "ARAVALLI", "BANASKANTHA", "BHARUCH", "BHAVNAGAR",
        "BOTAD", "CHHOTA UDEPUR", "DAHOD", "DANG", "DEVBHOOMI DWARKA", "GANDHINAGAR",
        "GIR SOMNATH", "JAMNAGAR", "JUNAGADH", "KACHCHH", "KHEDA", "MAHISAGAR", "MEHSANA",
        "MORBI", "NARMADA", "NAVSARI", "PANCHMAHALS", "PATAN", "PORBANDAR", "RAJKOT",
        "SABARKANTHA", "SURAT", "SURENDRANAGAR", "TAPI", "VADODARA", "VALSAD"
    ],
    "HARYANA": [
        "AMBALA", "BHIWANI", "CHARKHI DADRI", "FARIDABAD", "FATEHABAD", "GURUGRAM",
        "HISAR", "JHAJJAR", "JIND", "KAITHAL", "KARNAL", "KURUKSHETRA", "MAHENDRAGARH",
        "NUH", "PALWAL", "PANCHKULA", "PANIPAT", "REWARI", "ROHTAK", "SIRSA",
        "SONIPAT", "YAMUNANAGAR"
    ],
    "HIMACHAL PRADESH": [
        "BILASPUR", "CHAMBA", "HAMIRPUR", "KANGRA", "KINNAUR", "KULLU", "LAHAUL AND SPITI",
        "MANDI", "SHIMLA", "SIRMAUR", "SOLAN", "UNA"
    ],
    "JHARKHAND": [
        "BOKARO", "CHATRA", "DEOGHAR", "DHANBAD", "DUMKA", "EAST SINGHBHUM", "GARHWA",
        "GIRIDIH", "GODDA", "GUMLA", "HAZARIBAGH", "JAMTARA", "KHUNTI", "KODERMA",
        "LATEHAR", "LOHARDAGA", "PAKUR", "PALAMU", "RAMGARH", "RANCHI", "SAHEBGANJ",
        "SARAIKELA-KHARSAWAN", "SIMDEGA", "WEST SINGHBHUM"
    ],
    "KARNATAKA": [
        "BAGALKOT", "BALLARI", "BELAGAVI", "BENGALURU RURAL", "BENGALURU URBAN",
        "BIDAR", "CHAMARAJANAGAR", "CHIKBALLAPUR", "CHIKKAMAGALURU", "CHITRADURGA",
        "DAKSHINA KANNADA", "DAVANAGERE", "DHARWAD", "GADAG", "HASSAN", "HAVERI",
        "KALABURAGI", "KODAGU", "KOLAR", "KOPPAL", "MANDYA", "MYSURU", "RAICHUR",
        "RAMANAGARA", "SHIVAMOGGA", "TUMAKURU", "UDUPI", "UTTARA KANNADA", "VIJAYAPURA",
        "YADGIR", "CHIKKODI"
    ],
    "KERALA": [
        "ALAPPUZHA", "ERNAKULAM", "IDUKKI", "KANNUR", "KASARAGOD", "KOLLAM", "KOTTAYAM",
        "KOZHIKODE", "MALAPPURAM", "PALAKKAD", "PATHANAMTHITTA", "THIRUVANANTHAPURAM",
        "THRISSUR", "WAYANAD"
    ],
    "MADHYA PRADESH": [
        "AGAR MALWA", "ALIRAJPUR", "ANUPPUR", "ASHOKNAGAR", "BALAGHAT", "BARWANI",
        "BETUL", "BHIND", "BHOPAL", "BURHANPUR", "CHHATARPUR", "CHHINDWARA",
        "DAMOH", "DATIA", "DEWAS", "DHAR", "DINDORI", "GUNA", "GWALIOR", "HARDA",
        "HOSHANGABAD", "INDORE", "JABALPUR", "JHABUA", "KATNI", "KHANDWA", "KHARGONE",
        "MANDLA", "MANDSAUR", "MORENA", "NARSINGHPUR", "NEEMUCH", "PANNA", "RAISEN",
        "RAJGARH", "RATLAM", "REWA", "SAGAR", "SATNA", "SEHORE", "SEONI", "SHAHDOL",
        "SHAJAPUR", "SHEOPUR", "SHIVPURI", "SIDHI", "SINGRAULI", "TIKAMGARH", "UJJAIN",
        "UMARIA", "VIDISHA"
    ],
    "MAHARASHTRA": [
        "AHMEDNAGAR", "AKOLA", "AMRAVATI", "AURANGABAD", "BEED", "BHANDARA", "BULDHANA",
        "CHANDRAPUR", "DHULE", "GADCHIROLI", "GONDIA", "HINGOLI", "JALGAON", "JALNA",
        "KOLHAPUR", "LATUR", "MUMBAI CITY", "MUMBAI SUBURBAN", "NAGPUR", "NANDED",
        "NANDURBAR", "NASHIK", "OSMANABAD", "PALGHAR", "PARBHANI", "PUNE", "RAIGAD",
        "RATNAGIRI", "SANGLI", "SATARA", "SINDHUDURG", "SOLAPUR", "THANE", "WARDHA",
        "WASHIM", "YAVATMAL"
    ],
    "MANIPUR": [
        "BISHNUPUR", "CHANDEL", "CHURACHANDPUR", "IMPHAL EAST", "IMPHAL WEST",
        "JIRIBAM", "KAKCHING", "KAMJONG", "KANGPOKPI", "NONEY", "PHERZAWL", "SENAPATI",
        "TAMENGLONG", "TENGNOUPAL", "THOUBAL", "UKHRUL"
    ],
    "MEGHALAYA": [
        "EAST GARO HILLS", "EAST JAINTIA HILLS", "EAST KHASI HILLS", "NORTH GARO HILLS",
        "RI BHOI", "SOUTH GARO HILLS", "SOUTH WEST GARO HILLS", "SOUTH WEST KHASI HILLS",
        "WEST GARO HILLS", "WEST JAINTIA HILLS", "WEST KHASI HILLS"
    ],
    "MIZORAM": [
        "AIZAWL", "CHAMPHAI", "HNAHTHIAL", "KOLASIB", "LAWNGTLAI", "LUNGLEI",
        "MAMIT", "SAITUAL", "SERCHHIP", "KHUAHLUI"
    ],
    "NAGALAND": [
        "CHUMOUKEDIMA", "DIMAPUR", "KIPHIRE", "KOHIMA", "LONGLENG", "MOKOKCHUNG",
        "MON", "NIULAND", "PEREN", "PHEK", "TUENSANG", "WOKHA", "ZUNHEBOTO"
    ],
    "ODISHA": [
        "ANGUL", "BALANGIR", "BALASORE", "BARGARH", "BHADRAK", "BOUDH", "CUTTACK",
        "DEOGARH", "DHENKANAL", "GAJAPATI", "GANJAM", "JAGATSINGHPUR", "JAJPUR",
        "JHARSUGUDA", "KALAHANDI", "KANDHAMAL", "KENDRAPARA", "KENDUJHAR", "KHORDHA",
        "KORAPUT", "MALKANGIRI", "MAYURBHANJ", "NABARANGPUR", "NAYAGARH", "NUAPADA",
        "PURI", "RAYAGADA", "SAMBALPUR", "SONEPUR", "SUNDARGARH"
    ],
    "PUNJAB": [
        "AMRITSAR", "BARNALA", "BATHINDA", "FARIDKOT", "FATEHGARH SAHIB", "FAZILKA",
        "FIROZEPUR", "GURDASPUR", "HOSHIARPUR", "JALANDHAR", "KAPURTHALA", "LUDHIANA",
        "MANSA", "MOGA", "MUKTSAR", "NAWANSHAHR", "PATHANKOT", "PATIALA", "RUPNAGAR",
        "SANGRUR", "SAS NAGAR", "TARN TARAN"
    ],
    "RAJASTHAN": [
        "AJMER", "ALWAR", "BANSWARA", "BARAN", "BARMER", "BHARATPUR", "BHILWARA",
        "BIKANER", "BUNDI", "CHITTORGARH", "CHURU", "DAUSA", "DHOLPUR", "DUNGARPUR",
        "HANUMANGARH", "JAIPUR", "JAISALMER", "JALORE", "JHALAWAR", "JHUNJHUNU",
        "JODHPUR", "KARAULI", "KOTA", "NAGAUR", "PALI", "PRATAPGARH", "RAJSAMAND",
        "SAWAI MADHOPUR", "SIKAR", "SIROHI", "SRI GANGANAGAR", "TONK", "UDAIPUR"
    ],
    "SIKKIM": [
        "EAST SIKKIM", "NORTH SIKKIM", "SOUTH SIKKIM", "WEST SIKKIM", "PAKYONG", "SORANG"
    ],
    "TAMIL NADU": [
        "ARIYALUR", "CHENGALPATTU", "CHENNAI", "COIMBATORE", "CUDDALORE", "DHARMAPURI",
        "DINDIGUL", "ERODE", "KALLAKURICHI", "KANCHIPURAM", "KANYAKUMARI", "KARUR",
        "KRISHNAGIRI", "MADURAI", "NAGAPATTINAM", "NAMAKKAL", "PERAMBALUR", "PUDUKKOTTAI",
        "RAMANATHAPURAM", "RANIPET", "SALEM", "SIVAGANGA", "TENKASI", "THANJAVUR",
        "THE NILGIRIS", "THENI", "THOOTHUKUDI", "TIRUCHIRAPPALLI", "TIRUNELVELI",
        "TIRUPATHUR", "TIRUPPUR", "TIRUVALLUR", "TIRUVANNAMALAI", "TIRUVARUR", "VELLORE",
        "VILLUPURAM", "VIRUDHUNAGAR"
    ],
    "TELANGANA": [
        "ADILABAD", "BHADRADRI KOTHAGUDEM", "HANAMKONDA", "HYDERABAD", "JAGTIAL",
        "JANGOAN", "JAYASHANKAR BHOOPALPALLY", "JOGULAMBA GADWAL", "KAMAREDDY", "KARIMNAGAR",
        "KHAMMAM", "KOMARAM BHEEM ASIFABAD", "MAHABUBABAD", "MAHABUBNAGAR", "MANCHERIAL",
        "MEDAK", "MEDCHAL–MALKAJGIRI", "MULUG", "NAGARKURNOOL", "NALGONDA", "NARAYANPET",
        "NIRMAL", "NIZAMABAD", "PEDDAPALLI", "RAJANNA SIRCILLA", "RANGAREDDY", "SANGAREDDY",
        "SIDDIPET", "SURYAPET", "VIKARABAD", "WANAPARTHY", "WARANGAL", "YADADRI BHUVANAGIRI"
    ],
    "TRIPURA": [
        "DHALAI", "GOMATI", "KHOWAI", "NORTH TRIPURA", "SEPAHIJALA", "SOUTH TRIPURA",
        "UNAKOTI", "WEST TRIPURA"
    ],
     "UTTAR PRADESH": [
        "AGRA", "ALIGARH", "ALLAHABAD (PRAYAGRAJ)", "AMBEDKAR NAGAR", "AMETHI",
        "AMROHA", "AURAIYA", "AZAMGARH", "BAGHPAT", "BAHRAICH", "BALLIA", "BALRAMPUR",
        "BANDA", "BARABANKI", "BAREILLY", "BASTI", "BHADOHI", "BIJNOR", "BUDAUN",
        "BULANDSHAHR", "CHANDAULI", "CHITRAKOOT", "DEORIA", "ETAH", "ETAWAH",
        "FAIZABAD (AYODHYA)", "FARRUKHABAD", "FATEHPUR", "FIROZABAD", "GAUTAM BUDDHA NAGAR",
        "GHAZIABAD", "GHAZIPUR", "GONDA", "GORAKHPUR", "HAMIRPUR", "HAPUR",
        "HARDOI", "HATHRAS", "JALAUN", "JAUNPUR", "JHANSI", "KANNAUJ", "KANPUR DEHAT",
        "KANPUR NAGAR", "KASGANJ", "KAUSHAMBI", "KHERI", "KUSHINAGAR", "LALITPUR",
        "LUCKNOW", "MAHARAJGANJ", "MAHOBA", "MAINPURI", "MATHURA", "MAU", "MEERUT",
        "MIRZAPUR", "MORADABAD", "MUZAFFARNAGAR", "PILIBHIT", "PRATAPGARH", "RAEBARELI",
        "RAMPUR", "SAHARANPUR", "SAMBHAL", "SANT KABIR NAGAR", "SHAHJAHANPUR",
        "SHAMLI", "SHRAVASTI", "SIDDHARTHNAGAR", "SITAPUR", "SONBHADRA", "SULTANPUR",
        "UNNAO", "VARANASI"
    ],
    "UTTARAKHAND": [
        "ALMORA", "BAGESHWAR", "CHAMOLI", "CHAMPAWAT", "DEHRADUN", "HARIDWAR",
        "NAINITAL", "PAURI GARHWAL", "PITHORAGARH", "RUDRAPRAYAG", "TEHRI GARHWAL",
        "UDHAM SINGH NAGAR", "UTTARKASHI"
    ],
    "WEST BENGAL": [
        "ALIPURDUAR", "BANKURA", "BIRBHUM", "COOCH BEHAR", "DAKSHIN DINAJPUR",
        "DARJEELING", "HOOGHLY", "HOWRAH", "JALPAIGURI", "JHARGRAM", "KALIMPONG",
        "KOLKATA", "MALDA", "MURSHIDABAD", "NADIA", "NORTH 24 PARGANAS", "PASCHIM BARDHAMAN",
        "PASCHIM MEDINIPUR", "PURBA BARDHAMAN", "PURBA MEDINIPUR", "PURULIA",
        "SOUTH 24 PARGANAS", "UTTAR DINAJPUR"
    ]
    
}

        
        # Create a mapping of district to state for easy lookup
        district_to_state = {}
        for state, districts in state_districts.items():
            for district in districts:
                district_to_state[district] = state
        
        # Check for diseases
        for disease in diseases:
            if disease in query_upper:
                entities["disease"] = disease
                break
        
        # Check for specific disease words that might be in lowercase
        disease_keywords = {
            "FEVER": ["fever", "temperature", "hot"],
            "MALARIA": ["malaria", "mosquito"],
            "TYPHOID": ["typhoid"],
            "DENGUE": ["dengue"],
            "COVID-19": ["covid", "coronavirus", "corona"],
        }
        
        if "disease" not in entities:
            for disease, keywords in disease_keywords.items():
                if any(keyword in query.lower() for keyword in keywords):
                    entities["disease"] = disease
                    break
        
        # Check for states
        for state in state_districts.keys():
            if state in query_upper:
                entities["state"] = state
                break
            
            # Check for state name variations
            state_variations = {
                "KARNATAKA": ["karnataka", "karnatak", "ktaka"],
                "MAHARASHTRA": ["maharashtra", "maha"],
                "TAMIL NADU": ["tamil nadu", "tamilnadu", "tn"],
            }
            
            if state in state_variations:
                if any(variation in query.lower() for variation in state_variations[state]):
                    entities["state"] = state
                    break
        
        # Check for districts and infer state if not already found
        for district, state in district_to_state.items():
            if district in query_upper:
                entities["district"] = district
                if "state" not in entities:
                    entities["state"] = state
                break
                
            # Check for district name variations (lowercase)
            if district.lower() in query.lower():
                entities["district"] = district
                if "state" not in entities:
                    entities["state"] = state
                break
        
        return entities
        

    
    def format_output(self, entities):
        """Format entities into the required output format"""
        output = ""
        if "disease" in entities:
            output += f"disease: {entities['disease']},\n"
        if "district" in entities:
            output += f"District: {entities['district']},\n"
        if "state" in entities:
            output += f"State: {entities['state']}\n"
        
        # If no disease is found but there's a query about health data
        health_keywords = ["cases", "patients", "infected", "suffering", "affected", "sick", "health", "deaths"]
        
        # Remove trailing comma from the last line
        if output.endswith(",\n"):
            output = output[:-2] + "\n"
            
        # If no entities were found
        if not output:
            output = "No relevant health entities found in the query."
            
        return output

# Create a simple interactive interface
    def interactive_entity_extraction(self,qur):
        
        entities = self.extract_entities(qur)
        formatted_output = self.format_output(entities)
        return  formatted_output

if __name__ == "__main__":
    print("Healthcare Entity Extractor - Zero-Shot Classification Mode")
    print("This system will attempt to use BART for zero-shot classification.")
    print("If dependencies are missing, they will be installed automatically.")
    print("If model loading fails, it will fall back to rule-based extraction.")
    print("-" * 60)
    
    hi = HealthcareEntityExtractor()
    
    while True:
        inp = input("\nInput the health query (or 'exit' to quit):\n")
        if inp.lower() == 'exit':
            break
        print("\nExtracted Entities:")
        print(hi.interactive_entity_extraction(inp))
        print("-" * 40)
