"""
Module 06: Multi-Agent Systems with Handoffs
===============================================
Build a team of specialized agents that route questions
to the right expert. The triage agent decides who handles what.
"""
from dotenv import load_dotenv

load_dotenv()
from agents import Agent, Runner

# ──────────────────────────────────────────────
# Step 1: Define specialist agents
# ──────────────────────────────────────────────
# Each specialist is good at one thing.
# handoff_description helps the triage agent know WHEN to delegate.

math_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist for math questions, calculations, and equations.",
    instructions="""You are an expert math tutor.
    Explain math step by step with worked examples.
    Use simple language that beginners can understand.""",
)

history_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist for history questions and historical events.",
    instructions="""You are an expert history tutor.
    Answer history questions with key facts and context.
    Include interesting stories to make history come alive.""",
)

science_agent = Agent(
    name="Science Tutor",
    handoff_description="Specialist for science questions (physics, chemistry, biology).",
    instructions="""You are an expert science tutor.
    Explain scientific concepts with real-world examples.
    Break down complex topics into simple steps.""",
)

# ──────────────────────────────────────────────
# Step 2: Define the triage agent
# ──────────────────────────────────────────────
# The triage agent routes questions to the right specialist.
# It has handoffs to all three specialists.

triage_agent = Agent(
    name="Triage Agent",
    instructions="""You are a helpful homework assistant.
    Your job is to route each question to the right specialist tutor.
    - Math questions → Math Tutor
    - History questions → History Tutor  
    - Science questions → Science Tutor
    If a question doesn't fit any category, do your best to answer it yourself.""",
    handoffs=[math_agent, history_agent, science_agent],
)

# ──────────────────────────────────────────────
# Step 3: Test with different questions
# ──────────────────────────────────────────────
questions = [
    "What is 15% of 240?",
    "Who built the Great Wall of China and why?",
    "How does photosynthesis work?",
    "What is the quadratic formula?",
]

for question in questions:
    print(f"Question: {question}")
    result = Runner.run_sync(triage_agent, question)
    print(f"Answer: {result.final_output}")
    print(f"Answered by: {result.last_agent.name}")
    print("-" * 60)
    print()

print("✅ Multi-agent handoff system working!")
print()
print("KEY CONCEPTS:")
print("  - handoff_description tells the triage agent when to delegate")
print("  - handoffs=[...] lists all agents that can receive handoffs")
print("  - result.last_agent.name shows which agent actually answered")
print("  - The specialist takes over the full conversation")
