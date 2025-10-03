"""
Integration example for the Healthcare Entity Extraction system
with the existing NL_2_GRAPH system
"""

from convert_queries_to_indian_information import HealthcareEntityExtractor
import sys
import os

# Add the parent directory to the path to import from NL_2_GRAPH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules from your project
try:
    from NL_2_GRPAH.llm_handler import query_sql
    from NL_2_GRPAH.db_handler import execute_query
except ImportError:
    print("Could not import modules from NL_2_GRPAH. Make sure the paths are correct.")
    query_sql = None
    execute_query = None

def process_healthcare_query(query):
    """
    Process a healthcare query by extracting entities and generating SQL
    
    Args:
        query (str): The natural language query
        
    Returns:
        dict: Results with extracted entities, SQL query, and execution results
    """
    results = {"original_query": query}
    
    # Step 1: Extract healthcare entities
    extractor = HealthcareEntityExtractor()
    entities = extractor.extract_entities(query)
    results["entities"] = entities
    
    # Step 2: Format the query with the extracted entities for better SQL generation
    enhanced_query = query
    if entities:
        # Add entity information to help SQL generation
        entity_hints = []
        if "disease" in entities:
            entity_hints.append(f"disease is {entities['disease']}")
        if "state" in entities:
            entity_hints.append(f"state is {entities['state']}")
        if "district" in entities:
            entity_hints.append(f"district is {entities['district']}")
            
        if entity_hints:
            enhanced_query += " (Note: " + ", ".join(entity_hints) + ")"
            
    results["enhanced_query"] = enhanced_query
    
    # Step 3: Generate SQL query (if the modules are available)
    if query_sql:
        sql_query = query_sql(enhanced_query)
        results["sql_query"] = sql_query
        
        # Step 4: Execute the SQL query
        if execute_query:
            try:
                query_result = execute_query(sql_query)
                results["execution_result"] = query_result
            except Exception as e:
                results["execution_error"] = str(e)
    
    return results

def demonstrate_integration():
    """Demonstrate the integration with sample queries"""
    sample_queries = [
        "Show me COVID-19 cases in Maharashtra",
        "How many dengue patients are there in Karnataka by district?",
        "Compare malaria cases between Rajasthan and Gujarat",
        "What is the trend of tuberculosis cases in Mumbai over the last 6 months?",
        "Show me districts with the highest number of diabetes patients in Tamil Nadu"
    ]
    
    for query in sample_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)
        
        results = process_healthcare_query(query)
        
        print("\nEXTRACTED ENTITIES:")
        for entity_type, value in results.get("entities", {}).items():
            print(f"  - {entity_type}: {value}")
            
        print("\nENHANCED QUERY:")
        print(results.get("enhanced_query", "N/A"))
        
        if "sql_query" in results:
            print("\nGENERATED SQL:")
            print(results["sql_query"])
            
            if "execution_result" in results:
                print("\nQUERY RESULTS:")
                print(results["execution_result"])
            elif "execution_error" in results:
                print("\nEXECUTION ERROR:")
                print(results["execution_error"])
        else:
            print("\nNOTE: SQL generation and execution skipped (modules not available)")
            
        print("-" * 70)

if __name__ == "__main__":
    demonstrate_integration()