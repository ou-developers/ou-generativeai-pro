from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS

from langchain_community.llms import OCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings

#In this demo we will explore using RetirvalQA chain to retrieve relevant documents and send these as a context in a query.
# We will use FASSS vectorstore.

#Step 1 - setup OCI Generative AI llm

# use default authN method API-key
llm = OCIGenAI(
    model_id="cohere.command-light",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="<<your compartment id>>",
    model_kwargs={"max_tokens":100}
)

#Step 2 - here we crete embeddings using 'cohere.embed-english-light-v2.0" model.

embeddings = OCIGenAIEmbeddings(
    model_id="cohere.embed-english-v3.0",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="compartment_id="<<your compartment id>>",
)

#Step 4 - here we load the index and create a retriever that gets relevant documents (similar in meaning to a query)

db = FAISS.load_local("faiss_index", embeddings)

#retv = db.as_retriever(search_kwargs={"k": 3})

retv = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

#Step 5 - here we can explore how similar documents to the query are returned by prining the document metadata. This step is optional

docs = retv.get_relevant_documents('Tell us which module is most relevant to LLMs and Generative AI')

def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)]
        )
    )

pretty_print_docs(docs)

for doc in docs:
    print(doc.metadata)


#Step 6 - here we create a retrieval chain that takes llm , retirever objects and invoke it to get a response to our query

chain = RetrievalQA.from_chain_type(llm=llm, retriever=retv,return_source_documents=True)

response = chain.invoke("Tell us which module is relevant to LLMs and Generative AI")

print(response)



