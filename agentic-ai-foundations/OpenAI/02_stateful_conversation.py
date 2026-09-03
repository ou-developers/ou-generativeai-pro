"""
Module 03: Stateful Conversations
===================================
The Responses API can remember previous turns automatically.
Just pass previous_response_id and it chains the conversation.

No need to send the full message history yourself!
"""
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

client = OpenAI()

# ──────────────────────────────────────────────
# Turn 1: Introduce yourself
# ──────────────────────────────────────────────
print("--- Turn 1 ---")
resp1 = client.responses.create(
    model="gpt-4.1",
    instructions="You are a friendly assistant with a great memory.",
    input="Hi! My name is Alice. I'm a software engineer who loves hiking.",
)
print(f"Assistant: {resp1.output_text}")
print()

# ──────────────────────────────────────────────
# Turn 2: Ask about what you said (the API remembers!)
# ──────────────────────────────────────────────
print("--- Turn 2 ---")
resp2 = client.responses.create(
    model="gpt-4.1",
    input="What is my name and what do I do for work?",
    previous_response_id=resp1.id,  # <-- This chains the conversation!
)
print(f"Assistant: {resp2.output_text}")
print()

# ──────────────────────────────────────────────
# Turn 3: Continue the conversation
# ──────────────────────────────────────────────
print("--- Turn 3 ---")
resp3 = client.responses.create(
    model="gpt-4.1",
    input="Can you suggest a good hiking trail for someone who also codes?",
    previous_response_id=resp2.id,  # <-- Chain from turn 2
)
print(f"Assistant: {resp3.output_text}")
print()

# ──────────────────────────────────────────────
# Key takeaway:
# You only send the NEW message each turn.
# OpenAI stores the full conversation history server-side.
# This saves tokens and simplifies your code!
# ──────────────────────────────────────────────
print("✅ The API remembered context across all 3 turns!")
print(f"   Response IDs: {resp1.id} → {resp2.id} → {resp3.id}")
