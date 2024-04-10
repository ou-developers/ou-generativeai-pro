import os
from uuid import uuid4
import langsmith
from langchain import smith
from langchain.smith import RunEvalConfig

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain.chains import RetrievalQA

unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "<<your langchain key>>>"  # Update to your API ke

from langchain_community.llms import OCIGenAI

#In this demo we will create a dataset for model evaluation.

# use default authN method API-key
llm = OCIGenAI(
    model_id="cohere.command",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="<<your compartment id>>",
    model_kwargs={"max_tokens":400}
)

embeddings = OCIGenAIEmbeddings(
    model_id="cohere.embed-english-v3.0",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="<<your compartment id>>",
)

# Step 4 - here we load the index and create a retriever that gets relevant documents (similar in meaning to a query)

db = FAISS.load_local("faiss_index", embeddings)

retv = db.as_retriever(search_kwargs={"k": 8})


chain = RetrievalQA.from_chain_type(llm=llm, retriever=retv)

# Define the evaluators to apply
#Default criteria are implemented for the following aspects: conciseness, relevance,
# correctness, coherence, harmfulness, maliciousness, helpfulness, controversiality, misogyny, and criminality.

eval_config = smith.RunEvalConfig(
    evaluators=[
        "cot_qa",
         RunEvalConfig.Criteria("relevance"),
    ],
    custom_evaluators=[],
    eval_llm=llm
)

client = langsmith.Client()

chain_results = client.run_on_dataset(
    dataset_name="AIFoundationsDS-111",
    llm_or_chain_factory=chain,
    evaluation=eval_config,
    concurrency_level=5,
    verbose=True,
)
