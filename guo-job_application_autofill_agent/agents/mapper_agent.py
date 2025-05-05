import json
import logging
from typing import Dict, List, Any, Optional, Union

# Import Phoenix tracing
from core.tracing import tracer

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@tracer.chain
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

@tracer.chain
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
        
        # Extract form fields and URL
        form_fields = scraped_data.get("form_fields", [])
        form_url = scraped_data.get("url", "")
        
        # Create field mappings in the new format
        field_mappings = []
        unmapped_required_fields = []
        
        # Flatten user data for easier mapping
        flat_user_data = flatten_user_data(user_data)
        
        # Process each form field
        for field in form_fields:
            field_name = field.get("name")
            field_type = field.get("type")
            required = field.get("required", False)
            options = field.get("options", [])
            
            # Skip fields without a name
            if not field_name:
                continue
            
            # Try to find a matching user data field
            value = None
            matched = False
            
            # Simple mapping strategy - match by field name or similar names
            for user_field, user_value in flat_user_data.items():
                # Direct match
                if field_name.lower() == user_field.lower():
                    value = user_value
                    matched = True
                    break
                
                # Partial match
                if field_name.lower() in user_field.lower() or user_field.lower() in field_name.lower():
                    value = user_value
                    matched = True
                    break
            
            # If it's a select field, try to find the best matching option
            if matched and field_type == "select" and options:
                selected_option = None
                
                # Try to find an option that matches the user value
                for option in options:
                    option_text = option.get("text", "").lower()
                    option_value = option.get("value", "").lower()
                    
                    # Skip empty options
                    if not option_text and not option_value:
                        continue
                    
                    # Check if user value matches this option
                    if (str(value).lower() in option_text or
                        str(value).lower() in option_value):
                        selected_option = option.get("value")
                        break
                
                # Add the mapping with the selected option
                if selected_option:
                    field_mappings.append({
                        "field_name": field_name,
                        "field_type": field_type,
                        "selected_option": selected_option
                    })
                else:
                    # Couldn't find a matching option
                    if required:
                        unmapped_required_fields.append(field_name)
            else:
                # Regular field mapping
                if matched:
                    field_mappings.append({
                        "field_name": field_name,
                        "field_type": field_type,
                        "value": value
                    })
                elif required:
                    unmapped_required_fields.append(field_name)
        
        # Create the fill instructions
        fill_instructions = {
            "form_url": form_url,
            "matched_fields": field_mappings,  # Renamed to match what instruction_generator expects
            "unmapped_required_fields": unmapped_required_fields,
            "use_url_generation": True  # Default to URL generation approach
        }
        
        logger.info(f"Generated {len(field_mappings)} field mappings")
        return json.dumps(fill_instructions, indent=2)
    except Exception as e:
        logger.error(f"Error generating fill instructions: {str(e)}", exc_info=True)
        return f"Error generating fill instructions: {str(e)}"

# Helper function to flatten nested user data
def flatten_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested user data for easier mapping
    
    Args:
        user_data: Nested user data dictionary
        
    Returns:
        Dict[str, Any]: Flattened dictionary with dot notation keys
    """
    flat_data = {}
    
    def flatten_dict(d, prefix=""):
        for key, value in d.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flatten_dict(value, f"{new_key}.")
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # For the first item in a list of dicts, flatten it with indexed keys
                    flatten_dict(value[0], f"{new_key}.")
                else:
                    # For list of simple values, just use the key
                    flat_data[new_key] = value
            else:
                flat_data[new_key] = value
    
    flatten_dict(user_data)
    return flat_data

# Legacy function for backward compatibility
@tracer.chain
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
        form_url = scraped_data.get("url", "")
        
        # Create a mock user data for demonstration
        mock_user_data = {
            "personal": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "Anytown, CA, USA"
            },
            "social": {
                "linkedin": "https://linkedin.com/in/johndoe",
                "website": "https://johndoe.com"
            }
        }
        
        # Generate field mappings using the new format
        field_mappings = []
        
        # Process each form field
        for field in form_fields:
            field_name = field.get("name")
            
            # Skip fields without a name
            if not field_name:
                continue
            
            # Simple mapping based on field name
            if "name" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["personal"]["name"]
                })
            elif "email" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["personal"]["email"]
                })
            elif "phone" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["personal"]["phone"]
                })
            elif "location" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["personal"]["location"]
                })
            elif "linkedin" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["social"]["linkedin"]
                })
            elif "website" in field_name.lower() or "url" in field_name.lower():
                field_mappings.append({
                    "field_name": field_name,
                    "value": mock_user_data["social"]["website"]
                })
        
        # Create result in the new format
        result = {
            "form_url": form_url,
            "field_mappings": field_mappings,
            "unmapped_required_fields": [],
            "use_url_generation": True
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error performing mapping: {str(e)}")
        return f"Error performing mapping: {str(e)}"