from playwright.sync_api import sync_playwright
import time
import json
import logging
import re
import random
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode

# Import Phoenix tracing
from core.tracing import tracer

# Global variables to store browser instances
_playwright = None
_browser = None
_page = None

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FormAutofiller:
    """Class for automatically filling out forms using Playwright"""
    
    def __init__(self, reuse_browser=False):
        """
        Initialize the form autofiller
        
        Args:
            reuse_browser: Whether to reuse an existing browser instance if available
        """
        global _playwright, _browser, _page
        
        if reuse_browser and _browser and _page:
            logger.info("Reusing existing browser instance")
            self.playwright = _playwright
            self.browser = _browser
            self.page = _page
        else:
            self.playwright = None
            self.browser = None
            self.page = None
    
    def start_browser(self):
        """Start the Playwright browser"""
        global _playwright, _browser, _page
        
        if self.browser and self.page:
            logger.info("Browser already started")
            return
            
        if not self.playwright:
            self.playwright = sync_playwright().start()
            _playwright = self.playwright
            
        self.browser = self.playwright.chromium.launch(headless=False)  # Set to True in production
        _browser = self.browser
        
        self.page = self.browser.new_page()
        _page = self.page
        
        logger.info("New browser instance started")
        
    def close_browser(self):
        """Close the browser and Playwright"""
        global _playwright, _browser, _page
        
        if self.browser:
            self.browser.close()
            _browser = None
            
        if self.playwright:
            self.playwright.stop()
            _playwright = None
            
        _page = None
        self.browser = None
        self.playwright = None
        self.page = None
    
    def navigate_to_url(self, url, navigation_timeout=60000, load_timeout=30000):
        """
        Navigate to the form URL using a robust approach
        
        Args:
            url: The URL to navigate to
            navigation_timeout: Timeout for the initial navigation in milliseconds
            load_timeout: Timeout for waiting for page elements in milliseconds
        """
        try:
            # Navigate to the URL and get the response
            logger.info(f"Navigating to URL with timeout {navigation_timeout}ms: {url}")
            response = self.page.goto(url, timeout=navigation_timeout)
            logger.debug(f"Navigation response status: {response.status if response else 'No response'}")
            
            logger.info("Waiting for page to load")
            try:
                # Step 1: Wait for basic HTML structure to load
                logger.debug(f"Waiting for basic HTML structure (domcontentloaded) with timeout {load_timeout}ms")
                self.page.wait_for_load_state("domcontentloaded", timeout=load_timeout)
                logger.debug("DOM content loaded successfully")
                
                # Step 2: Wait for form elements to appear
                logger.debug(f"Waiting for form elements to be visible with timeout {load_timeout}ms")
                form_selector = "form, input[type='text'], input[type='email'], button, a"
                self.page.wait_for_selector(form_selector, state="visible", timeout=load_timeout)
                logger.debug("Form elements are now visible")
                
                # Add a small fixed delay for any remaining JS to initialize
                logger.debug("Waiting 2 seconds for JS initialization")
                # time.sleep(2)
                
                logger.info("Page loaded successfully")
            except Exception as e:
                logger.warning(f"Page load timeout, proceeding anyway: {str(e)}")
                # Continue even if there's a timeout, as the page might still be usable
            
            # Log page title for verification
            title = self.page.title()
            logger.info(f"Page title: {title}")
            
            return True
        except Exception as e:
            logger.error(f"Error navigating to URL: {str(e)}")
            return False
    
    def fill_form_with_instructions(self, form_fields):
        """Fill form fields using structured autofill instructions with human-like behavior"""
        filled_fields = []
        not_filled_fields = []
        
        logger.info(f"Processing {len(form_fields)} form fields")
        
        for i, field in enumerate(form_fields):
            field_name = field.get('field_name', '')
            field_type = field.get('field_type', '')
            selector = field.get('selector', '')
            fill_method = field.get('fill_method', '')
            
            logger.info(f"Field {i+1}/{len(form_fields)}: {field_name} ({field_type}) (selector: {selector})")
            logger.debug(f"  - Selector: {selector}")
            logger.debug(f"  - Fill method: {fill_method}")
            
            # Skip fields without necessary information
            if not selector:
                logger.warning(f"No selector provided for field '{field_name}', skipping")
                not_filled_fields.append(field_name)
                continue
            
            try:
                # Try to wait for the element to be visible first
                try:
                    self.page.wait_for_selector(selector, state="visible", timeout=5000)
                except Exception as e:
                    logger.warning(f"Element not visible for selector: {selector}, but continuing: {str(e)}")
                
                # Check if the element exists
                element = self.page.query_selector(selector)
                if not element:
                    logger.warning(f"Element not found for selector: {selector}")
                    not_filled_fields.append(field_name)
                    continue
                
                # Fill the field based on the fill method
                if fill_method == "fill":
                    value = field.get("value", "")
                    logger.debug(f"  - Value: {value}")
                    
                    # Clear the field first (more human-like)
                    self.page.click(selector)
                    self.page.keyboard.press("Control+a")
                    self.page.keyboard.press("Delete")
                    
                    # Type the value with random delays between characters (more human-like)
                    for char in str(value):
                        self.page.type(selector, char, delay=random.uniform(50, 150))
                        
                    logger.info(f"✓ Filled text field '{field_name}' with value '{value}'")
                    filled_fields.append(selector)
                    
                elif fill_method == "select_option":
                    selected_value = field.get("selected_value", "")
                    logger.debug(f"  - Selected value: {selected_value}")
                    self.page.select_option(selector, value=selected_value)
                    logger.info(f"✓ Selected option '{selected_value}' in field '{field_name}'")
                    filled_fields.append(selector)
                    
                elif fill_method == "check":
                    checked = field.get("checked", False)
                    logger.debug(f"  - Checked: {checked}")
                    if checked:
                        self.page.check(selector)
                    else:
                        self.page.uncheck(selector)
                    logger.info(f"✓ Set checkbox '{field_name}' to {checked}")
                    filled_fields.append(selector)
                    
                elif fill_method == "set_input_files":
                    file_paths = field.get("file_paths", [])
                    if file_paths:
                        logger.debug(f"  - File paths: {file_paths}")
                        self.page.set_input_files(selector, file_paths)
                        logger.info(f"✓ Set file input '{field_name}' with files")
                        filled_fields.append(selector)
                    else:
                        logger.warning(f"No file paths provided for file input '{field_name}'")
                        not_filled_fields.append(selector)
                
                else:
                    logger.warning(f"Unknown fill method '{fill_method}' for field '{field_name}'")
                    not_filled_fields.append(selector)
                
                # Verify the field was filled correctly (for text fields)
                if fill_method == "fill":
                    try:
                        actual_value = self.page.evaluate("el => el.value", element)
                        logger.debug(f"  - Verified value: {actual_value}")
                    except Exception as e:
                        logger.warning(f"Could not verify field value: {str(e)}")
                
                # Add a random delay between field fills to appear more human-like
                delay = random.uniform(0.5, 1.5)
                logger.debug(f"  - Waiting {delay:.2f} seconds...")
                # time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error filling field '{field_name}': {str(e)}")
                not_filled_fields.append(selector)
        
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
            "a:has-text('Continue')",
            "button[type='submit']",
            "input[type='submit']"
        ]
        
        logger.info("Looking for pagination buttons")
        for selector in next_button_selectors:
            try:
                logger.debug(f"Checking for selector: {selector}")
                if self.page.query_selector(selector):
                    logger.info(f"Found pagination button: {selector}")
                    
                    # Click the button
                    self.page.click(selector)
                    logger.info("Clicked pagination button")
                    
                    # Wait for navigation to complete
                    try:
                        logger.debug("Waiting for navigation after pagination")
                        self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                        self.page.wait_for_selector("form, input[type='text'], input[type='email']",
                                                   state="visible", timeout=30000)
                        logger.info("Navigation after pagination completed")
                    except Exception as e:
                        logger.warning(f"Timeout waiting for navigation after pagination: {str(e)}")
                    
                    return True
            except Exception as e:
                logger.warning(f"Error clicking next button '{selector}': {str(e)}")
        
        logger.info("No pagination buttons found")
        return False
    
    def extract_current_url(self):
        """Get the current URL after form filling"""
        return self.page.url
    
    def autofill_form_with_instructions(self, form_url, form_fields, handle_pagination=False,
                                       navigation_timeout=90000, load_timeout=45000, close_browser=False):
        """
        Main method to autofill a form using structured instructions with robust error handling
        
        Args:
            form_url: URL of the form to fill
            form_fields: List of field instructions for filling the form
            handle_pagination: Whether to handle form pagination
            navigation_timeout: Timeout for initial page navigation in milliseconds
            load_timeout: Timeout for waiting for page elements in milliseconds
            close_browser: Whether to close the browser after finishing (default: True)
        """
        results = {
            'success': False,
            'filled_fields': [],
            'not_filled_fields': [],
            'final_url': '',
            'error': None
        }
        
        
        try:
            # Start browser if not already started
            if not self.browser or not self.page:
                logger.info("Starting browser")
                self.start_browser()
            else:
                logger.info("Using existing browser instance")
            
            # Set up console log listener
            self.page.on("console", lambda msg: logger.debug(f"BROWSER CONSOLE: {msg.text} (type: {msg.type})"))
            
            # Navigate to the form with custom timeouts
            logger.info(f"Navigating to form URL: {form_url}")
            if not self.navigate_to_url(form_url, navigation_timeout, load_timeout):
                results['error'] = "Failed to navigate to the form URL"
                logger.error("Navigation failed")
                return results
            
            
            # Fill the form using instructions
            logger.info(f"Filling form with {len(form_fields)} fields")
            fill_results = self.fill_form_with_instructions(form_fields)
            results['filled_fields'].extend(fill_results['filled_fields'])
            results['not_filled_fields'].extend(fill_results['not_filled_fields'])
            
            
            # Handle pagination if needed
            if handle_pagination:
                pagination_result = self.handle_pagination()
                if pagination_result:
                    logger.info("Form pagination detected, filling next page")
                    # If we moved to a next page, fill that form too
                    next_fill_results = self.fill_form_with_instructions(form_fields)
                    results['filled_fields'].extend(next_fill_results['filled_fields'])
                    results['not_filled_fields'].extend(next_fill_results['not_filled_fields'])
                    
            
            # Get the final URL
            results['final_url'] = self.extract_current_url()
            results['success'] = True
            
            
            logger.info(f"Form filling completed: {len(results['filled_fields'])} fields filled, {len(results['not_filled_fields'])} fields not filled")
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error in autofill_form_with_instructions: {str(e)}")
            
                
        finally:
            if close_browser:
                logger.info("Closing browser")
                self.close_browser()
            else:
                logger.info("Keeping browser open as requested")
        
        return results

# Function to be used by the AutofillAgent
@tracer.chain
def perform_autofill(form_data):
    """
    Function to be called by the autofill agent
    
    Args:
        form_data: JSON object containing form URL and field instructions
        
    Returns:
        JSON string with results of the autofill operation
    """
    try:
        # Parse input if it's a string
        if isinstance(form_data, str):
            form_data = json.loads(form_data)
        
        # Extract form URL and fields
        form_url = form_data.get('form_url', '')
        form_fields = form_data.get('form_fields', [])
        
        # Validate inputs
        if not form_url:
            return json.dumps({
                'success': False,
                'error': 'No form URL provided'
            }, indent=2)
        
        if not form_fields:
            return json.dumps({
                'success': False,
                'error': 'No form fields provided'
            }, indent=2)
        
        # Extract timeout parameters if provided
        navigation_timeout = form_data.get('navigation_timeout', 90000)  # Default 90 seconds
        load_timeout = form_data.get('load_timeout', 45000)  # Default 45 seconds
        
        # Perform the form autofill using browser automation
        # Extract browser control parameters
        keep_browser_open = form_data.get('keep_browser_open', True)
        reuse_browser = form_data.get('reuse_browser', True)
        
        logger.info(f"Starting form autofill for URL: {form_url} with timeouts: navigation={navigation_timeout}ms, load={load_timeout}ms")
        logger.info(f"Browser will {'remain open' if keep_browser_open else 'be closed'} after completion")
        logger.info(f"{'Reusing' if reuse_browser else 'Creating new'} browser instance")
        
        autofiller = FormAutofiller(reuse_browser=reuse_browser)
        results = autofiller.autofill_form_with_instructions(
            form_url,
            form_fields,
            handle_pagination=False,
            navigation_timeout=navigation_timeout,
            load_timeout=load_timeout,
            close_browser=not keep_browser_open
        )
        
        # Add metrics for evaluation
        results['metrics'] = {
            'filled_count': len(results['filled_fields']),
            'not_filled_count': len(results['not_filled_fields']),
            'fill_rate': len(results['filled_fields']) / (len(results['filled_fields']) + len(results['not_filled_fields'])) * 100 if (len(results['filled_fields']) + len(results['not_filled_fields'])) > 0 else 0
        }
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error performing form autofill: {str(e)}")
        return json.dumps({
            'success': False,
            'error': f"Error performing form autofill: {str(e)}"
        }, indent=2)