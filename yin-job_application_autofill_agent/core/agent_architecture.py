import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import os

# Configuration for the agents
config_list = [
    {
        "model": "gpt-4",
        "api_key": os.environ.get("OPENAI_API_KEY")
    }
]

# Define agent configurations with specific instructions
scraper_config = {
    "name": "ScrapeAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2
    },
    "system_message": """You are a web scraping specialist. Your task is to:
    1. Navigate to a provided URL
    2. Extract all form fields and their attributes (name, id, type, required status)
    3. Identify any special requirements for each field
    4. Return the structured data in a consistent JSON format
    5. Handle different types of forms including multi-page applications
    Be precise and thorough in your extraction."""
}

mapper_config = {
    "name": "MapperAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1
    },
    "system_message": """You analyze form field requirements and map them to user data.
    Your tasks:
    1. Review scraped form field data
    2. Identify required vs optional fields
    3. Map form fields to appropriate user profile data fields
    4. Handle special cases like dropdowns, checkboxes, and radio buttons
    5. Return a mapping object that matches form fields to user data fields
    Be intelligent about inferring relationships between differently named fields."""
}

db_config = {
    "name": "DatabaseAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.1
    },
    "system_message": """You manage user profile information storage and retrieval.
    Your tasks:
    1. Retrieve relevant user data based on field mapping requirements
    2. Ensure data privacy and security
    3. Format user data for form submission
    4. Handle missing data by prompting the user for additional information
    Be accurate and protect sensitive information."""
}

autofill_config = {
    "name": "AutofillAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2
    },
    "system_message": """You automate the process of filling out forms on websites.
    Your tasks:
    1. Use Playwright to navigate to the form URL
    2. Identify form elements on the page
    3. Fill each field with the correct user data based on the mapping
    4. Handle special form elements like dropdowns, checkboxes, etc.
    5. Navigate through multi-page forms when necessary
    6. Return the URL of the final page for user review
    Be careful to handle errors gracefully."""
}

orchestrator_config = {
    "name": "OrchestratorAgent",
    "llm_config": {
        "config_list": config_list,
        "temperature": 0.2
    },
    "system_message": """You coordinate the entire job application form filling process. Your purpose is to guide the workflow through these steps:

1. First, request the ScrapeAgent to extract form fields by asking it to use the scrape_url function
2. Next, ask the MapperAgent to map the form fields to user data by using the map_fields function
3. Then, ask the DatabaseAgent to retrieve the necessary user information using the query_database function
4. Finally, direct the AutofillAgent to fill the form using the fill_form function
5. Present the results back to the user

IMPORTANT: You don't have direct web access. Instead, you must ask the specialized agents to perform their tasks through function calls. Never ask the user to provide form field information manually.

Always keep track of which step in the process you're on, and explicitly name which agent you're addressing in each message. If any agent encounters an error, help resolve it by suggesting appropriate actions.

Use the following format when addressing agents:
"@ScrapeAgent: Please extract the form fields from [URL] using the scrape_url function."""
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