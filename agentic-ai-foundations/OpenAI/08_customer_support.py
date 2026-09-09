"""
Lesson 07: Complete Project — Customer Support Agent System
=============================================================
This brings together EVERYTHING from the course:
  - Multiple agents with handoffs 
  - Custom function tools 
  - Input guardrails 
  - Hosted tools — WebSearchTool 
  - Structured output with Pydantic

Architecture:
  User → Triage Agent → Order Status Agent (with lookup_order tool)
                       → Refund Agent (with process_refund tool)
                       → FAQ Agent (with web search)
"""
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()
import asyncio
from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    function_tool,
    InputGuardrail,
    GuardrailFunctionOutput,
    input_guardrail,
    WebSearchTool,
)


# ══════════════════════════════════════════════
# PART 1: Define Custom Tools
# ══════════════════════════════════════════════

# Simulated order database
ORDERS_DB = {
    "ORD-001": {"item": "Wireless Headphones", "status": "Shipped", "eta": "March 22"},
    "ORD-002": {"item": "Python Programming Book", "status": "Delivered", "eta": "March 18"},
    "ORD-003": {"item": "USB-C Cable 3-pack", "status": "Processing", "eta": "March 25"},
}


@function_tool
def lookup_order(order_id: str) -> str:
    """Look up the status of a customer order by order ID (e.g., ORD-001)."""
    order = ORDERS_DB.get(order_id.upper())
    if order:
        return (
            f"Order {order_id.upper()}:\n"
            f"  Item: {order['item']}\n"
            f"  Status: {order['status']}\n"
            f"  Estimated Arrival: {order['eta']}"
        )
    return f"Order {order_id} not found. Please check the order ID and try again."


@function_tool
def process_refund(order_id: str, reason: str) -> str:
    """Process a refund request for a given order ID with a reason."""
    order = ORDERS_DB.get(order_id.upper())
    if not order:
        return f"Cannot process refund: Order {order_id} not found."
    if order["status"] == "Processing":
        return f"Refund for {order_id} cannot be processed — order hasn't shipped yet. It can be cancelled instead."
    return (
        f"✅ Refund initiated for Order {order_id.upper()}\n"
        f"  Item: {order['item']}\n"
        f"  Reason: {reason}\n"
        f"  Refund amount will be credited within 5-7 business days."
    )


# ══════════════════════════════════════════════
# PART 2: Define the Guardrail
# ══════════════════════════════════════════════

class SupportCheck(BaseModel):
    is_support_question: bool
    reasoning: str


guardrail_checker = Agent(
    name="Support Topic Checker",
    instructions="""Determine if the user's message is a customer support question.
    Valid topics: order status, refunds, returns, product questions, shipping, FAQs.
    Invalid topics: personal advice, jokes, coding help, unrelated conversations.
    Return is_support_question=True ONLY for customer support topics.""",
    output_type=SupportCheck,
    model="gpt-5.5",
)


@input_guardrail
async def support_only(ctx, agent, input):
    """Only allow customer support questions."""
    result = await Runner.run(guardrail_checker, input, context=ctx.context)
    final = result.final_output_as(SupportCheck)
    return GuardrailFunctionOutput(
        output_info={"reasoning": final.reasoning},
        tripwire_triggered=not final.is_support_question,
    )


# ══════════════════════════════════════════════
# PART 3: Define Specialist Agents
# ══════════════════════════════════════════════

order_agent = Agent(
    name="Order_Status_Agent",
    handoff_description="Handles questions about order status, shipping, and delivery.",
    instructions="""You help customers check their order status.
    Use the lookup_order tool to find order information.
    If the customer doesn't provide an order ID, ask for it.
    Be friendly and professional.""",
    tools=[lookup_order],
)

refund_agent = Agent(
    name="Refund_Agent",
    handoff_description="Handles refund requests, returns, and cancellations.",
    instructions="""You help customers with refunds and returns.
    Use the process_refund tool to initiate refunds.
    Always ask for the order ID and reason before processing.
    Be empathetic and helpful.""",
    tools=[process_refund],
)

faq_agent = Agent(
    name="FAQ_Agent",
    handoff_description="Handles general product questions and frequently asked questions.",
    instructions="""You answer general customer questions and FAQs.
    Use web search when you need current information.
    Common topics: shipping policies, return windows, product details.
    Be helpful and concise.""",
    tools=[WebSearchTool()],
)


# ══════════════════════════════════════════════
# PART 4: Define the Triage Agent
# ══════════════════════════════════════════════

triage_agent = Agent(
    name="Customer_Support_Triage",
    instructions="""You are the front-line customer support agent.
    Your job is to understand the customer's issue and route them
    to the right specialist:
    
    - Order status, shipping, delivery questions → Order Status Agent
    - Refund requests, returns, cancellations → Refund Agent
    - General questions, product info, FAQs → FAQ Agent
    
    Be warm, professional, and route quickly.""",
    handoffs=[order_agent, refund_agent, faq_agent],
    input_guardrails=[support_only],  # Block off-topic questions!
)


# ══════════════════════════════════════════════
# PART 5: Run the System!
# ══════════════════════════════════════════════

async def handle_customer(message: str):
    """Process a customer message through the support system."""
    print(f"🧑 Customer: {message}")
    try:
        result = await Runner.run(triage_agent, message)
        print(f"🤖 {result.last_agent.name}: {result.final_output}")
    except Exception as e:
        print(f"🚫 Blocked: This doesn't appear to be a support question.")
    print("=" * 70)
    print()


async def main():
    print("=" * 70)
    print("  CUSTOMER SUPPORT AGENT SYSTEM — DEMO")
    print("=" * 70)
    print()

    # Test 1: Order status (→ Order Status Agent → lookup_order tool)
    await handle_customer("Where is my order ORD-001?")
    
    # Test 2: Refund request (→ Refund Agent → process_refund tool)
    await handle_customer("I want a refund for order ORD-002. The book arrived damaged.")

    # Test 3: General FAQ (→ FAQ Agent → web search)
    await handle_customer("What is Amazon return policy?")

    # Test 4: Off-topic (→ BLOCKED by guardrail)
    await handle_customer("Can you help me write a poem about cats?")

    print()
    print("🎉 Course Complete! You've built a full customer support agent system.")
    print()
    print("WHAT THIS PROJECT USED:")
    print("  ✓ Multiple agents with handoffs (triage → specialists)")
    print("  ✓ Custom function tools (lookup_order, process_refund)")
    print("  ✓ Input guardrails (support_only blocks off-topic)")
    print("  ✓ Hosted tools (WebSearchTool for FAQs)")
    print("  ✓ Structured output (SupportCheck for guardrail)")
    print()
    print("NEXT STEPS:")
    print("  → Add more specialist agents (billing, technical support)")
    print("  → Connect to a real database instead of mock data")
    print("  → Add output guardrails to check response quality")
    print("  → View your traces at: platform.openai.com → Traces")


if __name__ == "__main__":
    asyncio.run(main())
