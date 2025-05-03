import re
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_url_from_message(message):
    """
    Extract a URL from a message
    
    Args:
        message (str): Message text to search for URLs
        
    Returns:
        str or None: First URL found in the message, or None if no URL is found
    """
    if not message or not isinstance(message, str):
        return None
        
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!.~\'*,;:=+$/?:@&=#]*)*', message)
    return urls[0] if urls else None

def extract_json_from_message(message, key=None):
    """
    Extract JSON data from a message
    
    Args:
        message (str): Message text to search for JSON data
        key (str, optional): Specific key to extract from the JSON data
        
    Returns:
        dict or None: Extracted JSON data, or None if no valid JSON is found
    """
    if not message or not isinstance(message, str):
        return None
        
    # Try to find JSON data in the message
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
    json_matches = re.findall(json_pattern, message)
    
    if not json_matches:
        return None
    
    # Try to parse each match as JSON
    for match in json_matches:
        try:
            data = json.loads(match)
            
            # If a specific key is requested, check for it
            if key and key in data:
                return data[key]
            
            return data
        except json.JSONDecodeError:
            continue
    
    return None

def extract_fields_from_message(message):
    """
    Extract field names from a message
    
    Args:
        message (str): Message text to search for field names
        
    Returns:
        list: List of field names found in the message
    """
    if not message or not isinstance(message, str):
        return []
        
    # Look for field names in quotes or brackets
    field_pattern = r'["\']([\w\._]+)["\']|\[([\w\._]+)\]'
    matches = re.findall(field_pattern, message)
    
    # Flatten the matches and remove empty strings
    fields = [match[0] or match[1] for match in matches]
    
    return fields if fields else []

def flatten_user_data(user_data):
    """
    Flatten nested user data for easier mapping
    
    Args:
        user_data (dict): Nested user data dictionary
        
    Returns:
        dict: Flattened user data with dot notation keys
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

def format_time_duration(seconds):
    """
    Format time duration in a human-readable format
    
    Args:
        seconds (float): Time duration in seconds
        
    Returns:
        str: Formatted time duration
    """
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)} minutes and {remaining_seconds:.2f} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{int(hours)} hours, {int(minutes)} minutes, and {remaining_seconds:.2f} seconds"

def calculate_percentage(part, total):
    """
    Calculate percentage with proper handling of edge cases
    
    Args:
        part (int or float): The part value
        total (int or float): The total value
        
    Returns:
        float: Calculated percentage
    """
    if total == 0:
        return 0.0
    return (part / total) * 100

def log_metrics(metrics, title=None):
    """
    Log metrics in a structured format
    
    Args:
        metrics (dict): Dictionary of metrics
        title (str, optional): Title for the metrics log
    """
    if title:
        logger.info(f"=== {title} ===")
    
    for key, value in metrics.items():
        if isinstance(value, dict):
            logger.info(f"{key}:")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, float):
                    logger.info(f"  {sub_key}: {sub_value:.2f}")
                else:
                    logger.info(f"  {sub_key}: {sub_value}")
        elif isinstance(value, float):
            logger.info(f"{key}: {value:.2f}")
        else:
            logger.info(f"{key}: {value}")