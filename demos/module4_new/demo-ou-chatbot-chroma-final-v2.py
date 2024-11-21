import chromadb
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.document_compressors import CohereRerank
import json
#from langchain_community.llms import OCIGenAI
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from LoadProperties import LoadProperties

#In this demo we will explore using RetirvalQA chain to retrieve relevant documents and send these as a context in a query.
# We will use Chroma vectorstore.

#Step 1 - this will set up chain , to be called later

def create_chain():
    properties = LoadProperties()
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
    memory = ConversationBufferMemory(llm=llm, memory_key="chat_history", return_messages=True, output_key='answer')
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=retv, memory=memory, return_source_documents=True)
    return qa

#Step 2 - create chain, here we create a ConversationalRetrievalChain.

chain = create_chain()

#Step 3 - here we declare a chat function
def chat(llm_chain, user_input):
    # generate a prediction for a prompt
    bot_json = llm_chain.invoke(user_input)
    print("bot json is ->", bot_json )
    return {"bot_response": bot_json}

#Step 4 - here we setup Streamlit text input and pass input text to chat function.
# chat function returns the response and we print it.

if __name__ == "__main__":
    import streamlit as st

    st.subheader("Chatbot that answers your study questions")
    col1 , col2 = st.columns([4,1])

    def initialize_session_state():
        if "llm_chain" not in st.session_state:
            st.session_state["llm_chain"] = create_chain()
            llm_chain = st.session_state["llm_chain"]
        else:
            llm_chain = st.session_state["llm_chain"]
        return llm_chain

    user_input = st.chat_input()
    with col1:
        col1.subheader("------Ask me a question about science chapters------")
        #col2.subheader("References")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if user_input:
            llm_chain = initialize_session_state()
            bot_response = chat(llm_chain, user_input)
            print("bot_response->\n", bot_response)
            st.session_state.messages.append({"role" : "chatbot", "content" : bot_response})
            #st.write("OU Assistant Response: ", bot_response)
            for message in st.session_state.messages:
                st.chat_message("user")
                st.write("Question: ", message['content']['bot_response']['question'])
                st.chat_message("assistant")
                st.write("Answer: ", message['content']['bot_response']['answer'])
            #with col2:
                st.chat_message("assistant")
                for doc in message['content']['bot_response']['source_documents']:
                    st.write("Reference: ", doc.metadata['source'] + "  \n"+ "-page->"+str(doc.metadata['page']))

                    #st.write("Reference: ", doc.metadata['source'] + "  \n"+ "-page->"+str(doc.metadata['page']) +
                    #             "  \n"+ "-relevance score->"+ str(doc.metadata['relevance_score'])
                    #    )
