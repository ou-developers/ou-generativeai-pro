# OpenAI Agents Course — Companion Code

## Setup

### 1. Install Python 3.10+
Make sure you have Python 3.10 or newer installed.

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install openai openai-agents pydantic
```

### 4. Set your API key
Get an API key from https://platform.openai.com/api-keys
```bash
export OPENAI_API_KEY="sk-..."   # Mac/Linux
# set OPENAI_API_KEY=sk-...      # Windows
```

## Code Files (Run in Order)

| File | Lesson | What You'll Learn |
|------|--------|-------------------|
| `01_hello_responses.py` | 01 | Your first Responses API call |
| `02_stateful_conversation.py` | 02 | Chaining conversations with state |
| `03_web_search.py` | 03 | Using built-in web search tool |
| `04_first_agent.py` | 04 | Your first agent with the Agents SDK |
| `05_function_tools.py` | 05 | Creating custom function tools |
| `06_multi_agent_handoffs.py` | 06 | Multi-agent system with handoffs |
| `07_guardrails.py` | 07 | Input guardrails for safety |
| `08_customer_support.py` | 08 | Complete project: customer support system |

## Running the Code
```bash
python 01_hello_responses.py
python 02_stateful_conversation.py
# ... and so on
```

## Notes
- Each file is self-contained — you can run them independently.
- Files build on each other conceptually, so run them in order for best learning.
- Modify the code! Change instructions, add tools, experiment.
- Check your traces at: https://platform.openai.com → Dashboard → Traces
