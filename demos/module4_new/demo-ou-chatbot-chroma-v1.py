from fastapi import FastAPI, Form
import chromadb
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import json
#from langchain_community.llms import OCIGenAI
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from LoadProperties import LoadProperties

#In this demo we will explore using RetirvalQA chain to retrieve relevant documents and send these as a context in a query.
# We will use Chroma vectorstore.

#Step 1 - authenticate using "DEFAULT" profile

properties = LoadProperties()

#Step 2 - this will set up chain , to be called later

def create_chain():
    client = chromadb.HttpClient(host="127.0.0.1",settings=Settings(allow_reset=True))
    embeddings = OCIGenAIEmbeddings(
    model_id=properties.getEmbeddingModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    )
    db = Chroma(client=client, embedding_function=embeddings)
    retv = db.as_retriever(serach_type="mmr", search_kwargs={"k": 5})

    llm = ChatOCIGenAI(
        model_id=properties.getModelName(),
        service_endpoint=properties.getEndpoint(),
        compartment_id=properties.getCompartment(),
        model_kwargs={"max_tokens":200}
        )
    memory = ConversationBufferMemory(llm=llm, memory_key="chat_history", return_messages=True)
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=retv,memory=memory)
    return qa

#Step 3 - create chain, here we create a ConversationalRetrievalChain.

chain = create_chain()

#Step 4 - here we declare a chat function
def chat(user_message: str = Form(...)):
    # generate a prediction for a prompt
    bot_json = chain.invoke({"question": user_message})
    return {"bot_response": bot_json}

#Step 5 - here we setup Streamlit text input and pass input text to chat function.
# chat function returns the response and we print it.

if __name__ == "__main__":
    import streamlit as st
    st.title("Oracle University Chatbot")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    user_input = st.chat_input()
    if user_input:
        bot_response = chat(user_input)
        st.session_state.messages.append({"role" : "chatbot", "content" : bot_response})
        #st.write("OU Assistant Response: ", bot_response)
        for message in st.session_state.messages:
            st.chat_message("user")
            st.write("Question: ", message['content']['bot_response']['question'])
            st.chat_message("assistant")
            st.write("Answer: ", message['content']['bot_response']['answer'])
