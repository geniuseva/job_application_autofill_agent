"""
Autofill Instruction Generator

This module provides functions to generate structured autofill instructions
based on matched fields from the Field Mapper Agent and original form fields.
"""

import json
import logging
from typing import Dict, List, Any, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_autofill_instructions(matched_fields_data: Union[Dict[str, Any], str]) -> str:
    """
    Generate autofill instructions from matched fields data.
    
    Args:
        matched_fields_data: Matched fields from the Field Mapper Agent
            
    Returns:
        JSON string with autofill instructions
    """
    try:
        logger.info("Generating autofill instructions")
        logger.info(f"Matched fields data: {matched_fields_data}")
        # Parse input if it's a string
        if isinstance(matched_fields_data, str):
            matched_fields_data = json.loads(matched_fields_data)
        
        # Extract matched fields
        matched_fields = matched_fields_data.get("matched_fields", [])
        form_url = matched_fields_data.get("form_url", "")
        
        

        # Initialize autofill instructions
        autofill_instructions = {
            "form_url": form_url,
            "form_fields": []
        }
        
        # Process each matched field
        for matched_field in matched_fields:
            field_name = matched_field.get("field_name", "")
            field_type = matched_field.get("field_type", "")
            value = matched_field.get("value", "")
            
            # Skip fields without a name or type
            if not field_name or not field_type:
                continue
            
            # Build a simple selector based on field name and type
            selector = build_selector_from_matched_field(field_name, field_type)
            
            # Determine the fill method
            fill_method = determine_fill_method(field_type)
            
            # Create field instruction
            field_instruction = {
                "field_name": field_name,
                "field_type": field_type,
                "selector": selector,
                "fill_method": fill_method
            }
            
            # Add type-specific properties
            if field_type == "select":
                # For select fields, add selected_value
                field_instruction["selected_value"] = value
            elif field_type == "checkbox" or field_type == "radio":
                # For checkboxes and radio buttons, add checked state
                field_instruction["checked"] = parse_boolean(value)
            else:
                # For text-like fields, add value
                field_instruction["value"] = value
            
            # Add the field instruction to the list
            autofill_instructions["form_fields"].append(field_instruction)
        
        logger.info(f"Generated {len(autofill_instructions['form_fields'])} field instructions")
        return json.dumps(autofill_instructions, indent=2)
    
    except Exception as e:
        logger.error(f"Error generating autofill instructions: {str(e)}")
        return f"Error generating autofill instructions: {str(e)}"


def build_selector_from_matched_field(field_name: str, field_type: str) -> str:
    """
    Build a CSS selector for the field based on field name and type.
    
    Args:
        field_name: Name of the form field
        field_type: Type of the form field
        
    Returns:
        CSS selector string
    """
    selectors = []
    
    # Build selectors based on field name and type
    if field_name:
        if field_type == "checkbox" or field_type == "radio":
            selectors.append(f"input[type='{field_type}'][name='{field_name}']")
        elif field_type == "select":
            selectors.append(f"select[name='{field_name}']")
        elif field_type == "textarea":
            selectors.append(f"textarea[name='{field_name}']")
        else:
            selectors.append(f"input[name='{field_name}']")
    
    # Try to use ID if it matches the field name (common pattern)
    selectors.append(f"#{field_name}")
    
    # Join selectors with comma for CSS selector OR operation
    return ", ".join(selectors) if selectors else ""


def determine_fill_method(field_type: str) -> str:
    """
    Determine the appropriate fill method based on field type.
    
    Args:
        field_type: Type of the form field
        
    Returns:
        Fill method string
    """
    if field_type == "select":
        return "select_option"
    elif field_type == "checkbox" or field_type == "radio":
        return "check"
    elif field_type == "file":
        return "set_input_files"
    else:
        return "fill"


def parse_boolean(value: Any) -> bool:
    """
    Parse a value as a boolean.
    
    Args:
        value: Value to parse
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return bool(value)  # Return True for any non-empty string
    else:
        return bool(value)