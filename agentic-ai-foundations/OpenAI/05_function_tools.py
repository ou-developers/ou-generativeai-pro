"""
==========================================================
OpenAI Agents SDK — Companion Code
==========================================================
Module 05: Function Tools — Give Your Agent Superpowers
  - The Agent Loop in action (similar to ReAct)
  - @function_tool turns any Python function into a tool

Prerequisites:
  pip install openai-agents python-dotenv

Setup:
  Create a .env file with: OPENAI_API_KEY=sk-your-key-here
==========================================================
"""
import os
import math
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# STEP 1: Import the SDK
# ─────────────────────────────────────────────

from agents import Agent, Runner, function_tool

# ─────────────────────────────────────────────
# STEP 2: Define Your Tools
# ─────────────────────────────────────────────
# Each tool needs: the @function_tool decorator, type hints,
# and a clear docstring. The LLM reads these to decide
# WHEN and HOW to use each tool.

@function_tool
def add(a: float, b: float) -> float:
    """Add two numbers together. Use for addition operations."""
    return a + b

@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together. Use for multiplication operations."""
    return a * b

@function_tool
def divide(a: float, b: float) -> str:
    """Divide the first number by the second. Returns error if dividing by zero."""
    if b == 0:
        return "Error: Cannot divide by zero"
    return str(a / b)

@function_tool
def square_root(number: float) -> str:
    """Calculate the square root of a number."""
    if number < 0:
        return "Error: Cannot take square root of a negative number"
    return str(math.sqrt(number))

tools = [add, multiply, divide, square_root]

print("=== Available Tools ===")
for t in tools:
    print(f"  • {t.name}: {t.description}")
print()

# ─────────────────────────────────────────────
# STEP 3: Create the Agent
# ─────────────────────────────────────────────
# The Agent combines a model + instructions + tools.
# The SDK's Runner handles the agent loop automatically:
#   Think → Act (call tool) → Observe → Repeat

agent = Agent(
    name="Math Assistant",
    instructions="""You are a helpful math assistant.
    Use the provided tools to perform calculations.
    Show your work step by step so the user can follow along.""",
    tools=tools,
)

# ─────────────────────────────────────────────
# STEP 4: Run the Agent!
# ─────────────────────────────────────────────

def run_agent(question: str):
    """Run the agent and print the result."""
    print(f"🧑 User: {question}")
    print("-" * 50)

    result = Runner.run_sync(agent, question)

    print(f"🤖 Agent answer: {result.final_output}")
    print(f"   (answered by: {result.last_agent.name})")
    print("=" * 50)
    print()

# ─────────────────────────────────────────────
# TEST CASES — Watch the agent loop in action!
# ─────────────────────────────────────────────

# Simple: single tool call
run_agent("What is 42 + 58?")

# Medium: multiple tool calls in sequence
run_agent("What is 15 multiplied by 8, then divided by 3?")

# Complex: the agent must plan a multi-step approach
run_agent(
    "I have a rectangle with width 12 and height 7. "
    "What is its area, and what is the square root of that area?"
)

# Edge case: the agent handles errors
run_agent("What is 100 divided by 0?")

print("✅ Agent demo complete!")
print("   View your traces at: https://platform.openai.com → Dashboard → Traces")
