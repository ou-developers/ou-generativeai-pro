"""
Module 03: Built-in Web Search Tool
=====================================
Add web search to any Responses API call with just one line!
The model decides when to search and incorporates results automatically.
"""
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

client = OpenAI()

# ──────────────────────────────────────────────
# Basic web search — one line to enable!
# ──────────────────────────────────────────────
print("--- Example 1: Current Events ---")
response = client.responses.create(
    model="gpt-4.1",
    tools=[{"type": "web_search"}],  # <-- That's it! One line.
    input="What are the latest developments in AI this week?",
)
print(response.output_text)
print()

# ──────────────────────────────────────────────
# The model decides WHEN to search
# (it won't search if it can answer from knowledge)
# ──────────────────────────────────────────────
print("--- Example 2: Factual question (might not search) ---")
response2 = client.responses.create(
    model="gpt-4.1",
    tools=[{"type": "web_search"}],
    input="What is the capital of France?",
)
print(response2.output_text)
print()

# ──────────────────────────────────────────────
# Combine web search with instructions
# ──────────────────────────────────────────────
print("--- Example 3: Research assistant ---")
response3 = client.responses.create(
    model="gpt-4.1",
    instructions="You are a research assistant. Provide concise, sourced answers.",
    tools=[{"type": "web_search"}],
    input="What is the current price of Bitcoin?",
)
print(response3.output_text)
print()

print("✅ Web search works! The model automatically decides when to search.")
