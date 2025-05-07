import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import os
from dotenv import load_dotenv
load_dotenv()
# Import agent functions
from agents.scraper_agent import perform_scraping
from agents.db_agent import db_agent_handler
from agents.autofill_agent import perform_autofill
from agents.instruction_generator import generate_autofill_instructions

# Import Phoenix tracing
from core.tracing import tracer

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
2. Generate complete autofill instructions with:
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
2. Then, ask the DatabaseAgent to get the user profile using query_database(action="get_profile")
3. Next, ask the FieldMapperAgent to match the form fields to the user data (it will only return fields with matches)
4. Then, ask the InstructionGeneratorAgent to generate complete autofill instructions based on the matched fields
5. Finally, ask the AutofillAgent to fill the form using the instructions
6. Present the results back to the user

Each agent has specific expertise:
- ScrapeAgent: Extracts form fields from websites
- DatabaseAgent: Retrieves user profile data
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
    "code_execution_config": {"last_n_messages": 3, 
                              "work_dir": "coding",
                              "use_docker": False},
    "llm_config": False  # No LLM for the user proxy
}  

# Function to create and setup all agents
@tracer.chain
def create_agents():
    """Create all the agents needed for the job application autofill system"""
    # Create the agents
    user_proxy = UserProxyAgent(**user_proxy_config)
    orchestrator = AssistantAgent(**orchestrator_config)
    scraper = AssistantAgent(**scraper_config)
    db_agent = AssistantAgent(**db_config)
    autofill_agent = AssistantAgent(**autofill_config)
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
    @tracer.chain
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
        agents=[user_proxy, orchestrator, scraper, db_agent, autofill_agent, field_mapper, instruction_generator],
        messages=[],
        max_round=50
    )
    
    # Create the group chat manager
    manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})
    
    return {
        "user_proxy": user_proxy,
        "orchestrator": orchestrator,
        "scraper": scraper,
        "db_agent": db_agent,
        "autofill_agent": autofill_agent,
        "field_mapper": field_mapper,
        "instruction_generator": instruction_generator,
        "groupchat": groupchat,
        "manager": manager
    }