import requests
from bs4 import BeautifulSoup
import json
import logging
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MAX_RETRIES = 3     # Number of retries for transient errors
RETRY_DELAY = 2     # Delay between retries in seconds
REQUEST_TIMEOUT = 30  # Timeout for requests in seconds

def scrape_form(url: str) -> Dict[str, Any]:
    """
    Function to scrape form fields from a URL using requests and BeautifulSoup
    
    Args:
        url: The URL of the form to scrape
        
    Returns:
        Dict containing form fields, pagination info, and URL
        
    Raises:
        Exception: If scraping fails after retries
    """
    retries = 0
    last_error = None
    
    while retries <= MAX_RETRIES:
        try:
            logger.info(f"Scraping URL: {url} (Attempt {retries + 1}/{MAX_RETRIES + 1})")
            
            # Send a GET request to the URL with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the HTML content using BeautifulSoup
            logger.info("Parsing HTML content")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all form elements
            forms = soup.find_all('form')
            logger.info(f"Found {len(forms)} form elements")
            
            # Initialize a list to store form field data
            form_fields = []
            
            # If no forms are found, try to find input elements directly
            if not forms:
                logger.info("No form elements found, looking for input elements directly")
                inputs = soup.find_all(['input', 'select', 'textarea'])
                for input_field in inputs:
                    field_data = extract_field_data(input_field)
                    if field_data:
                        form_fields.append(field_data)
            else:
                # Extract field data from each form
                for form in forms:
                    form_id = form.get('id', '')
                    form_name = form.get('name', '')
                    
                    # Find all input elements within the form
                    inputs = form.find_all(['input', 'select', 'textarea'])
                    
                    for input_field in inputs:
                        field_data = extract_field_data(input_field)
                        if field_data:
                            field_data['form_id'] = form_id
                            field_data['form_name'] = form_name
                            form_fields.append(field_data)
            
            # Check if there are pagination elements
            pagination = check_for_pagination(soup)
            
            # Return the scraped data
            result = {
                "form_fields": form_fields,
                "pagination": pagination,
                "url": url
            }
            
            logger.info(f"Successfully scraped {len(form_fields)} form fields")
            return result
                
        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(f"Timeout error on attempt {retries + 1}: {str(e)}")
            retries += 1
            if retries <= MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed after {MAX_RETRIES + 1} attempts due to timeout")
                raise Exception(f"Timeout error after {MAX_RETRIES + 1} attempts: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Request error on attempt {retries + 1}: {str(e)}")
            retries += 1
            if retries <= MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed after {MAX_RETRIES + 1} attempts due to request error")
                raise Exception(f"Request error after {MAX_RETRIES + 1} attempts: {str(e)}")
                
        except Exception as e:
            last_error = e
            logger.error(f"Error on attempt {retries + 1}: {str(e)}", exc_info=True)
            retries += 1
            if retries <= MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed after {MAX_RETRIES + 1} attempts")
                raise

def extract_field_data(input_field):
    """
    Extract relevant data from an input field
    """
    field_type = input_field.name  # input, select, textarea
    
    if field_type == 'input':
        input_type = input_field.get('type', 'text')
        
        # Skip hidden fields and submit buttons
        if input_type in ['hidden', 'submit', 'button']:
            return None
    
    field_data = {
        'type': field_type if field_type != 'input' else input_field.get('type', 'text'),
        'name': input_field.get('name', ''),
        'id': input_field.get('id', ''),
        'class': input_field.get('class', ''),
        'placeholder': input_field.get('placeholder', ''),
        'required': input_field.has_attr('required'),
        'options': []
    }
    
    # Get label text if available
    label = find_label_for_field(input_field)
    if label:
        field_data['label'] = label
    
    # For select fields, extract options
    if field_type == 'select':
        options = input_field.find_all('option')
        for option in options:
            option_value = option.get('value', '')
            option_text = option.get_text().strip()
            if option_value or option_text:  # Skip empty options
                field_data['options'].append({
                    'value': option_value,
                    'text': option_text,
                    'selected': option.has_attr('selected')
                })
    
    return field_data

def find_label_for_field(input_field):
    """
    Find the label text for a given input field
    """
    field_id = input_field.get('id')
    if field_id:
        # Try to find a label that references this field by id
        label = input_field.find_previous('label', attrs={'for': field_id})
        if not label:
            # Try to find a label that comes after the field
            label = input_field.find_next('label', attrs={'for': field_id})
        
        if label:
            return label.get_text().strip()
    
    # Look for a label that contains this input
    parent_label = input_field.find_parent('label')
    if parent_label:
        # Remove the input text from the label
        label_text = parent_label.get_text().strip()
        return label_text
    
    return None

def check_for_pagination(soup):
    """
    Check if the form has pagination elements
    """
    # Common pagination indicators
    pagination_indicators = [
        soup.find_all(attrs={'class': lambda x: x and ('pagination' in x.lower() if x else False)}),
        soup.find_all(attrs={'id': lambda x: x and ('pagination' in x.lower() if x else False)}),
        soup.find_all('button', string=lambda x: x and ('next' in x.lower() or 'continue' in x.lower() if x else False)),
        soup.find_all('a', string=lambda x: x and ('next' in x.lower() or 'continue' in x.lower() if x else False))
    ]
    
    for indicators in pagination_indicators:
        if indicators:
            return True
    
    return False

# Function to be used by the ScrapeAgent
def perform_scraping(url: str) -> str:
    """
    Function to be called by the scraping agent
    
    Args:
        url: The URL to scrape
        
    Returns:
        JSON string of scraped data or error message
    """
    try:
        logger.info(f"Starting scraping process for URL: {url}")
        scraped_data = scrape_form(url)
        logger.info(f"Successfully scraped form with {len(scraped_data.get('form_fields', []))} fields")
        return json.dumps(scraped_data, indent=2)
    except Exception as e:
        logger.error(f"Error scraping the form: {str(e)}", exc_info=True)
        return f"Error scraping the form: {str(e)}"