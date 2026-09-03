"""
=============================================================================
OCI Enterprise AI Agents — Agents SDK Version
=============================================================================
Companion code for the "OCI Enterprise AI Agents — Beginner Course"

This is the SAME math agent as oci_first_agent.py, but using the
OpenAI Agents SDK instead of a manual loop. The SDK handles the
entire ReAct loop for you — no while True, no previous_response_id.

Three ways to build the same agent:
  1. oci_first_agent.py         → Manual loop (OCI Responses API)
  2. oci_first_agent_sdk.py     → OpenAI Agents SDK (THIS FILE)
  3. 02_first_agent.py          → LangChain (create_agent)

Prerequisites:
  pip install openai-agents

Authentication:
  1. Create an API Key in OCI Console → Generative AI → API Keys
  2. Add IAM policy:
     allow any-user to use generative-ai-family in compartment <n>
       where ALL { request.principal.type='generativeaiapikey' }
  3. Set environment variable:
     Windows (cmd):   set OCI_GENAI_API_KEY=your-key-here
     Windows (PS):    $env:OCI_GENAI_API_KEY='your-key-here'
     macOS / Linux:   export OCI_GENAI_API_KEY='your-key-here'
  4. Set OCI_REGION and OCI_PROJECT_ID below

Reference:
  https://docs.oracle.com/en-us/iaas/Content/generative-ai/agents.htm
  https://openai.github.io/openai-agents-python/
=============================================================================
"""

import asyncio
import math
import os

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunConfig,
    ModelProvider,
    OpenAIChatCompletionsModel,
    function_tool,
    set_tracing_disabled,
)

# ─── Configuration ──────────────────────────────────────────────────────────
# IMPORTANT: Change these to match YOUR OCI tenancy.

OCI_REGION = "us-chicago-1"   # <-- CHANGE THIS to your region

OCI_BASE_URL = (
    f"https://inference.generativeai.{OCI_REGION}"
    f".oci.oraclecloud.com/openai/v1"
)

MODEL = "openai.gpt-oss-120b"

# OCI Project ID (REQUIRED)
# OCI Console → Generative AI → Projects → your project → OCID
OCI_PROJECT_ID = ""


# ─── OCI Model Provider ────────────────────────────────────────────────────
# The Agents SDK needs a ModelProvider to know how to reach the LLM.
# This is the ONLY OCI-specific setup — everything else is standard SDK code.

def _create_oci_client():
    """Create an async OpenAI client pointing to OCI."""
    api_key = os.getenv("OCI_GENAI_API_KEY")
    if not api_key:
        print("ERROR: Set the OCI_GENAI_API_KEY environment variable.")
        print()
        print("  Windows (cmd):    set OCI_GENAI_API_KEY=your-key-here")
        print("  Windows (PS):     $env:OCI_GENAI_API_KEY='your-key-here'")
        print("  macOS / Linux:    export OCI_GENAI_API_KEY='your-key-here'")
        exit(1)

    if not OCI_PROJECT_ID or OCI_PROJECT_ID.startswith("<"):
        print("ERROR: Set OCI_PROJECT_ID in the script.")
        print("       OCI Console → Generative AI → Projects → Copy OCID")
        exit(1)

    return AsyncOpenAI(
        api_key=api_key,
        base_url=OCI_BASE_URL,
        default_headers={
            "OpenAI-Project": OCI_PROJECT_ID,
        },
    )


# Create the client and disable tracing (OCI doesn't host OpenAI's trace backend)
oci_client = _create_oci_client()
set_tracing_disabled(True)


class OciModelProvider(ModelProvider):
    """
    Routes the Agents SDK to OCI instead of OpenAI.
    This is the equivalent of changing base_url in the OpenAI SDK.
    """
    def get_model(self, model_name: str | None = None):
        return OpenAIChatCompletionsModel(
            model=model_name or MODEL,
            openai_client=oci_client,
        )


OCI_PROVIDER = OciModelProvider()


# =============================================================================
# STEP 1: Define the Math Tools
# =============================================================================
# The @function_tool decorator works almost identically to LangChain's @tool.
# The SDK reads the function name, docstring, and type hints to auto-generate
# the JSON Schema — you don't write it by hand.
#
# Compare all three approaches:
#   LangChain          →  @tool
#   Agents SDK         →  @function_tool     (this file)
#   Manual Responses   →  JSON dict          (oci_first_agent.py)

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


# =============================================================================
# STEP 2: Create the Agent
# =============================================================================
# In LangChain:   agent = create_agent(model=model, tools=tools)
# In Agents SDK:  agent = Agent(name=..., instructions=..., tools=tools)
#
# The Agent object defines WHAT the agent can do.
# The Runner handles HOW it runs (the loop).

agent = Agent(
    name="MathAgent",
    instructions=(
        "You are a helpful math assistant. Use the provided tools to "
        "perform calculations. Always use tools — do not calculate in your head."
    ),
    tools=tools,
    model=MODEL,
)


# =============================================================================
# STEP 3: Run the Agent
# =============================================================================
# In LangChain:   result = agent.invoke({"messages": [("user", question)]})
# In Agents SDK:  result = await Runner.run(agent, question, run_config=...)
#
# Runner.run() handles the ENTIRE agentic loop:
#   Send question → Model calls tool → Execute tool → Feed back → Repeat → Done
# No while True. No previous_response_id. No manual dispatch.

async def run_agent(question: str):
    """Run the agent on a question and print the result."""
    print(f"🧑 User: {question}")
    print("-" * 50)

    result = await Runner.run(
        agent,
        question,
        run_config=RunConfig(model_provider=OCI_PROVIDER),
    )

    # Print the execution trace (tool calls made by the agent)
    for item in result.raw_responses:
        for output in item.output:
            if output.type == "function_call":
                print(f"  🔧 Tool call: {output.name}({output.arguments})")

    print(f"🤖 Agent: {result.final_output}")
    print("=" * 50)
    print()


# =============================================================================
# EXAMPLE 1: Simple Chat (no tools)
# =============================================================================
async def simple_chat_example():
    """Simple chat — no tools, just a text response."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Chat (no tools)")
    print("=" * 60)

    # For a simple chat, create a tool-less agent
    chat_agent = Agent(
        name="ChatAgent",
        instructions="You are a helpful assistant.",
        model=MODEL,
    )

    result = await Runner.run(
        chat_agent,
        "Explain what an AI agent is in 3 sentences, "
        "using a real-world analogy.",
        run_config=RunConfig(model_provider=OCI_PROVIDER),
    )

    print(f"\n🤖 {result.final_output}\n")


# =============================================================================
# EXAMPLE 2: Math Agent — Same test cases as 02_first_agent.py
# =============================================================================
async def math_agent_example():
    """Same test cases from LangChain 02_first_agent.py."""
    print("=" * 60)
    print("EXAMPLE 2: Math Agent (4 tools — add, multiply, divide, sqrt)")
    print("=" * 60)
    print()

    # Print available tools
    print("=== Available Tools ===")
    for t in tools:
        print(f"  • {t.name}: {t.description}")
    print()

    # ── Test Case 1: Simple — single tool call ──
    await run_agent("What is 42 + 58?")

    # ── Test Case 2: Medium — multiple tool calls in sequence ──
    await run_agent("What is 15 multiplied by 8, then divided by 3?")

    # ── Test Case 3: Complex — multi-step planning ──
    await run_agent(
        "I have a rectangle with width 12 and height 7. "
        "What is its area, and what is the square root of that area?"
    )

    # ── Test Case 4: Edge case — error handling ──
    await run_agent("What is 100 divided by 0?")


# =============================================================================
# Main
# =============================================================================
async def main():
    print()
    print("─" * 60)
    print("  OCI Enterprise AI Agents — Agents SDK Version")
    print("  (Based on LangChain 02_first_agent.py)")
    print("─" * 60)
    print()
    print(f"  Endpoint : {OCI_BASE_URL}")
    print(f"  Model    : {MODEL}")
    print(f"  SDK      : OpenAI Agents SDK")
    print()

    # Example 1: Simple chat
    await simple_chat_example()

    # Example 2: Math agent
    await math_agent_example()

    print("─" * 60)
    print("  Done! Compare this file with the other two approaches:")
    print("─" * 60)
    print()
    print("  ┌───────────────────────┬──────────────────────────────────┐")
    print("  │ File                  │ Approach                         │")
    print("  ├───────────────────────┼──────────────────────────────────┤")
    print("  │ 02_first_agent.py     │ LangChain  (@tool + create_agent)│")
    print("  │ oci_first_agent.py    │ Manual     (JSON + while loop)   │")
    print("  │ oci_first_agent_sdk.py│ Agents SDK (@function_tool)      │")
    print("  └───────────────────────┴──────────────────────────────────┘")
    print()


if __name__ == "__main__":
    asyncio.run(main())

