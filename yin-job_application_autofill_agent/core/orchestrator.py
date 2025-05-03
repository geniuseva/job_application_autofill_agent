import autogen
import json
import time
import os
import re
import logging

# Import agent configurations and agent implementations
from core.agent_architecture import create_agents, config_list
from agents.scraper_agent import perform_scraping
from agents.mapper_agent import perform_mapping
from agents.db_agent import db_agent_handler
from agents.autofill_agent import perform_autofill

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def orchestrator_workflow(url=None):
    """Main function to orchestrate the job application autofill workflow"""
    
    # Create agents
    agents = create_agents()
    
    # Extract individual agents
    user_proxy = agents["user_proxy"]
    manager = agents["manager"]
    
    # Initialize metrics collection
    token_logs = []
    time_logs = []

    # Configuration for the agents
    config_list = [
        {
            "model": "gpt-4",
            "api_key": os.environ.get("OPENAI_API_KEY")
        }
    ]
    
    # Start the conversation with the initial message
    initial_message = (
        f"I need to fill out a job application form. "
        f"Here's the URL: {url or 'https://example.com/job-application'}. "
        f"Can you help me automatically fill it out with my profile information?"
    )
    
    # Measure total time
    total_start_time = time.time()

    # Start the conversation
    user_proxy.initiate_chat(
        manager,
        message=initial_message
    )

    # Calculate total time
    total_end_time = time.time()
    
    # Log total time
    time_logs.append({
        "agent": "OrchestratorAgent",
        "operation": "complete_workflow",
        "duration": total_end_time - total_start_time
    })

    # Extract results
    chat_history = user_proxy.chat_history[list(user_proxy.chat_history.keys())[0]]
    
    # Find the autofill result in the chat history
    autofill_result = None
    for message in reversed(chat_history):
        if message["role"] == "user" and "fill_form" in message.get("content", ""):
            if message.get("function_call") and message.get("function_call").get("name") == "fill_form":
                if message.get("function_call").get("output"):
                    try:
                        autofill_result = json.loads(message["function_call"]["output"])
                        break
                    except:
                        pass
    
    return autofill_result, token_logs, time_logs

# Helper functions
def extract_url_from_message(message):
    """Extract a URL from a message"""
    if not message or not isinstance(message, str):
        return None
        
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!.~\'*,;:=+$/?:@&=#]*)*', message)
    return urls[0] if urls else None

def extract_json_from_message(message, key=None):
    """Extract JSON data from a message"""
    if not message or not isinstance(message, str):
        return None
    
    # Try to find JSON data in the message
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
    json_matches = re.findall(json_pattern, message)
    
    if not json_matches:
        return None
    
    # Try to parse each match as JSON
    for match in json_matches:
        try:
            data = json.loads(match)
            
            # If a specific key is requested, check for it
            if key and key in data:
                return data[key]
            
            return data
        except json.JSONDecodeError:
            continue
    
    return None

def extract_fields_from_message(message):
    """Extract field names from a message"""
    if not message or not isinstance(message, str):
        return []
    
    # Look for field names in quotes or brackets
    field_pattern = r'["\']([\w\._]+)["\']|\[([\w\._]+)\]'
    matches = re.findall(field_pattern, message)
    
    # Flatten the matches and remove empty strings
    fields = [match[0] or match[1] for match in matches]
    
    return fields if fields else []

def flatten_user_data(user_data):
    """Flatten nested user data for easier mapping"""
    flat_data = {}
    
    def flatten_dict(d, prefix=""):
        for key, value in d.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flatten_dict(value, f"{new_key}.")
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # For the first item in a list of dicts, flatten it with indexed keys
                    flatten_dict(value[0], f"{new_key}.")
                else:
                    # For list of simple values, just use the key
                    flat_data[new_key] = value
            else:
                flat_data[new_key] = value
    
    flatten_dict(user_data)
    return flat_data

# Main execution function
def run_orchestrator(url=None):
    """Run the orchestrator workflow with a provided URL"""
    result, token_logs, time_logs = orchestrator_workflow(url)
    
    # Print results and metrics
    logger.info("Job Application Autofill completed!")
    
    if result:
        logger.info(f"Form filling success: {result.get('success', False)}")
        logger.info(f"Filled fields: {len(result.get('filled_fields', []))}")
        logger.info(f"Not filled fields: {len(result.get('not_filled_fields', []))}")
        
        if result.get('metrics'):
            logger.info(f"Fill rate: {result['metrics'].get('fill_rate', 0):.2f}%")
    
    # Log time metrics
    total_time = sum(log["duration"] for log in time_logs)
    logger.info(f"Total execution time: {total_time:.2f} seconds")
    
    # Breakdown by agent
    agent_times = {}
    for log in time_logs:
        agent = log["agent"]
        if agent not in agent_times:
            agent_times[agent] = 0
        agent_times[agent] += log["duration"]
    
    for agent, duration in agent_times.items():
        logger.info(f"{agent} execution time: {duration:.2f} seconds ({(duration/total_time)*100:.2f}%)")
    
    return result

if __name__ == "__main__":
    # If this script is run directly, execute the orchestrator with a test URL
    test_url = "https://example.com/job-application"
    run_orchestrator(test_url)