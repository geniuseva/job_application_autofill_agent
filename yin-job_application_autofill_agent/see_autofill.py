from agents.autofill_agent import FormAutofiller
import time
import json
import os

def main():
    # Use the local HTML file we created
    current_dir = os.path.dirname(os.path.abspath(__file__))
    form_path = os.path.join(current_dir, "test_form.html")
    form_url = f"file://{form_path}"
    
    print(f"Using local test form: {form_url}")
    
    # Create field mappings that match our test_form.html
    field_mappings = {
        "first_name": {"user_field": "first_name", "field_type": "text"},
        "last_name": {"user_field": "last_name", "field_type": "text"},
        "email": {"user_field": "email", "field_type": "email"},
        "phone": {"user_field": "phone", "field_type": "tel"},
        "address": {"user_field": "address", "field_type": "text"},
        "education": {"user_field": "education", "field_type": "select",
                     "options": [
                         {"text": "High School", "value": "high_school"},
                         {"text": "Bachelor's Degree", "value": "bachelors"},
                         {"text": "Master's Degree", "value": "masters"},
                         {"text": "PhD", "value": "phd"}
                     ]},
        "experience": {"user_field": "experience", "field_type": "text"}
    }
    
    # Sample user data with more fields
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1 (555) 123-4567",
        "address": "123 Main St, Anytown, CA 12345",
        "education": "masters",
        "experience": "5"
    }
    
    print("Starting browser to fill form...")
    
    # Create the autofiller
    autofiller = FormAutofiller()
    
    try:
        # Start the browser (this will be visible with headless=False)
        autofiller.start_browser()
        
        # Navigate to the form
        print(f"Navigating to local test form...")
        if not autofiller.navigate_to_url(form_url):
            print("Failed to navigate to the form URL")
            return
        
        # Fill the form
        print("Filling form fields...")
        fill_results = autofiller.fill_form(field_mappings, user_data)
        
        # Take a screenshot
        screenshot_path = "form_filled.png"
        print(f"Taking screenshot and saving to {screenshot_path}...")
        autofiller.take_screenshot(screenshot_path)
        
        # Show results
        print("\nResults:")
        print(f"Filled fields: {fill_results['filled_fields']}")
        print(f"Not filled fields: {fill_results['not_filled_fields']}")
        
        # Wait for user to see the browser
        input("\nPress Enter to close the browser...")
        
    finally:
        # Close the browser
        autofiller.close_browser()
        print("Browser closed.")

if __name__ == "__main__":
    main()