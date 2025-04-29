## 🧠 Job Application Autofill Agent – Implementation Plan  
**Team:** CodeRAGers  
**Members:** Yin Hu, Guo Fan  
**Framework:** Python + [AutoGen](https://github.com/microsoft/autogen)  
**Optional Evaluation** [Arize Phoenix](https://github.com/Arize-ai/phoenix)

---

## 📁 Recommended Repository Structure

```
job-autofill-agent/
├── agents/
│   ├── __init__.py
│   ├── scraper_agent.py         # Extract form fields from job URLs
│   ├── mapping_agent.py         # Map scraped fields to user data
│   ├── db_agent.py              # Interface for user data storage
│   ├── autofill_agent.py        # Automate form filling via Playwright
│   └── orchestrator.py          # (Optional) Handles workflows
│   └── user_proxy_agent.py      # Handles user feedback injection
│
├── workflows/
│   ├── orchestrator_worker.py   # Multi-agent orchestrator architecture
│   ├── prompt_chaining.py       # Prompt chaining-based architecture
│   ├── groupchat_hitl.py        # Orchestrator with user agent 
│
├── data/
│   ├── users.json               # Mock user database
│   └── ground_truths.json       # Manual labels for accuracy eval
│
├── evaluation/
│   ├── evaluator.py             # Evaluate time, token, accuracy
│   └── metrics_logger.py        # For structured results logging
│
├── utils/
│   ├── form_utils.py            # HTML parsing, field ID extraction
│   ├── logger.py                # Unified logging
│   └── config.py                # Configuration (token limits, retries)
│
├── tests/
│   ├── test_scraper_agent.py
│   ├── test_mapping_agent.py
│   └── test_autofill_agent.py
│
├── notebooks/                   # Exploratory or debugging notebooks
│   └── form_scraping_demo.ipynb
│
├── .env                         # API keys, secrets
├── README.md
├── requirements.txt
└── main.py                      # Entry point for the orchestrator
```

---

## 🚀 Incremental Development Plan

### ✅ **Phase 1: Setup & Baseline Agents**
- [ ] Create repo structure with placeholders and stubs
- [ ] Implement ScraperAgent using Playwright
- [ ] Mock basic form page to test extraction
- [ ] Implement MappingAgent with simple field matching logic
- [ ] Mock user database (JSON-based)
- [ ] Implement DBAgent with CRUD and query support

### ✅ **Phase 2: End-to-End Autofill Pipeline**
- [ ] Develop FormAutofillAgent with Playwright actions (click, input, submit)
- [ ] Integrate all agents with basic sequential flow
- [ ] Create orchestration layer via `AutoGen` (GroupChat / GroupChatManager)
- [ ] Add CLI or minimal UI to input job URL and return filled review URL
- [ ] Insert hook for potential user feedback after MappingAgent(Optional)

### ✅ **Phase 3: Evaluation Module**
- [ ] Build `evaluator.py` to track:
  - Accuracy (using `ground_truths.json`)
  - Token count (via OpenAI usage API or `AutoGen` logging)
  - Time per agent (timestamp logs)
- [ ] Save evaluation results in a structured CSV/JSON for analysis

### 🔁 **Phase 4: User Feedback Integration(Optional) **

#### 4.1 Introduce `UserProxyAgent`
- [ ] Create a `UserProxyAgent` that simulates user prompts and responses
- [ ] Customize behavior (auto-respond in dev mode or allow real-time input)
- [ ] Trigger only when:
  - Mapping is incomplete (e.g., missing phone number, resume)
  - Confidence is low (can use basic heuristic or flag)

#### 4.2 Add GroupChatManager for Workflow Coordination
- [ ] Wrap all agents (Scraper, Mapping, DB, Autofill, UserProxy) into a `GroupChatManager`
- [ ] Define rules:
   - If MappingAgent identifies a missing field → ask `UserProxyAgent`
   - If all fields filled → proceed to AutofillAgent

#### 4.3 Mock Inputs for Testing
- [ ] Provide CLI/JSON mock interactions from users (simulate user saying “My phone number is...”)
- [ ] Log all user-agent conversations for later review

### 🔁 **Phase 5 (Optional): Integration with Arize Phoenix**
- [ ] Integrate `phoenix.trace()` to track LLM performance
- [ ] Visualize token cost, success rate, time, anomalies
- [ ] Compare versions (with/without optimization)
- [ ] Add **HITL-enabled vs. fully automated workflows** to benchmark:

| Setup                  | Accuracy ↑ | Token Cost ↑ | Time ↑ |
|------------------------|------------|---------------|--------|
| Fully Automated        | Medium     | Low           | Fast   |
| HITL via UserProxyAgent| High       | Medium        | Medium |

## 📊 Evaluation Matrix

| Metric          | Tools Used                    | Goal                             |
|----------------|-------------------------------|----------------------------------|
| Accuracy        | Manual labels, `difflib`      | Match filled vs ground truth     |
| Token Usage     | `AutoGen` logs, OpenAI API    | Optimize by caching, prompt ref. |
| Time Taken      | `time.perf_counter()` logs    | Lower with workflow optimizations|

---

