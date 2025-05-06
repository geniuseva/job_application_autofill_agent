# Job Application Autofill Agent

An AI-powered system that automates the job application process by intelligently filling out online application forms.

## Project Overview

The Job Application Autofill Agent is designed to streamline the job application process by automatically filling out online application forms. It leverages a multi-agent AI architecture to extract form fields, map user data to appropriate fields, and complete applications with high accuracy. This significantly reduces the time and effort required by job seekers when applying to multiple positions.

## Features

- **Automated Form Scraping**: Extracts form fields and their attributes from job application websites
- **Intelligent Field Mapping**: Maps user profile data to form fields using semantic matching
- **Automated Form Filling**: Uses browser automation to fill out forms with mapped data
- **Multi-page Form Support**: Handles pagination in complex application forms
- **Evaluation Framework**: Tracks performance metrics like fill rate and completion time
- **Human-in-the-Loop Option**: Enhanced implementation that incorporates human feedback for missing fields

## Architecture

The system is built on a multi-agent architecture using the [AutoGen](https://github.com/microsoft/autogen) framework, where each agent specializes in a specific aspect of the form-filling process:

### Key Components

- **ScraperAgent**: Extracts form fields and attributes from web pages
- **DBAgent**: Manages user profile data storage and retrieval
- **FieldMapperAgent**: Maps user data to form fields using semantic matching
- **InstructionGeneratorAgent**: Generates detailed autofill instructions
- **AutofillAgent**: Executes form filling using browser automation
- **OrchestratorAgent**: Coordinates the overall workflow

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/job_application_autofill_agent.git
   cd job_application_autofill_agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file to add your OpenAI API key
   ```

## Usage

### Basic Usage

Run the autofill agent with a specific job application URL:

```bash
python -m guo-job_application_autofill_agent.main --url "https://example.com/job-application"
```


### Human-in-the-Loop Version

For the enhanced version with human feedback:

```bash
python -m human_in_the_loop.main --url "https://example.com/job-application"
```

## Requirements

- Python 3.8+
- OpenAI API key
- Playwright for browser automation
- AutoGen framework for multi-agent orchestration
- Additional dependencies listed in requirements.txt

## Development

### Project Structure

```
job_application_autofill_agent/
├── guo-job_application_autofill_agent/  # Core implementation
│   ├── main.py                         # Entry point
│   ├── agents/                         # Agent implementations
│   ├── core/                           # Core architecture
│   ├── data/                           # Data files
│   └── utils/                          # Helper utilities
├── human_in_the_loop/                  # Human feedback implementation
└── yin-job_application_autofill_agent/ # Alternative implementation
```