import os
from uuid import uuid4
from langsmith import Client
from LoadProperties import LoadProperties

#In this demo we create dataset for model evaluation

properties = LoadProperties()

unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = properties.getlangChainEndpoint()
os.environ["LANGCHAIN_API_KEY"] = properties.getLangChainKey()  # Update to your API key

# create dataset for evaluation
dataset_inputs = [
  "Tell us about Oracle Cloud Infrastructure AI Foundations Course and Certification",
  "Tell us which module in this course is relevant to Deep Learning.",
  "Tell us about which module is relevant to LLMs and Transformers",
  "Tell me about instructors of this course"
  # ... add more as desired
]

# Outputs are provided to the evaluator, so it knows what to compare to
# Outputs are optional but recommended.
dataset_outputs = [
    {"must_mention": ["AI", "LLM"]},
    {"must_mention": ["CNN", "Neural Network"]},
    {"must_mention": ["Module 5", "Transformer", "LLM"]},
    {"must_mention": ["Hemant", "Himanshu", "Nick"]}
]

client = Client()
dataset_name = "AIFoundationsDS-112"

# Storing inputs in a dataset lets us
# run chains and LLMs over a shared set of examples.
dataset = client.create_dataset(
    dataset_name=dataset_name,
    description="AI Foundations QA.",
)
client.create_examples(
    inputs=[{"question": q} for q in dataset_inputs],
    outputs=dataset_outputs,
    dataset_id=dataset.id,
)
