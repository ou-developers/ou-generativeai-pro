"""
==========================================================
LangChain for AI Agents — Companion Code
==========================================================
Lesson 1: Core Building Blocks
  - Models, Prompts, Chains, Output Parsers, Memory, Tools

Demo order (matches the lessons):
  Lesson 1 → Models, Prompts, Chains, Memory
  Lesson 2 → Tools

Prerequisites:
  pip install langchain langchain-openai python-dotenv

Setup:
  Create a .env file with: OPENAI_API_KEY=sk-your-key-here
==========================================================
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file sitting next to THIS script (not wherever we ran from).
# Path(__file__) = this file; .parent = its folder. This makes the key load
# correctly no matter which directory you launch python from.
script_dir = Path(__file__).resolve().parent
env_path = script_dir / ".env"

#print("Current working directory:", os.getcwd())
#print("Script directory:", script_dir)
#print("Using .env from:", env_path)

load_dotenv(dotenv_path=env_path)

# Quick sanity check that the key actually loaded before we call the model.
print("OPENAI_API_KEY found:", bool(os.getenv("OPENAI_API_KEY")))

# ─────────────────────────────────────────────
# 1. MODELS — The Reasoning Engine
# ─────────────────────────────────────────────
# The "model" is the LLM itself — the part that actually thinks.
# init_chat_model gives ONE interface to every provider: to switch from
# OpenAI to Anthropic or Google, you change only the string below.

from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.5")
# model = init_chat_model("anthropic:claude-3-5-sonnet-latest")
# model = init_chat_model("google_genai:gemini-2.0-flash")

# The simplest possible use: send text in, get an answer back.
# .invoke() is the universal "run it" method across LangChain.
response = model.invoke("What is LangChain in one sentence?")
print("=== Model Response ===")
print(response.content)   # .content = just the text of the reply
print()

# ─────────────────────────────────────────────
# 2. PROMPT TEMPLATES — Steering the Model
# ─────────────────────────────────────────────
# A prompt template is a reusable sentence with blanks ({placeholders})
# you fill in later — write the wording once, reuse it many times.

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# PromptTemplate = a single plain-text string with blanks.
simple_template = PromptTemplate(
    input_variables=["topic"],
    template="Explain {topic} to a complete beginner in 2-3 sentences."
)

# .format() fills the blank and returns the finished text.
formatted = simple_template.format(topic="AI agents")
print("=== Formatted Prompt ===")
print(formatted)
print()

# ChatPromptTemplate = built from ROLES (system / human), which is how chat
# models expect their input. "system" sets behavior, "human" is the user turn.
chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful coding tutor. Keep answers short and clear."),
    ("human", "Explain {concept} with a simple Python example."),
])

# .format_messages() fills the blanks and returns a LIST of messages.
messages = chat_template.format_messages(concept="list comprehension")
# {concept} in the template is the empty blank, and concept="list comprehension" is you handing it the word that goes in the blank.
print("=== Chat Messages ===")
for msg in messages:
    print(f"  [{msg.type}]: {msg.content[:80]}...")
print()

# ─────────────────────────────────────────────
# 3. CHAINS — Connecting the Pieces with LCEL
# ─────────────────────────────────────────────
# The pipe | glues components into a pipeline. Each step's output flows
# into the next, left to right:  prompt | model | parser.

from langchain_core.output_parsers import StrOutputParser

# prompt fills the blanks → model answers → parser pulls out clean text.
# StrOutputParser just extracts the plain string from the model's reply
# object, so you don't have to write .content yourself every time.
chain = chat_template | model | StrOutputParser()

# Run the whole pipeline with a single .invoke().
result = chain.invoke({"concept": "for loops"})
print("=== Chain Output ===")
print(result)
print()

# ─────────────────────────────────────────────
# 4. MEMORY — Giving the Model Context
# ─────────────────────────────────────────────
# Models are stateless — they forget everything between calls.
# "Memory" is simply us storing past messages and feeding them back in.
# (Modern LangChain uses ChatMessageHistory; the old
#  ConversationBufferMemory is deprecated and out of the core package.)

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# A simple in-memory store that holds the conversation.
memory = InMemoryChatMessageHistory()

# Hand-build a short conversation so we have something to "remember".
memory.add_message(HumanMessage(content="My name is Alex and I'm learning LangChain"))
memory.add_message(AIMessage(content="Nice to meet you, Alex! LangChain is a great choice."))
memory.add_message(HumanMessage(content="What tools should I learn first?"))
memory.add_message(AIMessage(content="Start with PromptTemplates and simple chains, then move to tools and agents."))

print("=== Memory Contents ===")
for msg in memory.messages:
    print(f"  [{msg.type}]: {msg.content[:80]}...")
print()

# The "placeholder" slot is where the stored messages get injected into the
# prompt, so the model can SEE the earlier conversation.
chat_with_memory = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful tutor. Use the conversation history to personalize your responses."),
    ("placeholder", "{history}"),   # past messages get dropped in here
    ("human", "{question}"),
])

chain_with_memory = chat_with_memory | model | StrOutputParser()

# We pass the stored history in alongside the new question.
# Watch the model correctly recall the name "Alex" — that's "memory".
result = chain_with_memory.invoke({
    "history": memory.messages,
    "question": "What was my name again?"
})
print("=== Memory-Aware Response ===")
print(result)
print()

# ─────────────────────────────────────────────
# 5. TOOLS — Giving the Model Abilities   (Lesson 2)
# ─────────────────────────────────────────────
# A tool is just a normal Python function the model is ALLOWED to call.
# The @tool decorator exposes it; the model reads the function's name,
# docstring, and type hints to decide WHEN and HOW to use it.

from langchain_core.tools import tool

@tool
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """Calculate Body Mass Index (BMI) given weight in kg and height in meters."""
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal weight"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"
    return f"BMI: {bmi:.1f} ({category})"

@tool
def get_word_count(text: str) -> int:
    """Count the number of words in a given text string."""
    return len(text.split())

# This is exactly what the model "sees" about a tool — the same info it
# uses to decide whether the tool fits the question.
#print("=== Tool Info ===")
#print(f"Name: {calculate_bmi.name}")
#print(f"Description: {calculate_bmi.description}")
#print(f"Args: {calculate_bmi.args}")
#print()

# bind_tools tells the model "these tools are available to you."
model_with_tools = model.bind_tools([calculate_bmi, get_word_count])

# IMPORTANT (say this out loud): the model only *requests* a tool call —
# it does NOT run the tool. It hands back which tool to call and with what
# arguments. Actually executing the tool and looping the result back is the
# AGENT's job.
response = model_with_tools.invoke("What's the BMI for someone who is 70kg and 1.75m tall?")
#print("=== Tool Call Response ===")
#print(f"Tool calls: {response.tool_calls}")
#print()

print("✅ All core concepts demonstrated! Next: first_agent.py")
