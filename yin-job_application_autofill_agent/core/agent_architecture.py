import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import os
import logging
from agents.instruction_generator import generate_autofill_instructions

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import agent functions
from agents.scraper_agent import perform_scraping
from agents.db_agent import db_agent_handler
from agents.autofill_agent import perform_autofill

# Retrieve the API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")
# Configuration for the agents
config_list = [
    {
        "model": "gpt-4-turbo-preview",
        "api_key": api_key
    }
]

# Define agent configurations with specific instructions
scraper_config = {
    "name": "ScrapeAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2,
        "functions": [
            {
                "name": "scrape_url",
                "description": "Scrape form fields from a URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to scrape"
                        }
                    },
                    "required": ["url"]
                }
            }
        ]
    },
    "system_message": """You are a web scraping specialist. Your task is to:
    1. Navigate to a provided URL
    2. Extract all form fields and their attributes (name, id, type, required status)
    3. Identify any special requirements for each field
    4. Return the structured data in a consistent JSON format
    5. Handle different types of forms including multi-page applications
    
    When asked to scrape a URL, use your scrape_url function with the URL as the parameter.
    Be precise and thorough in your extraction."""
}

# Form analyzer agent configuration
form_analyzer_config = {
    "name": "FormAnalyzerAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1
    },
    "system_message": """You are a form analysis specialist. Your task is to:
    1. Analyze form fields and their attributes
    2. Identify the purpose of each field (name, email, etc.)
    3. Categorize fields by type and importance
    4. Return a structured analysis in JSON format
    
    When analyzing form fields, consider:
    - Field name, ID, and label text
    - Field type (text, select, checkbox, etc.)
    - Whether the field is required
    - Any placeholder text or default values
    - Options for select/dropdown fields
    
    For each field, determine what user information it's requesting (e.g., full name, email address, phone number).
    
    Be precise and thorough in your analysis.
    
    After your task finished, call OrchestratorAgent using the following format and send it your result:
    "@OrchestratorAgent: [result]"
    """
}

# Query generator agent configuration
query_generator_config = {
    "name": "QueryGeneratorAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1
    },
    "system_message": """You are a database query specialist. Your task is to:
    1. Review form field analysis from the FormAnalyzerAgent
    2. Review database schema from the DatabaseAgent
    3. Determine what user data is needed based on the form fields
    4. Generate an efficient query structure that matches the actual database schema
    5. Return a structured query in JSON format
    
    IMPORTANT: You must wait until you have BOTH:
    - The form field analysis from FormAnalyzerAgent
    - The database schema from DatabaseAgent
    
    Based on the form analysis and database schema, create a query that specifies:
    - Required fields that must be retrieved (using the exact field names from the database schema)
    - Optional fields that would be helpful
    - Special fields that need specific handling (like dropdowns)
    
    Your query should be structured to help the database agent retrieve exactly the right information.
    Make sure the field names in your query match the actual field names in the database schema.
    
    For example, if the form needs a "full name" but the database has "personal.first_name" and "personal.last_name",
    include both of these fields in your query.
    
    Focus on retrieving only the necessary data."""
}

# Field mapper agent configuration
field_mapper_config = {
    "name": "FieldMapperAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1
    },
    "system_message": """You are a field mapping specialist. Your task is to match user data to form fields.

For each user data, find the most appropriate for filed that can be filled by this data:

IMPORTANT: Only return fields that have matching user data. Skip fields without matches.

For each matched field, include:
1. field_name: The name of the form field
2. field_type: The type of the form field (text, select, checkbox, etc.)
3. value: The matching user data value

Note: If the value is empty, don't generate it.
""
{
"field_name": "comments",
"field_type": "textarea",
"value": ""
}
""

Return your matches as a JSON object with a "matched_fields" array."""
}

# Instruction generator agent configuration
instruction_generator_config = {
    "name": "InstructionGeneratorAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1,
        "functions": [
            {
                "name": "generate_autofill_instructions",
                "description": "Generate autofill instructions from matched fields data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "matched_fields_data": {
                            "type": "object",
                            "description": "The matched fields from the Field Mapper Agent"
                        }
                    },
                    "required": ["matched_fields_data"]
                }
            }
        ]
    },
    "system_message": """You are an autofill instruction generator. Your task is to take matched form fields and generate complete autofill instructions.

Your job is to:
1. Take the matched fields from the Field Mapper Agent
3. Generate complete autofill instructions with:
   - field_name
   - field_type
   - selector (built from field name and type)
   - fill_method (based on field type)
   - value (from matched fields)

Use the generate_autofill_instructions function with the matched_fields_data parameter to create these instructions.

The output should be a JSON object with:
- form_url: The URL of the form to fill
- form_fields: Array of field instructions with field_type, selector, fill_method, and value

This will be used directly by the AutofillAgent to fill out the form."""
}

db_config = {
    "name": "DatabaseAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1,
        "functions": [
            {
                "name": "query_database",
                "description": "Query the user profile database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The database action to perform",
                            "enum": ["get_profile", "get_schema", "get_fields"]
                        },
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of fields to retrieve (for get_fields action)"
                        }
                    },
                    "required": ["action"]
                }
            }
        ]
    },
    "system_message": """You manage user profile information storage and retrieval.
    Your tasks:
    1. Retrieve relevant user data based on field mapping requirements
    2. Provide the database schema when requested
    3. Format user data for form submission
    4. Handle missing data by providing reasonable defaults
    
    When asked to retrieve user data, use your query_database function with the appropriate action:
    - Use action="get_profile" to get the complete user profile
    - Use action="get_schema" to get the user profile schema (this returns the structure of the database)
    - Use action="get_fields" with fields=[field1, field2, ...] to get specific fields
    
    When providing the schema, make sure to explain the structure of the user profile data, including:
    - The nested structure (personal, education, experience, etc.)
    - The data types of each field
    - Any special formatting requirements
    
    Be accurate and provide helpful information about the database structure."""
}

autofill_config = {
    "name": "AutofillAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2,
        "functions": [
            {
                "name": "fill_form",
                "description": "Fill out a form with structured autofill instructions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "form_data": {
                            "type": "object",
                            "description": "The form data with field instructions"
                        }
                    },
                    "required": ["form_data"]
                }
            }
        ]
    },
    "system_message": """You automate the process of filling out forms on websites.
    Your tasks:
    1. Use Playwright to navigate to the form URL
    2. Fill each field using its specific fill method:
       - Text fields: Use fill() with the provided value
       - Select dropdowns: Use select_option() with the selected_value
       - Checkboxes/Radio buttons: Use check() based on the checked state
    3. Handle special form elements appropriately
    4. Take a screenshot of the filled form
    5. Return detailed results of the filling process
    
    When asked to fill a form, use your fill_form function with the form_data parameter.
    The form_data should contain:
    - form_url: The URL of the form to fill
    - form_fields: Array of field instructions with field_type, selector, fill_method, and value
    
    Be careful to handle errors gracefully and provide detailed logging."""
}

orchestrator_config = {
    "name": "OrchestratorAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2
    },
    "system_message": """You coordinate the entire job application form filling process. Your purpose is to guide the workflow through these steps:

1. First, ask the ScrapeAgent to scrape form fields from the URL
2. Then,ask the FormAnalyzerAgent to analyze the form structure and field types
3. After it, ask the DatabaseAgent to get the database schema using query_database(action="get_schema")
3. After having results from steps 2 and 3, ask the QueryGeneratorAgent to create a database query based on the form analysis AND the database schema
4. Then, ask the DatabaseAgent to retrieve the necessary user information using the query
5. Next, ask the FieldMapperAgent to match the form fields to the user data (it will only return fields with matches)
6. Then, ask the InstructionGeneratorAgent to generate complete autofill instructions based on the matched fields
7. Finally, ask the AutofillAgent to fill the form using the mapping
8. Present the results back to the user

Each agent has specific expertise:
- ScrapeAgent: Extracts form fields from websites
- FormAnalyzerAgent: Analyzes form structure and identifies field purposes
- DatabaseAgent: Retrieves user profile data and schema information
- QueryGeneratorAgent: Creates efficient database queries based on form analysis and database schema
- FieldMapperAgent: Matches form fields to user data (only returns fields with matches)
- InstructionGeneratorAgent: Generates complete autofill instructions with selectors and fill methods from matched fields
- AutofillAgent: Fills forms with the structured instructions

Always keep track of which step in the process you're on, and explicitly name which agent you're addressing in each message. If any agent encounters an error, help resolve it by suggesting appropriate actions.

Use the following format when addressing agents:
"@ScrapeAgent: Please extract the form fields from [URL]"
"""
}

user_proxy_config = {
    "name": "UserProxyAgent",
    "human_input_mode": "ALWAYS",  # We'll need user input for missing information
    "max_consecutive_auto_reply": 10,
    "code_execution_config": {"use_docker": False},
    "llm_config": False  # No LLM for the user proxy
}

# Function to create and setup all agents
def create_agents():
    """Create all the agents needed for the job application autofill system"""
    # Create the agents
    user_proxy = UserProxyAgent(**user_proxy_config)
    orchestrator = AssistantAgent(**orchestrator_config)
    scraper = AssistantAgent(**scraper_config)
    db_agent = AssistantAgent(**db_config)
    autofill_agent = AssistantAgent(**autofill_config)
    form_analyzer = AssistantAgent(**form_analyzer_config)
    query_generator = AssistantAgent(**query_generator_config)
    field_mapper = AssistantAgent(**field_mapper_config)
    instruction_generator = AssistantAgent(**instruction_generator_config)
    
    # Register functions with their respective agents
    scraper.register_function(
        function_map={
            "scrape_url": perform_scraping
        }
    )
    
    instruction_generator.register_function(
        function_map={
            "generate_autofill_instructions": generate_autofill_instructions
        }
    )
    
    # Create a wrapper for db_agent_handler to handle different actions
    def db_function(action="get_profile", fields=None):
        if action == "get_profile":
            return db_agent_handler("get_profile", {"user_id": "default_user"})
        elif action == "get_schema":
            return db_agent_handler("get_profile_schema", {"user_id": "default_user"})
        elif action == "get_fields" and fields:
            return db_agent_handler("get_fields", {"user_id": "default_user", "fields": fields})
        else:
            return "Please specify a valid database action: get_profile, get_schema, or get_fields with field names."
    
    db_agent.register_function(
        function_map={
            "query_database": db_function
        }
    )
    
    autofill_agent.register_function(
        function_map={
            "fill_form": perform_autofill
        }
    )
    
    # Define the group chat
    groupchat = GroupChat(
        agents=[user_proxy, orchestrator, scraper, db_agent, autofill_agent,
                form_analyzer, query_generator, field_mapper, instruction_generator, autofill_agent],
        messages=[],
        max_round=50,
    )
    
    # Create the group chat manager
    manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

    return {
        "user_proxy": user_proxy,
        "orchestrator": orchestrator,
        "scraper": scraper,
        "db_agent": db_agent,
        "form_analyzer": form_analyzer,
        "query_generator": query_generator,
        "field_mapper": field_mapper,
        "instruction_generator": instruction_generator,
        "autofill_agent": autofill_agent,
        "groupchat": groupchat,
        "manager": manager
    }