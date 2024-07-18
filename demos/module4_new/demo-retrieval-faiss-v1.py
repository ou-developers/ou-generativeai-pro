from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS

from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage

from LoadProperties import LoadProperties

#In this demo we will explore using RetirvalQA chain to retrieve relevant documents and send these as a context in a query.
# We will use FASSS vectorstore.

#Step 1 - setup OCI Generative AI llm

properties = LoadProperties()

# use default authN method
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":200}
)

#Step 2 - here we crete embeddings using 'cohere.embed-english-light-v2.0" model.

embeddings = OCIGenAIEmbeddings(
    model_id=properties.getEmbeddingModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
)

#Step 3 - here we load the index and create a retriever that gets relevant documents (similar in meaning to a query)

db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

#retv = db.as_retriever(search_kwargs={"k": 3})

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

docs1 = []

for doc in docs:
    #print(doc)
    docs1.append({"snippet": doc.page_content})
    #print(docs1)


#Step 4 - here we create a retrieval chain that takes llm , retirever objects and invoke it to get a response to our query

chain = RetrievalQA.from_chain_type(llm=llm, retriever=retv,return_source_documents=True)

response = chain.invoke("Tell us which module is relevant to LLMs and Generative AI")

# ChatOCIGenAI supports documents, following code passes the documents directly to ChatOCIGenAI directly.
#messages = [HumanMessage(content="Tell us which module of AI Foundations course is relevant to Transformers")]
#response = llm.invoke(messages,documents=docs1)

print(response)


