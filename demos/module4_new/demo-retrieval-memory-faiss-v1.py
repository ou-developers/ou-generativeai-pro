from langchain.chains import RetrievalQA
from langchain.schema import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
import oci
from LoadProperties import LoadProperties

#In this demo we will explore using RetirvalQA chain to retrieve relevant documents and send these as a context in a query.
#We will useFASSS vectorstore.

# Step 1 - authenticate using "DEFAULT" profile

properties = LoadProperties()

# Step 2 - setup OCI Generative AI llm

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens": 100}
)

# Step 3 - here we crete embeddings using 'cohere.embed-english-light-v2.0" model.

embeddings = OCIGenAIEmbeddings(
    model_id=properties.getEmbeddingModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
)

# Step 4 - here we load the index and create a retriever that gets relevant documents (similar in meaning to a query)

db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

retv = db.as_retriever(search_kwargs={"k": 8})


# Step 5 - here we can explore how similar documents to the query are returned by prining the document metadata. This step is optional

docs = retv.invoke('Module 5: Generative AI and LLM Foundations')

print(docs)

for doc in docs:
    print(doc.metadata)

# Step 6 - here we create a memory to remember chat messages.

memory = ConversationBufferMemory(llm=llm, memory_key="chat_history", return_messages=True)

# Step 7 - here we create a chain that uses llm, retriever and memory.

# You can also define the chain type as one of the four options: “stuff”, “map reduce”, “refine”, “map_rerank”.

qa = ConversationalRetrievalChain.from_llm(llm, retriever=retv, memory=memory)

# Step 8 - we ask question 1 and print relevant document's metadata and chat messages.
docs = retv.invoke("How many modules are there in AI Foundations Course ")
print(len(docs))

for doc in docs:
    print(doc.metadata)

qa.invoke({"question": "Tell us about oracle cloud ai foundations Module 5"})
print(memory.chat_memory.messages)

# Step 8 - we ask question 2 and print relevant document's metadata and chat messages.
docs = retv.invoke("Tell us more about oracle cloud multicloud federation")
print(len(docs))

for doc in docs:
    print(doc.metadata)

qa.invoke({"question": "Tell us more about oracle cloud multicloud federation"})
print(memory.chat_memory.messages)
