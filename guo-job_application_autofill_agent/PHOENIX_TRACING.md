# Phoenix Tracing for Job Application Autofill Agent

This document explains how to use Arize Phoenix tracing with the Job Application Autofill Agent.

## Overview

[Arize Phoenix](https://github.com/Arize-ai/phoenix) is an open-source observability tool for ML models and LLM applications. It helps with tracing, evaluating, and monitoring ML systems. We've integrated Phoenix tracing into this project to provide visibility into the agent workflow and help with debugging and performance optimization.

## Setup Instructions

### 1. Install Dependencies

The required dependencies have been added to `requirements.txt`:
- `arize-phoenix>=3.0.0`
- `opentelemetry-sdk>=1.32.1`
- `opentelemetry-exporter-otlp>=1.32.1`

Install them using:

```bash
pip install -r requirements.txt
```

### 2. Run Self-Hosted Phoenix Server

Create a directory for Phoenix data:

```bash
mkdir -p phoenix-data
```

Run the Phoenix server using Docker:

```bash
docker run -p 6006:6006 -v $(pwd)/phoenix-data:/tmp/phoenix arizephoenix/phoenix:latest
```

This will start the Phoenix server on port 6006, and you can access the UI at http://localhost:6006.

### 3. Run the Application

Run the application as usual:

```bash
python guo-job_application_autofill_agent/main.py --url "https://example.com/job-application"
```

The application will now send traces to the Phoenix server.

## What's Being Traced

The following components have been instrumented with Phoenix tracing:

1. **Main Application Flow**
   - Main function execution
   - Phoenix tracing setup

2. **Orchestrator**
   - Workflow orchestration
   - Agent interactions
   - Workflow state tracking

3. **Scraper Agent**
   - Form scraping
   - Field extraction
   - Pagination detection

4. **Mapper Agent**
   - Form field extraction
   - User data mapping
   - Field matching

5. **DB Agent**
   - Profile loading
   - Profile retrieval
   - Field extraction

6. **Instruction Generator**
   - Autofill instruction generation
   - Selector building
   - Fill method determination

7. **Autofill Agent**
   - Browser automation
   - Form filling
   - Pagination handling

## Viewing Traces

1. Open the Phoenix UI at http://localhost:6006
2. Navigate to the "Traces" tab
3. You'll see traces for each run of the application
4. Click on a trace to see the detailed span hierarchy
5. Explore spans to see attributes, events, and metrics

## Analyzing Performance

Phoenix traces can help you identify:

1. **Bottlenecks**: Which parts of the workflow take the most time
2. **Error Patterns**: Where errors occur and their causes
3. **Success Rates**: How often different operations succeed or fail
4. **Field Mapping Accuracy**: How well the system maps user data to form fields
5. **Form Fill Rates**: Percentage of fields successfully filled

## Advanced Usage

### Adding Custom Events

You can add custom events to spans:

```python
from arize.phoenix.trace import current_span

# Add an event to the current span
current_span().add_event("form_submission_started")
```

### Recording Exceptions

Capture exceptions in your traces:

```python
try:
    # Some code that might fail
except Exception as e:
    current_span().record_exception(e)
    raise
```

### Adding Custom Attributes

Add relevant attributes to spans:

```python
current_span().set_attribute("field_count", len(form_fields))
```

## Troubleshooting

If you don't see traces in the Phoenix UI:

1. Ensure the Phoenix server is running
2. Check that the application completed successfully
3. Verify that the OTLP endpoint is correct (default: localhost:4317)
4. Check for any errors in the application logs related to tracing