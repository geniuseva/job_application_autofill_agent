import re
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def map_fields_to_user_data(form_fields, user_data_schema):
    """
    Map scraped form fields to user data schema
    
    Args:
        form_fields (list): List of form fields from scraper
        user_data_schema (dict): Schema of user data fields available
        
    Returns:
        dict: Mapping of form field names to user data field names
    """
    mapping = {}
    required_missing_fields = []
    
    # Common mapping patterns
    field_mapping_patterns = {
        'name': ['name', 'full[ _-]?name', 'your[ _-]?name'],
        'first[ _-]?name': ['first[ _-]?name', 'given[ _-]?name', 'forename'],
        'last[ _-]?name': ['last[ _-]?name', 'family[ _-]?name', 'surname'],
        'email': ['email', 'e[ _-]?mail', 'email[ _-]?address'],
        'phone': ['phone', 'telephone', 'mobile', 'cell', 'phone[ _-]?number'],
        'address': ['address', 'street[ _-]?address', 'mailing[ _-]?address'],
        'city': ['city', 'town'],
        'state': ['state', 'province', 'region'],
        'zip': ['zip', 'zip[ _-]?code', 'postal[ _-]?code'],
        'country': ['country', 'nation'],
        'education': ['education', 'degree', 'qualification'],
        'university': ['university', 'college', 'school', 'institution'],
        'major': ['major', 'field[ _-]?of[ _-]?study', 'course'],
        'gpa': ['gpa', 'grade[ _-]?point[ _-]?average'],
        'graduation': ['graduation[ _-]?date', 'year[ _-]?of[ _-]?graduation', 'completion[ _-]?date'],
        'experience': ['experience', 'work[ _-]?experience', 'employment[ _-]?history'],
        'company': ['company', 'employer', 'organization', 'firm'],
        'position': ['position', 'title', 'job[ _-]?title', 'role'],
        'start_date': ['start[ _-]?date', 'from', 'beginning[ _-]?date'],
        'end_date': ['end[ _-]?date', 'to', 'completion[ _-]?date'],
        'skills': ['skills', 'abilities', 'competencies', 'proficiencies'],
        'languages': ['languages', 'language[ _-]?proficiency'],
        'resume': ['resume', 'cv', 'curriculum[ _-]?vitae'],
        'cover_letter': ['cover[ _-]?letter', 'motivation[ _-]?letter', 'application[ _-]?letter'],
        'references': ['references', 'referees'],
        'portfolio': ['portfolio', 'work[ _-]?samples', 'projects'],
        'linkedin': ['linkedin', 'linkedin[ _-]?profile', 'linkedin[ _-]?url'],
        'github': ['github', 'github[ _-]?profile', 'github[ _-]?url'],
        'website': ['website', 'personal[ _-]?website', 'portfolio[ _-]?website'],
        'salary': ['salary', 'salary[ _-]?expectation', 'expected[ _-]?salary', 'desired[ _-]?salary'],
        'availability': ['availability', 'start[ _-]?date', 'when[ _-]?can[ _-]?you[ _-]?start'],
        'visa': ['visa[ _-]?status', 'work[ _-]?authorization', 'right[ _-]?to[ _-]?work'],
        'gender': ['gender', 'sex'],
        'race': ['race', 'ethnicity'],
        'veteran': ['veteran[ _-]?status', 'military[ _-]?service'],
        'disability': ['disability', 'disability[ _-]?status'],
    }
    
    for field in form_fields:
        field_name = field.get('name', '').lower()
        field_id = field.get('id', '').lower()
        field_label = field.get('label', '').lower() if field.get('label') else ''
        field_placeholder = field.get('placeholder', '').lower()
        field_required = field.get('required', False)
        
        # Try to map the field using name, id, label, or placeholder
        mapped = False
        for user_field, patterns in field_mapping_patterns.items():
            for pattern in patterns:
                # Create a regex pattern
                regex_pattern = f".*{pattern}.*"
                
                # Check if any field identifier matches the pattern
                if (re.match(regex_pattern, field_name) or
                    re.match(regex_pattern, field_id) or
                    re.match(regex_pattern, field_label) or
                    re.match(regex_pattern, field_placeholder)):
                    
                    if user_field in user_data_schema:
                        mapping[field['name']] = {
                            'user_field': user_field,
                            'required': field_required,
                            'field_type': field['type'],
                            'options': field.get('options', [])
                        }
                        mapped = True
                        break
            
            if mapped:
                break
        
        # If the field is required but couldn't be mapped, add it to the missing list
        if field_required and not mapped:
            required_missing_fields.append({
                'name': field_name or field_id,
                'label': field_label,
                'type': field['type'],
                'options': field.get('options', [])
            })
    
    return {
        'field_mapping': mapping,
        'required_missing_fields': required_missing_fields
    }

def analyze_mapping_quality(mapping_result, form_fields):
    """
    Analyze the quality of the mapping
    
    Args:
        mapping_result (dict): Result from map_fields_to_user_data
        form_fields (list): Original form fields from scraper
        
    Returns:
        dict: Quality metrics and suggestions
    """
    total_fields = len(form_fields)
    mapped_fields = len(mapping_result['field_mapping'])
    missing_required = len(mapping_result['required_missing_fields'])
    
    mapping_coverage = (mapped_fields / total_fields) * 100 if total_fields > 0 else 0
    
    quality_analysis = {
        'total_form_fields': total_fields,
        'mapped_fields': mapped_fields,
        'mapping_coverage': mapping_coverage,
        'missing_required_fields': missing_required,
        'quality_assessment': 'Good' if mapping_coverage >= 80 else 'Fair' if mapping_coverage >= 50 else 'Poor',
        'suggestions': []
    }
    
    # Generate suggestions for improvement
    if missing_required > 0:
        quality_analysis['suggestions'].append(
            f"Need to collect {missing_required} required fields that couldn't be mapped automatically"
        )
    
    if mapping_coverage < 80:
        quality_analysis['suggestions'].append(
            "Consider enhancing user data schema to improve mapping coverage"
        )
    
    return quality_analysis

# Function to be used by the MapperAgent
def perform_mapping(scraped_data, user_data_schema):
    """Function to be called by the mapping agent"""
    try:
        # Parse scraped data if it's a JSON string
        if isinstance(scraped_data, str):
            scraped_data = json.loads(scraped_data)
        
        form_fields = scraped_data.get('form_fields', [])
        
        # Perform the mapping
        mapping_result = map_fields_to_user_data(form_fields, user_data_schema)
        
        # Analyze the mapping quality
        quality_analysis = analyze_mapping_quality(mapping_result, form_fields)
        
        # Combine results
        result = {
            'mapping_result': mapping_result,
            'quality_analysis': quality_analysis,
            'original_url': scraped_data.get('url', '')
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error performing mapping: {str(e)}")
        return f"Error performing mapping: {str(e)}"