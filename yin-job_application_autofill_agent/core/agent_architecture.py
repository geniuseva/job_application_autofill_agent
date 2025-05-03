import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import os
from dotenv import load_dotenv
load_dotenv()
# Import agent functions
from agents.scraper_agent import perform_scraping
from agents.mapper_agent import perform_mapping
from agents.db_agent import db_agent_handler
from agents.autofill_agent import perform_autofill

# Retrieve the API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")
# Configuration for the agents
config_list = [
    {
        "model": "gpt-4",
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

mapper_config = {
    "name": "MapperAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1,
        "functions": [
            {
                "name": "map_fields",
                "description": "Map form fields to user data fields",
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
    "system_message": """You analyze form field requirements and map them to user data.
    Your tasks:
    1. Review scraped form field data
    2. Identify required vs optional fields
    3. Map form fields to appropriate user profile data fields
    4. Handle special cases like dropdowns, checkboxes, and radio buttons
    5. Return a mapping object that matches form fields to user data fields
    
    When asked to map fields, use your map_fields function with the scraped data as the parameter.
    Be intelligent about inferring relationships between differently named fields."""
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
    2. Ensure data privacy and security
    3. Format user data for form submission
    4. Handle missing data by prompting the user for additional information
    
    When asked to retrieve user data, use your query_database function with the appropriate action:
    - Use action="get_profile" to get the complete user profile
    - Use action="get_schema" to get the user profile schema
    - Use action="get_fields" with fields=[field1, field2, ...] to get specific fields
    
    Be accurate and protect sensitive information."""
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

1. First, ask the ScrapeAgent to extract form fields from the URL
2. Next, ask the MapperAgent to map the form fields to user data
3. Then, ask the DatabaseAgent to retrieve the necessary user information
4. Finally, ask the AutofillAgent to fill the form
5. Present the results back to the user

IMPORTANT: Each agent has its own function that it can call directly:
- ScrapeAgent can call scrape_url(url)
- MapperAgent can call map_fields(scraped_data)
- DatabaseAgent can call query_database(action, fields)
- AutofillAgent can call fill_form(mapping_data, form_url)

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
    
    # Register functions with their respective agents
    scraper.register_function(
        function_map={
            "scrape_url": perform_scraping
        }
    )
    
    mapper.register_function(
        function_map={
            "map_fields": perform_mapping
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
        agents=[user_proxy, orchestrator, scraper, mapper, db_agent, autofill_agent],
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
        "groupchat": groupchat,
        "manager": manager
    }