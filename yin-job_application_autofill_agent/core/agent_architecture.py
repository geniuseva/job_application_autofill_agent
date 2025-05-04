import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import os
from dotenv import load_dotenv
load_dotenv()
# Import agent functions
from agents.scraper_agent import perform_scraping
from agents.mapper_agent import extract_form_fields, generate_autofill_instructions, perform_mapping
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
    
    Be precise and thorough in your analysis."""
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
    "system_message": """You are a field mapping specialist. Your task is to:
    1. Match form fields to user data
    2. Handle different field types appropriately
    3. Select the best options for dropdowns and checkboxes
    4. Return detailed mapping instructions in JSON format
    
    For each form field:
    - Find the most appropriate user data value
    - For text fields, provide the exact value
    - For select/dropdown fields, choose the best matching option
    - For checkbox fields, determine if they should be checked
    - For radio buttons, select the appropriate option
    
    Your mapping instructions should be clear and precise, ready for the autofill agent to use.
    
    Be intelligent about inferring relationships between differently named fields."""
}

# Mapper agent configuration (simplified coordinator role)
mapper_config = {
    "name": "MapperAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1,
        "functions": [
            {
                "name": "extract_key_information",
                "description": "Extract key information from scraped form fields for DB queries",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scraped_data": {
                            "type": "object",
                            "description": "The scraped form field data"
                        }
                    },
                    "required": ["scraped_data"]
                }
            },
            {
                "name": "generate_fill_instructions",
                "description": "Generate fill instructions for the autofill agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scraped_data": {
                            "type": "object",
                            "description": "The scraped form field data"
                        },
                        "user_data": {
                            "type": "object",
                            "description": "User data from the database"
                        }
                    },
                    "required": ["scraped_data", "user_data"]
                }
            },
            {
                "name": "map_fields",
                "description": "Legacy function to map form fields to user data fields",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scraped_data": {
                            "type": "object",
                            "description": "The scraped form field data"
                        }
                    },
                    "required": ["scraped_data"]
                }
            }
        ]
    },
    "system_message": """You are a coordinator for form field mapping. Your role is to:
    
    1. Coordinate with other specialized agents:
       - FormAnalyzerAgent: Analyzes form structure and field types
       - QueryGeneratorAgent: Creates database queries based on form analysis
       - FieldMapperAgent: Maps form fields to user data
    
    2. Provide interfaces for the orchestrator:
       - extract_key_information: Prepares data for database queries
       - generate_fill_instructions: Prepares instructions for form filling
    
    You don't need to perform the actual analysis or mapping yourself - that's handled by the specialized agents.
    Your job is to coordinate the process and ensure the right information flows between agents."""
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
                "description": "Fill out a form with user data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mapping_data": {
                            "type": "object",
                            "description": "The mapping between form fields and user data"
                        },
                        "form_url": {
                            "type": "string",
                            "description": "The URL of the form to fill"
                        }
                    },
                    "required": ["mapping_data", "form_url"]
                }
            }
        ]
    },
    "system_message": """You automate the process of filling out forms on websites.
    Your tasks:
    1. Use Playwright to navigate to the form URL
    2. Identify form elements on the page
    3. Fill each field with the correct user data based on the mapping
    4. Handle special form elements like dropdowns, checkboxes, etc.
    5. Navigate through multi-page forms when necessary
    6. Return the URL of the final page for user review
    
    When asked to fill a form, use your fill_form function with the mapping data and form URL as parameters.
    Be careful to handle errors gracefully."""
}

orchestrator_config = {
    "name": "OrchestratorAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2
    },
    "system_message": """You coordinate the entire job application form filling process. Your purpose is to guide the workflow through these steps:

1. First, ask the ScrapeAgent to scrape form fields from the URL
2. Then, in parallel:
   a. Ask the FormAnalyzerAgent to analyze the form structure and field types
   b. Ask the DatabaseAgent to get the database schema using query_database(action="get_schema")
3. After both steps 2a and 2b are complete, ask the QueryGeneratorAgent to create a database query based on the form analysis AND the database schema
4. Then, ask the DatabaseAgent to retrieve the necessary user information using the query
5. Next, ask the FieldMapperAgent to map the form fields to the user data
6. Finally, ask the AutofillAgent to fill the form using the mapping
7. Present the results back to the user

Each agent has specific expertise:
- ScrapeAgent: Extracts form fields from websites
- FormAnalyzerAgent: Analyzes form structure and identifies field purposes
- DatabaseAgent: Retrieves user profile data and schema information
- QueryGeneratorAgent: Creates efficient database queries based on form analysis and database schema
- FieldMapperAgent: Maps form fields to user data
- AutofillAgent: Fills forms with the mapped data
- MapperAgent: Coordinates between specialized agents

IMPORTANT: The QueryGeneratorAgent MUST have both the form analysis from FormAnalyzerAgent AND the database schema from DatabaseAgent before it can generate an accurate query.

The MapperAgent serves as a coordinator between these specialized agents and provides interfaces for you to use:
- extract_key_information(scraped_data): Prepares data for database queries
- generate_fill_instructions(scraped_data, user_data): Prepares instructions for form filling

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

# Create the agents
user_proxy = autogen.UserProxyAgent(**user_proxy_config)
orchestrator = autogen.AssistantAgent(**orchestrator_config)
scraper = autogen.AssistantAgent(**scraper_config)
mapper = autogen.AssistantAgent(**mapper_config)
db_agent = autogen.AssistantAgent(**db_config)
autofill_agent = autogen.AssistantAgent(**autofill_config)
form_analyzer = autogen.AssistantAgent(**form_analyzer_config)
query_generator = autogen.AssistantAgent(**query_generator_config)
field_mapper = autogen.AssistantAgent(**field_mapper_config)

# Function to create and setup all agents
def create_agents():
    """Create all the agents needed for the job application autofill system"""
    # Create the agents
    user_proxy = UserProxyAgent(**user_proxy_config)
    orchestrator = AssistantAgent(**orchestrator_config)
    scraper = AssistantAgent(**scraper_config)
    mapper = AssistantAgent(**mapper_config)
    db_agent = AssistantAgent(**db_config)
    autofill_agent = AssistantAgent(**autofill_config)
    form_analyzer = AssistantAgent(**form_analyzer_config)
    query_generator = AssistantAgent(**query_generator_config)
    field_mapper = AssistantAgent(**field_mapper_config)
    
    # Register functions with their respective agents
    scraper.register_function(
        function_map={
            "scrape_url": perform_scraping
        }
    )
    
    mapper.register_function(
        function_map={
            "extract_key_information": extract_form_fields,
            "generate_fill_instructions": generate_autofill_instructions,
            "map_fields": perform_mapping  # Legacy function for backward compatibility
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
        agents=[user_proxy, orchestrator, scraper, mapper, db_agent, autofill_agent,
                form_analyzer, query_generator, field_mapper],
        messages=[],
        max_round=50
    )
    
    # Create the group chat manager
    manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})
    
    return {
        "user_proxy": user_proxy,
        "orchestrator": orchestrator,
        "scraper": scraper,
        "mapper": mapper,
        "db_agent": db_agent,
        "autofill_agent": autofill_agent,
        "form_analyzer": form_analyzer,
        "query_generator": query_generator,
        "field_mapper": field_mapper,
        "groupchat": groupchat,
        "manager": manager
    }