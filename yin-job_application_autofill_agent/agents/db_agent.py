import json
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserDatabase:
    """Simple user database for storing and retrieving user profile information"""
    
    def __init__(self, db_file="data/user_profiles.json"):
        """Initialize the database with a file path"""
        self.db_file = db_file
        self.profiles = {}
        self.load_profiles()
    
    def load_profiles(self):
        """Load user profiles from the database file"""
        logger.info(f"Loading profiles from {self.db_file}")
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    self.profiles = json.load(f)
                logger.info(f"Successfully loaded profiles: {list(self.profiles.keys())}")
            except json.JSONDecodeError:
                # If file exists but is invalid JSON, start with empty dict
                logger.error(f"Error parsing JSON from {self.db_file}")
                self.profiles = {}
        else:
            # If file doesn't exist, start with empty dict
            logger.warning(f"Database file {self.db_file} not found")
            self.profiles = {}
    
    def save_profiles(self):
        """Save user profiles to the database file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def get_profile(self, user_id):
        """Get a user profile by ID"""
        return self.profiles.get(user_id, None)
    
    def create_profile(self, user_id, profile_data):
        """Create a new user profile"""
        if user_id in self.profiles:
            return False, "User ID already exists"
        
        self.profiles[user_id] = profile_data
        self.save_profiles()
        return True, "Profile created successfully"
    
    def update_profile(self, user_id, profile_data):
        """Update an existing user profile"""
        if user_id not in self.profiles:
            return False, "User ID not found"
        
        # Update only provided fields
        for key, value in profile_data.items():
            self.profiles[user_id][key] = value
        
        self.save_profiles()
        return True, "Profile updated successfully"
    
    def delete_profile(self, user_id):
        """Delete a user profile"""
        if user_id not in self.profiles:
            return False, "User ID not found"
        
        del self.profiles[user_id]
        self.save_profiles()
        return True, "Profile deleted successfully"
    
    def get_profile_fields(self, user_id, fields=None):
        """Get specific fields from a user profile"""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        if not fields:
            return profile
        
        result = {}
        for field in fields:
            if field in profile:
                result[field] = profile[field]
        
        return result
    
    def create_default_profile(self):
        """Create a default profile for testing"""
        default_user_id = "default_user"
        default_profile = {
            "personal": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
                "country": "USA",
                "birthdate": "1990-01-01",
                "linkedin": "https://linkedin.com/in/johndoe",
                "github": "https://github.com/johndoe",
                "website": "https://johndoe.com"
            },
            "education": [
                {
                    "institution": "University of Example",
                    "degree": "Bachelor of Science",
                    "field_of_study": "Computer Science",
                    "start_date": "2008-09-01",
                    "end_date": "2012-05-31",
                    "gpa": "3.8"
                },
                {
                    "institution": "Example Graduate School",
                    "degree": "Master of Science",
                    "field_of_study": "Artificial Intelligence",
                    "start_date": "2012-09-01",
                    "end_date": "2014-05-31",
                    "gpa": "3.9"
                }
            ],
            "experience": [
                {
                    "company": "Tech Company Inc.",
                    "position": "Software Engineer",
                    "location": "San Francisco, CA",
                    "start_date": "2014-06-15",
                    "end_date": "2018-12-31",
                    "description": "Developed and maintained web applications using Python and JavaScript."
                },
                {
                    "company": "AI Innovations LLC",
                    "position": "Senior Developer",
                    "location": "Seattle, WA",
                    "start_date": "2019-01-15",
                    "end_date": "present",
                    "description": "Lead developer for machine learning applications."
                }
            ],
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "Machine Learning",
                "Data Analysis", "SQL", "MongoDB", "Git", "Docker"
            ],
            "languages": [
                {"language": "English", "proficiency": "Native"},
                {"language": "Spanish", "proficiency": "Intermediate"},
                {"language": "French", "proficiency": "Basic"}
            ],
            "certifications": [
                {
                    "name": "AWS Certified Developer",
                    "issuer": "Amazon Web Services",
                    "date": "2018-06-01",
                    "expires": "2021-06-01"
                },
                {
                    "name": "Google Cloud Professional",
                    "issuer": "Google",
                    "date": "2019-03-15",
                    "expires": "2022-03-15"
                }
            ],
            "projects": [
                {
                    "name": "Data Visualization Tool",
                    "description": "A web-based data visualization tool using D3.js",
                    "url": "https://github.com/johndoe/data-viz"
                },
                {
                    "name": "Machine Learning Framework",
                    "description": "A framework for quickly deploying machine learning models",
                    "url": "https://github.com/johndoe/ml-framework"
                }
            ]
        }
        
        self.create_profile(default_user_id, default_profile)
        return default_user_id, default_profile

# Function to be used by the DatabaseAgent
def db_agent_handler(action, params=None):
    """Handle database operations for the DB Agent"""
    logger.info(f"DB Agent handling action: {action} with params: {params}")
    db = UserDatabase()
    
    # If the database is empty, create a default profile
    if not db.profiles:
        logger.info("No profiles found, creating default profile")
        db.create_default_profile()
    
    if action == "get_profile":
        user_id = params.get("user_id", "default_user")
        logger.info(f"Getting profile for user ID: {user_id}")
        profile = db.get_profile(user_id)
        if profile:
            logger.info(f"Successfully retrieved profile for {user_id}")
            return json.dumps(profile, indent=2)
        else:
            logger.warning(f"Profile for user ID '{user_id}' not found")
            return f"Profile for user ID '{user_id}' not found"
    
    elif action == "get_fields":
        user_id = params.get("user_id", "default_user")
        fields = params.get("fields", [])
        logger.info(f"Getting fields {fields} for user ID: {user_id}")
        result = db.get_profile_fields(user_id, fields)
        if result:
            logger.info(f"Successfully retrieved fields for {user_id}")
            return json.dumps(result, indent=2)
        else:
            logger.warning(f"Could not retrieve fields for user ID '{user_id}'")
            return f"Could not retrieve fields for user ID '{user_id}'"
    
    elif action == "get_profile_schema":
        # Return the schema of available user data fields
        user_id = params.get("user_id", "default_user")
        profile = db.get_profile(user_id)
        if not profile:
            return "No user profile found to extract schema"
        
        schema = extract_schema_from_profile(profile)
        return json.dumps(schema, indent=2)
    
    elif action == "update_profile":
        user_id = params.get("user_id", "default_user")
        profile_data = params.get("profile_data", {})
        success, message = db.update_profile(user_id, profile_data)
        return message
    
    elif action == "create_profile":
        user_id = params.get("user_id")
        profile_data = params.get("profile_data", {})
        success, message = db.create_profile(user_id, profile_data)
        return message
    
    else:
        return f"Unknown action: {action}"

def extract_schema_from_profile(profile):
    """Extract a flat schema from a nested profile"""
    schema = {}
    
    def process_dict(d, prefix=""):
        for key, value in d.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                process_dict(value, f"{new_key}.")
            elif isinstance(value, list):
                if value and not isinstance(value, (str, int, float, bool)):
                    if isinstance(value[0], dict):
                        # For list of dicts, use the first item as example
                        for sub_key in value[0].keys():
                            schema[f"{new_key}.{sub_key}"] = True
                    else:
                        # For list of simple values
                        schema[new_key] = True
                else:
                    schema[new_key] = True
            else:
                schema[new_key] = True
    
    process_dict(profile)
    return list(schema.keys())