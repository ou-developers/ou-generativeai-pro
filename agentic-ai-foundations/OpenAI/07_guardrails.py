"""
Module 07: Guardrails — Keeping Your Agents Safe
===================================================
Guardrails validate input and output to prevent your agent
from going off-topic or producing unsafe responses.
"""

import asyncio
from agents import (
    Agent,
    Runner,
    InputGuardrail,
    GuardrailFunctionOutput,
    input_guardrail,
)
from pydantic import BaseModel


# ──────────────────────────────────────────────
# Step 1: Define the guardrail's output structure
# ──────────────────────────────────────────────
class TopicCheck(BaseModel):
    """Structured output for the guardrail checker."""
    is_on_topic: bool
    reasoning: str


# ──────────────────────────────────────────────
# Step 2: Create a small "checker" agent
# ──────────────────────────────────────────────
# This agent's ONLY job is to check if the input
# is a valid science question.
topic_checker = Agent(
    name="Topic Checker",
    instructions="""Determine if the user's message is a science question 
    (physics, chemistry, biology, astronomy, etc.).
    
    Return is_on_topic=True ONLY for science-related questions.
    Return is_on_topic=False for everything else (math, history, 
    general chat, off-topic requests, etc.).""",
    output_type=TopicCheck,
    model="gpt-4.1-mini",  # Use a fast, cheap model for guardrails!
)


# ──────────────────────────────────────────────
# Step 3: Define the guardrail function
# ──────────────────────────────────────────────
@input_guardrail
async def science_only_guardrail(ctx, agent, input):
    """Only allow science questions through."""
    result = await Runner.run(topic_checker, input, context=ctx.context)
    final = result.final_output_as(TopicCheck)
    
    return GuardrailFunctionOutput(
        output_info={"reasoning": final.reasoning},
        tripwire_triggered=not final.is_on_topic,  # Block if NOT science
    )


# ──────────────────────────────────────────────
# Step 4: Create the main agent WITH the guardrail
# ──────────────────────────────────────────────
science_agent = Agent(
    name="Science Tutor",
    instructions="""You are an expert science tutor.
    Explain scientific concepts clearly with real-world examples.""",
    input_guardrails=[science_only_guardrail],  # <-- Attach guardrail!
)


# ──────────────────────────────────────────────
# Step 5: Test it!
# ──────────────────────────────────────────────
async def main():
    # This should PASS the guardrail (it's a science question)
    print("--- Test 1: Science question (should work) ---")
    try:
        result = await Runner.run(science_agent, "How does gravity work?")
        print(f"✅ Answer: {result.final_output}")
    except Exception as e:
        print(f"❌ Blocked: {e}")
    print()

    # This should FAIL the guardrail (it's a math question)
    print("--- Test 2: Math question (should be blocked) ---")
    try:
        result = await Runner.run(science_agent, "What is 15 * 23?")
        print(f"✅ Answer: {result.final_output}")
    except Exception as e:
        print(f"❌ Blocked! The guardrail prevented this off-topic question.")
        print(f"   Error type: {type(e).__name__}")
    print()

    # This should also FAIL (general chat)
    print("--- Test 3: General chat (should be blocked) ---")
    try:
        result = await Runner.run(science_agent, "Tell me a joke.")
        print(f"✅ Answer: {result.final_output}")
    except Exception as e:
        print(f"❌ Blocked! The guardrail prevented this off-topic request.")
    print()

    print("KEY CONCEPTS:")
    print("  - Guardrails use a small 'checker' agent to validate input")
    print("  - If the check fails, tripwire_triggered=True stops the main agent")
    print("  - Use a fast, cheap model (gpt-4.1-mini) for guardrail checks")
    print("  - You can have multiple guardrails on the same agent")


if __name__ == "__main__":
    asyncio.run(main())
