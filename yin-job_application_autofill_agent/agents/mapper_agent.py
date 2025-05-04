import json
import logging
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_form_fields(scraped_data: Union[Dict[str, Any], str]) -> str:
    """
    Action 1: Extract key information from scraped form fields for DB queries
    This function now delegates to the FormAnalyzerAgent and QueryGeneratorAgent
    
    Args:
        scraped_data: The scraped form data from the scraper agent
        
    Returns:
        str: JSON string with structured query for the DB agent
    """
    try:
        logger.info("Extracting key information from scraped form fields")
        
        # Parse scraped data if it's a JSON string
        if isinstance(scraped_data, str):
            scraped_data = json.loads(scraped_data)
        
        # The actual analysis is now done by the FormAnalyzerAgent and QueryGeneratorAgent
        # This function just prepares and returns the data in a format expected by the orchestrator
        
        # For backward compatibility, return a basic structure
        query = {
            "query_type": "form_fields",
            "required_fields": [],
            "optional_fields": [],
            "special_fields": [],
            "form_fields": scraped_data.get("form_fields", [])
        }
        
        logger.info("Prepared form fields for analysis")
        return json.dumps(query, indent=2)
    except Exception as e:
        logger.error(f"Error extracting key information: {str(e)}", exc_info=True)
        return f"Error extracting key information: {str(e)}"

def generate_autofill_instructions(scraped_data: Union[Dict[str, Any], str], user_data: Union[Dict[str, Any], str]) -> str:
    """
    Action 2: Generate fill instructions for the autofill agent
    This function now delegates to the FieldMapperAgent
    
    Args:
        scraped_data: The scraped form data
        user_data: User data from the database
        
    Returns:
        str: JSON string with fill instructions for the autofill agent
    """
    try:
        logger.info("Generating fill instructions for autofill agent")
        
        # Parse inputs if they are JSON strings
        if isinstance(scraped_data, str):
            scraped_data = json.loads(scraped_data)
        
        if isinstance(user_data, str):
            user_data = json.loads(user_data)
        
        # The actual mapping is now done by the FieldMapperAgent
        # This function just prepares and returns the data in a format expected by the orchestrator
        
        # For backward compatibility, return a basic structure
        fill_instructions = {
            "field_mappings": [],
            "unmapped_required_fields": [],
            "fill_strategy": "sequential",
            "original_url": scraped_data.get("url", ""),
            "form_fields": scraped_data.get("form_fields", []),
            "user_data": user_data
        }
        
        logger.info("Prepared data for field mapping")
        return json.dumps(fill_instructions, indent=2)
    except Exception as e:
        logger.error(f"Error generating fill instructions: {str(e)}", exc_info=True)
        return f"Error generating fill instructions: {str(e)}"

# Legacy function for backward compatibility
def perform_mapping(scraped_data: Union[Dict[str, Any], str], user_data_schema: Dict[str, Any] = None) -> str:
    """
    Legacy function to be called by the mapping agent
    
    Args:
        scraped_data: The scraped form data
        user_data_schema: Schema of user data fields available
        
    Returns:
        str: JSON string with mapping results
    """
    try:
        logger.warning("Using legacy perform_mapping function - consider updating to new interface")
        
        # Parse scraped data if it's a JSON string
        if isinstance(scraped_data, str):
            scraped_data = json.loads(scraped_data)
        
        form_fields = scraped_data.get("form_fields", [])
        
        # For backward compatibility, return a basic structure
        result = {
            "mapping_result": {
                "field_mapping": {},
                "required_missing_fields": []
            },
            "quality_analysis": {
                "total_form_fields": len(form_fields),
                "mapped_fields": 0,
                "mapping_coverage": 0,
                "missing_required_fields": 0,
                "quality_assessment": "Unknown",
                "suggestions": ["Use new interface functions for better results"]
            },
            "original_url": scraped_data.get("url", "")
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error performing mapping: {str(e)}")
        return f"Error performing mapping: {str(e)}"