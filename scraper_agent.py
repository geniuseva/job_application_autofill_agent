import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()
# Retrieve the API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in the .env file")

# Initialize the model client with the API key
model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=api_key)
async def scrap_web_form(message: str) -> str:
    """
    This function extracts and scrapes web forms from a given URL.
    """
    # Extract the URL from the message
    url = message.split(" ")[-1]

    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all form elements on the page
        forms = soup.find_all('form')

        if not forms:
            return f"No forms found on the page at {url}"

        # Iterate through all forms and collect their prettified HTML
        form_details = []
        for i, form in enumerate(forms, start=1):
            form_details.append(f"Form {i}:\n{form.prettify()}\n")

        # Combine all form details into a single string
        return scraped_form + "\n".join(form_details)

    except requests.exceptions.RequestException as e:
        return f"An error occurred while trying to scrape the URL {url}: {e}"

scraper_agent = AssistantAgent(
    name="scraper_agent",
    model_client=model_client,
    tools=[scrap_web_form],
    system_message=(
        "You are a web form scraper assistant. Your task is to help users extract web forms accurately and efficiently. "
    ),
    reflect_on_tool_use=True,
    model_client_stream=True,  # Enable streaming tokens from the model client.
)

async def main() -> None:

    await Console(
        scraper_agent.run_stream(task="scraped the form from the website https://jobs.lever.co/snaplogic/16e205f1-0f6e-46eb-9ff1-beafb2a87fb2/apply")
    )
    # Close the connection to the model client.
    await model_client.close()

asyncio.run(main())