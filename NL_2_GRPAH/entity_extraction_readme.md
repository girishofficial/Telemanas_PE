# Healthcare Entity Extraction System

This system uses a hybrid approach combining zero-shot classification with pre-trained language models and rule-based extraction to identify healthcare entities in natural language queries about Indian healthcare data.

## Features

- Extracts diseases, states, and districts mentioned in healthcare queries
- Uses BART for zero-shot classification to identify entities
- Falls back to rule-based extraction when needed
- Comprehensive database of Indian states and districts
- Auto-installs dependencies

## Installation

```bash
pip install -r requirements_entity_extraction.txt
```

## Usage

```python
from convert_queries_to_indian_information import HealthcareEntityExtractor

extractor = HealthcareEntityExtractor()
query = "Show me COVID-19 cases in Maharashtra"
entities = extractor.extract_entities(query)
formatted_result = extractor.format_output(entities)
print(formatted_result)
```

## Hybrid Approach Benefits

This implementation uses a hybrid approach that combines the strengths of both zero-shot classification and rule-based extraction:

1. **Zero-shot Classification**: Leverages pre-trained language models to understand semantic relationships and handle variations in language.

2. **Rule-based Extraction**: Provides high precision for specific entity types and handles edge cases with domain-specific knowledge.

3. **Combined Results**: The system uses the best of both approaches, preferring the model-based approach for understanding context while relying on rules for specific entity identification.

## Testing

Run the test script to see the entity extraction in action:

```bash
python test_entity_extraction.py
```
