import os
from uuid import uuid4
import langsmith
from langchain import smith
from langchain.smith import RunEvalConfig

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.chains import RetrievalQA

from LoadProperties import LoadProperties

#In this demo we evaluate the model using the dataset we created

properties = LoadProperties()

unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = properties.getlangChainEndpoint()
os.environ["LANGCHAIN_API_KEY"] = properties.getLangChainKey() # Update to your API ke


#In this demo we will create a dataset for model evaluation.

#Step 1 - create models

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":400}
)

embeddings = OCIGenAIEmbeddings(
    model_id=properties.getEmbeddingModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
)

# Step 2 - here we load the index and create a retriever that gets relevant documents (similar in meaning to a query)

db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)

retv = db.as_retriever(search_kwargs={"k": 8})

#Step 3 - crate chain


chain = RetrievalQA.from_chain_type(llm=llm, retriever=retv)

# Step 4 - Define the evaluators to apply
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

# Step 5 - evaluate model

chain_results = client.run_on_dataset(
    dataset_name="AIFoundationsDS-111",
    llm_or_chain_factory=chain,
    evaluation=eval_config,
    concurrency_level=5,
    verbose=True,
)
