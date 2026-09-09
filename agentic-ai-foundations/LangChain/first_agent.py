"""
==========================================================
LangChain for AI Agents — Companion Code
==========================================================

This program demonstrates:
- How an AI Agent uses the ReAct pattern (Reason → Act → Observe)
- How to build an agent using LangChain's create_agent()

Prerequisites:
  pip install langchain langchain-openai langgraph python-dotenv

Setup:
  Create a .env file with:
  OPENAI_API_KEY=sk-your-key-here
==========================================================
"""

# -------------------------------------------------------
# STEP 0: Load environment variables
# -------------------------------------------------------
# We store sensitive information like API keys in a .env file.
# This keeps secrets out of the code (best practice).

import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables like OPENAI_API_KEY into environment


# -------------------------------------------------------
# STEP 1: Initialize the Model (the "brain")
# -------------------------------------------------------
# This is the LLM that will:
# - Understand the question
# - Decide which tool to use
# - Generate the final answer

from langchain.chat_models import init_chat_model

# "gpt-5.5" is the latest model
model = init_chat_model("openai:gpt-5.5")


# -------------------------------------------------------
# STEP 2: Define Your Tools (the "hands")
# -------------------------------------------------------
# Tools allow the agent to DO things instead of just responding.
# Each tool must have:
#   1. A clear name
#   2. A descriptive docstring (VERY important!)
#   3. Type hints (so the LLM knows expected inputs)

from langchain_core.tools import tool
import math

@tool
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    The agent will use this when it detects an addition problem.
    """
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers together.
    Used for multiplication tasks.
    """
    return a * b


@tool
def divide(a: float, b: float) -> str:
    """
    Divide the first number by the second.
    Includes error handling for division by zero.
    """
    if b == 0:
        return "Error: Cannot divide by zero"
    return str(a / b)


@tool
def square_root(number: float) -> str:
    """
    Calculate the square root of a number.
    Includes error handling for negative inputs.
    """
    if number < 0:
        return "Error: Cannot take square root of a negative number"
    return str(math.sqrt(number))


# Combine all tools into a list
tools = [add, multiply, divide, square_root]


# Print available tools (helps learners see what the agent has access to)
print("=== Available Tools ===")
for t in tools:
    print(f"  • {t.name}: {t.description}")
print()


# -------------------------------------------------------
# STEP 3: Create the Agent (the "loop")
# -------------------------------------------------------
# create_agent automatically builds the ReAct loop:
#
#   1. Reason → LLM decides what to do
#   2. Act → calls a tool (if needed)
#   3. Observe → gets the result
#   4. Repeat until done
#
# You don't have to manually write the loop — the framework does it.

from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=tools,
)


# -------------------------------------------------------
# STEP 4: Run the Agent
# -------------------------------------------------------
# This function sends a question to the agent and prints:
# - The final answer
# - (Optional) the internal execution trace

def run_agent(question: str):
    """Run the agent and print a clean, beginner-friendly execution trace."""

    print(f"\n🧑 User: {question}")
    print("-" * 60)

    result = agent.invoke({
        "messages": [("user", question)]
    })

    print("🔎 Clean Agent Execution Trace")
    print("-" * 60)

    step = 1

    for msg in result["messages"]:

        # 1. Human message = original user question
        if msg.type == "human":
            print(f"{step}. User asked:")
            print(f"   {msg.content}")
            step += 1

        # 2. AI message with tool_calls = agent decided to use a tool
        elif msg.type == "ai" and getattr(msg, "tool_calls", None):
            for tool_call in msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                print(f"{step}. Agent decision:")
                print(f"   I need to use the tool: {tool_name}")
                print(f"   Tool input: {tool_args}")
                step += 1

        # 3. Tool message = result returned by the tool
        elif msg.type == "tool":
            print(f"{step}. Tool observation:")
            print(f"   Tool returned: {msg.content}")
            step += 1

        # 4. Final AI message = final response to user
        elif msg.type == "ai" and msg.content:
            print(f"{step}. Final answer:")
            print(f"   {msg.content}")
            step += 1

    print("=" * 60)

# -------------------------------------------------------
# TEST CASES — Watch the agent in action!
# -------------------------------------------------------

# 1. Simple case → single tool call
# Agent should directly use "add"
run_agent("What is 42 + 58?")


# 2. Medium complexity → multiple steps
# Agent must:
#   multiply → then divide
run_agent("What is 15 multiplied by 8, then divided by 3?")


# 3. Complex reasoning → planning required
# Agent must:
#   step 1: calculate area
#   step 2: calculate square root
run_agent(
    "I have a rectangle with width 12 and height 7. "
    "What is its area, and what is the square root of that area?"
)


# 4. Edge case → error handling
# Agent should handle divide-by-zero gracefully
run_agent("What is 100 divided by 0?")


# Final message
print("✅ Agent demo complete! Next: try 03_search_agent.py")
