from langchain.chains import RetrievalQA
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from LoadProperties import LoadProperties

#In this demo we will retrieve documents and send these as a context to the LLM.

#Step 1 - setup OCI Generative AI llm

properties = LoadProperties()

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":100}
)

#Step 2 - here we connect to a chromadb server. we need to run the chromadb server before we connect to it

client = chromadb.HttpClient(host="127.0.0.1")

#Step 3 - here we crete embeddings using 'cohere.embed-english-light-v2.0" model.

embeddings = OCIGenAIEmbeddings(
    model_id=properties.getEmbeddingModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
)

#Step 4 - here we create a retriever that gets relevant documents (similar in meaning to a query)

db = Chroma(client=client, embedding_function=embeddings)

retv = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

#Step 5 - here we can explore how similar documents to the query are returned by prining the document metadata. This step is optional

docs = retv.invoke('Tell us which module is most relevant to LLMs and Generative AI')

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

response = chain.invoke("Tell us which module is most relevant to LLMs and Generative AI")

print(response)


