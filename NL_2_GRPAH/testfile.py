# Healthcare Entity Extraction for Indian Healthcare Queries
# Uses a rule-based approach to identify diseases, states, and districts

class HealthcareEntityExtractor:
    def __init__(self):
        """
        Initialize the healthcare entity extractor with knowledge of Indian states,
        districts and common diseases.
        """
        print("Initializing Healthcare Entity Extractor...")
        print("Healthcare Entity Extractor loaded successfully!")
    
    def extract_entities(self, query):
        """
        Extract healthcare-related entities from the query.
        
        Args:
            query (str): The user's natural language query
            
        Returns:
            dict: Categories of entities found in the query
        """
        # Use rule-based extraction as a more reliable approach
        entities = self._rule_based_extraction(query)
        return entities
    
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

    inp  = input(" Input the health query:\n")
    hi = HealthcareEntityExtractor()
    print(hi.interactive_entity_extraction(inp))
