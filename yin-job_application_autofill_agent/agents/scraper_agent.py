from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_form(url):
    """
    Function to scrape form fields from a URL using BeautifulSoup and Playwright
    """
    # Use Playwright to render JavaScript and get the fully rendered page
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        
        # Wait for the page to load completely
        page.wait_for_load_state("networkidle")
        
        # Get the HTML content
        html_content = page.content()
        
        # Create a soup object
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all form elements
        forms = soup.find_all('form')
        
        # Initialize a list to store form field data
        form_fields = []
        
        # If no forms are found, try to find input elements directly
        if not forms:
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
        
        # Close browser
        browser.close()
        
        # Return the scraped data
        return {
            "form_fields": form_fields,
            "pagination": pagination,
            "url": url
        }

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

# Example function to be used by the ScrapeAgent
def perform_scraping(url):
    """Function to be called by the scraping agent"""
    try:
        scraped_data = scrape_form(url)
        return json.dumps(scraped_data, indent=2)
    except Exception as e:
        return f"Error scraping the form: {str(e)}"