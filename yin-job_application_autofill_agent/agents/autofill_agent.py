from playwright.sync_api import sync_playwright
import time
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FormAutofiller:
    """Class for automatically filling out forms using Playwright"""
    
    def __init__(self):
        """Initialize the form autofiller"""
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start_browser(self):
        """Start the Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)  # Set to True in production
        self.page = self.browser.new_page()
        
    def close_browser(self):
        """Close the browser and Playwright"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def navigate_to_url(self, url):
        """Navigate to the form URL"""
        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            logger.error(f"Error navigating to URL: {str(e)}")
            return False
    
    def fill_form(self, field_mappings, user_data):
        """Fill form fields with user data based on mappings"""
        filled_fields = []
        not_filled_fields = []
        
        for form_field_name, mapping_info in field_mappings.items():
            user_field = mapping_info.get('user_field')
            field_type = mapping_info.get('field_type')
            options = mapping_info.get('options', [])
            
            if not user_field or user_field not in user_data:
                not_filled_fields.append(form_field_name)
                continue
            
            try:
                value = user_data[user_field]
                
                # Handle different field types
                if field_type == 'text' or field_type == 'email' or field_type == 'tel' or field_type == 'url':
                    # For text inputs
                    selector = f"input[name='{form_field_name}'], input[id='{form_field_name}']"
                    if self.page.query_selector(selector):
                        self.page.fill(selector, str(value))
                        filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                elif field_type == 'select':
                    # For dropdown selects
                    selector = f"select[name='{form_field_name}'], select[id='{form_field_name}']"
                    if self.page.query_selector(selector):
                        # Try to find a matching option
                        match_found = False
                        
                        for option in options:
                            option_text = option.get('text', '').lower()
                            option_value = option.get('value', '').lower()
                            
                            # Check if the user value matches any option
                            if (str(value).lower() in option_text or 
                                str(value).lower() in option_value):
                                self.page.select_option(selector, value=option.get('value'))
                                filled_fields.append(form_field_name)
                                match_found = True
                                break
                        
                        if not match_found:
                            not_filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                elif field_type == 'radio':
                    # For radio buttons
                    selector = f"input[type='radio'][name='{form_field_name}'][value='{value}']"
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                elif field_type == 'checkbox':
                    # For checkboxes
                    selector = f"input[type='checkbox'][name='{form_field_name}']"
                    if self.page.query_selector(selector):
                        current_state = self.page.is_checked(selector)
                        desired_state = value if isinstance(value, bool) else (value.lower() == 'true')
                        
                        if current_state != desired_state:
                            self.page.click(selector)
                        
                        filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                elif field_type == 'textarea':
                    # For text areas
                    selector = f"textarea[name='{form_field_name}'], textarea[id='{form_field_name}']"
                    if self.page.query_selector(selector):
                        self.page.fill(selector, str(value))
                        filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                else:
                    # Default to treating as a text input
                    selector = f"input[name='{form_field_name}'], input[id='{form_field_name}']"
                    if self.page.query_selector(selector):
                        self.page.fill(selector, str(value))
                        filled_fields.append(form_field_name)
                    else:
                        not_filled_fields.append(form_field_name)
                
                # Add a small delay to avoid overwhelming the page
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error filling field '{form_field_name}': {str(e)}")
                not_filled_fields.append(form_field_name)
        
        return {
            'filled_fields': filled_fields,
            'not_filled_fields': not_filled_fields
        }
    
    def handle_pagination(self):
        """Handle form pagination by looking for and clicking next buttons"""
        next_button_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "input[type='submit'][value='Next']",
            "input[type='submit'][value='Continue']",
            "a:has-text('Next')",
            "a:has-text('Continue')"
        ]
        
        for selector in next_button_selectors:
            try:
                if self.page.query_selector(selector):
                    self.page.click(selector)
                    self.page.wait_for_load_state("networkidle")
                    return True
            except Exception as e:
                logger.warning(f"Error clicking next button '{selector}': {str(e)}")
        
        return False
    
    def extract_current_url(self):
        """Get the current URL after form filling"""
        return self.page.url
    
    def take_screenshot(self, filename="form_filled.png"):
        """Take a screenshot of the filled form"""
        return self.page.screenshot(path=filename)
    
    def autofill_form(self, url, field_mappings, user_data, handle_pagination=True):
        """Main method to autofill a form"""
        results = {
            'success': False,
            'filled_fields': [],
            'not_filled_fields': [],
            'final_url': '',
            'error': None
        }
        
        try:
            self.start_browser()
            
            # Navigate to the form
            if not self.navigate_to_url(url):
                results['error'] = "Failed to navigate to the form URL"
                return results
            
            # Fill the form
            fill_results = self.fill_form(field_mappings, user_data)
            results['filled_fields'].extend(fill_results['filled_fields'])
            results['not_filled_fields'].extend(fill_results['not_filled_fields'])
            
            # Handle pagination if needed
            if handle_pagination and self.handle_pagination():
                # If we moved to a next page, fill that form too
                next_fill_results = self.fill_form(field_mappings, user_data)
                results['filled_fields'].extend(next_fill_results['filled_fields'])
                results['not_filled_fields'].extend(next_fill_results['not_filled_fields'])
            
            # Get the final URL
            results['final_url'] = self.extract_current_url()
            results['success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error in autofill_form: {str(e)}")
        # finally:
        #     self.close_browser()
        
        return results

# Function to be used by the AutofillAgent
def perform_autofill(form_url, mapping_data=None, mapping=None):
    """Function to be called by the autofill agent"""
    try:
        # Check if form_url is provided
        if not form_url:
            return "Error: No form URL provided. Please specify the URL of the form to fill."
            
        # Handle different parameter formats
        # If mapping_data is provided, use it
        if mapping_data:
            if isinstance(mapping_data, str):
                try:
                    mapping_data = json.loads(mapping_data)
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format in mapping_data parameter"
            
            # Extract field mappings
            field_mappings = mapping_data.get('mapping_result', {}).get('field_mapping', {})
            user_data = mapping_data.get('user_data', {})
            
            # Check if field_mappings is empty
            if not field_mappings:
                field_mappings = mapping_data.get('field_mapping', {})
                
                # Check if there's a 'field_mappings' key with a list of field mappings
                if not field_mappings and mapping_data.get('field_mappings') and isinstance(mapping_data.get('field_mappings'), list):
                    # Convert the list of mappings to the format expected by autofill_form
                    mappings_list = mapping_data.get('field_mappings')
                    field_mappings = {}
                    user_data = {}
                    for item in mappings_list:
                        field_name = item.get('field_name')
                        if field_name:
                            field_mappings[field_name] = {
                                'user_field': field_name,
                                'field_type': item.get('type', 'text')
                            }
                            user_data[field_name] = item.get('value', '')
                
                # Check if there's a 'fields' key with a list of field mappings (used in main.py)
                elif not field_mappings and mapping_data.get('fields') and isinstance(mapping_data.get('fields'), list):
                    # Convert the list of fields to the format expected by autofill_form
                    fields_list = mapping_data.get('fields')
                    field_mappings = {}
                    user_data = {}
                    for item in fields_list:
                        field_name = item.get('name')  # Note: using 'name' instead of 'field_name'
                        if field_name:
                            field_mappings[field_name] = {
                                'user_field': field_name,
                                'field_type': item.get('type', 'text')
                            }
                            user_data[field_name] = item.get('value', '')
                
                elif not field_mappings and isinstance(mapping_data, dict):
                    # Try to use the mapping_data directly as field_mappings
                    field_mappings = mapping_data
                    user_data = mapping_data
                    
        # If mapping is provided directly, use it
        elif mapping:
            # Convert the mapping list to a field_mappings dictionary
            field_mappings = {}
            for item in mapping:
                field_id = item.get('field_id') or item.get('field_name')
                if field_id:
                    field_mappings[field_id] = {
                        'user_field': 'custom',
                        'field_type': item.get('field_type', 'text')
                    }
            
            # Create a flat user_data dictionary from the mapping values
            user_data = {}
            for item in mapping:
                field_id = item.get('field_id') or item.get('field_name')
                if field_id:
                    user_data[field_id] = item.get('value', '')
        else:
            return "Error: No mapping data provided. Please provide either 'mapping_data' or 'mapping' parameter with field mapping information."
        
        # Perform the form autofill
        autofiller = FormAutofiller()
        results = autofiller.autofill_form(form_url, field_mappings, user_data)
        
        # Add metrics for evaluation
        results['metrics'] = {
            'filled_count': len(results['filled_fields']),
            'not_filled_count': len(results['not_filled_fields']),
            'fill_rate': len(results['filled_fields']) / (len(results['filled_fields']) + len(results['not_filled_fields'])) * 100 if (len(results['filled_fields']) + len(results['not_filled_fields'])) > 0 else 0
        }
        
        return json.dumps(results, indent=2)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in perform_autofill: {str(e)}\n{error_details}")
        return f"Error performing form autofill: {str(e)}"